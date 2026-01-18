import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from db import get_db, engine, Base
from models import TailorRun
from schemas import TailorResponse, AnalyzeResponse, RunUpdateRequest
from services.score_service import extract_keywords, keyword_coverage_score, ats_format_score, top_requirements
from services.embed_service import embed, cosine_sim
from services.openai_service import openai_generate, openai_stream
from services.render_service import render_md, render_html
from services.export_service import html_to_pdf
from services.tailor_service import process_and_save_run, extract_section, update_run_text
from utils import render_prompt, safe_filename
from config import settings
from services.parse_service import parse_via_tika

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Startup DB Error (non-fatal): {e}")
    yield

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Resume AI Tailor (SaaS Core)", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("/app/_data")
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
):
    file_bytes = await resume_file.read()
    # No Tika URL needed anymore
    resume_text = await parse_via_tika(file_bytes, resume_file.filename)
    
    if len(resume_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not parse resume text.")

    # Use AI to extract intelligent keywords and responsibilities
    ai_keywords = []
    ai_responsibilities = []
    try:
        from services.ai_keyword_service import extract_keywords_with_ai
        ai_result = await extract_keywords_with_ai(settings.openai_api_key, settings.openai_model, jd_text)
        ai_keywords = ai_result.get("keywords", [])
        ai_responsibilities = ai_result.get("responsibilities", [])
    except Exception as e:
        print(f"AI keyword extraction failed: {e}")
    
    # Fallback to basic extraction only if AI completely fails
    keywords = ai_keywords if ai_keywords else extract_keywords(jd_text)
    kw_score, missing, matched = keyword_coverage_score(resume_text, keywords)
    ats_score = ats_format_score(resume_text)

    try:
        # No embeddings URL needed
        embs = await embed([jd_text[:2000], resume_text[:2000]])
        sem_score = cosine_sim(embs[0], embs[1])
    except Exception as e:
        print(f"Embedding failed: {e}")
        sem_score = 0.0

    total = round(0.45 * kw_score + 0.45 * sem_score + 0.10 * ats_score, 4)

    # Include AI-extracted responsibilities in the prompt
    responsibilities_text = "\n".join([f"- {r}" for r in ai_responsibilities[:10]]) if ai_responsibilities else "N/A"
    
    prompt = render_prompt(
        "prompts/tailor_resume.txt",
        JD_TEXT=jd_text,
        RESUME_TEXT=resume_text,
        MISSING_KEYWORDS=", ".join(missing[:30]),
        RESPONSIBILITIES=responsibilities_text
    )

    async def generate_and_save():
        full_text = ""
        try:
            gen = openai_stream(settings.openai_api_key, settings.openai_model, prompt)

            async for chunk in gen:
                full_text += chunk
                yield chunk

            ctx = {
                "full_name": full_name, "location": location, "phone": phone, "email": email,
                "linkedin": linkedin, "portfolio": portfolio, "job_title": job_title, "company": company,
                "jd_text": jd_text, "resume_text": resume_text, "kw_score": kw_score, "sem_score": sem_score,
                "ats_score": ats_score, "total": total, "missing": missing
            }
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
):
    file_bytes = await resume_file.read()
    # No Tika URL needed
    resume_text = await parse_via_tika(file_bytes, resume_file.filename)

    keywords = extract_keywords(jd_text)
    kw_score, missing, matched = keyword_coverage_score(resume_text, keywords)
    ats_score = ats_format_score(resume_text)

    try:
        # No embeddings URL needed
        embs = await embed([jd_text[:2000], resume_text[:2000]])
        sem_score = cosine_sim(embs[0], embs[1])
    except Exception as e:
        print(f"Embedding failed: {e}")
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
    
    update_run_text(db, run, req.tailored_text)
    return {"status": "success"}

@app.get("/runs/{run_id}/download/{fmt}")
async def download_run(run_id: int, fmt: str, name: str = "", mode: str = "attachment", db: Session = Depends(get_db)):
    run = db.query(TailorRun).filter(TailorRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Determine filename
    if name:
        filename = f"{safe_filename(name)}.{fmt}"
    else:
        base = safe_filename(run.full_name or "Tailored")
        filename = f"{base}_Resume.{fmt}"

    base_name = f"run_{run.id}_{safe_filename(run.job_title or 'role')}"
    
    if fmt == "txt":
        path = DATA_DIR / f"{base_name}.txt"
        if not path.exists(): path.write_text(run.tailored_text)
        return FileResponse(path, filename=filename, content_disposition_type=mode)
    
    elif fmt == "md":
        path = DATA_DIR / f"{base_name}.md"
        if not path.exists(): path.write_text(run.tailored_md)
        return FileResponse(path, filename=filename, content_disposition_type=mode)
    
    elif fmt == "pdf":
        path = DATA_DIR / f"{base_name}.pdf"
        # Always re-gen PDF (Gotenberg removed)
        pdf_bytes = await html_to_pdf(run.tailored_html)
        path.write_bytes(pdf_bytes)
        return FileResponse(path, filename=filename, content_disposition_type=mode)
    
    raise HTTPException(status_code=400, detail="Invalid format")
