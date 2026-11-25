"""First seen, last seen, removed, and building the files from raw data."""

import csv
import json
from datetime import datetime, timezone

from jobwatcher.build import COLUMNS, build, build_history
from jobwatcher.raw import raw_days, write_raw
from jobwatcher.run import run
from jobwatcher.sources import BY_KEY

D1, D2, D3, D4 = "2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"


def posting(source, source_id, title="Financial Analyst"):
    return {
        "posting_id": f"{source}:{source_id}",
        "source": source,
        "source_id": source_id,
        "employer": source.title(),
        "title": title,
        "location": "",
        "department": "",
        "posted_date": "",
        "url": f"https://example.com/{source_id}",
    }


def history(*days):
    return {row["posting_id"]: row for row in build_history(days)}


def test_first_seen_stays_and_last_seen_moves():
    rows = history(
        (D1, {"a": [posting("a", "1")]}),
        (D2, {"a": [posting("a", "1"), posting("a", "2")]}),
    )
    assert (rows["a:1"]["first_seen"], rows["a:1"]["last_seen"]) == (D1, D2)
    assert (rows["a:2"]["first_seen"], rows["a:2"]["last_seen"]) == (D2, D2)


def test_first_run_is_only_the_first_file_of_each_source():
    rows = history(
        (D1, {"a": [posting("a", "1")]}),
        (D2, {"a": [posting("a", "1"), posting("a", "2")], "b": [posting("b", "9")]}),
        (D3, {"b": [posting("b", "9"), posting("b", "10")]}),
    )
    assert rows["a:1"]["first_run"] is True
    assert rows["a:2"]["first_run"] is False
    assert rows["b:9"]["first_run"] is True  # b's first file is on day two
    assert rows["b:10"]["first_run"] is False


def test_removed_gets_that_days_date_and_stays_removed():
    rows = history(
        (D1, {"a": [posting("a", "1"), posting("a", "2")]}),
        (D2, {"a": [posting("a", "2")]}),
        (D3, {"a": [posting("a", "2")]}),
    )
    gone = rows["a:1"]
    assert gone["status"] == "removed"
    assert gone["removed_date"] == D2
    assert gone["last_seen"] == D1
    assert rows["a:2"]["status"] == "open"
    assert rows["a:2"]["removed_date"] == ""


def test_a_source_without_a_raw_file_removes_nothing():
    rows = history(
        (D1, {"a": [posting("a", "1")], "b": [posting("b", "1")]}),
        (D2, {"b": [posting("b", "1")]}),  # a failed
    )
    assert rows["a:1"]["status"] == "open"
    assert rows["a:1"]["last_seen"] == D1


def test_a_relisted_posting_reopens_with_the_same_first_seen():
    rows = history(
        (D1, {"a": [posting("a", "1"), posting("a", "2")]}),
        (D2, {"a": [posting("a", "2")]}),
        (D3, {"a": [posting("a", "1", "New Title"), posting("a", "2")]}),
    )
    back = rows["a:1"]
    assert back["status"] == "open"
    assert back["removed_date"] == ""
    assert (back["first_seen"], back["last_seen"]) == (D1, D3)
    assert back["first_run"] is True
    assert back["title"] == "New Title"
    assert back["in_role"] is False  # the rule follows the latest title


def test_rows_are_sorted_by_posting_id():
    rows = build_history(
        [(D1, {"b": [posting("b", "1")], "a": [posting("a", "2"), posting("a", "10")]})]
    )
    assert [r["posting_id"] for r in rows] == ["a:10", "a:2", "b:1"]


def greenhouse(*ids):
    return [
        {"jobs": [{"id": i, "title": "Financial Analyst", "absolute_url": f"u/{i}"} for i in ids]}
    ]


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_build_depends_on_the_raw_files_alone(tmp_path):
    write_raw(tmp_path / "raw", D2, "stripe", greenhouse(2))
    write_raw(tmp_path / "raw", D1, "stripe", greenhouse(1, 2))
    build(tmp_path)
    first = (tmp_path / "history.csv").read_bytes()

    (tmp_path / "history.csv").write_text("junk", encoding="utf-8")
    build(tmp_path)
    assert (tmp_path / "history.csv").read_bytes() == first

    rows = read_csv(tmp_path / "history.csv")
    assert list(rows[0]) == COLUMNS
    assert rows[0]["status"] == "removed" and rows[0]["removed_date"] == D2
    assert rows[0]["in_role"] == "true" and rows[0]["first_run"] == "true"
    assert b"\r\n" not in first


def fake_fetcher(boards):
    def fetch(source):
        ids = boards[source.key]
        if ids is None:
            raise RuntimeError("blocked")
        return greenhouse(*ids), len(ids)

    return fetch


def run_day(tmp_path, day, boards, hour=12):
    sources = [BY_KEY[key] for key in boards]
    now = datetime.fromisoformat(f"{day}T{hour:02d}:00:00").replace(tzinfo=timezone.utc)
    return run(tmp_path, sources, fake_fetcher(boards), now)


def test_one_failed_source_does_not_stop_the_run(tmp_path):
    status = run_day(tmp_path, D1, {"stripe": [1], "affirm": None})
    assert status["sources"] == [
        {"name": "stripe", "ok": True, "count": 1},
        {"name": "affirm", "ok": False, "count": 0},
    ]
    assert (tmp_path / "raw" / D1 / "stripe.json.gz").exists()
    assert not (tmp_path / "raw" / D1 / "affirm.json.gz").exists()


def test_status_counts(tmp_path):
    run_day(tmp_path, D1, {"stripe": [1, 2]})
    run_day(tmp_path, D2, {"stripe": [2, 3], "affirm": [7]})
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert status == {
        "run_time": f"{D2}T12:00:00Z",
        "first_run_date": D1,
        "days_with_success": 2,
        "open": 3,
        "new_today": 1,  # stripe 3; affirm 7 is a first-run posting
        "removed_today": 1,
        "sources": [
            {"name": "stripe", "ok": True, "count": 2},
            {"name": "affirm", "ok": True, "count": 1},
        ],
    }


def test_a_second_run_replaces_the_days_files_and_counts_once(tmp_path):
    run_day(tmp_path, D1, {"stripe": [1], "affirm": [7]})
    run_day(tmp_path, D2, {"stripe": [2], "affirm": [7]}, hour=9)
    status = run_day(tmp_path, D2, {"stripe": [1, 2], "affirm": None}, hour=15)
    assert status["days_with_success"] == 2
    assert status["removed_today"] == 0
    assert not (tmp_path / "raw" / D2 / "affirm.json.gz").exists()
    rows = {r["posting_id"]: r for r in read_csv(tmp_path / "history.csv")}
    assert rows["stripe:1"]["status"] == "open"
    assert rows["stripe:2"]["first_seen"] == D2


def test_a_run_where_everything_fails_keeps_earlier_files(tmp_path):
    run_day(tmp_path, D1, {"stripe": [1]}, hour=9)
    status = run_day(tmp_path, D1, {"stripe": None}, hour=15)
    assert status["days_with_success"] == 1
    assert status["sources"][0]["ok"] is False
    assert [day for day, _ in raw_days(tmp_path / "raw")] == [D1]


def test_a_day_without_any_raw_file_is_not_counted(tmp_path):
    run_day(tmp_path, D1, {"stripe": [1]})
    status = run_day(tmp_path, D4, {"stripe": None})
    assert status["days_with_success"] == 1
    assert status["removed_today"] == 0
    assert status["open"] == 1
