from pathlib import Path
import re

import pandas as pd

from src.file_utils import calculate_file_hash
from src.parser import parse_arabica_report
from src.robusta_parser import parse_robusta_report
from src.validator import (
    COMMON_COLUMNS,
    validate_report,
    validate_consolidated_dataset,
)


def _extract_robusta_report_datetime(
    file_path: Path,
) -> pd.Timestamp:
    """
    Extract report date and timestamp from a Robusta
    filename such as:

    Stock_Report_RC_20260424_103022.csv
    """

    match = re.search(
        r"Stock_Report_RC_(\d{8})_(\d{6})\.csv$",
        file_path.name,
    )

    if not match:
        raise ValueError(
            f"Unexpected Robusta filename format: "
            f"{file_path.name}"
        )

    date_text = match.group(1)
    time_text = match.group(2)

    report_datetime = pd.to_datetime(
        f"{date_text}{time_text}",
        format="%Y%m%d%H%M%S",
        errors="coerce",
    )

    if pd.isna(report_datetime):
        raise ValueError(
            f"Could not parse report timestamp "
            f"from {file_path.name}"
        )

    return report_datetime


def _deduplicate_robusta_files(
    robusta_files: list[Path],
) -> tuple[list[Path], int]:
    """
    Detect identical Robusta source files for the same
    report date.

    If multiple files have:
        1. The same report date
        2. The same SHA-256 hash

    the file with the latest timestamp in its filename
    is retained.

    Different files with different hashes are not silently
    removed.

    Returns:
        selected_files:
            Robusta files selected for parsing.

        duplicate_groups_count:
            Number of identical duplicate groups detected.
    """

    print("\nChecking Robusta source files for duplicates...")

    file_metadata = []

    for file_path in robusta_files:
        report_datetime = (
            _extract_robusta_report_datetime(
                file_path
            )
        )

        file_hash = calculate_file_hash(
            file_path
        )

        file_metadata.append(
            {
                "file_path": file_path,
                "report_date": report_datetime.date(),
                "report_datetime": report_datetime,
                "hash": file_hash,
            }
        )

    metadata_df = pd.DataFrame(
        file_metadata
    )

    selected_files = []

    duplicate_groups = []

    for report_date, group in metadata_df.groupby(
        "report_date"
    ):
        # ---------------------------------------------------------
        # Only one file exists for this report date.
        # ---------------------------------------------------------

        if len(group) == 1:
            selected_files.append(
                group.iloc[0]["file_path"]
            )
            continue

        # ---------------------------------------------------------
        # Group same-date files by SHA-256.
        # ---------------------------------------------------------

        hash_groups = group.groupby(
            "hash"
        )

        for file_hash, hash_group in hash_groups:

            if len(hash_group) == 1:
                # Different content for the same report date.
                # Do not silently discard it.
                selected_files.append(
                    hash_group.iloc[0]["file_path"]
                )
                continue

            # -----------------------------------------------------
            # Identical files for the same report date.
            # Keep the latest timestamp.
            # -----------------------------------------------------

            latest_row = hash_group.sort_values(
                "report_datetime"
            ).iloc[-1]

            selected_files.append(
                latest_row["file_path"]
            )

            duplicate_groups.append(
                {
                    "report_date": report_date,
                    "files": hash_group[
                        "file_path"
                    ].tolist(),
                    "kept_file": latest_row[
                        "file_path"
                    ],
                    "hash": file_hash,
                }
            )

    # ---------------------------------------------------------
    # Report duplicate files
    # ---------------------------------------------------------

    if duplicate_groups:
        print(
            f"\nIdentical duplicate groups found: "
            f"{len(duplicate_groups)}"
        )

        for duplicate in duplicate_groups:
            print(
                f"\nReport date: "
                f"{duplicate['report_date']}"
            )

            print("Duplicate files:")

            for file_path in duplicate["files"]:
                print(
                    f"  - {file_path.name}"
                )

            print(
                f"Keeping latest: "
                f"{duplicate['kept_file'].name}"
            )

    else:
        print(
            "No identical Robusta duplicate files found."
        )

    # ---------------------------------------------------------
    # Check for same-date files with different content
    # ---------------------------------------------------------

    conflicting_dates = (
        metadata_df.groupby("report_date")
        ["hash"]
        .nunique()
    )

    conflicting_dates = (
        conflicting_dates[
            conflicting_dates > 1
        ]
    )

    if not conflicting_dates.empty:
        print(
            "\nWARNING: Multiple different files "
            "were found for the same report date:"
        )

        for report_date in conflicting_dates.index:
            print(
                f"  - {report_date}"
            )

        raise ValueError(
            "Found multiple different source files "
            "for the same Robusta report date. "
            "These require investigation before "
            "continuing."
        )

    selected_files = sorted(
        selected_files,
        key=lambda path: _extract_robusta_report_datetime(
            path
        ),
    )

    print(
        f"\nRobusta files before "
        f"deduplication: {len(robusta_files)}"
    )

    print(
        f"Robusta files selected for parsing: "
        f"{len(selected_files)}"
    )

    return selected_files, len(duplicate_groups)


