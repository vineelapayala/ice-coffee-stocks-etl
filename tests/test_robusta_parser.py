from datetime import date
from pathlib import Path

import pandas as pd

from src.robusta_parser import parse_robusta_report


ROBUSTA_SAMPLE_FILE = Path(
    "data/raw/robusta/Stock_Report_RC_20251003_103420.csv"
)


def test_parse_robusta_report_returns_dataframe():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert isinstance(df, pd.DataFrame)


def test_parse_robusta_report_has_expected_columns():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    expected_columns = [
        "report_date",
        "cut_off_date",
        "coffee_type",
        "origin",
        "location_code",
        "stock_category",
        "quantity",
        "unit",
    ]

    assert list(df.columns) == expected_columns


def test_parse_robusta_report_has_correct_report_date():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert df["report_date"].nunique() == 1
    assert df["report_date"].iloc[0] == date(
        2025,
        10,
        3,
    )


def test_parse_robusta_report_has_correct_cut_off_date():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert df["cut_off_date"].nunique() == 1
    assert df["cut_off_date"].iloc[0] == pd.Timestamp(
        "2025-10-02"
    )


def test_parse_robusta_report_has_correct_coffee_type():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert df["coffee_type"].nunique() == 1
    assert df["coffee_type"].iloc[0] == "Robusta"


def test_parse_robusta_report_has_correct_unit():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert df["unit"].nunique() == 1
    assert df["unit"].iloc[0] == "lots"


def test_parse_robusta_report_has_valid_stock_categories():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    valid_categories = {
        "VALID_CERTIFICATE",
        "NON_TENDERABLE",
        "SUSPENDED",
    }

    actual_categories = set(
        df["stock_category"].unique()
    )

    assert actual_categories.issubset(
        valid_categories
    )


def test_parse_robusta_report_has_positive_quantities():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert df["quantity"].notna().all()
    assert (df["quantity"] > 0).all()


def test_parse_robusta_report_has_null_origin():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert df["origin"].isna().all()


def test_parse_robusta_report_excludes_grand_total():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert not (
        df["location_code"]
        .astype(str)
        .str.upper()
        .eq("GRANDTOTAL")
        .any()
    )


def test_parse_robusta_report_has_expected_locations():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    expected_locations = {
        "ANT",
        "LON",
        "TRI",
    }

    actual_locations = set(
        df["location_code"].dropna().unique()
    )

    assert expected_locations.issubset(
        actual_locations
    )


def test_parse_robusta_report_has_expected_row_count():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert len(df) > 0


def test_parse_robusta_report_has_numeric_quantities():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert pd.api.types.is_numeric_dtype(
        df["quantity"]
    )