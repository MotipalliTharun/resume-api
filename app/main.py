import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Header
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from db import get_db, engine, Base
from models import TailorRun
from schemas import TailorResponse, AnalyzeResponse, RunUpdateRequest, BatchJobInput, BatchTailorResult
from services.score_service import extract_keywords, keyword_coverage_score, ats_format_score, top_requirements
from services.embed_service import embed, cosine_sim
from services.openai_service import openai_generate, openai_stream
from services.render_service import render_md, render_html
from services.export_service import create_resume_docx
from services.tailor_service import process_and_save_run, extract_section, update_run_text
from utils import render_prompt, safe_filename, build_resume_filename
from config import settings
from services.parse_service import parse_via_tika
from models import CoverLetter, User
from services.auth_service import get_current_active_user
from routers import auth, subscription, payment, job_ops

# ...


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        
        # Auto-migration for existing tables
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("users")]
            with engine.connect() as conn:
                if "reset_token" not in columns:
                    print("Migrating: Adding reset_token")
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR(256)"))
                if "reset_token_expires" not in columns:
                    print("Migrating: Adding reset_token_expires")
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires TIMESTAMP WITH TIME ZONE"))
                if "google_id" not in columns:
                    print("Migrating: Adding google_id")
                    conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(256)"))
                if "stripe_customer_id" not in columns:
                    print("Migrating: Adding stripe_customer_id")
                    conn.execute(text("ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(256)"))
                    conn.execute(text("CREATE INDEX ix_users_stripe_customer_id ON users (stripe_customer_id)"))
                
                # Auto-authorize all users per user request
                # Auto-authorize all users per user request
                print("Setting all users to active and 'pro' tier...")
                conn.execute(text("UPDATE users SET is_active = 1, subscription_tier = 'pro'"))
                conn.commit()
    except Exception as e:
        print(f"Startup DB Error (non-fatal): {e}")
    yield

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CluesStack.io (SaaS Core)", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(subscription.router)
app.include_router(payment.router)
app.include_router(job_ops.router)

# Determine DATA_DIR relative to this file
DATA_DIR = Path(__file__).resolve().parent / "_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok", "engine": "openai-native"}

