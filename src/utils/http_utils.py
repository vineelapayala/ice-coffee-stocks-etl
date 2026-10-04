import requests


DEFAULT_TIMEOUT = 30


def create_session() -> requests.Session:
    """Create a new HTTP session."""

    return requests.Session()


def get_retry_wait_seconds(
    retry_after: str | None,
    attempt: int,
    max_wait_seconds: int = 900,
) -> int:
    """
    Calculate how long to wait before retrying a request.

    Uses the Retry-After header when available.
    Otherwise, uses exponential backoff.
    """

    if retry_after:
        try:
            return int(retry_after)
        except ValueError:
            return 60

    return min(
        60 * (2 ** (attempt - 1)),
        max_wait_seconds,
    )