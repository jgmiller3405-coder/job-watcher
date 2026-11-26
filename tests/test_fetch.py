"""Reading whole boards, and refusing partial ones."""

import pytest

from jobwatcher import fetch
from jobwatcher.http import FetchError
from jobwatcher.sources import BY_KEY


@pytest.fixture(autouse=True)
def no_pause(monkeypatch):
    monkeypatch.setattr(fetch, "PAUSE", 0)


def smartrecruiters_board(count, total=None):
    total = count if total is None else total

    def get(url):
        offset = int(url.split("offset=")[1])
        batch = [{"id": str(i), "name": "x"} for i in range(offset, min(offset + 100, count))]
        return {"totalFound": total, "content": batch}

    return get


def test_smartrecruiters_reads_every_page():
    pages, count = fetch.fetch_source(BY_KEY["experian"], get=smartrecruiters_board(250))
    assert (len(pages), count) == (3, 250)


def test_an_incomplete_download_fails():
    with pytest.raises(FetchError, match="incomplete"):
        fetch.fetch_source(BY_KEY["experian"], get=smartrecruiters_board(30, total=100))


def test_a_posting_skipped_by_reordering_is_found_on_a_second_pass():
    calls = []

    def get(url):
        offset = int(url.split("offset=")[1])
        calls.append(offset)
        # The first pass repeats one posting and misses another.
        ids = range(150) if len(calls) > 2 else [*range(149), 0]
        batch = [{"id": str(i), "name": "x"} for i in list(ids)[offset : offset + 100]]
        return {"totalFound": 150, "content": batch}

    _, count = fetch.fetch_source(BY_KEY["experian"], get=get)
    assert count == 150
    assert calls == [0, 100, 0, 100]


def test_a_few_postings_that_are_never_listed_are_accepted_after_two_passes():
    pages, count = fetch.fetch_source(BY_KEY["experian"], get=smartrecruiters_board(999, total=1000))
    assert count == 999
    assert len(pages) == 22  # two passes of ten pages and an empty reply each, not five


def test_workday_reads_every_page_and_counts_placeholders():
    jobs = [{"title": "t", "externalPath": f"/job/x/t_R{n}", "bulletFields": [f"R{n}"]} for n in range(44)]
    jobs.append({"bulletFields": ["R99"]})

    def get(url, body=None):
        offset = body["offset"]
        total = len(jobs) if offset == 0 else 0  # Workday reports it once
        return {"total": total, "jobPostings": jobs[offset : offset + body["limit"]]}

    pages, count = fetch.fetch_source(BY_KEY["jbhunt"], get=get)
    assert (len(pages), count) == (3, 44)


def test_workday_boards_too_large_to_read_fail():
    with pytest.raises(FetchError, match="search term"):
        fetch.fetch_source(BY_KEY["jbhunt"], get=lambda url, body: {"total": 2000, "jobPostings": []})


def test_icims_pages_by_number_and_sends_the_search_term():
    urls = []

    def get(url):
        urls.append(url)
        page = int(url.split("page=")[1].split("&")[0])
        ids = range((page - 1) * 100, min(page * 100, 130))
        return {"totalCount": 130, "jobs": [{"data": {"slug": str(i), "title": "Analyst"}} for i in ids]}

    _, count = fetch.fetch_source(BY_KEY["ulta"], get=get)
    assert count == 130
    assert len(urls) == 2
    assert all("keywords=analyst" in url for url in urls)


def test_phenom_pages():
    def get(url, body):
        ids = range(body["from"], min(body["from"] + body["size"], 150))
        jobs = [{"jobSeqNo": str(i), "title": "t"} for i in ids]
        return {"refineSearch": {"totalHits": 150, "data": {"jobs": jobs}}}

    _, count = fetch.fetch_source(BY_KEY["abbott"], get=get)
    assert count == 150


def test_ukg_pages():
    def get(url, body):
        skip = body["opportunitySearch"]["Skip"]
        jobs = [{"Id": str(i), "Title": "t"} for i in range(skip, min(skip + 100, 120))]
        return {"totalCount": 120, "opportunities": jobs}

    _, count = fetch.fetch_source(BY_KEY["hallmark"], get=get)
    assert count == 120


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

