from datetime import date, timedelta
from pathlib import Path
import time

import requests

from src.extractor import download_arabica_report


def extract_arabica_date_range(
    start_date: date,
    end_date: date,
    output_dir: Path,
) -> list[dict]:

    if start_date > end_date:
        raise ValueError(
            "start_date must be before "
            "or equal to end_date."
        )

    extraction_results = []

    current_date = start_date

    with requests.Session() as session:

        while current_date <= end_date:

            expected_file = (
                output_dir
                / f"coffee_cert_stock_"
                  f"{current_date:%Y%m%d}.xls"
            )

            if expected_file.exists():

                print(
                    f"Already exists: "
                    f"{expected_file.name}"
                )

                extraction_results.append(
                    {
                        "report_date": current_date,
                        "status": "already_exists",
                        "file_path": expected_file,
                    }
                )

            else:

                file_path = download_arabica_report(
                    report_date=current_date,
                    output_dir=output_dir,
                    session=session,
                )

                if file_path is None:

                    extraction_results.append(
                        {
                            "report_date": current_date,
                            "status": "unavailable",
                            "file_path": None,
                        }
                    )

                else:

                    extraction_results.append(
                        {
                            "report_date": current_date,
                            "status": "downloaded",
                            "file_path": file_path,
                        }
                    )

            # Wait between requests to reduce
            # the chance of triggering ICE rate limits.
            time.sleep(5)

            current_date += timedelta(days=1)

    return extraction_results