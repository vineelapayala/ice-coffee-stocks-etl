"""
Parses ICE Robusta certified warehouse stock reports into a standardized
DataFrame structure.

The parser reads the raw Robusta CSV reports, extracts report and cutoff dates,
maps stock categories to standardized values, excludes aggregate GrandTotal
records, and returns the data using the common consolidated dataset schema.
"""
from pathlib import Path

import pandas as pd

from src.robusta_parser import parse_robusta_report


ROBUSTA_DATA_DIR = Path("data/raw/robusta")


def get_robusta_sample_file() -> Path:
    """Return the first available Robusta extracted report."""
    files = sorted(ROBUSTA_DATA_DIR.glob("*.csv"))

    if not files:
        raise FileNotFoundError(
            f"No Robusta reports found in {ROBUSTA_DATA_DIR}"
        )

    return files[0]


ROBUSTA_SAMPLE_FILE = get_robusta_sample_file()


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


def test_parse_robusta_report_has_correct_coffee_type():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert df["coffee_type"].eq("Robusta").all()


def test_parse_robusta_report_has_correct_unit():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert df["unit"].eq("lots").all()


def test_parse_robusta_report_has_valid_stock_categories():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    valid_categories = {
        "VALID_CERTIFICATE",
        "NON_TENDERABLE",
        "SUSPENDED",
    }

    assert set(df["stock_category"]).issubset(valid_categories)


def test_parse_robusta_report_has_positive_quantities():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert df["quantity"].notna().all()
    assert (df["quantity"] > 0).all()


def test_parse_robusta_report_has_null_origin():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert df["origin"].isna().all()


def test_parse_robusta_report_excludes_grand_total():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert "GrandTotal" not in df["location_code"].values


def test_parse_robusta_report_has_numeric_quantities():
    df = parse_robusta_report(ROBUSTA_SAMPLE_FILE)

    assert pd.api.types.is_numeric_dtype(df["quantity"])