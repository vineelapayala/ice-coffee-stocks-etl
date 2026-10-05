"""
Downloads the Robusta stock CSV reports discovered from ICE Report 173.
Handles individual file downloads, HTTP 429 rate limiting, retries, five-second
intervals between batch downloads, and local storage of the historical reports.
"""
import time
from pathlib import Path

from src.utils.file_utils import save_file
from src.utils.http_utils import (
    DEFAULT_TIMEOUT,
    create_session,
    get_retry_wait_seconds,
)


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/octet-stream,*/*",
}


def download_robusta_report(
    url: str,
    output_path: Path,
    max_retries: int = 3,
) -> Path:
    """
    Download a single Robusta stock report.

    Returns:
        Path to the downloaded CSV file.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if output_path.exists():
        print(
            f"Already exists: {output_path.name}"
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
                    f"{output_path.name}"
                )

                print(
                    f"Waiting "
                    f"{wait_seconds} seconds "
                    f"before retry "
                    f"{attempt}/{max_retries}..."
                )

                if attempt < max_retries:
                    time.sleep(
                        wait_seconds
                    )
                    continue

                raise RuntimeError(
                    "Maximum retries exceeded "
                    f"for Robusta report: {url}"
                )

            response.raise_for_status()

            if not response.content:
                raise ValueError(
                    f"Empty response received "
                    f"from {url}"
                )

            save_file(
                content=response.content,
                output_path=output_path,
            )

            print(
                f"Downloaded: "
                f"{output_path.name}"
            )

            return output_path

    raise RuntimeError(
        "Failed to download "
        f"Robusta report: {url}"
    )


def download_robusta_reports(
    reports: list[dict],
    output_dir: Path,
    delay_seconds: float = 5.0,
) -> list[dict]:
    """
    Download multiple Robusta stock reports.

    Returns:
        List containing the status of each report.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    for index, report in enumerate(
        reports,
        start=1,
    ):

        report_date = report["report_date"]
        report_url = report["url"]
        file_name = report["file_name"]

        output_path = (
            output_dir / file_name
        )

        already_existed = (
            output_path.exists()
        )

        print(
            f"\n[{index}/{len(reports)}] "
            f"{report_date}"
        )

        try:
            download_robusta_report(
                url=report_url,
                output_path=output_path,
            )

            results.append(
                {
                    "report_date": report_date,
                    "status": (
                        "already_exists"
                        if already_existed
                        else "downloaded"
                    ),
                    "file_path": output_path,
                }
            )

        except (RuntimeError, ValueError) as exc:

            print(
                f"Failed: {report_date}"
            )

            print(exc)

            results.append(
                {
                    "report_date": report_date,
                    "status": "failed",
                    "file_path": None,
                    "error": str(exc),
                }
            )

        if (
            index < len(reports)
            and not already_existed
        ):
            print(
                f"Waiting "
                f"{delay_seconds} seconds..."
            )

            time.sleep(
                delay_seconds
            )

    return results