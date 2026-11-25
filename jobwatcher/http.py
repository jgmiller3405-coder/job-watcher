"""A small JSON-over-HTTP helper with retries, built on the standard library."""

import json
import time
import urllib.error
import urllib.request

USER_AGENT = "job-watcher/1.0"
RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


class FetchError(Exception):
    """A request or a source could not be read completely."""


def request_json(
    url: str,
    body: dict | None = None,
    headers: dict | None = None,
    method: str | None = None,
    attempts: int = 4,
    timeout: int = 60,
):
    """Send a request and decode the JSON reply, retrying temporary failures."""
    data = None if body is None else json.dumps(body).encode()
    all_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if data is not None:
        all_headers["Content-Type"] = "application/json"
    all_headers.update(headers or {})

    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, data=data, headers=all_headers, method=method)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in RETRY_STATUS or attempt == attempts:
                raise FetchError(f"HTTP {error.code} from {url}") from error
        except (OSError, ValueError) as error:  # network trouble or a reply that is not JSON
            if attempt == attempts:
                raise FetchError(f"{type(error).__name__} from {url}: {error}") from error
        time.sleep(2**attempt)
    raise FetchError(f"no attempts made for {url}")
