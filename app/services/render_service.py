from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

# Initialize Jinja2 environment (assumes 'templates' directory is in the current working directory or provided path)
# We can just look at the parent directory or common paths.
# Given usage: render_md("templates/ats_resume.md", data)
# We'll set up a loader that looks at current directory (root of app).
import markdown

env = Environment(
    loader=FileSystemLoader("."),
    autoescape=select_autoescape(enabled_extensions=('html', 'xml'), default_for_string=True)
)

def md_filter(text):
    if not text:
        return ""
    # Convert markdown to HTML
    return markdown.markdown(text, extensions=['extra', 'nl2br'])

env.filters['md'] = md_filter

def render_md(template_path: str, data: dict) -> str:
    template = env.get_template(template_path)
    return template.render(**data)

def render_html(template_path: str, data: dict) -> str:
    template = env.get_template(template_path)
    return template.render(**data)

