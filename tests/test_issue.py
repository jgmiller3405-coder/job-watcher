"""The daily GitHub Issue."""

from jobwatcher.issue import MARKER, line, publish, report_lines, split

STATUS = {
    "run_time": "2026-01-02T12:00:00Z",
    "open": 2,
    "days_with_success": 2,
    "sources": [{"name": "stripe", "ok": True, "count": 2}, {"name": "ramp", "ok": False, "count": 0}],
}


def row(posting_id, **changes):
    base = {
        "posting_id": posting_id, "title": f"Title {posting_id}", "employer": "Co",
        "location": "NY", "url": f"https://example.com/{posting_id}", "in_role": "false",
        "first_run": "false", "first_seen": "2026-01-01", "removed_date": "",
    }
    return base | changes


def test_report_lists_new_and_removed_with_links():
    rows = [
        row("new", first_seen="2026-01-02", in_role="true"),
        row("firstrun", first_seen="2026-01-02", first_run="true"),
        row("gone", removed_date="2026-01-02"),
        row("old"),
    ]
    text = "\n".join(report_lines(rows, STATUS))
    assert "## New postings (1)" in text and "## Removed postings (1)" in text
    assert "(https://example.com/new)" in text and "(https://example.com/gone)" in text
    assert "firstrun" not in text and "Title old" not in text
    assert "Failed sources: ramp" in text


def test_a_quiet_day_still_has_a_report():
    text = "\n".join(report_lines([], STATUS))
    assert text.count("None.") == 2


def test_posting_text_cannot_mention_people_or_break_links():
    text = line(row("x", title="Analyst @octocat [Remote]", url="https://e.com/a (b)"))
    assert "@octocat" not in text
    assert "\\[Remote\\]" in text
    assert "(https://e.com/a%20%28b%29)" in text


def test_long_reports_are_split():
    chunks = split([f"line {n:03d}" for n in range(100)], limit=100)
    assert all(len(chunk) <= 100 for chunk in chunks)
    assert "\n".join(chunks).count("line") == 100


class FakeGitHub:
    def __init__(self, issues, comments=()):
        self.issues, self.comments, self.calls = issues, list(comments), []

    def pages(self, path):
        return self.comments if path.endswith("/comments") else self.issues

    def call(self, method, path, body=None):
        self.calls.append((method, path, body))
        return {"number": 99}


def issue(number, title, state="open"):
    return {"number": number, "title": title, "state": state}


def test_a_new_day_opens_an_issue_and_closes_the_previous_one():
    api = FakeGitHub([issue(1, "2026-01-01"), issue(2, "A question")])
    assert publish(api, "2026-01-02", ["body", "more"], pause=0) == 99
    assert [(m, p) for m, p, _ in api.calls] == [
        ("POST", "/issues"),
        ("POST", "/issues/99/comments"),
        ("PATCH", "/issues/1"),
    ]
    assert api.calls[0][2]["title"] == "2026-01-02"
    assert api.calls[2][2] == {"state": "closed"}


def test_a_second_run_updates_the_same_issue():
    api = FakeGitHub(
        [issue(5, "2026-01-02")],
        [{"id": 11, "body": f"{MARKER}\nold"}, {"id": 12, "body": "a person's note"}],
    )
    assert publish(api, "2026-01-02", ["body"], pause=0) == 5
    assert [(m, p) for m, p, _ in api.calls] == [
        ("PATCH", "/issues/5"),
        ("DELETE", "/issues/comments/11"),
    ]
