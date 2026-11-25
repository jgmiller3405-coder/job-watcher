"""Each source system's reply becomes the common columns."""

from jobwatcher.convert import convert, utc_date
from jobwatcher.sources import BY_KEY, SOURCES

COMMON = {
    "posting_id", "source", "source_id", "employer", "title", "location", "department",
    "posted_date", "url",
}


def only(source_key, page):
    rows = convert(BY_KEY[source_key], [page])
    assert len(rows) == 1
    assert set(rows[0]) == COMMON
    return rows[0]


def test_every_system_in_the_watch_list_is_covered_here():
    assert {s.ats for s in SOURCES} == {
        "greenhouse", "ashby", "lever", "smartrecruiters", "oracle",
    }
    assert len({s.employer for s in SOURCES}) >= 15
    assert len(BY_KEY) == len(SOURCES)


def test_greenhouse():
    page = {
        "jobs": [
            {
                "id": 42,
                "title": "  Finance   Analyst ",
                "absolute_url": "https://example.com/jobs/42",
                "location": {"name": "New York"},
                "departments": [{"name": "Finance"}],
                "first_published": "2026-03-01T22:00:00-05:00",
            }
        ]
    }
    row = only("stripe", page)
    assert row["posting_id"] == "stripe:42"
    assert row["title"] == "Finance Analyst"
    assert (row["location"], row["department"]) == ("New York", "Finance")
    assert row["posted_date"] == "2026-03-02"  # converted to the UTC date
    assert row["url"] == "https://example.com/jobs/42"


def test_ashby():
    page = {
        "jobs": [
            {
                "id": "abc",
                "title": "Analyst",
                "department": "Operations",
                "location": "Remote",
                "publishedAt": "2026-04-07T17:12:35.753+00:00",
                "jobUrl": "https://jobs.ashbyhq.com/ramp/abc",
            }
        ]
    }
    row = only("ramp", page)
    assert row["posting_id"] == "ramp:abc"
    assert (row["location"], row["department"]) == ("Remote", "Operations")
    assert row["posted_date"] == "2026-04-07"
    assert row["url"].endswith("/ramp/abc")


def test_lever():
    page = [
        {
            "id": "xyz",
            "text": "FP&A Analyst",
            "categories": {"location": "Denver", "team": "Finance"},
            "createdAt": 1_767_225_600_000,
            "hostedUrl": "https://jobs.lever.co/palantir/xyz",
        }
    ]
    row = only("palantir", page)
    assert row["posting_id"] == "palantir:xyz"
    assert row["title"] == "FP&A Analyst"
    assert (row["location"], row["department"]) == ("Denver", "Finance")
    assert row["posted_date"] == "2026-01-01"
    assert row["url"] == "https://jobs.lever.co/palantir/xyz"


def test_smartrecruiters():
    page = {
        "totalFound": 1,
        "content": [
            {
                "id": "744",
                "name": "Financial Analyst",
                "releasedDate": "2026-11-25T18:40:39.014Z",
                "location": {"fullLocation": "São Paulo, , Brazil"},
                "department": {"label": "Finance"},
            }
        ],
    }
    row = only("experian", page)
    assert row["posting_id"] == "experian:744"
    assert row["location"] == "São Paulo, Brazil"
    assert row["department"] == "Finance"
    assert row["posted_date"] == "2026-11-25"
    assert row["url"] == "https://jobs.smartrecruiters.com/Experian/744"


def test_oracle():
    page = {
        "items": [
            {
                "TotalJobsCount": 1,
                "requisitionList": [
                    {
                        "Id": "210",
                        "Title": "Financial Analyst",
                        "PostedDate": "2026-11-25",
                        "PrimaryLocation": "Tampa, FL, United States",
                        "Department": None,
                        "JobFamily": "Analysts",
                    }
                ],
            }
        ]
    }
    row = only("jpmorgan", page)
    assert row["posting_id"] == "jpmorgan:210"
    assert row["department"] == "Analysts"
    assert row["posted_date"] == "2026-11-25"
    assert row["url"] == (
        "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210"
    )


def test_missing_values_are_left_empty():
    row = only("stripe", {"jobs": [{"id": 1, "title": "x", "absolute_url": "u", "location": None}]})
    assert row["location"] == row["department"] == row["posted_date"] == ""


def test_a_posting_listed_twice_is_one_row():
    page = {"jobs": [{"id": 1, "title": "x", "absolute_url": "u"}]}
    assert len(convert(BY_KEY["stripe"], [page, page])) == 1


def test_utc_date():
    assert utc_date(None) == utc_date("") == ""
    assert utc_date("2026-01-31") == "2026-01-31"
    assert utc_date("2026-01-31T23:30:00-02:00") == "2026-02-01"
