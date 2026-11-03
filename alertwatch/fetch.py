from __future__ import annotations

import time

import httpx

from alertwatch.config import RequestSpec


def fetch_url(url: str, request: RequestSpec) -> str:
    """GET url with configured timeout, user-agent, and basic retries."""
    headers = {"User-Agent": request.user_agent}
    attempts = max(request.retries, 0) + 1
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = httpx.get(
                url,
                headers=headers,
                timeout=request.timeout,
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.text
        except (httpx.HTTPError, OSError) as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(0.25 * (attempt + 1))
    assert last_error is not None
    raise last_error