@app.post("/tailor-stream")
async def tailor_stream_endpoint(
    jd_text: str = Form(...),
    resume_file: UploadFile = File(...),
    job_title: str = Form(""),
    company: str = Form(""),
    full_name: str = Form(""),
    location: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    linkedin: str = Form(""),
    portfolio: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    x_openai_key: str | None = Header(None, alias="X-OpenAI-Key")
):
    api_key = x_openai_key if x_openai_key and x_openai_key not in ["null", "undefined", ""] else settings.openai_api_key
    file_bytes = await resume_file.read()
    # No Tika URL needed anymore
    resume_text = await parse_via_tika(file_bytes, resume_file.filename)
    
    if len(resume_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not parse resume text.")

    # ... rest of the function remains similar but simplified context ...

    # Use AI to extract intelligent keywords and responsibilities
    ai_keywords = []
    ai_responsibilities = []
    try:
        from services.ai_keyword_service import extract_keywords_with_ai
        ai_result = await extract_keywords_with_ai(api_key, settings.openai_model, jd_text)
        ai_keywords = ai_result.get("keywords", [])
        ai_responsibilities = ai_result.get("responsibilities", [])
    except Exception as e:
        print(f"AI keyword extraction failed: {e}")
        ai_result = {} 

    # If any critical contact info is missing, try to extract it from resume via AI
    if not (full_name.strip() and email.strip() and phone.strip()):
        try:
            from services.ai_keyword_service import extract_contact_info_with_ai
            print("Extracting contact info via AI (filling gaps)...")
            contact_info = await extract_contact_info_with_ai(api_key, settings.openai_model, resume_text)
            
            full_name = full_name or contact_info.get("full_name", "")
            email = email or contact_info.get("email", "")
            phone = phone or contact_info.get("phone", "")
            linkedin = linkedin or contact_info.get("linkedin", "")
            location = location or contact_info.get("location", "")
            portfolio = portfolio or contact_info.get("portfolio", "")
        except Exception as e:
            print(f"Contact extraction failed: {e}")

    # Fallback to basic extraction
    keywords = ai_keywords if ai_keywords else extract_keywords(jd_text)
    
    # --- WEIGHTED ATS SCORING ---
    from services.score_service import ATSScoreEngine
    
    kw_score = 0.0
    sem_score = 0.0
    ats_score = 0.0
    
    try:
        categorized_input = ai_result.get("categories", {"core_tech": keywords}) if ai_result else {"core_tech": keywords}
        score_result = ATSScoreEngine.calculate_weighted_score(resume_text, categorized_input)
        kw_score = score_result["total_score"]
        
        all_kws = []
        for klist in categorized_input.values(): all_kws.extend(klist)
        matched_kws = [m["keyword"] for m in score_result["matched_details"]]
        missing = list(set(all_kws) - set(matched_kws))
        matched = matched_kws

    except Exception as e:
        print(f"ATS Scoring Failed: {e}")
        kw_score = 50.0 
        missing = []
        matched = []

    try:
        ats_score = ats_format_score(resume_text)
    except: ats_score = 0.5

    try:
        embs = await embed([jd_text[:2000], resume_text[:2000]])
        sem_score = cosine_sim(embs[0], embs[1])
    except Exception as e:
        sem_score = 0.0

    final_keyword_score = float(kw_score)
    final_semantic = float(sem_score * 100)
    final_format = float(ats_score * 100)

    # Weighted scoring: keyword coverage dominates (ATS is primarily keyword matching)
    # Targets: keyword ≥ 92, semantic ≥ 80, format ≥ 90 → total ≥ 96
    total = round(
        (0.85 * final_keyword_score) +
        (0.10 * final_semantic) +
        (0.05 * final_format),
        1
    )

    responsibilities_text = "\n".join([f"- {r}" for r in ai_responsibilities[:10]]) if ai_responsibilities else "N/A"
    
    input_missing_text = ", ".join(missing[:50])
    
    if ai_result and "categories" in ai_result:
        cats = ai_result["categories"]
        lines = []
        order = ["core_tech", "frameworks", "architecture", "cloud", "databases", "tools", "domain", "soft_skills"]
        for cat in order:
            kws = cats.get(cat, [])
            relevant = [k for k in kws if k in missing]
            if relevant:
                lines.append(f"**{cat.replace('_', ' ').title()}**: {', '.join(relevant)}")
        if lines:
            input_missing_text = "\n".join(lines)

    # Build ALL JD keywords list (not just missing) so the prompt can maximize coverage
    all_jd_keywords_text = ""
    if ai_result and "categories" in ai_result:
        cats = ai_result["categories"]
        all_lines = []
        order = ["core_tech", "frameworks", "architecture", "cloud", "databases", "tools", "domain", "soft_skills"]
        for cat in order:
            kws = cats.get(cat, [])
            if kws:
                all_lines.append(f"**{cat.replace('_', ' ').title()}**: {', '.join(kws)}")
        all_jd_keywords_text = "\n".join(all_lines)

    prompt = render_prompt(
        "prompts/tailor_resume.txt",
        JD_TEXT=jd_text,
        RESUME_TEXT=resume_text,
        MISSING_KEYWORDS=input_missing_text,
        RESPONSIBILITIES=responsibilities_text
    )

    async def generate_and_save():
        full_text = ""
        try:
            gen = openai_stream(api_key, settings.openai_model, prompt)

            async for chunk in gen:
                full_text += chunk
                yield chunk
            
            ctx = {
                "full_name": full_name, "location": location, "phone": phone, "email": email,
                "linkedin": linkedin, "portfolio": portfolio, "job_title": job_title, "company": company,
                "jd_text": jd_text, "resume_text": resume_text, "kw_score": kw_score, "sem_score": sem_score,
                "ats_score": ats_score, "total": total, "missing": missing
            }
            # Note: process_and_save_run assumes anonymous user for now, but we can update it later to link user_id
            run = process_and_save_run(db, full_text, ctx)

            meta = {
                "run_id": run.id,
                "scores": {
                    "keyword_score": round(kw_score, 4),
                    "semantic_score": round(sem_score, 4),
                    "ats_score": round(ats_score, 4),
                    "total_score": total,
                    "missing_keywords": missing[:30],
                    "matched_keywords": matched[:30]
                }
            }
            yield f"\n\n---METADATA---\n{json.dumps(meta)}"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"\n\n[STREAM_ERROR: {str(e)}]"

    return StreamingResponse(
        generate_and_save(), 
        media_type="text/plain",
        headers={"X-Accel-Buffering": "no"}
    )

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    jd_text: str = Form(...),
    resume_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    x_openai_key: str | None = Header(None, alias="X-OpenAI-Key")
):
    file_bytes = await resume_file.read()
    resume_text = await parse_via_tika(file_bytes, resume_file.filename)

    keywords = extract_keywords(jd_text)
    kw_score, missing, matched = keyword_coverage_score(resume_text, keywords)
    ats_score = ats_format_score(resume_text)

    try:
        embs = await embed([jd_text[:2000], resume_text[:2000]])
        sem_score = cosine_sim(embs[0], embs[1])
    except Exception as e:
        sem_score = 0.0

    total = round(0.45 * kw_score + 0.45 * sem_score + 0.10 * ats_score, 4)
    reqs = top_requirements(jd_text)

    return AnalyzeResponse(
        scores={
            "keyword_score": round(kw_score, 4),
            "semantic_score": round(sem_score, 4),
            "ats_score": round(ats_score, 4),
            "total_score": total,
            "missing_keywords": missing[:30],
            "matched_keywords": matched[:30]
        },
        extracted_keywords=keywords[:30],
        jd_top_requirements=reqs[:5]
    )

