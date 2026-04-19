"""
Job Operations Router — /job-ops
Handles batch resume tailoring, URL scraping, and ZIP export.

Endpoints:
  POST /job-ops/scrape-url          → Fetch JD from a job posting URL
  POST /job-ops/tailor-batch        → Batch-tailor one resume for N jobs → returns results + run_ids
  GET  /job-ops/batch/{batch_id}/download → Download ZIP of all DOCXs in a batch
"""

import json
import io
import zipfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db import get_db
from models import User
from services.auth_service import get_current_active_user
from services.job_scraper_service import fetch_job_description, scrape_multiple_jobs
from services.parse_service import parse_via_tika
from services.score_service import ATSScoreEngine, ats_format_score, extract_keywords
from services.embed_service import embed, cosine_sim
from services.openai_service import openai_generate
from services.tailor_service import process_and_save_run
from schemas import BatchJobInput, BatchTailorResult
from utils import render_prompt, safe_filename, build_resume_filename
from config import settings

router = APIRouter(prefix="/job-ops", tags=["Job Operations"])

DATA_DIR = Path(__file__).resolve().parent.parent / "_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# 1. URL Scraper
# ─────────────────────────────────────────────

@router.post("/scrape-url")
async def scrape_job_url(
    url: str = Form(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Fetch and extract job description text from a URL.
    Returns the extracted text so the frontend can populate the JD field.
    """
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL. Must start with http or https.")

    result = await fetch_job_description(url)

    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail=result.get("error") or "Could not extract job description from this URL."
        )

    return {
        "url": url,
        "title": result.get("title", ""),
        "jd_text": result["text"],
        "char_count": len(result["text"])
    }


@router.post("/scrape-urls-bulk")
async def scrape_multiple_urls(
    urls_json: str = Form(...),   # JSON array of URL strings
    current_user: User = Depends(get_current_active_user)
):
    """
    Scrape multiple job URLs at once. Returns list of results.
    """
    try:
        urls = json.loads(urls_json)
        if not isinstance(urls, list):
            raise ValueError("Expected JSON array")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid urls_json: {e}")

    if len(urls) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 URLs per batch request.")

    results = await scrape_multiple_jobs(urls)

    return [
        {
            "url": url,
            "title": r.get("title", ""),
            "jd_text": r.get("text", ""),
            "success": r.get("success", False),
            "error": r.get("error"),
            "char_count": len(r.get("text", ""))
        }
        for url, r in zip(urls, results)
    ]


# ─────────────────────────────────────────────
# 2. Batch Tailor (N jobs × 1 resume)
# ─────────────────────────────────────────────

@router.post("/tailor-batch", response_model=List[BatchTailorResult])
async def tailor_batch(
    resume_file: UploadFile = File(...),
    jobs_json: str = Form(...),        # JSON array of {job_title, company, jd_text, job_url?}
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
    Generate a tailored resume for EACH job description provided.

    Accepts:
      - resume_file: the candidate's base resume (PDF/DOCX)
      - jobs_json: JSON array of job objects
        [
          {
            "job_title": "Senior Software Engineer",
            "company": "Google",
            "jd_text": "...",          ← provide text OR url (or both)
            "job_url": "https://..."   ← optional: scrape if jd_text is empty
          },
          ...
        ]
      - username: used in file naming (<username>_<job-title>_resume.docx)

    Returns list of results with run_id and filename for each job.
    """
    api_key = (
        x_openai_key
        if x_openai_key and x_openai_key not in ["null", "undefined", ""]
        else settings.openai_api_key
    )

    # Parse resume
    file_bytes = await resume_file.read()
    resume_text = await parse_via_tika(file_bytes, resume_file.filename)
    if len(resume_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not parse resume text.")

    # Parse job list
    try:
        raw_jobs = json.loads(jobs_json)
        jobs = [BatchJobInput(**j) for j in raw_jobs]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid jobs_json: {e}")

    if not jobs:
        raise HTTPException(status_code=400, detail="No jobs provided.")
    if len(jobs) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 jobs per batch.")

    # Auto-extract contact info if not supplied
    if not (full_name.strip() and email.strip()):
        try:
            from services.ai_keyword_service import extract_contact_info_with_ai
            contact = await extract_contact_info_with_ai(api_key, settings.openai_model, resume_text)
            full_name = full_name or contact.get("full_name", "")
            email = email or contact.get("email", "")
            phone = phone or contact.get("phone", "")
            linkedin = linkedin or contact.get("linkedin", "")
            location = location or contact.get("location", "")
            portfolio = portfolio or contact.get("portfolio", "")
        except Exception:
            pass

    results: List[BatchTailorResult] = []

    for job in jobs:
        jd_text = job.jd_text.strip()

        # If JD text is empty but URL is provided, scrape it
        if not jd_text and job.job_url:
            try:
                scraped = await fetch_job_description(job.job_url)
                if scraped["success"]:
                    jd_text = scraped["text"]
                    # Auto-fill job title from page title if not provided
                    if not job.job_title and scraped.get("title"):
                        job.job_title = scraped["title"]
            except Exception as scrape_err:
                results.append(BatchTailorResult(
                    job_title=job.job_title or job.job_url or "Unknown",
                    company=job.company,
                    run_id=-1,
                    filename="",
                    total_score=0.0,
                    missing_keywords=[],
                    status="error",
                    error=f"URL scraping failed: {scrape_err}"
                ))
                continue

        if not jd_text:
            results.append(BatchTailorResult(
                job_title=job.job_title,
                company=job.company,
                run_id=-1,
                filename="",
                total_score=0.0,
                missing_keywords=[],
                status="error",
                error="No job description text available (empty text and no valid URL)."
            ))
            continue

        try:
            # ── AI Keyword Extraction ──────────────────────
            ai_result = {}
            try:
                from services.ai_keyword_service import extract_keywords_with_ai
                ai_result = await extract_keywords_with_ai(api_key, settings.openai_model, jd_text)
            except Exception:
                pass

            keywords = ai_result.get("keywords", extract_keywords(jd_text))
            ai_responsibilities = ai_result.get("responsibilities", [])

            # ── Scoring ───────────────────────────────────
            categorized_input = (
                ai_result.get("categories", {"core_tech": keywords})
                if ai_result else {"core_tech": keywords}
            )
            score_result = ATSScoreEngine.calculate_weighted_score(resume_text, categorized_input)
            kw_score = score_result["total_score"]

            all_kws = []
            for klist in categorized_input.values():
                all_kws.extend(klist)
            matched_kws = [m["keyword"] for m in score_result["matched_details"]]
            missing = list(set(all_kws) - set(matched_kws))

            try:
                embs = await embed([jd_text[:2000], resume_text[:2000]])
                sem_score = cosine_sim(embs[0], embs[1])
            except Exception:
                sem_score = 0.0

            ats_score = ats_format_score(resume_text)
            total = round((0.85 * kw_score) + (0.10 * sem_score * 100) + (0.05 * ats_score * 100), 1)

            # ── Build Prompt ─────────────────────────────
            responsibilities_text = (
                "\n".join([f"- {r}" for r in ai_responsibilities[:10]])
                if ai_responsibilities else "N/A"
            )

            missing_text = ", ".join(missing[:50])
            if ai_result and "categories" in ai_result:
                cats = ai_result["categories"]
                lines = []
                order = ["core_tech", "frameworks", "architecture", "cloud",
                         "databases", "tools", "domain", "soft_skills"]
                for cat in order:
                    kws = cats.get(cat, [])
                    relevant = [k for k in kws if k in missing]
                    if relevant:
                        lines.append(f"**{cat.replace('_', ' ').title()}**: {', '.join(relevant)}")
                if lines:
                    missing_text = "\n".join(lines)

            prompt = render_prompt(
                "prompts/tailor_resume.txt",
                JD_TEXT=jd_text,
                RESUME_TEXT=resume_text,
                MISSING_KEYWORDS=missing_text,
                RESPONSIBILITIES=responsibilities_text
            )

            # ── Generate ──────────────────────────────────
            full_text = await openai_generate(api_key, settings.openai_model, prompt)

            ctx = {
                "full_name": full_name, "location": location, "phone": phone,
                "email": email, "linkedin": linkedin, "portfolio": portfolio,
                "job_title": job.job_title, "company": job.company,
                "jd_text": jd_text, "resume_text": resume_text,
                "kw_score": kw_score, "sem_score": sem_score,
                "ats_score": ats_score, "total": total, "missing": missing
            }
            run = process_and_save_run(db, full_text, ctx)

            # ── Rename DOCX to <username>_<job-title>_resume.docx ──
            filename = build_resume_filename(username, job.job_title, "docx")
            base = f"run_{run.id}_{safe_filename(run.job_title or 'role')}"
            src_docx = DATA_DIR / f"{base}.docx"
            dest_docx = DATA_DIR / filename

            if src_docx.exists():
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


# ─────────────────────────────────────────────
# 3. Batch ZIP Download
# ─────────────────────────────────────────────

@router.post("/download-batch-zip")
async def download_batch_zip(
    filenames_json: str = Form(...),  # JSON array of filenames
    current_user: User = Depends(get_current_active_user)
):
    """
    Bundle multiple generated DOCX files into a single ZIP for download.
    Accepts a JSON array of filenames (as returned by /job-ops/tailor-batch).
    """
    try:
        filenames: list[str] = json.loads(filenames_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid filenames_json: {e}")

    if not filenames:
        raise HTTPException(status_code=400, detail="No filenames provided.")

    # Build ZIP in memory
    zip_buffer = io.BytesIO()
    added = 0

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname in filenames:
            # Sanitize — prevent path traversal
            safe_name = safe_filename(fname.replace(".docx", "")) + ".docx"
            fpath = DATA_DIR / safe_name

            if fpath.exists():
                zf.write(fpath, arcname=safe_name)
                added += 1

    if added == 0:
        raise HTTPException(
            status_code=404,
            detail="None of the requested files were found. They may have expired."
        )

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=tailored_resumes.zip"
        }
    )


# ─────────────────────────────────────────────
# 4. Single Run DOCX by filename
# ─────────────────────────────────────────────

@router.get("/download/{filename}")
async def download_named_file(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download a specific named DOCX file generated by the batch process."""
    from fastapi.responses import FileResponse

    # Sanitize filename
    safe_name = safe_filename(filename.replace(".docx", "")) + ".docx"
    fpath = DATA_DIR / safe_name

    if not fpath.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {safe_name}")

    return FileResponse(
        fpath,
        filename=safe_name,
        content_disposition_type="attachment"
    )
