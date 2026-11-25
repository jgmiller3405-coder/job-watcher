"""Reading whole boards, and refusing partial ones."""

import pytest

from jobwatcher import fetch
from jobwatcher.http import FetchError
from jobwatcher.sources import BY_KEY


@pytest.fixture(autouse=True)
def no_pause(monkeypatch):
    monkeypatch.setattr(fetch, "PAUSE", 0)


def workday_board(ids, total=None, report_total_once=True):
    total = len(ids) if total is None else total

    def get(url, body=None):
        offset = body["offset"]
        jobs = [
            {"title": "t", "externalPath": f"/job/x/t_{i}", "bulletFields": [i]}
            for i in ids[offset : offset + body["limit"]]
        ]
        shown = total if offset == 0 or not report_total_once else 0
        return {"total": shown, "jobPostings": jobs}

    return get


def test_workday_reads_every_page():
    ids = [f"R{n}" for n in range(45)]
    pages, count = fetch.fetch_source(BY_KEY["nasdaq"], get=workday_board(ids))
    assert count == 45
    assert len(pages) == 3


def test_an_incomplete_download_fails():
    ids = [f"R{n}" for n in range(30)]
    with pytest.raises(FetchError, match="incomplete"):
        fetch.fetch_source(BY_KEY["nasdaq"], get=workday_board(ids, total=100))


def test_a_workday_placeholder_counts_toward_the_total():
    def get(url, body=None):
        return {
            "total": 2,
            "jobPostings": [
                {"title": "t", "externalPath": "/job/x/t_R1", "bulletFields": ["R1"]},
                {"bulletFields": ["R2"]},
            ],
        }

    pages, count = fetch.fetch_source(BY_KEY["nasdaq"], get=get)
    assert (len(pages), count) == (1, 1)


def test_workday_boards_too_large_to_read_fail():
    with pytest.raises(FetchError, match="search term"):
        fetch.fetch_source(BY_KEY["nasdaq"], get=workday_board(["R1"], total=2000))


def test_an_empty_board_fails():
    with pytest.raises(FetchError, match="no postings"):
        fetch.fetch_source(BY_KEY["stripe"], get=lambda url: {"jobs": []})


def test_oracle_sends_the_search_term_and_pages():
    urls = []

    def get(url):
        urls.append(url)
        offset = int(url.split("offset=")[1].split(",")[0])
        batch = [{"Id": str(i), "Title": "Analyst"} for i in range(offset, min(offset + 200, 250))]
        return {"items": [{"TotalJobsCount": 250, "requisitionList": batch}]}

    _, count = fetch.fetch_source(BY_KEY["jpmorgan"], get=get)
    assert count == 250
    assert len(urls) == 2
    assert all("keyword=%22analyst%22" in url for url in urls)


def test_smartrecruiters_pages():
    def get(url):
        offset = int(url.split("offset=")[1])
        batch = [{"id": str(i), "name": "x"} for i in range(offset, min(offset + 100, 150))]
        return {"totalFound": 150, "content": batch}

    _, count = fetch.fetch_source(BY_KEY["experian"], get=get)
    assert count == 150
