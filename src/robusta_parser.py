"""
Parses ICE Robusta stock report CSV files into the common coffee stock schema.
Extracts report and cutoff dates, port identifiers, and certificate stock categories
while converting source quantities into normalized stock records measured in lots.
"""
from pathlib import Path

import pandas as pd


def parse_robusta_report(file_path: Path) -> pd.DataFrame:
    """
    Parse an ICE Robusta stock report CSV.

    Returns a long-format DataFrame with:
        report_date
        cut_off_date
        coffee_type
        origin
        location_code
        stock_category
        quantity
        unit

    The source contains three stock categories:
        LotsWithValCert
        LotsNonTend
        LotsSuspended

    The GrandTotal row is excluded from the detailed data
    and used for source-total validation.
    """

    # ---------------------------------------------------------
    # 1. Read CSV
    # ---------------------------------------------------------

    raw_df = pd.read_csv(file_path)

    raw_df.columns = (
        raw_df.columns
        .str.strip()
    )

    required_columns = [
        "Commodity",
        "CutOffDate",
        "PortId",
        "LotsWithValCert",
        "LotsNonTend",
        "LotsSuspended",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in raw_df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # ---------------------------------------------------------
    # 2. Separate detail rows from GrandTotal
    # ---------------------------------------------------------

    commodity_values = (
        raw_df["Commodity"]
        .astype(str)
        .str.strip()
    )

    grand_total_rows = raw_df[
        commodity_values.eq("GrandTotal")
    ].copy()

    detail_df = raw_df[
        commodity_values.eq("RC")
    ].copy()

    if grand_total_rows.empty:
        raise ValueError(
            "Could not find GrandTotal row."
        )

    if detail_df.empty:
        raise ValueError(
            "Could not find Robusta detail rows."
        )

    # ---------------------------------------------------------
    # 3. Validate commodity
    # ---------------------------------------------------------

    commodities = (
        detail_df["Commodity"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    if not all(
        commodity == "RC"
        for commodity in commodities
    ):
        raise ValueError(
            f"Unexpected commodity values: {commodities}"
        )

    # ---------------------------------------------------------
    # 4. Extract and validate cut-off date
    # ---------------------------------------------------------

    # Strip whitespace first because historical files may
    # contain harmless leading/trailing spaces.
    cut_off_text = (
        detail_df["CutOffDate"]
        .astype("string")
        .str.strip()
    )

    # Let pandas recognize the historical ICE date formats
    # instead of enforcing one exact textual representation.
    detail_df["cut_off_date"] = pd.to_datetime(
        cut_off_text,
        format="mixed",
        errors="coerce",
    )

    invalid_cut_off_dates = detail_df[
        detail_df["cut_off_date"].isna()
        & cut_off_text.notna()
        & cut_off_text.ne("")
    ]

    if not invalid_cut_off_dates.empty:
        invalid_values = (
            invalid_cut_off_dates["CutOffDate"]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            "Could not parse one or more CutOffDate values "
            f"in {file_path.name}. "
            f"Invalid values: {invalid_values}"
        )

    # A report should have exactly one cut-off date.
    cut_off_dates = (
        detail_df["cut_off_date"]
        .dropna()
        .dt.normalize()
        .unique()
    )

    if len(cut_off_dates) != 1:
        raise ValueError(
            f"Expected one CutOffDate in "
            f"{file_path.name}, found: "
            f"{cut_off_dates}"
        )

    cut_off_date = pd.Timestamp(
        cut_off_dates[0]
    )

    detail_df["cut_off_date"] = cut_off_date

    # ---------------------------------------------------------
    # 5. Determine report date from filename
    # ---------------------------------------------------------

    # Example:
    # Stock_Report_RC_20261001_104024.csv

    filename = file_path.stem
    filename_parts = filename.split("_")

    if len(filename_parts) < 5:
        raise ValueError(
            f"Unexpected Robusta filename format: "
            f"{file_path.name}"
        )

    report_date_text = filename_parts[3]

    report_date = pd.to_datetime(
        report_date_text,
        format="%Y%m%d",
        errors="coerce",
    )

    if pd.isna(report_date):
        raise ValueError(
            f"Could not extract report date from filename: "
            f"{file_path.name}"
        )

    report_date = report_date.date()

    # ---------------------------------------------------------
    # 6. Convert quantity columns to numeric
    # ---------------------------------------------------------

    stock_columns = [
        "LotsWithValCert",
        "LotsNonTend",
        "LotsSuspended",
    ]

    for column in stock_columns:
        detail_df[column] = pd.to_numeric(
            detail_df[column],
            errors="coerce",
        )

    # Check for invalid numeric values before melting.
    for column in stock_columns:
        invalid_count = detail_df[column].isna().sum()

        if invalid_count > 0:
            raise ValueError(
                f"Could not parse {invalid_count} value(s) "
                f"in {column} for {file_path.name}."
            )

    # ---------------------------------------------------------
    # 7. Validate source GrandTotal
    # ---------------------------------------------------------

    if len(grand_total_rows) != 1:
        raise ValueError(
            f"Expected exactly one GrandTotal row, "
            f"found {len(grand_total_rows)}."
        )

    grand_total_row = grand_total_rows.iloc[0]

    source_totals = {}

    for column in stock_columns:
        source_value = pd.to_numeric(
            grand_total_row[column],
            errors="coerce",
        )

        if pd.isna(source_value):
            raise ValueError(
                f"Could not parse GrandTotal for "
                f"{column} in {file_path.name}."
            )

        source_totals[column] = int(
            source_value
        )

    # ---------------------------------------------------------
    # 8. Convert wide → long
    # ---------------------------------------------------------

    long_df = detail_df.melt(
        id_vars=[
            "cut_off_date",
            "PortId",
        ],
        value_vars=stock_columns,
        var_name="source_category",
        value_name="quantity",
    )

    # ---------------------------------------------------------
    # 9. Map source category names
    # ---------------------------------------------------------

    category_mapping = {
        "LotsWithValCert": "VALID_CERTIFICATE",
        "LotsNonTend": "NON_TENDERABLE",
        "LotsSuspended": "SUSPENDED",
    }

    long_df["stock_category"] = (
        long_df["source_category"]
        .map(category_mapping)
    )

    if long_df["stock_category"].isna().any():
        raise ValueError(
            "Unknown stock category found."
        )

    # ---------------------------------------------------------
    # 10. Clean location and quantity
    # ---------------------------------------------------------

    long_df["location_code"] = (
        long_df["PortId"]
        .astype(str)
        .str.strip()
    )

    if (
        long_df["location_code"].isna().any()
        or long_df["location_code"].eq("").any()
    ):
        raise ValueError(
            f"Missing PortId/location code "
            f"in {file_path.name}."
        )

    long_df["quantity"] = pd.to_numeric(
        long_df["quantity"],
        errors="coerce",
    )

    if long_df["quantity"].isna().any():
        raise ValueError(
            f"Invalid quantity found in "
            f"{file_path.name}."
        )

    # Keep non-zero stock records.
    long_df = long_df[
        long_df["quantity"] > 0
    ].copy()

    # ---------------------------------------------------------
    # 11. Validate each stock category
    # ---------------------------------------------------------

    category_source_mapping = {
        "VALID_CERTIFICATE": "LotsWithValCert",
        "NON_TENDERABLE": "LotsNonTend",
        "SUSPENDED": "LotsSuspended",
    }

    for category, source_column in category_source_mapping.items():

        parsed_total = int(
            long_df.loc[
                long_df["stock_category"] == category,
                "quantity",
            ].sum()
        )

        source_total = source_totals[
            source_column
        ]

        if parsed_total != source_total:
            raise ValueError(
                f"Robusta source-total validation "
                f"failed for {category} in "
                f"{file_path.name}. "
                f"Parsed total = {parsed_total}, "
                f"Source total = {source_total}."
            )

    # ---------------------------------------------------------
    # 12. Add common metadata
    # ---------------------------------------------------------

    long_df["report_date"] = report_date
    long_df["coffee_type"] = "Robusta"

    # Robusta source does not provide origin.
    long_df["origin"] = pd.NA

    long_df["unit"] = "lots"

    # ---------------------------------------------------------
    # 13. Final column order
    # ---------------------------------------------------------

    long_df = long_df[
        [
            "report_date",
            "cut_off_date",
            "coffee_type",
            "origin",
            "location_code",
            "stock_category",
            "quantity",
            "unit",
        ]
    ]

    return long_df.reset_index(
        drop=True
    )