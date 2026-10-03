from pathlib import Path
import re

import pandas as pd


def parse_arabica_report(file_path: Path) -> pd.DataFrame:
    """
    Parse the TOTAL BAGS CERTIFIED section from an ICE Arabica
    certified warehouse stock XLS report.

    Returns a long-format DataFrame with:
        report_date
        origin
        location_code
        quantity
        coffee_type
        stock_category
        unit

    Also validates the parsed warehouse total against the
    source 'Total in Bags' value.
    """

    raw_df = pd.read_excel(
        file_path,
        sheet_name="Sheet1",
        header=None,
    )

    # ---------------------------------------------------------
    # 1. Extract report date from the "As of:" row
    # ---------------------------------------------------------

    first_column = raw_df.iloc[:, 0].astype(str).str.strip()

    as_of_matches = first_column[
        first_column.str.startswith("As of:", na=False)
    ]

    if as_of_matches.empty:
        raise ValueError(
            "Could not find 'As of:' row in the report."
        )

    as_of_text = as_of_matches.iloc[0]

    # Example:
    # "As of: Oct 1, 2026 1:43:53PM"
    date_match = re.search(
        r"As of:\s*([A-Za-z]{3}\s+\d{1,2},\s+\d{4})",
        as_of_text,
    )

    if not date_match:
        raise ValueError(
            f"Could not extract report date from: {as_of_text}"
        )

    report_date = pd.to_datetime(
        date_match.group(1),
        format="%b %d, %Y",
    ).date()

    # ---------------------------------------------------------
    # 2. Locate TOTAL BAGS CERTIFIED section
    # ---------------------------------------------------------

    section_matches = first_column[
        first_column.eq("TOTAL BAGS CERTIFIED")
    ]

    if section_matches.empty:
        raise ValueError(
            "Could not find 'TOTAL BAGS CERTIFIED' section."
        )

    section_start = section_matches.index[0]

    # ---------------------------------------------------------
    # 3. Find warehouse header row
    # ---------------------------------------------------------

    header_row = None

    for row_index in range(
        section_start + 1,
        len(raw_df),
    ):
        row_values = (
            raw_df.iloc[row_index]
            .astype(str)
            .str.strip()
            .tolist()
        )

        if "ANT" in row_values and "Total" in row_values:
            header_row = row_index
            break

    if header_row is None:
        raise ValueError(
            "Could not find warehouse header row."
        )

    # ---------------------------------------------------------
    # 4. Find "Total in Bags" row
    # ---------------------------------------------------------

    total_matches = first_column[
        first_column.eq("Total in Bags")
    ]

    if total_matches.empty:
        raise ValueError(
            "Could not find 'Total in Bags' row."
        )

    total_row = total_matches[
        total_matches.index > header_row
    ]

    if total_row.empty:
        raise ValueError(
            "Could not find 'Total in Bags' after "
            "'TOTAL BAGS CERTIFIED' section."
        )

    total_row_index = total_row.index[0]

    # ---------------------------------------------------------
    # 5. Extract source total
    # ---------------------------------------------------------

    headers = raw_df.iloc[header_row].tolist()

    total_column_index = headers.index("Total")

    source_total = pd.to_numeric(
        raw_df.iloc[total_row_index, total_column_index],
        errors="coerce",
    )

    if pd.isna(source_total):
        raise ValueError(
            "Could not parse source 'Total in Bags' value."
        )

    source_total = int(source_total)

    # ---------------------------------------------------------
    # 6. Extract origin/location table
    # ---------------------------------------------------------

    data = raw_df.iloc[
        header_row + 1 : total_row_index
    ].copy()

    # Explicitly name the first column.
    data.columns = [
        "origin" if index == 0 else column
        for index, column in enumerate(headers)
    ]

    # Physical warehouse/location columns only.
    location_columns = [
        column
        for column in headers[1:]
        if pd.notna(column)
        and str(column).strip()
        and str(column).strip() != "Total"
    ]

    data = data[
        ["origin"] + location_columns
    ]

    # ---------------------------------------------------------
    # 7. Remove empty origins
    # ---------------------------------------------------------

    data["origin"] = (
        data["origin"]
        .astype(str)
        .str.strip()
    )

    data = data[
        data["origin"].notna()
        & (data["origin"] != "")
        & (data["origin"] != "nan")
    ]

    # ---------------------------------------------------------
    # 8. Convert wide → long
    # ---------------------------------------------------------

    long_df = data.melt(
        id_vars=["origin"],
        value_vars=location_columns,
        var_name="location_code",
        value_name="quantity",
    )

    # ---------------------------------------------------------
    # 9. Clean values
    # ---------------------------------------------------------

    long_df["origin"] = (
        long_df["origin"]
        .astype(str)
        .str.strip()
    )

    long_df["location_code"] = (
        long_df["location_code"]
        .astype(str)
        .str.strip()
    )

    long_df["quantity"] = pd.to_numeric(
        long_df["quantity"],
        errors="coerce",
    )

    long_df = long_df.dropna(
        subset=["quantity"]
    )

    # Keep non-zero stock records.
    long_df = long_df[
        long_df["quantity"] > 0
    ].copy()

    # ---------------------------------------------------------
    # 10. Validate against source total
    # ---------------------------------------------------------

    parsed_total = int(
        long_df["quantity"].sum()
    )

    if parsed_total != source_total:
        raise ValueError(
            "Arabica source-total validation failed. "
            f"Parsed total = {parsed_total}, "
            f"Source total = {source_total}."
        )

    # ---------------------------------------------------------
    # 11. Add metadata
    # ---------------------------------------------------------

    long_df["report_date"] = report_date
    long_df["coffee_type"] = "Arabica"
    long_df["stock_category"] = "TOTAL_BAGS_CERTIFIED"
    long_df["unit"] = "bags"

    # Put columns in final order.
    long_df = long_df[
        [
            "report_date",
            "coffee_type",
            "origin",
            "location_code",
            "stock_category",
            "quantity",
            "unit",
        ]
    ]

    return long_df.reset_index(drop=True)