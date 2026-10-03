from datetime import date
from pathlib import Path
import time

import requests


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
    session: requests.Session | None = None,
    max_retries: int = 3,
) -> Path | None:

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

    output_path = (
        output_dir / file_name
    )

    if output_path.exists():
        print(
            f"Already exists: {file_name}"
        )
        return output_path

    client = (
        session
        if session is not None
        else requests.Session()
    )

    for attempt in range(
        1,
        max_retries + 1,
    ):

        try:

            response = client.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=30,
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

                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )

                if retry_after:

                    try:
                        wait_seconds = int(
                            retry_after
                        )
                    except ValueError:
                        wait_seconds = 60

                else:

                    wait_seconds = min(
                        60 * (2 ** (attempt - 1)),
                        900,
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

                time.sleep(
                    wait_seconds
                )

                continue

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

            output_path.write_bytes(
                response.content
            )

            print(
                f"Downloaded: {file_name}"
            )

            return output_path

        except requests.RequestException as exc:

            if attempt == max_retries:

                raise RuntimeError(
                    "Failed to download "
                    f"Arabica report for "
                    f"{report_date}: {exc}"
                ) from exc

            wait_seconds = min(
                10 * (2 ** (attempt - 1)),
                120,
            )

            print(
                f"Request failed for "
                f"{report_date}: {exc}"
            )

            print(
                f"Retrying in "
                f"{wait_seconds} seconds..."
            )

            time.sleep(
                wait_seconds
            )

    raise RuntimeError(
        f"Failed to download "
        f"Arabica report for "
        f"{report_date}"
    )