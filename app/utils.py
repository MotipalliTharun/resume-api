from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Use a separate environment or shared? 
# For simplicity, create one here.
env = Environment(loader=FileSystemLoader("."))

def read_text(path: str) -> str:
    # Deprecated for rendering, but kept if used elsewhere
    return Path(path).read_text(encoding="utf-8")

def render_prompt(prompt_path: str, **kwargs) -> str:
    template = env.get_template(prompt_path)
    return template.render(**kwargs)


def safe_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in name)


def job_title_slug(title: str) -> str:
    """Convert job title to lowercase hyphenated slug for file naming."""
    import re
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "resume"


def build_resume_filename(username: str, job_title: str, fmt: str = "docx") -> str:
    """Generate standardized filename: <username>_<job-title-slug>_resume.<fmt>"""
    user_slug = safe_filename(username.lower().replace(" ", "_"))
    title_slug = job_title_slug(job_title)
    return f"{user_slug}_{title_slug}_resume.{fmt}"
