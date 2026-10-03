from pathlib import Path

import pandas as pd
import pytest

from src.validator import (
    validate_schema,
    validate_required_fields,
    validate_coffee_type,
    validate_units,
    validate_quantities,
    validate_dates,
    validate_duplicates,
    validate_consolidated_dataset,
)


VALID_DATA = pd.DataFrame(
    {
        "report_date": [
            pd.Timestamp("2026-10-01"),
            pd.Timestamp("2026-10-01"),
        ],
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
            pd.NA,
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


FILE_PATH = Path("test_sample.csv")


# ---------------------------------------------------------------------------
# Valid data tests
# ---------------------------------------------------------------------------


def test_validate_schema_accepts_valid_data():
    validate_schema(VALID_DATA, FILE_PATH)


def test_validate_required_fields_accepts_valid_data():
    validate_required_fields(VALID_DATA, FILE_PATH)


def test_validate_coffee_type_accepts_valid_data():
    validate_coffee_type(VALID_DATA, FILE_PATH)


def test_validate_units_accepts_valid_data():
    validate_units(VALID_DATA, FILE_PATH)


def test_validate_quantities_accepts_valid_data():
    validate_quantities(VALID_DATA, FILE_PATH)


def test_validate_dates_accepts_valid_data():
    validate_dates(VALID_DATA, FILE_PATH)


def test_validate_duplicates_accepts_valid_data():
    validate_duplicates(VALID_DATA, FILE_PATH)


def test_validate_consolidated_dataset_accepts_valid_data():
    validate_consolidated_dataset(VALID_DATA)


# ---------------------------------------------------------------------------
# Invalid data tests
# ---------------------------------------------------------------------------


def test_validate_schema_rejects_missing_column():
    df = VALID_DATA.drop(columns=["quantity"])

    with pytest.raises(ValueError):
        validate_schema(df, FILE_PATH)


def test_validate_required_fields_rejects_null_required_field():
    df = VALID_DATA.copy()
    df.loc[0, "report_date"] = pd.NaT

    with pytest.raises(ValueError):
        validate_required_fields(df, FILE_PATH)


def test_validate_coffee_type_rejects_invalid_coffee_type():
    df = VALID_DATA.copy()
    df.loc[0, "coffee_type"] = "Unknown"

    with pytest.raises(ValueError):
        validate_coffee_type(df, FILE_PATH)


def test_validate_units_rejects_invalid_unit():
    df = VALID_DATA.copy()
    df.loc[0, "unit"] = "kg"

    with pytest.raises(ValueError):
        validate_units(df, FILE_PATH)


def test_validate_quantities_rejects_null_quantity():
    df = VALID_DATA.copy()
    df.loc[0, "quantity"] = None

    with pytest.raises(ValueError):
        validate_quantities(df, FILE_PATH)


def test_validate_quantities_rejects_negative_quantity():
    df = VALID_DATA.copy()
    df.loc[0, "quantity"] = -100

    with pytest.raises(ValueError):
        validate_quantities(df, FILE_PATH)


def test_validate_dates_rejects_invalid_report_date():
    df = VALID_DATA.copy()
    df.loc[0, "report_date"] = pd.NaT

    with pytest.raises(ValueError):
        validate_dates(df, FILE_PATH)


def test_validate_duplicates_rejects_duplicate_rows():
    df = pd.concat(
        [
            VALID_DATA,
            VALID_DATA.iloc[[0]],
        ],
        ignore_index=True,
    )

    with pytest.raises(ValueError):
        validate_duplicates(df, FILE_PATH)


def test_validate_consolidated_dataset_rejects_invalid_coffee_type():
    df = VALID_DATA.copy()
    df.loc[0, "coffee_type"] = "Unknown"

    with pytest.raises(ValueError):
        validate_consolidated_dataset(df)