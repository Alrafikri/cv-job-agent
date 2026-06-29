# CV Job Agent

An **OpenCode MCP agent** that tailors your CV to job descriptions and generates polished application materials — ATS-friendly PDF, cover letter, and interview answers.

```
@job-applier [paste job description]
```

## What it does

Given a job description, the agent:

1. Creates an application folder with a structured job context file
2. Reads your master CV and tailors it to match job keywords
3. Generates an **ATS-friendly PDF** via weasyprint
4. Writes a **cover letter** and **interview answers**
5. Documents every tailoring change and why it was made

## Prerequisites

- Python 3.11+
- OpenCode
- A master CV in Markdown format (`cv.md`)

## Quick start

```bash
curl -fsSL https://raw.githubusercontent.com/alrafikri/cv-job-agent/main/install.sh | bash
```

Then start OpenCode in the project directory and type:

```
@job-applier [paste job description]
```

The install script sets up OpenCode config (`.opencode/mcp.json` and `.opencode/agents/job-applier.md`) in your project root automatically.

## How it works

```
                  ┌─────────────────┐
                  │   @job-applier  │ (OpenCode subagent)
                  │   (LLM does     │
                  │   creative work)│
                  └────────┬────────┘
                           │
               ┌───────────┴───────────┐
               │                       │
        ┌──────▼──────┐        ┌───────▼───────┐
        │init_applicat│        │  render_pdf   │
        │ion (MCP)    │        │  (MCP tool)   │
        │- creates    │        │- .md → .pdf   │
        │  folder     │        │  via weasyprint│
        │- writes     │        └───────┬───────┘
        │  context    │                │
        └──────┬──────┘                │
               │                       │
               ▼                       ▼
        ┌──────────────────────────────────┐
        │  applications/<Company>-<Role>/  │
        │  ├── job-context.md              │
        │  ├── tailored-resume.md          │
        │  ├── Your Name_CV_Company.pdf    │
        │  ├── cover-letter.md             │
        │  ├── tailoring-notes.md          │
        │  └── interview-answers.md        │
        └──────────────────────────────────┘
```

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `CV_PATH` | `./cv.md` | Path to your master CV |
| `APPLICATIONS_DIR` | `./applications` | Output directory |
| `USER_NAME` | `Candidate` | Your name for PDF filenames |
| `RENDER_DIR` | `./scripts/render` | HTML template directory |

## Output

```
applications/
└── Acme-Data-Engineer-2026-06-29/
    ├── job-context.md            # Parsed job description
    ├── tailored-resume.md        # CV rewritten for the role
    ├── Your Name_CV_Acme.pdf    # ATS-friendly PDF
    ├── cover-letter.md           # Tailored cover letter
    ├── tailoring-notes.md        # What changed and why
    └── interview-answers.md      # (if questions provided)
```

## License

MIT
