from pathlib import Path
import time

import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/octet-stream,*/*",
}


def download_robusta_report(
    report_url: str,
    output_path: Path,
    session: requests.Session | None = None,
    max_retries: int = 3,
) -> Path:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if output_path.exists():
        print(
            f"Already exists: {output_path.name}"
        )
        return output_path

    client = session or requests.Session()

    for attempt in range(1, max_retries + 1):

        try:

            response = client.get(
                report_url,
                headers=DEFAULT_HEADERS,
                timeout=30,
            )

            # Respect ICE rate limiting.
            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:
                    try:
                        wait_seconds = int(
                            retry_after
                        )
                    except ValueError:
                        wait_seconds = 60
                else:
                    # Exponential backoff.
                    wait_seconds = min(
                        60 * (2 ** (attempt - 1)),
                        900,
                    )

                print(
                    f"HTTP 429 for "
                    f"{output_path.name}"
                )

                print(
                    f"Waiting {wait_seconds} "
                    f"seconds before retry "
                    f"{attempt}/{max_retries}..."
                )

                time.sleep(
                    wait_seconds
                )

                continue

            response.raise_for_status()

            if not response.content:
                raise ValueError(
                    "Empty response received."
                )

            content_type = response.headers.get(
                "Content-Type",
                "",
            ).lower()

            if (
                "text/csv" not in content_type
                and not report_url.lower().endswith(
                    ".csv"
                )
            ):
                raise ValueError(
                    "Response does not appear "
                    "to be a CSV file."
                )

            output_path.write_bytes(
                response.content
            )

            print(
                f"Downloaded: "
                f"{output_path.name}"
            )

            return output_path

        except requests.RequestException as exc:

            if attempt == max_retries:
                raise RuntimeError(
                    f"Failed to download "
                    f"Robusta report: "
                    f"{report_url}"
                ) from exc

            wait_seconds = min(
                10 * (2 ** (attempt - 1)),
                120,
            )

            print(
                f"Request failed for "
                f"{output_path.name}: "
                f"{exc}"
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
        f"Robusta report: {report_url}"
    )


def download_robusta_reports(
    reports: list[dict],
    output_dir: Path,
    delay_seconds: float = 5.0,
) -> list[dict]:

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    with requests.Session() as session:

        for index, report in enumerate(
            reports,
            start=1,
        ):

            report_date = report[
                "report_date"
            ]

            report_url = report[
                "url"
            ]

            file_name = report[
                "file_name"
            ]

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
                    report_url=report_url,
                    output_path=output_path,
                    session=session,
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

            except (
                requests.RequestException,
                RuntimeError,
                ValueError,
            ) as exc:

                print(
                    f"Failed: "
                    f"{report_date}"
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

            # Pace requests to reduce the chance
            # of triggering ICE rate limits.
            if index < len(reports):
                print(
                    f"Waiting "
                    f"{delay_seconds} seconds..."
                )

                time.sleep(
                    delay_seconds
                )

    return results