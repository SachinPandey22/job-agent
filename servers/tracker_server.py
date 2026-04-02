import sqlite3
import json
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

DB_PATH = Path(__file__).parent.parent / "data" / "applications.db"
VALID_STATUSES = {"applied", "phone_screen", "interview", "offer", "rejected", "ghosted"}

mcp = FastMCP("job-tracker")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                company       TEXT NOT NULL,
                title         TEXT NOT NULL,
                url           TEXT NOT NULL,
                status        TEXT NOT NULL DEFAULT 'applied',
                applied_date  TEXT NOT NULL,
                notes         TEXT,
                resume_version TEXT,
                cover_letter  TEXT
            )
        """)
        conn.commit()


@mcp.tool()
def add_application(company: str, title: str, url: str, notes: str = "") -> str:
    """Add a new job application to the tracker. Returns the new application ID."""
    applied_date = date.today().isoformat()
    with get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO applications (company, title, url, status, applied_date, notes)
               VALUES (?, ?, ?, 'applied', ?, ?)""",
            (company, title, url, applied_date, notes),
        )
        conn.commit()
        new_id = cursor.lastrowid
    return f"Application added with ID {new_id} — {company} / {title} on {applied_date}"


@mcp.tool()
def update_status(id: int, status: str) -> str:
    """Update the status of an application. Valid statuses: applied, phone_screen, interview, offer, rejected, ghosted."""
    if status not in VALID_STATUSES:
        return f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
    with get_conn() as conn:
        result = conn.execute(
            "UPDATE applications SET status = ? WHERE id = ?", (status, id)
        )
        conn.commit()
        if result.rowcount == 0:
            return f"No application found with ID {id}"
    return f"Application {id} status updated to '{status}'"


@mcp.tool()
def get_applications(status: str = "all") -> str:
    """Return all applications as JSON, optionally filtered by status. Sort by applied_date descending."""
    with get_conn() as conn:
        if status == "all":
            rows = conn.execute(
                "SELECT * FROM applications ORDER BY applied_date DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM applications WHERE status = ? ORDER BY applied_date DESC",
                (status,),
            ).fetchall()
    applications = [dict(row) for row in rows]
    return json.dumps(applications, indent=2)


if __name__ == "__main__":
    init_db()
    mcp.run(transport="stdio")
