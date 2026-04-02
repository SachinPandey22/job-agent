import json
import os
from datetime import date, datetime, timedelta

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs/us/search/1"

H1B_KEYWORDS = [
    "h1b", "h-1b", "visa sponsorship", "sponsor work authorization",
    "willing to sponsor",
]

mcp = FastMCP("job-search")


def _ghost_risk(posted_date_str: str, description: str) -> str:
    if len(description) < 200:
        return "high"
    try:
        posted = datetime.fromisoformat(posted_date_str.replace("Z", "+00:00")).date()
        days_old = (date.today() - posted).days
    except Exception:
        return "medium"
    if days_old > 30:
        return "high"
    if days_old > 15:
        return "medium"
    return "low"


def _has_h1b(description: str) -> bool:
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in H1B_KEYWORDS)


@mcp.tool()
def search_jobs(
    title: str,
    location: str = "USA",
    remote: bool = False,
    h1b: bool = False,
    salary_min: int = 0,
    days_old: int = 14,
) -> str:
    """Search for jobs via Adzuna. Returns up to 20 results with ghost risk and H1B signals."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return json.dumps({"error": "ADZUNA_APP_ID or ADZUNA_APP_KEY not set in .env"})

    params: dict = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 20,
        "what": title,
        "where": location,
        "max_days_old": days_old,
        "content-type": "application/json",
    }
    if salary_min > 0:
        params["salary_min"] = salary_min
    if remote:
        params["what"] = f"{title} remote"

    try:
        resp = httpx.get(ADZUNA_BASE, params=params, timeout=15)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Adzuna API error {e.response.status_code}: {e.response.text}"})
    except httpx.RequestError as e:
        return json.dumps({"error": f"Network error: {str(e)}"})

    data = resp.json()
    results = data.get("results", [])

    output = []
    for job in results:
        description = job.get("description", "")
        posted_str = job.get("created", "")
        ghost = _ghost_risk(posted_str, description)

        if h1b and not _has_h1b(description):
            continue

        salary_min_val = job.get("salary_min")
        salary_max_val = job.get("salary_max")

        output.append({
            "title": job.get("title", ""),
            "company": job.get("company", {}).get("display_name", ""),
            "url": job.get("redirect_url", ""),
            "salary_min": salary_min_val,
            "salary_max": salary_max_val,
            "location": job.get("location", {}).get("display_name", ""),
            "posted_date": posted_str,
            "description_preview": description[:300],
            "ghost_risk": ghost,
        })

    return json.dumps(output, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
