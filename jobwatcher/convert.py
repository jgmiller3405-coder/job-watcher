"""Turn each applicant tracking system's reply into one common set of columns."""

from datetime import datetime, timezone

from .sources import Source


def clean(value) -> str:
    """Collapse whitespace; treat a missing value as empty."""
    return " ".join(str(value).split()) if value is not None else ""


def utc_date(value) -> str:
    """The UTC date of an ISO 8601 string or a millisecond timestamp, else empty."""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date().isoformat()
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is not None:
        moment = moment.astimezone(timezone.utc)
    return moment.date().isoformat()


def _row(source_id, title, url, location="", department="", posted_date="") -> dict:
    return {
        "source_id": clean(source_id),
        "title": clean(title),
        "location": clean(location),
        "department": clean(department),
        "posted_date": posted_date,
        "url": clean(url),
    }


def workday_id(job: dict) -> str:
    """The requisition ID at the end of the posting's path, e.g. ``R-12345-1``.

    The rest of the path holds the title and location, which employers edit. The
    requisition number (first bullet field) says where the stable part begins.
    """
    tail = job["externalPath"].rstrip("/").rsplit("/", 1)[-1]
    for field in job.get("bulletFields") or []:
        start = tail.rfind("_" + field)
        if field and start >= 0:
            return tail[start + 1 :]
    return tail.rsplit("_", 1)[-1]


def convert_workday(source: Source, page: dict):
    for job in page["jobPostings"]:
        if "externalPath" not in job:  # Workday occasionally returns an empty placeholder
            continue
        # "postedOn" is relative text ("Posted 30+ Days Ago"), so there is no posted date.
        yield _row(
            workday_id(job),
            job.get("title"),
            f"https://{source.host}/{source.board}{job['externalPath']}",
            location=job.get("locationsText"),
        )


def convert_greenhouse(source: Source, page: dict):
    for job in page["jobs"]:
        departments = job.get("departments") or []
        yield _row(
            job["id"],
            job.get("title"),
            job.get("absolute_url"),
            location=(job.get("location") or {}).get("name"),
            department=departments[0].get("name") if departments else "",
            posted_date=utc_date(job.get("first_published")),
        )


def convert_ashby(source: Source, page: dict):
    for job in page["jobs"]:
        yield _row(
            job["id"],
            job.get("title"),
            job.get("jobUrl"),
            location=job.get("location"),
            department=job.get("department"),
            posted_date=utc_date(job.get("publishedAt")),
        )


def convert_lever(source: Source, page: list):
    for job in page:
        categories = job.get("categories") or {}
        yield _row(
            job["id"],
            job.get("text"),
            job.get("hostedUrl"),
            location=categories.get("location"),
            department=categories.get("department") or categories.get("team"),
            posted_date=utc_date(job.get("createdAt")),
        )


def convert_smartrecruiters(source: Source, page: dict):
    for job in page["content"]:
        location = job.get("location") or {}
        full = location.get("fullLocation") or ", ".join(
            location.get(part) or "" for part in ("city", "region", "country")
        )
        yield _row(
            job["id"],
            job.get("name"),
            f"https://jobs.smartrecruiters.com/{source.board}/{job['id']}",
            location=", ".join(part.strip() for part in full.split(",") if part.strip()),
            department=(job.get("department") or {}).get("label"),
            posted_date=utc_date(job.get("releasedDate")),
        )


def convert_oracle(source: Source, page: dict):
    for job in page["items"][0]["requisitionList"]:
        yield _row(
            job["Id"],
            job.get("Title"),
            f"https://{source.host}/hcmUI/CandidateExperience/en/sites/{source.board}/job/{job['Id']}",
            location=job.get("PrimaryLocation"),
            department=job.get("Department") or job.get("JobFamily"),
            posted_date=utc_date(job.get("PostedDate")),
        )


CONVERTERS = {
    "workday": convert_workday,
    "greenhouse": convert_greenhouse,
    "ashby": convert_ashby,
    "lever": convert_lever,
    "smartrecruiters": convert_smartrecruiters,
    "oracle": convert_oracle,
}


def convert(source: Source, pages: list) -> list[dict]:
    """All postings in a source's pages, one row per source ID."""
    rows: dict[str, dict] = {}
    for page in pages:
        for row in CONVERTERS[source.ats](source, page):
            row = {
                "posting_id": f"{source.key}:{row['source_id']}",
                "source": source.key,
                "employer": source.employer,
                **row,
            }
            rows[row["posting_id"]] = row
    return list(rows.values())
