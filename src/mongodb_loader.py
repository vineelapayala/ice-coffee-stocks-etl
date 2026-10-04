import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne


NATURAL_KEY = [
    "report_date",
    "cut_off_date",
    "coffee_type",
    "origin",
    "location_code",
    "stock_category",
    "unit",
]


def _get_mongodb_config() -> tuple[str, str, str]:
    """Get MongoDB connection settings from environment variables."""

    load_dotenv()

    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        raise ValueError(
            "MONGODB_URI is not set in the environment."
        )

    mongodb_database = os.getenv(
        "MONGODB_DATABASE",
        "ice_coffee_stocks",
    )

    mongodb_collection = os.getenv(
        "MONGODB_COLLECTION",
        "coffee_stock",
    )

    return (
        mongodb_uri,
        mongodb_database,
        mongodb_collection,
    )


def _prepare_record(
    record: dict,
) -> dict:
    """Convert a pandas record into MongoDB-compatible values."""

    for column in [
        "report_date",
        "cut_off_date",
    ]:
        if pd.isna(record[column]):
            record[column] = None
        elif hasattr(
            record[column],
            "to_pydatetime",
        ):
            record[column] = (
                record[column].to_pydatetime()
            )

    # Origin is unavailable in the Robusta source.
    if pd.isna(record["origin"]):
        record["origin"] = None

    record["quantity"] = int(
        record["quantity"]
    )

    return record


def _prepare_mongodb_operations(
    csv_path: Path,
) -> list[UpdateOne]:
    """
    Read the consolidated CSV and prepare MongoDB upsert operations.
    """

    df = pd.read_csv(csv_path)

    df["report_date"] = pd.to_datetime(
        df["report_date"],
        errors="raise",
    )

    df["cut_off_date"] = pd.to_datetime(
        df["cut_off_date"],
        errors="coerce",
    )

    df["quantity"] = pd.to_numeric(
        df["quantity"],
        errors="raise",
    )

    records = df.to_dict(
        orient="records"
    )

    operations = []

    for record in records:
        record = _prepare_record(record)

        filter_document = {
            field: record[field]
            for field in NATURAL_KEY
        }

        operations.append(
            UpdateOne(
                filter_document,
                {"$set": record},
                upsert=True,
            )
        )

    return operations


def load_to_mongodb(
    csv_path: Path,
) -> int:
    """
    Load the consolidated coffee stock dataset into MongoDB.

    Records are upserted using the dataset's natural key,
    making the load idempotent.

    Args:
        csv_path: Path to the consolidated CSV file.

    Returns:
        Number of records processed.
    """

    (
        mongodb_uri,
        mongodb_database,
        mongodb_collection,
    ) = _get_mongodb_config()

    operations = _prepare_mongodb_operations(
        csv_path
    )

    with MongoClient(mongodb_uri) as client:
        database = client[
            mongodb_database
        ]

        collection = database[
            mongodb_collection
        ]

        collection.create_index(
            NATURAL_KEY,
            unique=True,
            name="coffee_stock_natural_key",
        )

        if operations:
            result = collection.bulk_write(
                operations,
                ordered=False,
            )

            print(
                f"MongoDB load complete: "
                f"{len(operations):,} records processed"
            )

            print(
                f"Inserted: "
                f"{result.upserted_count:,}"
            )

            print(
                f"Modified: "
                f"{result.modified_count:,}"
            )

    return len(operations)