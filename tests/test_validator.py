"""
Tests the validation rules for the consolidated Arabica and Robusta coffee
stock dataset.

The tests cover schema validation, required fields, coffee types, units,
quantities, dates, duplicate records, and consolidated dataset validation.
"""
from pathlib import Path

import pandas as pd
import pytest

from src.validator import (
    COMMON_COLUMNS,
    validate_coffee_type,
    validate_consolidated_dataset,
    validate_dates,
    validate_duplicates,
    validate_quantities,
    validate_report,
    validate_required_fields,
    validate_schema,
    validate_units,
)


FILE_PATH = Path("test_sample.csv")


VALID_DATA = pd.DataFrame(
    {
        "report_date": pd.to_datetime(
            ["2026-10-01", "2026-10-01"]
        ),
        "cut_off_date": [
            pd.NaT,
            pd.Timestamp("2026-09-30"),
        ],
        "coffee_type": [
            "Arabica",
            "Robusta",
        ],
        "origin": [
            "Brazil",
            None,
        ],
        "location_code": [
            "ANT",
            "LON",
        ],
        "stock_category": [
            "TOTAL_BAGS_CERTIFIED",
            "VALID_CERTIFICATE",
        ],
        "quantity": [
            1000,
            500,
        ],
        "unit": [
            "bags",
            "lots",
        ],
    }
)


def test_validate_schema_valid_data():
    validate_schema(VALID_DATA, FILE_PATH)


def test_validate_schema_missing_column():
    df = VALID_DATA.drop(columns=["quantity"])

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_schema(df, FILE_PATH)


def test_validate_required_fields():
    validate_required_fields(VALID_DATA, FILE_PATH)


def test_validate_required_fields_null_report_date():
    df = VALID_DATA.copy()
    df.loc[0, "report_date"] = pd.NaT

    with pytest.raises(ValueError, match="report_date"):
        validate_required_fields(df, FILE_PATH)


def test_validate_coffee_type():
    validate_coffee_type(VALID_DATA, FILE_PATH)


def test_validate_coffee_type_invalid():
    df = VALID_DATA.copy()
    df.loc[0, "coffee_type"] = "Unknown"

    with pytest.raises(ValueError, match="Invalid coffee type"):
        validate_coffee_type(df, FILE_PATH)


def test_validate_units():
    validate_units(VALID_DATA, FILE_PATH)


def test_validate_units_invalid():
    df = VALID_DATA.copy()
    df.loc[0, "unit"] = "kg"

    with pytest.raises(ValueError, match="Invalid unit"):
        validate_units(df, FILE_PATH)


def test_validate_quantities():
    validate_quantities(VALID_DATA, FILE_PATH)


def test_validate_quantities_null():
    df = VALID_DATA.copy()
    df.loc[0, "quantity"] = None

    with pytest.raises(ValueError, match="Quantity"):
        validate_quantities(df, FILE_PATH)


def test_validate_quantities_negative():
    df = VALID_DATA.copy()
    df.loc[0, "quantity"] = -100

    with pytest.raises(ValueError, match="negative"):
        validate_quantities(df, FILE_PATH)


def test_validate_dates():
    validate_dates(VALID_DATA, FILE_PATH)


def test_validate_dates_invalid_report_date():
    df = VALID_DATA.copy()

    # Convert to object so an invalid string can be inserted
    # without pandas rejecting it before validation.
    df["report_date"] = df["report_date"].astype(object)
    df.loc[0, "report_date"] = "invalid-date"

    with pytest.raises(ValueError, match="report_date"):
        validate_dates(df, FILE_PATH)


def test_validate_dates_missing_robusta_cutoff():
    df = VALID_DATA.copy()
    df.loc[1, "cut_off_date"] = pd.NaT

    with pytest.raises(ValueError, match="cut_off_date"):
        validate_dates(df, FILE_PATH)


def test_validate_duplicates():
    validate_duplicates(VALID_DATA, FILE_PATH)


def test_validate_duplicates_invalid():
    df = pd.concat(
        [VALID_DATA, VALID_DATA.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="duplicate"):
        validate_duplicates(df, FILE_PATH)


def test_validate_report():
    validate_report(VALID_DATA, FILE_PATH)


def test_validate_consolidated_dataset():
    validate_consolidated_dataset(VALID_DATA)


def test_validate_consolidated_dataset_empty():
    empty_df = pd.DataFrame(columns=COMMON_COLUMNS)

    with pytest.raises(ValueError, match="empty"):
        validate_consolidated_dataset(empty_df)


def test_validate_consolidated_dataset_invalid_coffee_type():
    df = VALID_DATA.copy()
    df.loc[0, "coffee_type"] = "Unknown"

    with pytest.raises(ValueError, match="Invalid coffee type"):
        validate_consolidated_dataset(df)