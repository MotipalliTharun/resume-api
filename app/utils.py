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
