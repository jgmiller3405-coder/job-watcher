"""The daily run: fetch every source, rebuild the history, and write the status.

Run it with:  uv run python -m jobwatcher.run
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .build import DATA, build
from .fetch import fetch_source
from .raw import clear_day, raw_days, write_raw
from .sources import SOURCES, Source

WORKERS = 6


def _attempt(source: Source, fetcher) -> tuple[Source, list | None, int, str]:
    try:
        pages, count = fetcher(source)
        return source, pages, count, ""
    except Exception as error:  # one failing source must never stop the run
        return source, None, 0, f"{type(error).__name__}: {error}"


def make_status(rows: list[dict], dates: list[str], now: datetime, results: list[dict]) -> dict:
    today = now.date().isoformat()
    return {
        "run_time": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "first_run_date": dates[0] if dates else "",
        "days_with_success": len(dates),
        "open": sum(row["status"] == "open" for row in rows),
        "new_today": sum(row["first_seen"] == today and not row["first_run"] for row in rows),
        "removed_today": sum(row["removed_date"] == today for row in rows),
        "sources": results,
    }


def run(
    data_dir: Path = DATA,
    sources=SOURCES,
    fetcher=fetch_source,
    now: datetime | None = None,
) -> dict:
    """Do one run and return the status that was written."""
    now = now or datetime.now(timezone.utc)
    today = now.date().isoformat()
    raw_dir = data_dir / "raw"

    with ThreadPoolExecutor(WORKERS) as pool:
        attempts = list(pool.map(lambda source: _attempt(source, fetcher), sources))

    # Replace the day's files. If every source failed (say the network was down),
    # keep whatever an earlier run today managed to collect.
    if any(pages is not None for _, pages, _, _ in attempts):
        clear_day(raw_dir, today)

    results = []
    for source, pages, count, error in attempts:
        ok = pages is not None
        if ok:
            write_raw(raw_dir, today, source.key, pages)
        results.append({"name": source.key, "ok": ok, "count": count})
        print(f"{'ok    ' if ok else 'FAILED'} {source.key:<15} {count:>6} {error}", flush=True)

    rows = build(data_dir)
    status = make_status(rows, [date for date, _ in raw_days(raw_dir)], now, results)
    (data_dir / "status.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA, help="data folder (default: data/)")
    args = parser.parse_args()
    status = run(args.data)
    summary = {key: value for key, value in status.items() if key != "sources"}
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