def build_consolidated_dataset(
    arabica_dir: Path,
    robusta_dir: Path,
) -> tuple[pd.DataFrame, dict]:
    """
    Parse, validate, and consolidate all Arabica and
    Robusta ICE stock reports into a normalized dataset.

    Returns:
        A tuple containing:

        1. Consolidated validated DataFrame.
        2. Pipeline statistics dictionary.
    """

    # ---------------------------------------------------------
    # 1. Discover report files
    # ---------------------------------------------------------

    arabica_files = sorted(
        arabica_dir.glob("*.xls")
    )

    robusta_files = sorted(
        robusta_dir.glob("*.csv")
    )

    if not arabica_files:
        raise FileNotFoundError(
            f"No Arabica XLS files found in {arabica_dir}"
        )

    if not robusta_files:
        raise FileNotFoundError(
            f"No Robusta CSV files found in {robusta_dir}"
        )

    # Preserve the original source-file counts before
    # Robusta deduplication.
    arabica_file_count = len(arabica_files)
    robusta_file_count = len(robusta_files)

    print(
        f"Arabica reports found: "
        f"{arabica_file_count}"
    )

    print(
        f"Robusta reports found: "
        f"{robusta_file_count}"
    )

    # ---------------------------------------------------------
    # 2. Deduplicate identical Robusta source files
    # ---------------------------------------------------------

    selected_robusta_files, duplicate_groups_count = (
        _deduplicate_robusta_files(
            robusta_files
        )
    )

    # ---------------------------------------------------------
    # 3. Parse and validate all Arabica reports
    # ---------------------------------------------------------

    arabica_frames = []

    for index, file_path in enumerate(
        arabica_files,
        start=1,
    ):
        print(
            f"[Arabica {index}/{len(arabica_files)}] "
            f"{file_path.name}"
        )

        df = parse_arabica_report(
            file_path
        )

        # Arabica does not contain a cut-off date.
        df["cut_off_date"] = pd.NaT

        validate_report(
            df,
            file_path,
        )

        arabica_frames.append(
            df[COMMON_COLUMNS]
        )

    if not arabica_frames:
        raise ValueError(
            "No Arabica reports were successfully parsed."
        )

    # ---------------------------------------------------------
    # 4. Parse and validate all Robusta reports
    # ---------------------------------------------------------

    robusta_frames = []

    for index, file_path in enumerate(
        selected_robusta_files,
        start=1,
    ):
        print(
            f"[Robusta {index}/{len(selected_robusta_files)}] "
            f"{file_path.name}"
        )

        df = parse_robusta_report(
            file_path
        )

        validate_report(
            df,
            file_path,
        )

        robusta_frames.append(
            df[COMMON_COLUMNS]
        )

    if not robusta_frames:
        raise ValueError(
            "No Robusta reports were successfully parsed."
        )

    # ---------------------------------------------------------
    # 5. Consolidate all reports
    # ---------------------------------------------------------

    combined_df = pd.concat(
        arabica_frames + robusta_frames,
        ignore_index=True,
    )

    # ---------------------------------------------------------
    # 6. Standardize data types
    # ---------------------------------------------------------

    combined_df["report_date"] = (
        pd.to_datetime(
            combined_df["report_date"],
            errors="coerce",
        )
        .dt.normalize()
    )

    combined_df["cut_off_date"] = (
        pd.to_datetime(
            combined_df["cut_off_date"],
            errors="coerce",
        )
        .dt.normalize()
    )

    combined_df["quantity"] = pd.to_numeric(
        combined_df["quantity"],
        errors="coerce",
    )

    # ---------------------------------------------------------
    # 7. Final consolidated-data validation
    # ---------------------------------------------------------

    validate_consolidated_dataset(
        combined_df
    )

    print(
        "\nData quality validation passed."
    )

    print(
        f"Total consolidated rows: "
        f"{len(combined_df):,}"
    )

    print(
        f"Arabica rows: "
        f"{(combined_df['coffee_type'] == 'Arabica').sum():,}"
    )

    print(
        f"Robusta rows: "
        f"{(combined_df['coffee_type'] == 'Robusta').sum():,}"
    )

    # ---------------------------------------------------------
    # 8. Sort final dataset
    # ---------------------------------------------------------

    combined_df = combined_df.sort_values(
        by=[
            "report_date",
            "coffee_type",
            "location_code",
            "stock_category",
            "origin",
        ],
        na_position="last",
    )

    combined_df = combined_df.reset_index(
        drop=True
    )

    # ---------------------------------------------------------
    # 9. Build pipeline statistics
    # ---------------------------------------------------------

    pipeline_stats = {
        "arabica_files_found": arabica_file_count,
        "robusta_files_found": robusta_file_count,
        "robusta_files_selected_for_parsing": len(
            selected_robusta_files
        ),
        "identical_duplicate_groups": duplicate_groups_count,
    }

    # ---------------------------------------------------------
    # 10. Return final DataFrame + statistics
    # ---------------------------------------------------------

    return combined_df, pipeline_stats