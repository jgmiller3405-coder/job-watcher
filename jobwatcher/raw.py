"""Read and write the compressed raw files: data/raw/<date>/<source>.json.gz."""

import gzip
import json
import re
from pathlib import Path

SUFFIX = ".json.gz"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def write_raw(raw_dir: Path, date: str, key: str, pages: list) -> Path:
    folder = raw_dir / date
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{key}{SUFFIX}"
    text = json.dumps({"source": key, "pages": pages}, ensure_ascii=False, separators=(",", ":"))
    path.write_bytes(gzip.compress(text.encode("utf-8"), mtime=0))
    return path


def read_raw(path: Path) -> tuple[str, list]:
    data = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
    return data["source"], data["pages"]


def clear_day(raw_dir: Path, date: str) -> None:
    """Remove a day's raw files, so a second run on that day replaces them."""
    for path in (raw_dir / date).glob(f"*{SUFFIX}"):
        path.unlink()


def raw_days(raw_dir: Path) -> list[tuple[str, list[Path]]]:
    """Every date that has at least one raw file, oldest first."""
    if not raw_dir.is_dir():
        return []
    days = []
    for folder in sorted(raw_dir.iterdir()):
        if folder.is_dir() and DATE.match(folder.name):
            files = sorted(folder.glob(f"*{SUFFIX}"))
            if files:
                days.append((folder.name, files))
    return days
