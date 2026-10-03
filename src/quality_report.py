from pathlib import Path
import json

import pandas as pd


def generate_quality_report(
    df: pd.DataFrame,
    arabica_file_count: int,
    robusta_file_count: int,
    robusta_selected_file_count: int,
    duplicate_groups_count: int,
    output_path: Path,
) -> dict:
    """
    Generate a data quality report for the validated consolidated dataset.

    The report is generated from the validated DataFrame and records
    source-file statistics, dataset statistics, nulls, duplicates,
    and validation-related metrics.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Basic dataset information
    # ------------------------------------------------------------------

    total_rows = len(df)

    arabica_rows = int(
        (df["coffee_type"] == "Arabica").sum()
    )

    robusta_rows = int(
        (df["coffee_type"] == "Robusta").sum()
    )

    # ------------------------------------------------------------------
    # Date information
    # ------------------------------------------------------------------

    report_date_min = df["report_date"].min()
    report_date_max = df["report_date"].max()

    # ------------------------------------------------------------------
    # Null information
    # ------------------------------------------------------------------

    null_counts = {
        column: int(df[column].isna().sum())
        for column in df.columns
    }

    # ------------------------------------------------------------------
    # Duplicate information
    # ------------------------------------------------------------------

    duplicate_columns = [
        "report_date",
        "cut_off_date",
        "coffee_type",
        "origin",
        "location_code",
        "stock_category",
        "unit",
    ]

    duplicate_row_count = int(
        df.duplicated(
            subset=duplicate_columns,
            keep=False,
        ).sum()
    )

    # ------------------------------------------------------------------
    # Quantity checks
    # ------------------------------------------------------------------

    null_quantity_count = int(
        df["quantity"].isna().sum()
    )

    negative_quantity_count = int(
        (df["quantity"] < 0).sum()
    )

    zero_quantity_count = int(
        (df["quantity"] == 0).sum()
    )

    # ------------------------------------------------------------------
    # Category distributions
    # ------------------------------------------------------------------

    coffee_type_counts = {
        str(key): int(value)
        for key, value in df["coffee_type"].value_counts().items()
    }

    stock_category_counts = {
        str(key): int(value)
        for key, value in df["stock_category"].value_counts().items()
    }

    unit_counts = {
        str(key): int(value)
        for key, value in df["unit"].value_counts().items()
    }

    # ------------------------------------------------------------------
    # Location information
    # ------------------------------------------------------------------

    location_counts = {
        str(key): int(value)
        for key, value in df["location_code"].value_counts().items()
    }

    # ------------------------------------------------------------------
    # Build report
    # ------------------------------------------------------------------

    report = {
        "report_metadata": {
            "dataset": "ICE Certified Coffee Stocks",
            "generated_at": pd.Timestamp.now().isoformat(),
        },

        "source_files": {
            "arabica_files_found": arabica_file_count,
            "robusta_files_found": robusta_file_count,
            "robusta_files_selected_for_parsing": (
                robusta_selected_file_count
            ),
            "identical_duplicate_groups": duplicate_groups_count,
        },

        "dataset_summary": {
            "total_rows": total_rows,
            "arabica_rows": arabica_rows,
            "robusta_rows": robusta_rows,
            "report_date_start": (
                report_date_min.strftime("%Y-%m-%d")
                if pd.notna(report_date_min)
                else None
            ),
            "report_date_end": (
                report_date_max.strftime("%Y-%m-%d")
                if pd.notna(report_date_max)
                else None
            ),
        },

        "distributions": {
            "coffee_type": coffee_type_counts,
            "stock_category": stock_category_counts,
            "unit": unit_counts,
            "location_code": location_counts,
        },

        "null_checks": {
            "null_counts_by_column": null_counts,
            "null_quantity_count": null_quantity_count,
        },

        "duplicate_checks": {
            "duplicate_row_count": duplicate_row_count,
        },

        "quantity_checks": {
            "negative_quantity_count": negative_quantity_count,
            "zero_quantity_count": zero_quantity_count,
        },

        "quality_status": {
            "validation_passed": True,
            "schema_valid": True,
            "required_fields_valid": True,
            "coffee_type_valid": True,
            "units_valid": True,
            "quantities_valid": (
                null_quantity_count == 0
                and negative_quantity_count == 0
            ),
            "duplicates_valid": (
                duplicate_row_count == 0
            ),
        },
    }

    # ------------------------------------------------------------------
    # Write JSON report
    # ------------------------------------------------------------------

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
        )

    print(
        f"\nData quality report saved to: {output_path}"
    )

    return report