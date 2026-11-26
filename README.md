# Job Watcher: Financial Analyst

[![Tests](https://github.com/jgmiller3405-coder/job-watcher/actions/workflows/tests.yml/badge.svg)](https://github.com/jgmiller3405-coder/job-watcher/actions/workflows/tests.yml)

Once a day this tool reads the job boards of 49 employers, compares them with
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

The list covers major employers in five areas (Northwest Arkansas, Kansas City,
Chicago, Dallas–Fort Worth, and New York) plus others hiring financial analysts.
"Area" is why an employer is on the list; its board may list jobs anywhere.

| Source key | Employer | Applicant tracking system | Board | Area |
|---|---|---|---|---|
| `jbhunt` | J.B. Hunt | Workday | `Careers` | Northwest Arkansas |
| `carmart` | America's Car-Mart | UKG Pro (UltiPro) | `AME1031ACM/JobBoard/9a085139-ceb8-4e6a-a651-272c1c59be0c` | Northwest Arkansas |
| `garmin` | Garmin | iCIMS | `careers.garmin.com` | Kansas City |
| `hrblock` | H&R Block | iCIMS | `careers.hrblock.com` | Kansas City |
| `hallmark` | Hallmark | UKG Pro (UltiPro) | `HAL1009HLLI/JobBoard/1af38e50-bef2-48c7-8919-d646ae0bee65` | Kansas City |
| `commercebank` | Commerce Bank | Phenom | `careers.commercebank.com` | Kansas City |
| `oracle` | Oracle | Oracle Recruiting | `CX_45001` | Kansas City |
| `abbott` | Abbott | Phenom | `www.jobs.abbott` | Chicago |
| `abbvie` | AbbVie | SmartRecruiters | `AbbVie` | Chicago |
| `conagra` | Conagra Brands | Phenom | `careers.conagrabrands.com` | Chicago |
| `united` | United Airlines | Phenom | `careers.united.com` | Chicago |
| `exelon` | Exelon | iCIMS | `jobs.exeloncorp.com` | Chicago |
| `ulta` | Ulta Beauty | iCIMS | `careers.ulta.com` | Chicago |
| `drw` | DRW | Greenhouse | `drweng` | Chicago |
| `imc` | IMC Trading | Greenhouse | `imc` | Chicago |
| `jumptrading` | Jump Trading | Greenhouse | `jumptrading` | Chicago |
| `williamblair` | William Blair | Greenhouse | `williamblair` | Chicago |
| `texasinstruments` | Texas Instruments | Oracle Recruiting | `CX` | Dallas–Fort Worth |
| `tenet` | Tenet Healthcare | Oracle Recruiting | `CX_1001` | Dallas–Fort Worth |
| `pepsico` | PepsiCo | iCIMS | `www.pepsicojobs.com` | Dallas–Fort Worth |
| `southwest` | Southwest Airlines | Phenom | `careers.southwestair.com` | Dallas–Fort Worth |
| `toyota` | Toyota North America | Phenom | `careers.toyota.com` | Dallas–Fort Worth |
| `matchgroup` | Match Group | Lever | `matchgroup` | Dallas–Fort Worth |
| `americanexpress` | American Express | Oracle Recruiting | `CX_1` | New York |
| `bny` | BNY | Oracle Recruiting | `CX_1001` | New York |
| `goldmansachs` | Goldman Sachs | Oracle Recruiting | `LateralHiring` | New York |
| `jpmorgan` | JPMorgan Chase | Oracle Recruiting | `CX_1001` | New York |
| `nbcuniversal` | NBCUniversal | SmartRecruiters | `NBCUniversal3` | New York |
| `datadog` | Datadog | Greenhouse | `datadog` | New York |
| `janestreet` | Jane Street | Greenhouse | `janestreet` | New York |
| `mongodb` | MongoDB | Greenhouse | `mongodb` | New York |
| `nytimes` | The New York Times | Greenhouse | `thenewyorktimes` | New York |
| `oscar` | Oscar Health | Greenhouse | `oscar` | New York |
| `spotify` | Spotify | Lever | `spotify` | New York |
| `citizens` | Citizens | Oracle Recruiting | `CX_1001` | Other |
| `cummins` | Cummins | Oracle Recruiting | `CX_1` | Other |
| `ford` | Ford | Oracle Recruiting | `CX_1` | Other |
| `honeywell` | Honeywell | Oracle Recruiting | `CX_1` | Other |
| `affirm` | Affirm | Greenhouse | `affirm` | Other |
| `coinbase` | Coinbase | Greenhouse | `coinbase` | Other |
| `point72` | Point72 | Greenhouse | `point72` | Other |
| `robinhood` | Robinhood | Greenhouse | `robinhood` | Other |
| `sofi` | SoFi | Greenhouse | `sofi` | Other |
| `stripe` | Stripe | Greenhouse | `stripe` | Other |
| `plaid` | Plaid | Ashby | `plaid` | Other |
| `ramp` | Ramp | Ashby | `ramp` | Other |
| `palantir` | Palantir | Lever | `palantir` | Other |
| `experian` | Experian | SmartRecruiters | `Experian` | Other |
| `servicenow` | ServiceNow | SmartRecruiters | `ServiceNow` | Other |

All boards return JSON without a login. iCIMS and Phenom boards are read through
the employer's own career site, which those systems run.

**Search term:** JPMorgan Chase, H&R Block, and Ulta Beauty list more than 5,000
postings, so each is requested with the search term **`analyst`**. Every other
board is read in full. A Workday board that reaches 2,000 postings (the most
Workday will count) is reported as failed until a search term is added.

**Left out:** Walmart and Tyson Foods use Workday boards that answered GitHub
Actions with block pages, as did most other Workday employers tried.

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

- **Workday** has no department, and gives only relative posting dates ("Posted
  30+ Days Ago"), so `posted_date` is empty. Postings with several locations show
  a count such as "2 Locations".
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

The Browse location filter starts on five areas: Northwest Arkansas and the
Kansas City, Chicago, Dallas–Fort Worth, and New York City metros. Each can be
picked alone, and "All locations" shows every open posting. The rules are in
[`site/areas.js`](site/areas.js). They read the one location kept for each
posting, so a job that names an area only as a second location may be missed.
The history file, Today page, Market page, and daily issue cover all locations.

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
| `site/areas.js` | the location areas for the Browse filter |
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
