import asyncio
import re
from urllib.parse import urlparse

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

load_dotenv()

mcp = FastMCP("job-import")

TIMEOUT_MS = 30_000


def _clean_text(text: str) -> str:
    """Remove excessive whitespace and blank lines."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _guess_company(url: str, page_title: str) -> str:
    """Best-effort company name from domain or page title."""
    domain = urlparse(url).netloc.lower()
    # Strip common subdomains and TLDs
    parts = domain.replace("www.", "").replace("boards.", "").replace("jobs.", "").split(".")
    return parts[0].capitalize() if parts else page_title.split("|")[0].strip()


async def _import(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="load", timeout=TIMEOUT_MS)
            # Give JS-heavy SPAs a moment to render content
            await page.wait_for_timeout(2000)
        except PlaywrightTimeout:
            await browser.close()
            return {"error": "timeout", "url": url}
        except Exception as e:
            await browser.close()
            return {"error": str(e), "url": url}

        try:
            # Title: prefer first H1, fall back to <title>
            h1 = await page.query_selector("h1")
            if h1:
                title = (await h1.inner_text()).strip()
            else:
                title = await page.title()

            # Full visible text from body
            body_text = await page.evaluate("() => document.body.innerText")
            description = _clean_text(body_text)[:5000]
            word_count = len(description.split())

            company = _guess_company(url, title)

        finally:
            await browser.close()

    ghost_risk = "high" if word_count < 200 else "low"

    return {
        "title": title,
        "company": company,
        "description": description,
        "url": url,
        "word_count": word_count,
        "ghost_risk": ghost_risk,
    }


@mcp.tool()
def import_job_url(url: str) -> str:
    """
    Scrape a job posting URL using headless Chromium and return structured data.
    Works on Greenhouse, Lever, Workday, LinkedIn, and company career pages.
    """
    result = asyncio.run(_import(url))
    import json
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
