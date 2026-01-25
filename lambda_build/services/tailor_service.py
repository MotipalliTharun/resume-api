import json
from pathlib import Path
from sqlalchemy.orm import Session
from models import TailorRun
from services.render_service import render_md, render_html
from utils import safe_filename

# Determine DATA_DIR relative to this file
# This file is in app/services/, so parent.parent is app/
import os
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    DATA_DIR = Path("/tmp")
else:
    DATA_DIR = Path(__file__).resolve().parent.parent / "_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def extract_section(full_text: str, heading: str) -> str:
    lines = full_text.splitlines()
    # Normalize heading for match (strip markdown chars like *, #)
    h_norm = heading.strip().upper().replace("*", "").replace("#", "")
    
    start = None
    for i, ln in enumerate(lines):
        ln_norm = ln.strip().upper().replace("*", "").replace("#", "")
        if ln_norm == h_norm:
            start = i + 1
            break
            
    if start is None:
        return ""
        
    end = len(lines)
    for j in range(start, len(lines)):
        s = lines[j].strip()
        # End of section heuristic: another potential header
        if s and s.upper() == s and len(s.replace("*", "")) <= 30:
            # Check if this looks like another header
            s_norm = s.replace("*", "").replace("#", "").strip()
            # If it's a known header or looks like one, stop
            if s_norm in ["SUMMARY", "SKILLS", "WORK EXPERIENCE", "EDUCATION", "PROJECTS", "CERTIFICATIONS", "ACHIEVEMENTS", "VOLUNTEER", "PERSONAL DETAILS"]:
                end = j
                break
    return "\n".join(lines[start:end]).strip()

def process_and_save_run(
    db: Session,
    full_text: str,
    run_context: dict
) -> TailorRun:
    """
    Common logic to parse AI output, render templates, save to DB, and write files.
    """
    first_line = full_text.splitlines()[0] if full_text.splitlines() else ""
    
    # --- PROGRAMMATIC KEYWORD NORMALIZATION ---
    # Enforce JD terminology (ReactJS vs React, AWS vs aws)
    try:
        from services.keyword_normalization_service import KeywordStandardizer
        jd = run_context.get("jd_text", "")
        full_text = KeywordStandardizer.normalize_text(full_text, jd)
    except Exception as e:
        print(f"Normalization Error (non-fatal): {e}")
    # ------------------------------------------

    data = {
        "full_name": run_context.get("full_name") or "YOUR NAME",
        "location": run_context.get("location") or "",
        "phone": run_context.get("phone") or "",
        "email": run_context.get("email") or "",
        "linkedin": run_context.get("linkedin") or "",
        "portfolio": run_context.get("portfolio") or "",
        "summary": extract_section(full_text, "SUMMARY"),
        "skills_block": extract_section(full_text, "SKILLS"),
        "experience_block": extract_section(full_text, "WORK EXPERIENCE"),
        "projects_block": extract_section(full_text, "PROJECTS"), 
        "certifications_block": extract_section(full_text, "CERTIFICATIONS"),
        "achievements_block": extract_section(full_text, "ACHIEVEMENTS"), 
        "volunteer_block": extract_section(full_text, "VOLUNTEER"),
        "education_block": extract_section(full_text, "EDUCATION"),
    }

    tailored_md = render_md("templates/ats_resume.md", data)
    tailored_html = render_html("templates/ats_resume.html", data)

    run = TailorRun(
        job_title=run_context.get("job_title", ""),
        company=run_context.get("company", ""),
        full_name=run_context.get("full_name", ""),
        jd_text=run_context.get("jd_text", ""),
        resume_text=run_context.get("resume_text", ""),
        score_keyword=float(run_context.get("kw_score", 0)),
        score_semantic=float(run_context.get("sem_score", 0)),
        score_ats=float(run_context.get("ats_score", 0)),
        score_total=float(run_context.get("total", 0)),
        missing_keywords=",".join(run_context.get("missing", [])[:60]),
        tailored_text=full_text,
        tailored_md=tailored_md,
        tailored_html=tailored_html,
    )
    
    db.add(run)
    db.commit()
    db.refresh(run)

    # Artifacts are no longer saved to disk eagerly to save space.
    # They will be generated on-the-fly if requested via download endpoints.
    
    return run

def update_run_text(db: Session, run: TailorRun, new_text: str):
    """
    Updates the run's tailored text and re-renders MD/HTML artifacts.
    """
    # Extract data using existing sections or keep original contact info
    data = {
        "full_name": run.full_name,
        # Extract Contact Info directly from text to avoid losing it during updates
        "contact_info_block": extract_section(new_text, "PERSONAL DETAILS"),
        "location": "", 
        "phone": "",
        "email": "",
        "linkedin": "",
        "portfolio": "",
        "summary": extract_section(new_text, "SUMMARY"),
        "skills_block": extract_section(new_text, "SKILLS"),
        "experience_block": extract_section(new_text, "WORK EXPERIENCE"),
        "projects_block": extract_section(new_text, "PROJECTS"),
        "certifications_block": extract_section(new_text, "CERTIFICATIONS"),
        "achievements_block": extract_section(new_text, "ACHIEVEMENTS"),
        "education_block": extract_section(new_text, "EDUCATION"),
        "volunteer_block": extract_section(new_text, "VOLUNTEER"),
    }

    run.tailored_text = new_text
    run.tailored_md = render_md("templates/ats_resume.md", data)
    run.tailored_html = render_html("templates/ats_resume.html", data)

    db.commit()
    db.refresh(run)

    # Artifacts are no longer saved to disk eagerly.
    # Download endpoints will handle regeneration.
    
    return run


def process_and_save_cover_letter(
    db: Session,
    full_text: str,
    run_context: dict
) -> TailorRun:
    from models import CoverLetter
    import datetime
    
    # Prepare data for template
    from services.render_service import md_filter
    body_html = md_filter(full_text)
    
    data = {
        "full_name": run_context.get("full_name") or "Your Name",
        "phone": run_context.get("phone") or "",
        "email": run_context.get("email") or "",
        "linkedin": run_context.get("linkedin") or "",
        "location": run_context.get("location") or "",
        "portfolio": run_context.get("portfolio") or "",
        "current_date": datetime.date.today().strftime("%B %d, %Y"),
        "hiring_manager": "Hiring Manager",
        "company": run_context.get("company", ""),
        "company_address": "",
        "body_html": body_html
    }

    # Render Artifacts
    cover_letter_html = render_html("templates/cover_letter.html", data)

    # Save to DB
    cl = CoverLetter(
        job_title=run_context.get("job_title", ""),
        company=run_context.get("company", ""),
        full_name=run_context.get("full_name", ""),
        jd_text=run_context.get("jd_text", ""),
        resume_text=run_context.get("resume_text", ""),
        cover_letter_text=full_text,
        cover_letter_html=cover_letter_html
    )
    db.add(cl)
    db.commit()
    db.refresh(cl)

    # Artifacts are no longer saved to disk eagerly.
    
    return cl

    return cl