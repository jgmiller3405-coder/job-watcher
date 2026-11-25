"""Open (or update) the GitHub Issue for the latest run and close older ones.

Needs GITHUB_TOKEN and GITHUB_REPOSITORY, both provided by GitHub Actions.
Run it with:  uv run python -m jobwatcher.issue
Add --dry-run to print the text without contacting GitHub.
"""

import argparse
import csv
import json
import os
import re
import time
from pathlib import Path

from .build import DATA
from .http import request_json

API = "https://api.github.com"
LIMIT = 60_000  # GitHub rejects bodies over 65,536 characters
MARKER = "<!-- job-watcher -->"
DATE_TITLE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def escape(text: str) -> str:
    """Keep a posting's text from becoming Markdown, HTML, or an @mention."""
    text = re.sub(r"([\\`*_\[\]])", r"\\\1", text)
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("@", "@​")


def line(row: dict) -> str:
    url = row["url"].replace(" ", "%20").replace("(", "%28").replace(")", "%29")
    place = f", {escape(row['location'])}" if row["location"] else ""
    return f"- [{escape(row['title'])}]({url}) · {escape(row['employer'])}{place}"


def report_lines(rows: list[dict], status: dict) -> list[str]:
    date = status["run_time"][:10]
    new = [r for r in rows if r["first_seen"] == date and r["first_run"] == "false"]
    removed = [r for r in rows if r["removed_date"] == date]
    failed = [s["name"] for s in status["sources"] if not s["ok"]]

    lines = [
        f"Run time: {status['run_time']}",
        f"Open postings: {status['open']} · New today: {len(new)} · "
        f"Removed today: {len(removed)} · Days with a successful run: {status['days_with_success']}",
        f"Failed sources: {', '.join(failed) if failed else 'none'}",
    ]
    for heading, postings in (("New postings", new), ("Removed postings", removed)):
        lines += ["", f"## {heading} ({len(postings)})"]
        if not postings:
            lines.append("None.")
            continue
        for label, in_role in (("In role: financial analyst", "true"), ("Everything else", "false")):
            group = sorted(
                (r for r in postings if r["in_role"] == in_role),
                key=lambda r: (r["employer"], r["title"], r["posting_id"]),
            )
            if group:
                lines += ["", f"### {label} ({len(group)})"]
                lines += [line(r) for r in group]
    return lines


def split(lines: list[str], limit: int = LIMIT) -> list[str]:
    """Join lines into as few chunks as fit within the limit."""
    chunks, current, size = [], [], 0
    for text in lines:
        if current and size + len(text) + 1 > limit:
            chunks.append("\n".join(current))
            current, size = [], 0
        current.append(text)
        size += len(text) + 1
    chunks.append("\n".join(current))
    return chunks


class GitHub:
    def __init__(self, repository: str, token: str):
        self.base = f"{API}/repos/{repository}"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
        }

    def call(self, method: str, path: str, body: dict | None = None):
        if method == "DELETE":
            return self._delete(path)
        # Creating things is not retried, so a lost reply cannot create a duplicate.
        attempts = 1 if method == "POST" else 4
        return request_json(
            self.base + path, body=body, headers=self.headers, method=method, attempts=attempts
        )

    def _delete(self, path: str) -> None:
        import urllib.request  # a delete returns no JSON

        request = urllib.request.Request(self.base + path, headers=self.headers, method="DELETE")
        with urllib.request.urlopen(request, timeout=60):
            pass

    def pages(self, path: str) -> list:
        items, page = [], 1
        while True:
            joiner = "&" if "?" in path else "?"
            batch = self.call("GET", f"{path}{joiner}per_page=100&page={page}")
            items += batch
            if len(batch) < 100:
                return items
            page += 1


def publish(api, date: str, chunks: list[str], pause: float = 1.0) -> int:
    """Write the day's issue, close earlier ones, and return the issue number."""
    daily = [
        issue
        for issue in api.pages("/issues?state=all")
        if "pull_request" not in issue and DATE_TITLE.match(issue["title"])
    ]
    body = f"{MARKER}\n{chunks[0]}"
    today = next((issue for issue in daily if issue["title"] == date), None)
    if today:
        number = today["number"]
        api.call("PATCH", f"/issues/{number}", {"body": body, "state": "open"})
        for comment in api.pages(f"/issues/{number}/comments"):
            if (comment.get("body") or "").startswith(MARKER):
                api.call("DELETE", f"/issues/comments/{comment['id']}")
    else:
        number = api.call("POST", "/issues", {"title": date, "body": body})["number"]

    for chunk in chunks[1:]:
        time.sleep(pause)  # GitHub limits how fast content can be created
        api.call("POST", f"/issues/{number}/comments", {"body": f"{MARKER}\n{chunk}"})

    for issue in daily:
        if issue["state"] == "open" and issue["title"] < date:
            api.call("PATCH", f"/issues/{issue['number']}", {"state": "closed"})
    return number


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA, help="data folder (default: data/)")
    parser.add_argument("--dry-run", action="store_true", help="print instead of publishing")
    args = parser.parse_args()

    status = json.loads((args.data / "status.json").read_text(encoding="utf-8"))
    with (args.data / "history.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    chunks = split(report_lines(rows, status))

    if args.dry_run:
        print("\n".join(chunks))
        return
    api = GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    number = publish(api, status["run_time"][:10], chunks)
    print(f"issue #{number} written with {len(chunks) - 1} comments")


if __name__ == "__main__":
    main()
