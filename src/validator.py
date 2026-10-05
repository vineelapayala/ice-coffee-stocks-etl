"""
Validates the consolidated Arabica and Robusta coffee stock dataset against the
required schema and business rules. Checks required fields, coffee types, units,
dates, quantities, and duplicate records before the final dataset is produced.
"""
from pathlib import Path

import pandas as pd


COMMON_COLUMNS = [
    "report_date",
    "cut_off_date",
    "coffee_type",
    "origin",
    "location_code",
    "stock_category",
    "quantity",
    "unit",
]


def validate_schema(
    df: pd.DataFrame,
    file_path: Path,
) -> None:
    """Validate the schema of a parsed report."""

    missing_columns = [
        column
        for column in COMMON_COLUMNS
        if column not in df.columns
    ]

    unexpected_columns = [
        column
        for column in df.columns
        if column not in COMMON_COLUMNS
    ]

    if missing_columns:
        raise ValueError(
            f"{file_path.name}: missing columns: "
            f"{missing_columns}"
        )

    if unexpected_columns:
        raise ValueError(
            f"{file_path.name}: unexpected columns: "
            f"{unexpected_columns}"
        )


def validate_required_fields(
    df: pd.DataFrame,
    file_path: Path,
) -> None:
    """Validate mandatory fields."""

    required_columns = [
        "report_date",
        "coffee_type",
        "location_code",
        "stock_category",
        "quantity",
        "unit",
    ]

    for column in required_columns:
        null_count = df[column].isna().sum()

        if null_count > 0:
            raise ValueError(
                f"{file_path.name}: "
                f"{null_count} null value(s) found "
                f"in '{column}'."
            )


def validate_coffee_type(
    df: pd.DataFrame,
    file_path: Path,
) -> None:
    """Validate coffee type."""

    valid_types = {
        "Arabica",
        "Robusta",
    }

    invalid_types = set(
        df["coffee_type"].dropna().unique()
    ) - valid_types

    if invalid_types:
        raise ValueError(
            f"{file_path.name}: invalid coffee type(s): "
            f"{invalid_types}"
        )


def validate_units(
    df: pd.DataFrame,
    file_path: Path,
) -> None:
    """Validate units and coffee-type/unit consistency."""

    valid_units = {
        "bags",
        "lots",
    }

    invalid_units = set(
        df["unit"].dropna().unique()
    ) - valid_units

    if invalid_units:
        raise ValueError(
            f"{file_path.name}: invalid unit(s): "
            f"{invalid_units}"
        )

    arabica_units = set(
        df.loc[
            df["coffee_type"] == "Arabica",
            "unit",
        ].dropna().unique()
    )

    if arabica_units - {"bags"}:
        raise ValueError(
            f"{file_path.name}: Arabica must use "
            f"'bags'. Found: {arabica_units}"
        )

    robusta_units = set(
        df.loc[
            df["coffee_type"] == "Robusta",
            "unit",
        ].dropna().unique()
    )

    if robusta_units - {"lots"}:
        raise ValueError(
            f"{file_path.name}: Robusta must use "
            f"'lots'. Found: {robusta_units}"
        )


def validate_quantities(
    df: pd.DataFrame,
    file_path: Path,
) -> None:
    """Validate quantity values."""

    if not pd.api.types.is_numeric_dtype(
        df["quantity"]
    ):
        raise ValueError(
            f"{file_path.name}: quantity is not numeric."
        )

    if df["quantity"].isna().any():
        raise ValueError(
            f"{file_path.name}: null quantities found."
        )

    if (df["quantity"] < 0).any():
        raise ValueError(
            f"{file_path.name}: negative quantities found."
        )


def validate_dates(
    df: pd.DataFrame,
    file_path: Path,
) -> None:
    """Validate report and Robusta cut-off dates."""

    report_dates = pd.to_datetime(
        df["report_date"],
        errors="coerce",
    )

    if report_dates.isna().any():
        raise ValueError(
            f"{file_path.name}: invalid report date found."
        )

    if df["coffee_type"].eq("Robusta").any():
        robusta = df[
            df["coffee_type"] == "Robusta"
        ]

        cut_off_dates = pd.to_datetime(
            robusta["cut_off_date"],
            errors="coerce",
        )

        if cut_off_dates.isna().any():
            raise ValueError(
                f"{file_path.name}: Robusta report "
                f"contains invalid cut-off date."
            )


def validate_duplicates(
    df: pd.DataFrame,
    file_path: Path,
) -> None:
    """Validate the expected natural grain."""

    grain_columns = [
        "report_date",
        "cut_off_date",
        "coffee_type",
        "origin",
        "location_code",
        "stock_category",
        "unit",
    ]

    duplicate_count = df.duplicated(
        subset=grain_columns,
        keep=False,
    ).sum()

    if duplicate_count > 0:
        raise ValueError(
            f"{file_path.name}: "
            f"{duplicate_count} duplicate row(s) "
            f"found at the expected natural grain."
        )


def validate_report(
    df: pd.DataFrame,
    file_path: Path,
) -> None:
    """Run all quality checks for a parsed report."""

    validate_schema(
        df,
        file_path,
    )

    validate_required_fields(
        df,
        file_path,
    )

    validate_coffee_type(
        df,
        file_path,
    )

    validate_units(
        df,
        file_path,
    )

    validate_quantities(
        df,
        file_path,
    )

    validate_dates(
        df,
        file_path,
    )

    validate_duplicates(
        df,
        file_path,
    )


def validate_consolidated_dataset(
    df: pd.DataFrame,
) -> None:
    """Run final quality checks on the consolidated dataset."""

    if df.empty:
        raise ValueError(
            "Consolidated dataset is empty."
        )

    file_path = Path("consolidated_dataset")

    validate_report(
        df,
        file_path,
    )