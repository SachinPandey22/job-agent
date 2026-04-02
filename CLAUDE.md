# Job Agent — Sachin Pandey

## Build Status (as of Day 6)
All 5 MCP servers are built, tested, and committed:
- [x] Day 2 — `servers/tracker_server.py` (SQLite tracker: add_application, update_status, get_applications)
- [x] Day 3 — `servers/job_search_server.py` (Adzuna search + ghost detection + H1B filter)
- [x] Day 4 — `servers/job_import_server.py` (Playwright URL scraper)
- [x] Day 5 — `servers/outreach_server.py` (LinkedIn URL builder + email drafter)
- [x] Day 6 — `servers/apply_server.py` (check_platform + open_and_prefill)
- [x] `.claude/mcp.json` updated with all 5 servers pointing to `.venv/bin/python3`
- [x] Integration test passed (all 13 steps)

Python venv is at `.venv/` — run `.venv/bin/python3` for all server testing.

## Commit Rules
After each meaningful unit of work (new file created, server built and tested, bug fixed):
1. Run `git add` (specific files only — never `git add -A`)
2. Run `git commit` with message format: `"Day X: [what was built and tested]"`
3. Never commit broken or untested code
4. Never commit `.env` or `data/*.db`
5. After finishing a session, update this CLAUDE.md with current build status

## Who I am
See full resume: /context/resume.md
See job preferences: /context/preferences.md
See companies to avoid: /context/blacklist.md

## My background (quick summary)
- CS student at Texas State University (GPA 4.0, graduating May 2027)
- Strong in Python, JavaScript, React, Node.js, Django, PostgreSQL
- Built full-stack apps and a RAG-based AI assistant
- Currently a Research Assistant doing data analysis with Python
- Looking for: SWE Internships anywhere in the USA

## Your job when I give you a task

### Job search
When I ask you to search for jobs:
1. Call search_jobs() with appropriate filters
2. Filter out ghost jobs (posted 30+ days ago, description < 200 words)
3. Rank results by fit score against my resume
4. Present top 5 clearly with: title, company, salary, remote/onsite, H1B status, URL

### Resume tailoring
When I say "tailor my resume for this job" or after importing a job URL, do all of this in sequence:
1. Read `context/resume.md`
2. Read the job description (from `import_job_url()` output or pasted text)
3. Identify: (a) skills they want that I have, (b) gaps, (c) keywords to mirror
4. Rewrite my resume bullets using the job's exact language — keep facts true, sharpen phrasing
5. Reorder the skills section to put their stack first
6. Write a cover letter: 3 paragraphs, under 250 words, specific to the role and company, no fluff
7. Output fit score (1–10) with reasoning
8. List gaps honestly — things they want I don't have yet
9. Save everything to `output/[Company]_[Role]_[YYYY-MM-DD].md`
10. Call `add_application()` to log it in the tracker DB
11. Commit with message: `"tailored: [Company] [Role]"`

### Application tracking
When I apply to a job:
1. Call add_application() with company, title, URL, and any notes
2. Confirm with the application ID so I can reference it later

### Recruiter outreach
When I ask to find a recruiter or send outreach:
1. Call find_recruiter() to get the LinkedIn search URL
2. Call draft_outreach() with my background summary
3. Ask me to confirm before sending via Gmail

## Ghost job signals — flag these
- Posted more than 30 days ago with no edit
- Description under 200 words
- No specific team, product, or manager mentioned
- "We're always looking for talent" language
- Same posting across 5+ job boards word-for-word

## Output format for job analysis
Always structure output like this:

```
## [Job Title] @ [Company]
URL: ...
Posted: ...
Fit score: X/10
Ghost risk: low/medium/high — [reason]

### Why it fits
[2-3 bullet points matching my skills to their requirements]

### Gaps
[Honest gaps — things they want I don't have yet]

### Tailored resume bullets
[Rewritten versions of my existing bullets using their language]

### Cover letter
[3 paragraphs]
```

## Rules
- Never invent experience I don't have
- If fit score < 5, flag it and ask before spending time tailoring
- Keep cover letters under 250 words
- Prefer companies known to sponsor H1B (check H1B data if available)
- Always track applications — never let me apply without logging it
