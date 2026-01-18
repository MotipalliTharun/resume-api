import json
from pathlib import Path
from sqlalchemy.orm import Session
from models import TailorRun
from services.render_service import render_md, render_html
from utils import safe_filename

DATA_DIR = Path("/app/_data")
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
            if s_norm in ["SUMMARY", "SKILLS", "WORK EXPERIENCE", "EDUCATION", "PROJECTS", "CERTIFICATIONS", "ACHIEVEMENTS"]:
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

    # Save Artifacts
    base = f"run_{run.id}_{safe_filename(run.job_title or 'role')}"
    (DATA_DIR / f"{base}.txt").write_text(full_text, encoding="utf-8")
    (DATA_DIR / f"{base}.md").write_text(tailored_md, encoding="utf-8")
    (DATA_DIR / f"{base}.html").write_text(tailored_html, encoding="utf-8")

    # [NEW] Save friendly named PDF for local overwrite
    try:
        from weasyprint import HTML
        friendly_name = f"{safe_filename(data['full_name'])}_Resume.pdf"
        pdf_path = DATA_DIR / friendly_name
        HTML(string=tailored_html).write_pdf(target=str(pdf_path))
        print(f"Saved friendly PDF to: {pdf_path}")
    except Exception as e:
        print(f"Failed to generate/save friendly PDF: {e}")
    
    return run

def extract_contact_details(text: str, existing_name: str) -> dict:
    """
    Simple heuristic extraction of contact details from the top of the resume.
    """
    import re
    
    # Heuristic: Scan first 10 lines
    head = "\n".join(text.splitlines()[:15])
    
    email_re = r'[\w\.-]+@[\w\.-]+\.\w+'
    phone_re = r'\(?\d{3}\)?[\s\.-]?\d{3}[\s\.-]?\d{4}'
    link_re = r'(https?://)?(www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/[^\s]*)?'
    
    email = re.search(email_re, head)
    phone = re.search(phone_re, head)
    
    # Find links roughly
    links = re.findall(link_re, head)
    # This regex is messy for extraction, better to just look for keywords
    
    linkedin = ""
    portfolio = ""
    
    for word in head.split():
        if "linkedin.com" in word:
            linkedin = word.strip("()")
        elif "github.com" in word or "portfolio" in word.lower():
            # precise extraction might be hard, assume user puts it clearly
            if "http" in word or "www" in word:
                portfolio = word.strip("()")

    return {
        "full_name": existing_name, # Usually name is not edited or we keep the run's name
        "email": email.group(0) if email else "",
        "phone": phone.group(0) if phone else "",
        "linkedin": linkedin,
        "portfolio": portfolio,
        "location": "" # Location hard to parse with regex, skip for now
    }

def update_run_text(db: Session, run: TailorRun, new_text: str):
    """
    Updates the run's tailored text and re-renders MD/HTML artifacts.
    """
    # Extract data using existing sections or keep original contact info
    contact_info = extract_contact_details(new_text, run.full_name)
    
    data = {
        "full_name": run.full_name, # Keep original name to be safe
        "location": contact_info["location"],
        "phone": contact_info["phone"],
        "email": contact_info["email"],
        "linkedin": contact_info["linkedin"],
        "portfolio": contact_info["portfolio"],
        "summary": extract_section(new_text, "SUMMARY"),
        "skills_block": extract_section(new_text, "SKILLS"),
        "experience_block": extract_section(new_text, "WORK EXPERIENCE"),
        "projects_block": extract_section(new_text, "PROJECTS"),
        "certifications_block": extract_section(new_text, "CERTIFICATIONS"),
        "achievements_block": extract_section(new_text, "ACHIEVEMENTS"),
        "education_block": extract_section(new_text, "EDUCATION"),
    }

    run.tailored_text = new_text
    run.tailored_md = render_md("templates/ats_resume.md", data)
    run.tailored_html = render_html("templates/ats_resume.html", data)

    db.commit()
    db.refresh(run)

    # Overwrite artifacts
    base = f"run_{run.id}_{safe_filename(run.job_title or 'role')}"
    (DATA_DIR / f"{base}.txt").write_text(new_text, encoding="utf-8")
    (DATA_DIR / f"{base}.md").write_text(run.tailored_md, encoding="utf-8")
    (DATA_DIR / f"{base}.html").write_text(run.tailored_html, encoding="utf-8")
    
    # Regenerate friendly PDF
    try:
        from weasyprint import HTML
        friendly_name = f"{safe_filename(data['full_name'])}_Resume.pdf"
        pdf_path = DATA_DIR / friendly_name
        HTML(string=run.tailored_html).write_pdf(target=str(pdf_path))
    except Exception as e:
        print(f"Failed to regenerate friendly PDF on edit: {e}")

    return run
