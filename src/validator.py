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
    """Validate report and cut-off dates."""

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
    """
    Run all quality checks for a parsed report.
    """

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
    """
    Run final quality checks on the consolidated dataset.
    """

    if df.empty:
        raise ValueError(
            "Consolidated dataset is empty."
        )

    # ---------------------------------------------------------
    # Required columns
    # ---------------------------------------------------------

    validate_schema(
        df,
        Path("consolidated_dataset"),
    )

    # ---------------------------------------------------------
    # Required fields
    # ---------------------------------------------------------

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
                f"Consolidated dataset contains "
                f"{null_count} null value(s) in "
                f"'{column}'."
            )

    # ---------------------------------------------------------
    # Coffee types
    # ---------------------------------------------------------

    valid_types = {
        "Arabica",
        "Robusta",
    }

    invalid_types = set(
        df["coffee_type"].unique()
    ) - valid_types

    if invalid_types:
        raise ValueError(
            f"Invalid coffee types found: "
            f"{invalid_types}"
        )

    # ---------------------------------------------------------
    # Quantity
    # ---------------------------------------------------------

    if df["quantity"].isna().any():
        raise ValueError(
            "Consolidated dataset contains "
            "null quantities."
        )

    if (df["quantity"] < 0).any():
        raise ValueError(
            "Consolidated dataset contains "
            "negative quantities."
        )

    # ---------------------------------------------------------
    # Units
    # ---------------------------------------------------------

    if not df.loc[
        df["coffee_type"] == "Arabica",
        "unit",
    ].eq("bags").all():
        raise ValueError(
            "Arabica records must use bags."
        )

    if not df.loc[
        df["coffee_type"] == "Robusta",
        "unit",
    ].eq("lots").all():
        raise ValueError(
            "Robusta records must use lots."
        )

    # ---------------------------------------------------------
    # Duplicate natural grain
    # ---------------------------------------------------------

    grain_columns = [
        "report_date",
        "cut_off_date",
        "coffee_type",
        "origin",
        "location_code",
        "stock_category",
        "unit",
    ]

    duplicates = df[
        df.duplicated(
            subset=grain_columns,
            keep=False,
        )
    ].sort_values(
        by=grain_columns
    )

    if not duplicates.empty:
        print("\nDuplicate records found:")
        print(
            duplicates.to_string(
                index=False
            )
        )

        raise ValueError(
            "Consolidated dataset contains "
            f"{len(duplicates)} duplicate row(s) "
            "at the expected natural grain."
        )


def generate_quality_report(
    df: pd.DataFrame,
) -> dict:
    """
    Generate summary data-quality metrics
    for the consolidated dataset.
    """

    grain_columns = [
        "report_date",
        "cut_off_date",
        "coffee_type",
        "origin",
        "location_code",
        "stock_category",
        "unit",
    ]

    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "date_min": df["report_date"].min(),
        "date_max": df["report_date"].max(),
        "arabica_rows": int(
            (df["coffee_type"] == "Arabica").sum()
        ),
        "robusta_rows": int(
            (df["coffee_type"] == "Robusta").sum()
        ),
        "null_values": int(
            df.isna().sum().sum()
        ),
        "duplicate_rows": int(
            df.duplicated(
                subset=grain_columns
            ).sum()
        ),
        "negative_quantities": int(
            (df["quantity"] < 0).sum()
        ),
        "unique_report_dates": int(
            df["report_date"].nunique()
        ),
        "unique_locations": int(
            df["location_code"].nunique()
        ),
        "unique_stock_categories": int(
            df["stock_category"].nunique()
        ),
    }