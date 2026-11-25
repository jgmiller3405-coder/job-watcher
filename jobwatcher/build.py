"""Build data/history.csv from the raw files and nothing else.

Run it with:  uv run python -m jobwatcher.build
"""

import argparse
import csv
from collections.abc import Iterable
from pathlib import Path

from .convert import convert
from .raw import raw_days, read_raw
from .roles import is_in_role
from .sources import BY_KEY

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

COLUMNS = [
    "posting_id", "source", "source_id", "employer", "title", "location", "department",
    "posted_date", "url", "in_role", "first_run", "first_seen", "last_seen", "status",
    "removed_date",
]


def apply_day(history: dict, date: str, listings: dict[str, list[dict]], seen_sources: set) -> None:
    """Fold one day into the history.

    ``listings`` maps each source that has a raw file that day to its postings.
    Sources without a raw file are absent, so their postings are left alone.
    """
    for source, postings in listings.items():
        first_file = source not in seen_sources
        seen_sources.add(source)
        listed = set()
        for posting in postings:
            posting_id = posting["posting_id"]
            listed.add(posting_id)
            row = history.get(posting_id)
            if row is None:
                row = history[posting_id] = {"first_run": first_file, "first_seen": date}
            row.update(posting)  # the latest listing wins for title, location, and so on
            row["in_role"] = is_in_role(row["title"])
            row["last_seen"] = date
            row["status"] = "open"
            row["removed_date"] = ""
        for posting_id, row in history.items():
            if row["source"] == source and row["status"] == "open" and posting_id not in listed:
                row["status"] = "removed"
                row["removed_date"] = date


def build_history(days: Iterable[tuple[str, dict[str, list[dict]]]]) -> list[dict]:
    """History rows, sorted by posting_id, from (date, listings) pairs in date order."""
    history: dict[str, dict] = {}
    seen_sources: set = set()
    for date, listings in days:
        apply_day(history, date, listings, seen_sources)
    return [history[posting_id] for posting_id in sorted(history)]


def load_days(raw_dir: Path):
    for date, files in raw_days(raw_dir):
        listings = {}
        for path in files:
            key, pages = read_raw(path)
            if key not in BY_KEY:
                raise SystemExit(f"{path}: source {key!r} is not in jobwatcher/sources.py")
            listings[key] = convert(BY_KEY[key], pages)
        yield date, listings


def write_history(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {k: str(v).lower() if isinstance(v, bool) else v for k, v in row.items()}
            )


def build(data_dir: Path = DATA) -> list[dict]:
    rows = build_history(load_days(data_dir / "raw"))
    write_history(rows, data_dir / "history.csv")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA, help="data folder (default: data/)")
    args = parser.parse_args()
    rows = build(args.data)
    print(f"{len(rows)} postings written to {args.data / 'history.csv'}")


if __name__ == "__main__":
    main()