@app.get("/runs")
def list_runs(db: Session = Depends(get_db)):
    runs = db.query(TailorRun).order_by(TailorRun.created_at.desc()).all()
    return [{"id": r.id, "job_title": r.job_title, "company": r.company, "created_at": r.created_at} for r in runs]

@app.get("/runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(TailorRun).filter(TailorRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {
        "id": run.id,
        "full_name": run.full_name,
        "jd_text": run.jd_text,
        "tailored_text": run.tailored_text,
        "scores": {
            "keyword_score": run.score_keyword,
            "semantic_score": run.score_semantic,
            "ats_score": run.score_ats,
            "total_score": run.score_total,
            "missing_keywords": run.missing_keywords.split(",") if run.missing_keywords else [],
            "matched_keywords": []
        },
        "resume_text": run.resume_text
    }

@app.patch("/runs/{run_id}")
def patch_run(run_id: int, req: RunUpdateRequest, db: Session = Depends(get_db)):
    run = db.query(TailorRun).filter(TailorRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        update_run_text(db, run, req.tailored_text)
        return {"status": "success"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@app.get("/runs/{run_id}/download/{fmt}")
async def download_run(run_id: int, fmt: str, name: str = "", mode: str = "attachment", db: Session = Depends(get_db)):
    run = db.query(TailorRun).filter(TailorRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Determine filename using standardized convention
    if name:
        clean_name = safe_filename(name)
        suffix = f".{fmt}".lower()
        while clean_name.lower().endswith(suffix):
            clean_name = clean_name[:-len(suffix)]
        filename = f"{clean_name}.{fmt}"
    else:
        # Use: <username>_<job-title-slug>_resume.<fmt>
        username_slug = safe_filename((run.full_name or "candidate").lower().replace(" ", "_"))
        filename = build_resume_filename(username_slug, run.job_title or "resume", fmt)

    base_name = f"run_{run.id}_{safe_filename(run.job_title or 'role')}"
    
    if fmt == "txt":
        path = DATA_DIR / f"{base_name}.txt"
        if not path.exists(): path.write_text(run.tailored_text)
        return FileResponse(path, filename=filename, content_disposition_type=mode)
    
    elif fmt == "md":
        path = DATA_DIR / f"{base_name}.md"
        if not path.exists(): path.write_text(run.tailored_md)
        return FileResponse(path, filename=filename, content_disposition_type=mode)
    
    elif fmt == "docx":
        path = DATA_DIR / f"{base_name}.docx"
        
        # 1. Serve existing file if available (Fastest & Safest)
        if path.exists():
             return FileResponse(path, filename=filename, content_disposition_type=mode)

        # 2. Fallback: Re-generate from stored text if file is missing
        try:
            from services.tailor_service import extract_section
            
            data = {
                "full_name": run.full_name,
                "location": "", 
                "phone": "",    
                "email": "",    
                "linkedin": "", 
                "portfolio": "",
                "summary": extract_section(run.tailored_text, "SUMMARY"),
                "skills_block": extract_section(run.tailored_text, "SKILLS"),
                "experience_block": extract_section(run.tailored_text, "WORK EXPERIENCE"),
                "projects_block": extract_section(run.tailored_text, "PROJECTS"),
                "education_block": extract_section(run.tailored_text, "EDUCATION"),
                "certifications_block": extract_section(run.tailored_text, "CERTIFICATIONS"),
                "achievements_block": extract_section(run.tailored_text, "ACHIEVEMENTS"),
                "volunteer_block": extract_section(run.tailored_text, "VOLUNTEER"),
            }
            
            create_resume_docx(data, str(path))
            return FileResponse(path, filename=filename, content_disposition_type=mode)
            
        except Exception as e:
            print(f"Failed to regenerate DOCX: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate DOCX: {str(e)}")

    elif fmt == "pdf":
        path = DATA_DIR / f"{base_name}.pdf"
        docx_path = DATA_DIR / f"{base_name}.docx"
        
        # 1. Serve existing
        if path.exists():
            return FileResponse(path, filename=filename, content_disposition_type=mode)
            
        # 2. Try to generate from DOCX if DOCX exists
        if docx_path.exists():
            from services.export_service import convert_docx_to_pdf
            new_pdf = convert_docx_to_pdf(str(docx_path))
            if new_pdf and Path(new_pdf).exists():
                 return FileResponse(Path(new_pdf), filename=filename, content_disposition_type=mode)
        
        # 3. If DOCX missing, try to generate DOCX then PDF (Deep Fallback)
        try:
            # We need to trigger the DOCX generation logic first
            # Reuse the DOCX block logic somewhat or call a helper. 
            # For simplicity, let's just error if DOCX is missing for now OR 
            # we can copy the regeneration logic. Let's do a simple check.
             raise HTTPException(status_code=404, detail="PDF not found and could not be generated (DOCX missing or conversion failed).")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    raise HTTPException(status_code=400, detail="Invalid format")

# --- Batch Tailoring Endpoint ---

@app.post("/tailor-batch", response_model=List[BatchTailorResult])
async def tailor_batch_endpoint(
    resume_file: UploadFile = File(...),
    jobs_json: str = Form(...),           # JSON array of BatchJobInput objects
    username: str = Form("candidate"),
    full_name: str = Form(""),
    location: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    linkedin: str = Form(""),
    portfolio: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    x_openai_key: str | None = Header(None, alias="X-OpenAI-Key")
):
    """
    Batch-tailor one base resume against multiple job descriptions.
    Generates a uniquely named DOCX for each job.
    File naming: <username>_<job-title-slug>_resume.docx
    """
    import json as _json
    api_key = x_openai_key if x_openai_key and x_openai_key not in ["null", "undefined", ""] else settings.openai_api_key
    file_bytes = await resume_file.read()
    resume_text = await parse_via_tika(file_bytes, resume_file.filename)

    if len(resume_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not parse resume text.")

    # Parse job list
    try:
        raw_jobs = _json.loads(jobs_json)
        jobs = [BatchJobInput(**j) for j in raw_jobs]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid jobs_json: {e}")

    if not jobs:
        raise HTTPException(status_code=400, detail="No jobs provided.")

    # Extract contact info if not supplied
    if not (full_name.strip() and email.strip()):
        try:
            from services.ai_keyword_service import extract_contact_info_with_ai
            contact_info = await extract_contact_info_with_ai(api_key, settings.openai_model, resume_text)
            full_name = full_name or contact_info.get("full_name", "")
            email = email or contact_info.get("email", "")
            phone = phone or contact_info.get("phone", "")
            linkedin = linkedin or contact_info.get("linkedin", "")
            location = location or contact_info.get("location", "")
            portfolio = portfolio or contact_info.get("portfolio", "")
        except Exception:
            pass

    results: List[BatchTailorResult] = []

    for job in jobs:
        try:
            # Extract keywords for this JD
            ai_result = {}
            try:
                from services.ai_keyword_service import extract_keywords_with_ai
                ai_result = await extract_keywords_with_ai(api_key, settings.openai_model, job.jd_text)
            except Exception:
                pass

            keywords = ai_result.get("keywords", extract_keywords(job.jd_text))
            ai_responsibilities = ai_result.get("responsibilities", [])

            # Score base resume against JD
            from services.score_service import ATSScoreEngine
            categorized_input = ai_result.get("categories", {"core_tech": keywords}) if ai_result else {"core_tech": keywords}
            score_result = ATSScoreEngine.calculate_weighted_score(resume_text, categorized_input)
            kw_score = score_result["total_score"]

            all_kws = []
            for klist in categorized_input.values():
                all_kws.extend(klist)
            matched_kws = [m["keyword"] for m in score_result["matched_details"]]
            missing = list(set(all_kws) - set(matched_kws))

            try:
                embs = await embed([job.jd_text[:2000], resume_text[:2000]])
                sem_score = cosine_sim(embs[0], embs[1])
            except Exception:
                sem_score = 0.0

            ats_score = ats_format_score(resume_text)

            total = round((0.85 * kw_score) + (0.10 * sem_score * 100) + (0.05 * ats_score * 100), 1)

            # Build prompt
            responsibilities_text = "\n".join([f"- {r}" for r in ai_responsibilities[:10]]) if ai_responsibilities else "N/A"
            missing_text = ", ".join(missing[:50])
            if ai_result and "categories" in ai_result:
                cats = ai_result["categories"]
                lines = []
                for cat in ["core_tech", "frameworks", "architecture", "cloud", "databases", "tools", "domain", "soft_skills"]:
                    kws = cats.get(cat, [])
                    relevant = [k for k in kws if k in missing]
                    if relevant:
                        lines.append(f"**{cat.replace('_', ' ').title()}**: {', '.join(relevant)}")
                if lines:
                    missing_text = "\n".join(lines)

            prompt = render_prompt(
                "prompts/tailor_resume.txt",
                JD_TEXT=job.jd_text,
                RESUME_TEXT=resume_text,
                MISSING_KEYWORDS=missing_text,
                RESPONSIBILITIES=responsibilities_text
            )

            # Generate tailored text (non-streaming for batch)
            full_text = await openai_generate(api_key, settings.openai_model, prompt)

            ctx = {
                "full_name": full_name, "location": location, "phone": phone, "email": email,
                "linkedin": linkedin, "portfolio": portfolio,
                "job_title": job.job_title, "company": job.company,
                "jd_text": job.jd_text, "resume_text": resume_text,
                "kw_score": kw_score, "sem_score": sem_score,
                "ats_score": ats_score, "total": total, "missing": missing
            }
            run = process_and_save_run(db, full_text, ctx)

            # Rename DOCX to username convention
            filename = build_resume_filename(username, job.job_title, "docx")
            base = f"run_{run.id}_{safe_filename(run.job_title or 'role')}"
            src_docx = DATA_DIR / f"{base}.docx"
            dest_docx = DATA_DIR / filename
            if src_docx.exists() and src_docx != dest_docx:
                import shutil
                shutil.copy2(str(src_docx), str(dest_docx))

            results.append(BatchTailorResult(
                job_title=job.job_title,
                company=job.company,
                run_id=run.id,
                filename=filename,
                total_score=total,
                missing_keywords=missing[:20],
                status="success"
            ))

        except Exception as e:
            import traceback
            traceback.print_exc()
            results.append(BatchTailorResult(
                job_title=job.job_title,
                company=job.company,
                run_id=-1,
                filename="",
                total_score=0.0,
                missing_keywords=[],
                status="error",
                error=str(e)
            ))

    return results

# --- Cover Letter Endpoints ---

@app.post("/cover-letter-stream")
async def cover_letter_stream_endpoint(
    jd_text: str = Form(...),
    resume_file: UploadFile = File(...),
    job_title: str = Form(""),
    company: str = Form(""),
    full_name: str = Form(""),
    location: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    linkedin: str = Form(""),
    portfolio: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    x_openai_key: str | None = Header(None, alias="X-OpenAI-Key")
):
    api_key = x_openai_key if x_openai_key and x_openai_key not in ["null", "undefined", ""] else settings.openai_api_key
    file_bytes = await resume_file.read()
    resume_text = await parse_via_tika(file_bytes, resume_file.filename)
    
    if len(resume_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not parse resume text.")

    # Contact Info Extractions (Reuse existing logic or trust form inputs)
    # Ideally should share extraction logic, but for speed, we stick to form inputs + basic extraction if needed.
    
    prompt = render_prompt(
        "prompts/generate_cover_letter.txt",
        JD_TEXT=jd_text,
        RESUME_TEXT=resume_text
    )

    async def generate_and_save():
        full_text = ""
        try:
            # Reusing openai_stream logic
            gen = openai_stream(api_key, settings.openai_model, prompt)

            async for chunk in gen:
                full_text += chunk
                yield chunk

            # Save logic
            from services.tailor_service import process_and_save_cover_letter
            ctx = {
                "full_name": full_name, "location": location, "phone": phone, "email": email,
                "linkedin": linkedin, "portfolio": portfolio, "job_title": job_title, "company": company,
                "jd_text": jd_text, "resume_text": resume_text
            }
            cl = process_and_save_cover_letter(db, full_text, ctx)
            
            # Yield metadata at end so frontend knows ID
            yield f"\n\n---METADATA---\n{json.dumps({'cl_id': cl.id})}"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"\n\n[STREAM_ERROR: {str(e)}]"

    return StreamingResponse(
        generate_and_save(), 
        media_type="text/plain",
        headers={"X-Accel-Buffering": "no"}
    )

@app.get("/cover-letters")
def list_cover_letters(db: Session = Depends(get_db)):
    # Limit to last 20
    cls = db.query(CoverLetter).order_by(CoverLetter.created_at.desc()).limit(20).all()
    return [{"id": c.id, "company": c.company, "created_at": c.created_at} for c in cls]

@app.get("/cover-letters/{cl_id}/download/{fmt}")
async def download_cover_letter_file(cl_id: int, fmt: str, mode: str = "attachment", db: Session = Depends(get_db)):
    cl = db.query(CoverLetter).filter(CoverLetter.id == cl_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail="Cover Letter not found")

    # Filename: {Full Name}_CoverLetter.pdf
    safe_name = safe_filename(cl.full_name or "Candidate")
    # Clean any potential accidental extension in the name (though less likely here as we construct it)
    suffix = f".{fmt}".lower()
    while safe_name.lower().endswith(suffix):
        safe_name = safe_name[:-len(suffix)]
    
    filename = f"{safe_name}_CoverLetter.{fmt}"
    
    base_name = f"cl_{cl.id}_{safe_filename(cl.company or 'company')}"
    
    if fmt == "txt":
        path = DATA_DIR / f"{base_name}.txt"
        if not path.exists(): path.write_text(cl.cover_letter_text)
        return FileResponse(path, filename=filename, content_disposition_type=mode)
    elif fmt == "docx":
        path = DATA_DIR / f"{base_name}.docx"
        # Cover letters use a different simple generator or just text dump.
        # In tailor_service we used specific code for it.
        # If file missing, fail.
        if not path.exists():
             raise HTTPException(status_code=404, detail="DOCX artifact not found.")
        return FileResponse(path, filename=filename, content_disposition_type=mode)
    
    elif fmt == "pdf":
        path = DATA_DIR / f"{base_name}.pdf"
        docx_path = DATA_DIR / f"{base_name}.docx"
        
        if path.exists():
            return FileResponse(path, filename=filename, content_disposition_type=mode)
        
        if docx_path.exists():
             from services.export_service import convert_docx_to_pdf
             new_pdf = convert_docx_to_pdf(str(docx_path))
             if new_pdf and Path(new_pdf).exists():
                 return FileResponse(Path(new_pdf), filename=filename, content_disposition_type=mode)
        
        raise HTTPException(status_code=404, detail="PDF not found.")

    raise HTTPException(status_code=400, detail="Invalid format")
