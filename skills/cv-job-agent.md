---
name: cv-job-agent
description: Install the CV Job Agent — an MCP agent that tailors CVs to job descriptions and generates ATS-friendly PDFs, cover letters, and interview answers
---

# CV Job Agent Skill

Installs the CV Job Agent into your OpenCode project. After this skill completes, use `@job-applier [paste job description]` to generate tailored application materials.

## What it does

1. Clones the repo to a managed location
2. Creates a Python venv and installs dependencies
3. Asks for your `cv.md` path and name
4. Writes `.opencode/mcp.json` and `.opencode/agents/job-applier.md`

## Instructions

- [ ] **Step 1: Clone the repo**

```bash
git clone https://github.com/alrafikri/cv-job-agent.git /tmp/cv-job-agent
```

- [ ] **Step 2: Copy files to project**

```bash
cp -r /tmp/cv-job-agent/scripts /tmp/cv-job-agent/requirements.txt /tmp/cv-job-agent/pyproject.toml /tmp/cv-job-agent/.env.example .
```

- [ ] **Step 3: Create Python venv and install deps**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 4: Ask the user for their `cv.md` path**

Ask the user: "What is the path to your master CV in Markdown format?"

Once they provide it, write `.env`:
```bash
cp .env.example .env
```

Edit `.env` to set `CV_PATH` to the user's CV path and prompt for their name to set `USER_NAME`.

- [ ] **Step 5: Write MCP config**

```json
{
  "mcpServers": {
    "cv-agent": {
      "command": ".venv/bin/python3",
      "args": ["scripts/cv_mcp_server.py"]
    }
  }
}
```

Write this to `.opencode/mcp.json`.

- [ ] **Step 6: Write agent config**

Write `.opencode/agents/job-applier.md` with the agent prompt from the repo's `install.sh`.

- [ ] **Step 7: Cleanup**

```bash
rm -rf /tmp/cv-job-agent
```

- [ ] **Step 8: Confirm**

Tell the user: "✅ CV Job Agent installed. Use `@job-applier [paste job description]` in this project."
