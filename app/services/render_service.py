from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

# Initialize Jinja2 environment (assumes 'templates' directory is in the current working directory or provided path)
# We can just look at the parent directory or common paths.
# Given usage: render_md("templates/ats_resume.md", data)
# We'll set up a loader that looks at current directory (root of app).
import markdown

# Determine absolute path to 'app' directory
TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_ROOT)),
    autoescape=select_autoescape(enabled_extensions=('html', 'xml'), default_for_string=True)
)

def md_filter(text):
    if not text:
        return ""
    # Pre-process: Convert text bullets to markdown bullets
    # Replace "•" with "-" at start of lines (or anywhere?) 
    # Usually "• " to "- "
    text = text.replace("•", "-")
    # Convert markdown to HTML
    return markdown.markdown(text, extensions=['extra', 'nl2br'])

env.filters['md'] = md_filter

def render_md(template_path: str, data: dict) -> str:
    template = env.get_template(template_path)
    return template.render(**data)

def render_html(template_path: str, data: dict) -> str:
    template = env.get_template(template_path)
    return template.render(**data)

