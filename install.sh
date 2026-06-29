#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/alrafikri/cv-job-agent.git"

# If running via curl | bash, $0 is not a real path
if [ ! -f "requirements.txt" ]; then
    echo "=== CV Job Agent Install ==="
    echo "Downloading repo..."
    TMP_DIR=$(mktemp -d)
    git clone --depth=1 "$REPO_URL" "$TMP_DIR" >/dev/null 2>&1
    cp -r "$TMP_DIR"/{scripts,skills,.opencode,requirements.txt,pyproject.toml,.env.example,.gitignore,LICENSE,README.md,cv.example.md,install.sh} . 2>/dev/null || true
    rm -rf "$TMP_DIR"
fi

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "=== CV Job Agent Install ==="

# Check Python
PYTHON=""
for cmd in python3.13 python3.12 python3.11 python3; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        maj=${ver%.*}
        min=${ver#*.}
        if [ "$maj" -ge 3 ] && [ "$min" -ge 11 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3.11+ is required"
    exit 1
fi
echo "Using: $($PYTHON --version)"

# Create venv
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv .venv
fi
source .venv/bin/activate

# Install deps
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Configure
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "=== Configuration ==="
    read -p "Path to your cv.md: " cv_path
    if [ -n "$cv_path" ]; then
        if [[ "$cv_path" != /* ]]; then
            cv_path="$(cd "$(dirname "$cv_path")" && pwd)/$(basename "$cv_path")"
        fi
        sed -i '' "s|CV_PATH=./cv.md|CV_PATH=$cv_path|" .env
    fi
    read -p "Your full name (for PDF filenames): " user_name
    if [ -n "$user_name" ]; then
        sed -i '' "s|USER_NAME=Your Name|USER_NAME=$user_name|" .env
    fi
else
    echo "Using existing .env"
fi

# Write OpenCode config with absolute path (more reliable)
mkdir -p .opencode
cat > .opencode/mcp.json << EOF
{
  "mcpServers": {
    "cv-agent": {
      "command": "$DIR/.venv/bin/python3",
      "args": ["$DIR/scripts/cv_mcp_server.py"]
    }
  }
}
EOF

# Ensure agent exists
mkdir -p .opencode/agents
if [ ! -f ".opencode/agents/job-applier.md" ]; then
    cat > .opencode/agents/job-applier.md << 'AGENT'
---
description: Creates tailored job applications from a master CV and job description
mode: subagent
color: "#2ecc71"
permission:
  read: allow
  write: allow
  bash: allow
  glob: allow
  grep: allow
---

You are a Job Application Assistant. Given a job description, you create a folder with tailored application materials.

## Workflow

1. **Extract company name and role** from the job description
2. **Call `init_application`** with company, role, and the full job description text
3. **Read `cv.md`** (master CV) and the generated `job-context.md`
4. **Write `tailored-resume.md`** — rewrite the CV to match job keywords while keeping facts truthful. Use Markdown format:
   - Start with name, email, phone, website
   - Section: Professional Summary (2-3 sentences aligning with the role)
   - Section: Skills (reordered to surface relevant ones)
   - Section: Work Experience (reverse chrono, bullets rewritten with JD keywords)
   - **IMPORTANT:** Always put a blank line between section headings, job titles, and bullet lists. Bullets must be separated from preceding text by a blank line or they won't render as `<ul>` in the PDF.
   - Section: Education
   - Section: Certifications/Achievements
5. **Call `render_pdf`** with the path to `tailored-resume.md` and the company name
6. **Write `tailoring-notes.md`** — document every change made to the original CV and why
7. **Write `cover-letter.md`** — professional, 3-4 paragraphs
8. **If the user provided questions**, write `interview-answers.md`
9. **Tell the user** the application folder path and what was created
AGENT
fi

echo ""
echo "=== Install complete ==="
echo ""
echo "To use, open OpenCode in this directory and run:"
echo "  @job-applier [paste job description]"
