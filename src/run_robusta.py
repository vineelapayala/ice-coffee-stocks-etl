"""
Runs the historical Robusta stock report download using previously discovered URLs.
Reads discovered_reports.json and downloads the corresponding ICE CSV reports into
the Robusta raw-data directory while reporting download results.
"""
import json
from pathlib import Path

from src.robusta_extractor import (
    download_robusta_reports,
)


DISCOVERY_FILE = Path(
    "data/raw/robusta_discovery/"
    "discovered_reports.json"
)

OUTPUT_DIR = Path(
    "data/raw/robusta"
)


def main():
    print("=" * 60)
    print("ROBUSTA HISTORICAL DOWNLOAD")
    print("=" * 60)

    if not DISCOVERY_FILE.exists():
        raise FileNotFoundError(
            f"Discovery file not found: "
            f"{DISCOVERY_FILE}"
        )

    reports = json.loads(
        DISCOVERY_FILE.read_text(
            encoding="utf-8"
        )
    )

    print(
        f"\nReports discovered: "
        f"{len(reports)}"
    )

    print(
        f"Output directory: "
        f"{OUTPUT_DIR}"
    )

    print(
        "\nStarting download..."
    )

    results = download_robusta_reports(
        reports=reports,
        output_dir=OUTPUT_DIR,
        delay_seconds=5.0,
    )

    downloaded = sum(
        1
        for result in results
        if result["status"]
        == "downloaded"
    )

    already_exists = sum(
        1
        for result in results
        if result["status"]
        == "already_exists"
    )

    failed = sum(
        1
        for result in results
        if result["status"]
        == "failed"
    )

    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)

    print(
        f"Downloaded:      {downloaded}"
    )

    print(
        f"Already existed: {already_exists}"
    )

    print(
        f"Failed:          {failed}"
    )

    print(
        f"Total reports:   {len(results)}"
    )


if __name__ == "__main__":
    main()