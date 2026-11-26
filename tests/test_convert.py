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
        "greenhouse", "ashby", "lever", "smartrecruiters", "oracle", "workday", "icims",
        "phenom", "ukg",
    }
    assert len({s.employer for s in SOURCES}) >= 15
    assert len(BY_KEY) == len(SOURCES)


def test_workday():
    page = {
        "total": 2,
        "jobPostings": [
            {
                "title": "Senior Financial Analyst",
                "externalPath": "/job/Lowell-AR/Senior-Financial-Analyst_R-1234-1",
                "locationsText": "Lowell, AR",
                "postedOn": "Posted 30+ Days Ago",
                "bulletFields": ["R-1234"],
            },
            {"bulletFields": ["R-9999"]},  # placeholder without a posting
        ],
    }
    assert only("jbhunt", page) == {
        "posting_id": "jbhunt:R-1234-1",
        "source": "jbhunt",
        "source_id": "R-1234-1",
        "employer": "J.B. Hunt",
        "title": "Senior Financial Analyst",
        "location": "Lowell, AR",
        "department": "",
        "posted_date": "",
        "url": "https://jbhunt.wd501.myworkdayjobs.com/Careers"
        "/job/Lowell-AR/Senior-Financial-Analyst_R-1234-1",
    }


def test_workday_id_survives_a_title_change_and_underscores():
    def page(path, bullets):
        return {"jobPostings": [{"title": "t", "externalPath": path, "bulletFields": bullets}]}

    before = only("jbhunt", page("/job/A/Old-Title_JR_55", ["JR_55"]))
    after = only("jbhunt", page("/job/B/New-Title_JR_55", ["JR_55"]))
    assert before["source_id"] == after["source_id"] == "JR_55"
    assert only("jbhunt", page("/job/A/Title_R77", []))["source_id"] == "R77"


def test_icims():
    page = {
        "totalCount": 1,
        "jobs": [
            {
                "data": {
                    "slug": "22218",
                    "title": "Financial Analyst",
                    "full_location": "Olathe, Kansas",
                    "categories": [{"name": "Finance"}],
                    "department": None,
                    "posted_date": "2026-11-17T22:16:00-0500",
                }
            }
        ],
    }
    row = only("garmin", page)
    assert row["posting_id"] == "garmin:22218"
    assert (row["location"], row["department"]) == ("Olathe, Kansas", "Finance")
    assert row["posted_date"] == "2026-11-18"
    assert row["url"] == "https://careers.garmin.com/jobs/22218"

    page["jobs"][0]["data"]["meta_data"] = {"canonical_url": "https://careers.garmin.com/a/22218"}
    assert only("garmin", page)["url"] == "https://careers.garmin.com/a/22218"


def test_phenom():
    job = {
        "jobSeqNo": "ABC1",
        "jobId": "1",
        "title": "Finance Analyst",
        "location": "United States - Illinois - Lake Forest",
        "cityStateCountry": "Lake Forest, Illinois, United States",
        "category": "Finance",
        "postedDate": "2026-11-06T00:00:00.000+0000",
        "applyUrl": "https://example.com/apply/1",
    }
    row = only("abbott", {"refineSearch": {"totalHits": 1, "data": {"jobs": [job]}}})
    assert row["posting_id"] == "abbott:ABC1"
    assert row["location"] == "Lake Forest, Illinois, United States"
    assert (row["department"], row["posted_date"]) == ("Finance", "2026-11-06")
    assert row["url"] == "https://example.com/apply/1"

    bare = {"jobSeqNo": "S1", "jobId": "R-1", "title": "t", "location": "Dallas, Texas"}
    row = only("southwest", {"refineSearch": {"data": {"jobs": [bare]}}})
    assert row["location"] == "Dallas, Texas"
    assert row["url"] == "https://careers.southwestair.com/us/en/job/R-1"


def test_ukg():
    job = {
        "Id": "g-1",
        "Title": "Financial Analyst",
        "JobCategoryName": "Finance",
        "PostedDate": "2026-11-23T16:07:25.658Z",
        "Locations": [{"Address": {"City": "Kansas City", "State": {"Code": "MO"}}}],
    }
    row = only("hallmark", {"totalCount": 1, "opportunities": [job]})
    assert row["posting_id"] == "hallmark:g-1"
    assert row["location"] == "Kansas City, MO"
    assert (row["department"], row["posted_date"]) == ("Finance", "2026-11-23")
    assert row["url"].endswith("/OpportunityDetail?opportunityId=g-1")

    job["Locations"] = [{"Address": None, "LocalizedDescription": "Home office"}]
    assert only("hallmark", {"opportunities": [job]})["location"] == "Home office"


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
