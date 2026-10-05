"""
Downloads ICE Coffee C Arabica certified warehouse stock reports from Report 42.
Generates date-specific XLS URLs and handles HTTP retries, rate limiting, and
local storage of the downloaded daily stock reports.
"""
from datetime import date
from pathlib import Path

from src.utils.file_utils import save_file
from src.utils.http_utils import (
    DEFAULT_TIMEOUT,
    create_session,
    get_retry_wait_seconds,
)


ARABICA_BASE_URL = (
    "https://www.ice.com/publicdocs/futures_us_reports/coffee"
)


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0 Safari/537.36"
    ),
    "Accept": "application/vnd.ms-excel,application/octet-stream,*/*",
}


def download_arabica_report(
    report_date: date,
    output_dir: Path,
    max_retries: int = 3,
) -> Path | None:
    """
    Download an ICE Arabica certified stock report.

    Returns:
        Path to the downloaded file, or None when
        the report is unavailable.
    """

    date_string = report_date.strftime("%Y%m%d")

    file_name = (
        f"coffee_cert_stock_{date_string}.xls"
    )

    url = (
        f"{ARABICA_BASE_URL}/{file_name}"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = output_dir / file_name

    if output_path.exists():
        print(
            f"Already exists: {file_name}"
        )
        return output_path

    with create_session() as client:

        for attempt in range(
            1,
            max_retries + 1,
        ):

            response = client.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=DEFAULT_TIMEOUT,
            )

            # Report genuinely does not exist.
            if response.status_code == 404:

                print(
                    f"Report unavailable: "
                    f"{report_date}"
                )

                return None

            # ICE rate limit.
            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                wait_seconds = get_retry_wait_seconds(
                    retry_after=retry_after,
                    attempt=attempt,
                )

                print(
                    f"HTTP 429 for "
                    f"{report_date}"
                )

                print(
                    f"Waiting "
                    f"{wait_seconds} seconds "
                    f"before retry "
                    f"{attempt}/{max_retries}..."
                )

                if attempt < max_retries:
                    import time

                    time.sleep(
                        wait_seconds
                    )
                    continue

                raise RuntimeError(
                    "Maximum retries exceeded "
                    f"for Arabica report: {report_date}"
                )

            response.raise_for_status()

            if not response.content:

                raise ValueError(
                    f"Empty response received "
                    f"from {url}"
                )

            # Validate that the response looks
            # like an old-style XLS file.
            if not response.content.startswith(
                b"\xD0\xCF\x11\xE0"
            ):

                raise ValueError(
                    "Response does not appear "
                    f"to be an XLS file: {url}"
                )

            save_file(
                content=response.content,
                output_path=output_path,
            )

            print(
                f"Downloaded: {file_name}"
            )

            return output_path

    raise RuntimeError(
        "Failed to download "
        f"Arabica report for {report_date}"
    )