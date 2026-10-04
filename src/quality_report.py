from pathlib import Path
import json

import pandas as pd


def _get_date_coverage(
    df: pd.DataFrame,
    coffee_type: str,
) -> dict:
    """
    Calculate report-date coverage for a coffee type.

    Missing calendar dates are reported for completeness analysis,
    but are not treated as validation failures because source
    reports may not be published on every calendar day.
    """

    coffee_df = df[
        df["coffee_type"] == coffee_type
    ].copy()

    report_dates = (
        pd.to_datetime(
            coffee_df["report_date"],
            errors="coerce",
        )
        .dropna()
        .dt.normalize()
        .drop_duplicates()
        .sort_values()
    )

    if report_dates.empty:
        return {
            "distinct_report_dates": 0,
            "report_date_start": None,
            "report_date_end": None,
            "missing_calendar_dates": 0,
            "missing_dates": [],
        }

    start_date = report_dates.iloc[0]
    end_date = report_dates.iloc[-1]

    expected_dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D",
    )

    observed_dates = set(report_dates)

    missing_dates = [
        date.strftime("%Y-%m-%d")
        for date in expected_dates
        if date not in observed_dates
    ]

    return {
        "distinct_report_dates": int(
            len(report_dates)
        ),
        "report_date_start": (
            start_date.strftime("%Y-%m-%d")
        ),
        "report_date_end": (
            end_date.strftime("%Y-%m-%d")
        ),
        "missing_calendar_dates": int(
            len(missing_dates)
        ),
        "missing_dates": missing_dates,
    }


def _get_value_counts(
    series: pd.Series,
) -> dict:
    """Return value counts as JSON-serializable integers."""

    return {
        str(key): int(value)
        for key, value in series.value_counts().items()
    }


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
    source-file statistics, dataset statistics, date coverage, nulls,
    duplicates, and validation-related metrics.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

    arabica_date_coverage = _get_date_coverage(
        df,
        "Arabica",
    )

    robusta_date_coverage = _get_date_coverage(
        df,
        "Robusta",
    )

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

    coffee_type_counts = _get_value_counts(
        df["coffee_type"]
    )

    stock_category_counts = _get_value_counts(
        df["stock_category"]
    )

    unit_counts = _get_value_counts(
        df["unit"]
    )

    # ------------------------------------------------------------------
    # Location information
    # ------------------------------------------------------------------

    location_counts = _get_value_counts(
        df["location_code"]
    )

    # ------------------------------------------------------------------
    # Build report
    # ------------------------------------------------------------------

    report = {
        "report_metadata": {
            "dataset": "ICE Certified Coffee Stocks",
            "generated_at": (
                pd.Timestamp.now().isoformat()
            ),
        },

        "source_files": {
            "arabica_files_found": arabica_file_count,
            "robusta_files_found": robusta_file_count,
            "robusta_files_selected_for_parsing": (
                robusta_selected_file_count
            ),
            "identical_duplicate_groups": (
                duplicate_groups_count
            ),
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

        "date_coverage": {
            "Arabica": arabica_date_coverage,
            "Robusta": robusta_date_coverage,
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
            "negative_quantity_count": (
                negative_quantity_count
            ),
            "zero_quantity_count": (
                zero_quantity_count
            ),
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
        f"\nData quality report saved to: "
        f"{output_path}"
    )

    return report