"""
Runs the historical Arabica stock report extraction for the configured date range.
Creates the required raw-data directory and invokes the Arabica downloader for each
date while reporting download and unavailable-file statistics.
"""
from datetime import date
from pathlib import Path

from src.historical_extractor import (
    extract_arabica_date_range,
)


START_DATE = date(2025, 10, 3)
END_DATE = date(2025, 10, 25)

OUTPUT_DIR = Path(
    "data/raw/arabica"
)


def main():

    print("=" * 60)
    print("ARABICA HISTORICAL DOWNLOAD")
    print("=" * 60)

    print(
        f"\nDate range: "
        f"{START_DATE} -> {END_DATE}"
    )

    print(
        f"Output directory: "
        f"{OUTPUT_DIR}"
    )

    results = extract_arabica_date_range(
        start_date=START_DATE,
        end_date=END_DATE,
        output_dir=OUTPUT_DIR,
    )

    downloaded = sum(
        1
        for result in results
        if result["status"] == "downloaded"
    )

    already_exists = sum(
        1
        for result in results
        if result["status"] == "already_exists"
    )

    unavailable = sum(
        1
        for result in results
        if result["status"] == "unavailable"
    )

    print("\n" + "=" * 60)
    print("ARABICA DOWNLOAD COMPLETE")
    print("=" * 60)

    print(
        f"Downloaded:      {downloaded}"
    )

    print(
        f"Already existed: {already_exists}"
    )

    print(
        f"Unavailable:     {unavailable}"
    )

    print(
        f"Total dates:     {len(results)}"
    )


if __name__ == "__main__":
    main()