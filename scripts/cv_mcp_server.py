#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import markdown
from jinja2 import Environment, FileSystemLoader

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent.parent
APPLICATIONS_DIR = Path(os.getenv("APPLICATIONS_DIR", PROJECT_DIR / "applications"))
RENDER_DIR = Path(os.getenv("RENDER_DIR", PROJECT_DIR / "scripts" / "render"))
PROFILES_DIR = PROJECT_DIR / "profiles"
USER_NAME = os.getenv("USER_NAME", "Candidate")

mcp = FastMCP("cv-agent", log_level="ERROR")
jinja_env = Environment(loader=FileSystemLoader(str(RENDER_DIR)))


def _extract_name_from_cv(cv_text: str) -> str:
    for line in cv_text.splitlines():
        stripped = line.strip().strip('#* ')
        if stripped and not stripped.startswith('+') and not stripped.startswith('http') and '@' not in stripped:
            return stripped
    return USER_NAME


@mcp.tool()
def init_application(company: str, role: str, job_description: str) -> str:
    folder_name = f"{company}-{role}-{date.today().isoformat()}"
    app_dir = APPLICATIONS_DIR / folder_name
    app_dir.mkdir(parents=True, exist_ok=True)

    context = f"""# Job Context: {role} @ {company}

**Company:** {company}
**Role:** {role}
**Date:** {date.today().isoformat()}

## Job Description

{job_description}
"""
    (app_dir / "job-context.md").write_text(context)
    return str(app_dir)


@mcp.tool()
def list_profiles() -> str:
    if not PROFILES_DIR.exists():
        return "No profiles directory found."
    profiles = sorted(f.stem for f in PROFILES_DIR.iterdir() if f.suffix == ".md")
    return "\n".join(profiles) if profiles else "No profiles found."


@mcp.tool()
def get_cv(profile: str = "") -> str:
    if profile:
        cv_file = PROFILES_DIR / f"{profile}.md"
        if not cv_file.exists():
            return f"Error: profile '{profile}' not found. Available: {[f.stem for f in PROFILES_DIR.glob('*.md')]}"
        return cv_file.read_text()
    cv_path = Path(os.getenv("CV_PATH", PROJECT_DIR / "cv.md"))
    if not cv_path.exists():
        return f"Error: CV not found at {cv_path}"
    return cv_path.read_text()


def _md_to_pdf_html(md_text: str) -> str:
    html_body = markdown.markdown(md_text, extensions=["extra"])
    template = jinja_env.get_template("template.html")
    return template.render(body_html=html_body)


@mcp.tool()
def render_pdf(md_path: str, company: str, name: str = "") -> str:
    md_file = Path(md_path)
    if not md_file.exists():
        return f"Error: file not found: {md_path}"
    md_text = md_file.read_text()
    user_name = name or _extract_name_from_cv(md_text) or USER_NAME
    html = _md_to_pdf_html(md_text)
    pdf_name = f"{user_name}_CV_{company}.pdf"
    pdf_path = md_file.parent / pdf_name
    from weasyprint import HTML
    HTML(string=html).write_pdf(str(pdf_path))
    return str(pdf_path)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
