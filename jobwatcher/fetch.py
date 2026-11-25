"""Download every posting from a source, keeping the replies exactly as returned.

Each fetcher returns a list of "pages" (the decoded JSON replies). A source is
only successful if the whole board was read: a partial download would make the
missing postings look removed.
"""

import time
import urllib.parse
from collections.abc import Callable

from .convert import convert
from .http import FetchError, request_json
from .sources import Source

ORACLE_PAGE = 200
SMARTRECRUITERS_PAGE = 100
PASSES = 5
TOLERANCE = 0.005  # share of a paged board that may be missed because it changed mid-download
PAUSE = 0.15  # seconds between pages, to be polite


def _paged(source: Source, get_page: Callable[[int], tuple[dict, int, int]]) -> list:
    """Collect pages until every posting has been seen.

    ``get_page(offset)`` returns (reply, number of postings in it, board total).
    Boards reorder while being read, so extra passes pick up anything skipped.
    """
    pages: list = []
    total = 0
    found = -1
    for _ in range(PASSES):
        previous = found
        offset = 0
        while True:
            reply, size, reply_total = get_page(offset)
            if offset == 0:
                total = reply_total
            pages.append(reply)
            offset += size
            if size == 0 or offset >= total:
                break
            time.sleep(PAUSE)
        found = len(convert(source, pages))
        # Some boards count a few postings they never list, so stop once a pass adds none.
        if found >= total or (found == previous and found >= total * (1 - TOLERANCE)):
            return pages
    if found >= total * (1 - TOLERANCE):
        return pages
    raise FetchError(f"incomplete download: {found} of {total} postings")


def fetch_oracle(source: Source, get=request_json) -> list:
    base = f"https://{source.host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"

    def get_page(offset: int):
        finder = [f"siteNumber={source.board}"]
        if source.search:
            finder.append("keyword=" + urllib.parse.quote(f'"{source.search}"'))
        finder += [f"limit={ORACLE_PAGE}", f"offset={offset}", "sortBy=POSTING_DATES_DESC"]
        reply = get(
            f"{base}?onlyData=true&expand=requisitionList.secondaryLocations"
            f"&finder=findReqs;{','.join(finder)}"
        )
        result = reply["items"][0]
        return reply, len(result["requisitionList"]), result["TotalJobsCount"]

    return _paged(source, get_page)


def fetch_smartrecruiters(source: Source, get=request_json) -> list:
    base = f"https://api.smartrecruiters.com/v1/companies/{source.board}/postings"

    def get_page(offset: int):
        query = {"limit": SMARTRECRUITERS_PAGE, "offset": offset}
        if source.search:
            query["q"] = source.search
        reply = get(f"{base}?{urllib.parse.urlencode(query)}")
        return reply, len(reply["content"]), reply["totalFound"]

    return _paged(source, get_page)


def fetch_greenhouse(source: Source, get=request_json) -> list:
    return [get(f"https://boards-api.greenhouse.io/v1/boards/{source.board}/jobs?content=true")]


def fetch_ashby(source: Source, get=request_json) -> list:
    return [get(f"https://api.ashbyhq.com/posting-api/job-board/{source.board}")]


def fetch_lever(source: Source, get=request_json) -> list:
    return [get(f"https://api.lever.co/v0/postings/{source.board}?mode=json")]


FETCHERS = {
    "oracle": fetch_oracle,
    "smartrecruiters": fetch_smartrecruiters,
    "greenhouse": fetch_greenhouse,
    "ashby": fetch_ashby,
    "lever": fetch_lever,
}


def fetch_source(source: Source, get=request_json) -> tuple[list, int]:
    """Return (pages, posting count). Raises if the board cannot be read."""
    pages = FETCHERS[source.ats](source, get=get)
    count = len(convert(source, pages))
    if count == 0:
        # An empty reply from these employers means a broken board, not zero openings.
        raise FetchError("board returned no postings")
    return pages, count
