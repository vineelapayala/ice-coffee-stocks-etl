from datetime import date
from pathlib import Path

import pandas as pd

from src.parser import parse_arabica_report


ARABICA_SAMPLE_FILE = Path(
    "data/raw/arabica/coffee_cert_stock_20261001.xls"
)


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


def test_parse_arabica_report_has_expected_report_date():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert df["report_date"].nunique() == 1
    assert df["report_date"].iloc[0] == date(
        2026,
        10,
        1,
    )


def test_parse_arabica_report_has_correct_coffee_type():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert df["coffee_type"].nunique() == 1
    assert df["coffee_type"].iloc[0] == "Arabica"


def test_parse_arabica_report_has_correct_unit():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert df["unit"].nunique() == 1
    assert df["unit"].iloc[0] == "bags"


def test_parse_arabica_report_has_positive_quantities():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert df["quantity"].notna().all()
    assert (df["quantity"] > 0).all()


def test_parse_arabica_report_has_expected_row_count():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert len(df) == 35


def test_parse_arabica_report_has_expected_total_quantity():
    df = parse_arabica_report(ARABICA_SAMPLE_FILE)

    assert df["quantity"].sum() == 260364