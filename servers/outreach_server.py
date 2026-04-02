from urllib.parse import quote_plus

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("outreach")

SACHIN = {
    "name": "Sachin Pandey",
    "email": "ihn10@txstate.edu",
    "linkedin": "linkedin.com/in/pandey-s/",
}


@mcp.tool()
def find_recruiter(company: str, role: str) -> str:
    """
    Build LinkedIn search URLs to find recruiters and employees at a company.
    Does not scrape LinkedIn — returns search URLs for manual use.
    """
    company_enc = quote_plus(company)
    role_enc = quote_plus(role)

    recruiter_url = (
        f"https://www.linkedin.com/search/results/people/"
        f"?keywords={company_enc}+recruiter+OR+talent+acquisition"
    )
    employee_url = (
        f"https://www.linkedin.com/search/results/people/"
        f"?keywords={company_enc}+{role_enc}"
    )

    note = (
        f"Open these URLs in your browser (must be logged into LinkedIn):\n"
        f"1. Recruiters at {company}: {recruiter_url}\n"
        f"2. {role} employees at {company}: {employee_url}\n\n"
        f"Find a recruiter or hiring manager, get their name, then call draft_outreach()."
    )
    return note


@mcp.tool()
def draft_outreach(
    recruiter_name: str,
    company: str,
    role_applying: str,
    my_background: str,
) -> str:
    """
    Generate a cold outreach email to a recruiter. Under 150 words.
    my_background: 1-2 sentence summary of who you are (e.g. 'CS junior at Texas State, 4.0 GPA, built full-stack apps and a RAG AI assistant').
    """
    subject = f"Subject: {role_applying} at {company} — quick introduction"

    email = f"""{subject}

Hi {recruiter_name},

{my_background} I'm currently seeking a {role_applying} role and {company} caught my attention.

I'm particularly drawn to {company} because [COMPANY_REASON]. I believe my background aligns well with what your team is building.

Would you be open to a 15-minute call to learn more? No pressure at all — happy to connect asynchronously too.

Thank you for your time.

Best,
{SACHIN["name"]}
{SACHIN["email"]} | {SACHIN["linkedin"]}"""

    word_count = len(email.split())
    return f"{email}\n\n---\nWord count: ~{word_count} (fill in [COMPANY_REASON] before sending)"


if __name__ == "__main__":
    mcp.run(transport="stdio")
