"""Assemble the website in _site/: the pages in site/ plus the two data files.

Preview locally:
    uv run python scripts/make_site.py
    uv run python -m http.server -d _site
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(out: Path = ROOT / "_site") -> None:
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(ROOT / "site", out)
    (out / "data").mkdir()
    for name in ("history.csv", "status.json"):
        shutil.copy(ROOT / "data" / name, out / "data" / name)
    print(f"site written to {out}")


if __name__ == "__main__":
    main()
