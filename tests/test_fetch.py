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

