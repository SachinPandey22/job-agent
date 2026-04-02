import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

load_dotenv()

mcp = FastMCP("apply")

TIMEOUT_MS = 30_000

# Sachin's static profile for autofill
PROFILE = {
    "name": "Sachin Pandey",
    "first_name": "Sachin",
    "last_name": "Pandey",
    "email": "ihn10@txstate.edu",
    "phone": "+1-737-213-2760",
    "linkedin": "https://www.linkedin.com/in/pandey-s/",
    "location": "San Marcos, TX",
    "city": "San Marcos",
    "state": "TX",
    "university": "Texas State University",
    "gpa": "4.0",
    "graduation": "May 2027",
}

# Field selectors to try for each profile key (ordered by specificity)
FIELD_MAP: dict[str, list[str]] = {
    "name": [
        'input[name*="name" i]:not([name*="first" i]):not([name*="last" i])',
        'input[placeholder*="full name" i]',
        'input[id*="full_name" i]',
    ],
    "first_name": [
        'input[name*="first" i]',
        'input[id*="first" i]',
        'input[placeholder*="first name" i]',
    ],
    "last_name": [
        'input[name*="last" i]',
        'input[id*="last" i]',
        'input[placeholder*="last name" i]',
    ],
    "email": [
        'input[type="email"]',
        'input[name*="email" i]',
        'input[id*="email" i]',
    ],
    "phone": [
        'input[type="tel"]',
        'input[name*="phone" i]',
        'input[id*="phone" i]',
        'input[placeholder*="phone" i]',
    ],
    "linkedin": [
        'input[name*="linkedin" i]',
        'input[id*="linkedin" i]',
        'input[placeholder*="linkedin" i]',
    ],
    "location": [
        'input[name*="location" i]',
        'input[id*="location" i]',
        'input[placeholder*="location" i]',
        'input[placeholder*="city" i]',
    ],
    "university": [
        'input[name*="school" i]',
        'input[name*="university" i]',
        'input[id*="school" i]',
        'input[placeholder*="school" i]',
        'input[placeholder*="university" i]',
    ],
    "gpa": [
        'input[name*="gpa" i]',
        'input[id*="gpa" i]',
        'input[placeholder*="gpa" i]',
    ],
    "graduation": [
        'input[name*="grad" i]',
        'input[id*="grad" i]',
        'input[placeholder*="graduation" i]',
    ],
}


def _detect_platform(url: str) -> str:
    u = url.lower()
    if "boards.greenhouse.io" in u or "greenhouse.io" in u:
        return "greenhouse"
    if "jobs.lever.co" in u or "lever.co" in u:
        return "lever"
    if "myworkdayjobs.com" in u or "workday.com" in u:
        return "workday"
    if "linkedin.com/jobs" in u:
        return "linkedin"
    return "company_page"


def _autofill_success(platform: str) -> str:
    rates = {
        "greenhouse": "high (~80%)",
        "lever": "high (~75%)",
        "workday": "medium (~40%)",
        "linkedin": "medium (~50%)",
        "company_page": "low (~30%)",
    }
    return rates.get(platform, "low (~20%)")


@mcp.tool()
def check_platform(job_url: str) -> str:
    """Detect the ATS platform of a job URL without opening a visible browser."""
    platform = _detect_platform(job_url)
    result = {
        "platform": platform,
        "direct_apply_url": job_url,
        "estimated_autofill_success": _autofill_success(platform),
    }
    return json.dumps(result, indent=2)


async def _prefill(apply_url: str, resume_path: str) -> dict:
    fields_filled: list[str] = []
    fields_needing_attention: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            await page.goto(apply_url, wait_until="load", timeout=TIMEOUT_MS)
            await page.wait_for_timeout(2000)
        except PlaywrightTimeout:
            await browser.close()
            return {
                "error": "Page timed out after 30 seconds",
                "fields_filled": [],
                "fields_needing_attention": ["all — page did not load"],
            }

        # Fill text fields
        for field_key, selectors in FIELD_MAP.items():
            value = PROFILE.get(field_key, "")
            filled = False
            for selector in selectors:
                try:
                    el = await page.query_selector(selector)
                    if el and await el.is_visible():
                        await el.fill(value)
                        fields_filled.append(field_key)
                        filled = True
                        break
                except Exception:
                    continue
            if not filled:
                fields_needing_attention.append(field_key)

        # Resume upload
        resume_file = Path(resume_path)
        if resume_file.exists():
            try:
                upload_input = await page.query_selector('input[type="file"]')
                if upload_input:
                    await upload_input.set_input_files(str(resume_file))
                    fields_filled.append("resume_upload")
                else:
                    fields_needing_attention.append("resume_upload (no file input found)")
            except Exception as e:
                fields_needing_attention.append(f"resume_upload (error: {e})")
        else:
            fields_needing_attention.append(f"resume_upload (file not found: {resume_path})")

        # Free-text / open-ended questions
        try:
            textareas = await page.query_selector_all("textarea")
            for i, ta in enumerate(textareas):
                if await ta.is_visible():
                    await ta.fill("[FILL THIS IN]")
                    fields_filled.append(f"textarea_{i+1}")
        except Exception:
            pass

        # Print summary to terminal
        print("\n" + "=" * 60)
        print("APPLY SERVER — PREFILL COMPLETE")
        print("=" * 60)
        print(f"Fields filled:  {', '.join(fields_filled) if fields_filled else 'none'}")
        print(f"Needs attention: {', '.join(fields_needing_attention) if fields_needing_attention else 'none'}")
        print("\nReview the browser, make any edits, then press Enter here to confirm submission...")

        try:
            input()  # Wait for user to review and manually submit
        except EOFError:
            pass  # Non-interactive context

        await browser.close()

    # After Enter: mark application as applied in tracker
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from tracker_server import update_status, get_applications
        import sqlite3
        from pathlib import Path as P
        DB_PATH = P(__file__).parent.parent / "data" / "applications.db"
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT id FROM applications ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        if row:
            update_status(row[0], "applied")
            print(f"Tracker updated: application {row[0]} marked as 'applied'")
    except Exception as e:
        print(f"Note: could not auto-update tracker: {e}")

    return {
        "fields_filled": fields_filled,
        "fields_needing_attention": fields_needing_attention,
    }


@mcp.tool()
def open_and_prefill(apply_url: str, resume_path: str) -> str:
    """
    Open a job application in a visible browser, prefill all known fields,
    and wait for you to review before marking as applied in the tracker.
    resume_path: absolute path to your resume PDF.
    """
    result = asyncio.run(_prefill(apply_url, resume_path))
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
