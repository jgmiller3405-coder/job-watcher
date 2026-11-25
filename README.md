# Job Watcher: Financial Analyst

[![Tests](https://github.com/jgmiller3405-coder/job-watcher/actions/workflows/tests.yml/badge.svg)](https://github.com/jgmiller3405-coder/job-watcher/actions/workflows/tests.yml)

Once a day this tool reads the job boards of 22 employers, compares them with
what it saw before, records which postings are new and which are gone, opens a
GitHub Issue listing both, and publishes the results as a website.

**Site:** <https://jgmiller3405-coder.github.io/job-watcher/>

## How a run works

GitHub Actions runs the pipeline daily at 11:17 UTC. A backup run at 18:47 UTC
does nothing if the day already has a successful run.

1. Every source is called and its replies are saved, compressed, in
   `data/raw/<date>/<source>.json.gz`. A source that fails writes no file and
   does not stop the others. A board that can only be read partly counts as
   failed, so missing pages are never mistaken for removed postings. (Some boards
   count a few postings they never list, so a steady shortfall under 0.5% is
   accepted.)
2. `data/history.csv` is rebuilt from all the raw files.
3. `data/status.json` records the run, including each source's success or failure.
4. An issue titled with the date lists new and removed postings, and earlier
   daily issues are closed. Long lists continue in comments.
5. The data is committed, the tests are started, and the site is republished.

Dates are UTC. A second run on the same day replaces that day's raw files and
updates the same issue. If every source fails, any files already collected that
day are kept and the workflow is marked failed.

## Building the history from the raw files

```bash
uv run python -m jobwatcher.build
```

The result depends only on the raw files and the code, so running it again gives
the same file, and a change to a rule applies to every day.

Other commands:

```bash
uv run pytest                                  # tests
uv run python -m jobwatcher.run                # a full run (fetches every board)
uv run python -m jobwatcher.issue --dry-run    # print the day's issue text
uv run python scripts/make_site.py             # assemble the site in _site/
uv run python -m http.server -d _site          # preview it at http://localhost:8000
```

## Title rule (financial analyst)

A posting is marked `in_role` when its title, ignoring case:

1. does **not** contain "investment banking", "engineer", "engineering",
   "developer", "system", or "systems"; and then either
2. names "FP&A" or "financial planning and/& analysis", and also says "analyst",
   or says "associate" without "director", "manager", "vice president", "VP", or
   "AVP"; or
3. otherwise says "analyst" and also "finance" or "financial". Those two words do
   not count inside "financial crime(s)", "financial intelligence", "financial
   service(s)", "financial institution(s)", "financial sponsor(s)", "financial
   advisor(s)", or "leveraged", "structured", "public", "project", "trade",
   "vendor", or "investment grade" finance.

The code is in [`jobwatcher/roles.py`](jobwatcher/roles.py).

## Sources

| Source key | Employer | Applicant tracking system | Board |
|---|---|---|---|
| `americanexpress` | American Express | Oracle Recruiting | `CX_1` |
| `bny` | BNY | Oracle Recruiting | `CX_1001` |
| `citizens` | Citizens | Oracle Recruiting | `CX_1001` |
| `cummins` | Cummins | Oracle Recruiting | `CX_1` |
| `ford` | Ford | Oracle Recruiting | `CX_1` |
| `goldmansachs` | Goldman Sachs | Oracle Recruiting | `LateralHiring` |
| `honeywell` | Honeywell | Oracle Recruiting | `CX_1` |
| `jpmorgan` | JPMorgan Chase | Oracle Recruiting | `CX_1001` |
| `texasinstruments` | Texas Instruments | Oracle Recruiting | `CX` |
| `affirm` | Affirm | Greenhouse | `affirm` |
| `coinbase` | Coinbase | Greenhouse | `coinbase` |
| `point72` | Point72 | Greenhouse | `point72` |
| `robinhood` | Robinhood | Greenhouse | `robinhood` |
| `sofi` | SoFi | Greenhouse | `sofi` |
| `stripe` | Stripe | Greenhouse | `stripe` |
| `plaid` | Plaid | Ashby | `plaid` |
| `ramp` | Ramp | Ashby | `ramp` |
| `palantir` | Palantir | Lever | `palantir` |
| `abbvie` | AbbVie | SmartRecruiters | `AbbVie` |
| `experian` | Experian | SmartRecruiters | `Experian` |
| `nbcuniversal` | NBCUniversal | SmartRecruiters | `NBCUniversal3` |
| `servicenow` | ServiceNow | SmartRecruiters | `ServiceNow` |

All boards return JSON without a login.

**Search term:** JPMorgan Chase lists more than 5,000 postings, so it is requested
with the search term **`analyst`**. Every other board is read in full.

Workday boards are not used: they were answering requests from GitHub Actions
with HTTP 429 block pages.

## Data

### `data/history.csv`

One row per posting, sorted by `posting_id`.

| Column | Meaning |
|---|---|
| `posting_id` | `<source>:<source_id>` |
| `source`, `source_id` | the source key and the board's own ID |
| `employer`, `title`, `location`, `department` | as most recently listed |
| `posted_date` | the board's posting date (UTC), if it gives one |
| `url` | link to the posting |
| `in_role` | `true` if the title rule matches |
| `first_run` | `true` if it was in the first raw file of its source |
| `first_seen`, `last_seen` | first and latest day the board listed it |
| `status` | `open` or `removed` |
| `removed_date` | the day it was first found missing |

Columns a board does not provide are empty:

- **Oracle** uses the job family as the department when no department is given.

### `data/status.json`

`run_time`, `first_run_date`, `days_with_success`, `open`, `new_today`,
`removed_today`, and `sources` (each with `name`, `ok`, and `count`).

## Website

| Page | Contents |
|---|---|
| Today (`index.html`) | last run time, the four counts, new and removed postings, source status |
| Browse (`browse.html`) | open postings with role switch, filters, title search, sort, apply links, and a shortlist saved in the browser |
| Market (`market.html`) | six findings computed in the browser from the history file |

The site installs as an app. Online it loads the data from the network; offline it
opens with the last data it loaded.

## Files

| File | What it does |
|---|---|
| `README.md` | this document |
| `pyproject.toml`, `uv.lock` | Python project and locked dependencies |
| `.gitignore` | files Git does not track |
| `.gitattributes` | keeps line endings identical so rebuilt files match |
| `jobwatcher/__init__.py` | marks the Python package |
| `jobwatcher/sources.py` | the watch list |
| `jobwatcher/http.py` | JSON requests with retries |
| `jobwatcher/fetch.py` | downloads each board completely |
| `jobwatcher/convert.py` | converts each system's replies to the common columns |
| `jobwatcher/raw.py` | reads and writes the compressed raw files |
| `jobwatcher/roles.py` | the title rule |
| `jobwatcher/build.py` | builds `history.csv` from the raw files |
| `jobwatcher/run.py` | the daily run: fetch, build, status |
| `jobwatcher/issue.py` | writes the daily issue and closes older ones |
| `scripts/make_site.py` | assembles the site with the data files |
| `.github/workflows/daily.yml` | the scheduled daily run |
| `.github/workflows/tests.yml` | runs the tests on every push |
| `.github/workflows/pages.yml` | publishes the site to GitHub Pages |
| `tests/test_convert.py` | tests each system's conversion |
| `tests/test_fetch.py` | tests paging and partial downloads |
| `tests/test_roles.py` | tests the title rule |
| `tests/test_history.py` | tests first seen, last seen, removed, reopened, and the run |
| `tests/test_issue.py` | tests the daily issue |
| `site/index.html`, `site/today.js` | Today page |
| `site/browse.html`, `site/browse.js` | Browse page |
| `site/market.html`, `site/market.js` | Market page |
| `site/charts.js` | draws the charts |
| `site/common.js` | loads the data and builds shared elements |
| `site/style.css` | the shared fonts, colors, and layout |
| `site/manifest.webmanifest` | makes the site installable |
| `site/sw.js` | service worker for offline use |
| `site/icons/icon-192.png`, `site/icons/icon-512.png` | app icons |
| `data/history.csv` | the posting history |
| `data/status.json` | the latest run |
| `data/raw/<date>/<source>.json.gz` | what each source returned each day |
