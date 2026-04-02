# job-agent

Personal AI-powered job application system built on Claude Code + MCP servers.

## What this does
- Searches for SWE intern jobs with filters (location, salary, H1B, remote)
- Imports any job posting from a URL (LinkedIn, Greenhouse, Lever, Workday)
- Tailors resume and generates cover letters per application
- Tracks all applications in a local SQLite database
- Finds recruiters and drafts outreach emails

## Stack
- **Claude Code** — the AI brain, reads CLAUDE.md on startup
- **MCP servers** — 4 Python servers exposing tools Claude Code can call
- **Adzuna API** — free job search API (250 req/day)
- **Playwright** — headless Chrome for scraping any job URL
- **SQLite** — local database for application tracking
- **Gmail MCP** — connected in Claude settings for sending outreach

## Setup

### 1. Install dependencies
```bash
npm install -g @anthropic-ai/claude-code
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY and ADZUNA_APP_ID/KEY
```

### 3. Get API keys
- **Anthropic:** console.anthropic.com
- **Adzuna:** developer.adzuna.com (free, 250 req/day)

### 4. Run
```bash
cd job-agent
claude
```

## Project structure
```
job-agent/
├── CLAUDE.md              # Claude Code reads this — your instructions + resume
├── context/
│   ├── resume.md          # Your resume (source of truth)
│   ├── preferences.md     # Job filters and preferences
│   └── blacklist.md       # Companies/roles to avoid
├── servers/
│   ├── tracker_server.py      # Day 2: SQLite application tracker
│   ├── job_search_server.py   # Day 3: Adzuna + H1B filter
│   ├── job_import_server.py   # Day 4: Playwright URL scraper
│   └── outreach_server.py     # Day 5: Recruiter finder + email drafter
├── data/                  # SQLite DB lives here (gitignored)
├── output/                # Tailored resumes saved here (gitignored)
├── .claude/
│   └── mcp.json           # MCP server registrations
├── .env.example
├── requirements.txt
└── README.md
```

## Build progress
- [x] Day 1 — Project setup, context files, CLAUDE.md
- [ ] Day 2 — tracker_server.py (SQLite)
- [ ] Day 3 — job_search_server.py (Adzuna + H1B)
- [ ] Day 4 — job_import_server.py (Playwright)
- [ ] Day 5 — outreach_server.py + Gmail

## Daily workflow (once complete)
```
claude
> search for SWE intern jobs, remote, H1B preferred
> import this job: [paste URL]
> tailor my resume for this application
> track this application — Cloudflare SWE Intern
> find a recruiter at Cloudflare and draft outreach
```
