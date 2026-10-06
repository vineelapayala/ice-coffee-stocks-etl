"""
Tests the Arabica report parser using the first available extracted report.

The tests validate the output structure, coffee type, unit, quantities,
and report date without depending on a specific extraction date or
historical data range.
"""

from pathlib import Path

import pandas as pd

from src.parser import parse_arabica_report


ARABICA_DATA_DIR = Path("data/raw/arabica")


def get_arabica_sample_file() -> Path:
    """Return the first available Arabica extracted report."""
    files = sorted(ARABICA_DATA_DIR.glob("*.xls"))

    if not files:
        raise FileNotFoundError(
            f"No Arabica reports found in {ARABICA_DATA_DIR}"
        )

    return files[0]


ARABICA_SAMPLE_FILE = get_arabica_sample_file()


def test_parse_arabica_report_returns_dataframe():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert isinstance(df, pd.DataFrame)


def test_parse_arabica_report_has_expected_columns():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    expected_columns = [
        "report_date",
        "coffee_type",
        "origin",
        "location_code",
        "stock_category",
        "quantity",
        "unit",
    ]

    assert list(df.columns) == expected_columns


def test_parse_arabica_report_has_correct_coffee_type():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert df["coffee_type"].eq("Arabica").all()


def test_parse_arabica_report_has_correct_unit():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert df["unit"].eq("bags").all()


def test_parse_arabica_report_has_positive_quantities():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert df["quantity"].notna().all()
    assert (df["quantity"] > 0).all()


def test_parse_arabica_report_has_valid_report_date():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert df["report_date"].notna().all()