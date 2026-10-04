import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne


# Natural key used to uniquely identify each coffee stock record.
# This prevents duplicate MongoDB documents when the pipeline is rerun.
NATURAL_KEY = [
    "report_date",
    "cut_off_date",
    "coffee_type",
    "origin",
    "location_code",
    "stock_category",
    "unit",
]


def load_to_mongodb(csv_path: Path) -> int:
    """
    Load the consolidated coffee stock dataset into MongoDB.

    Records are upserted using the dataset's natural key, making
    the load idempotent.

    Args:
        csv_path: Path to the consolidated CSV file.

    Returns:
        Number of records processed.
    """

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

    records = df.to_dict(orient="records")

    operations = []

    for record in records:
        # Convert pandas timestamps to Python datetime objects,
        # and convert missing dates to None for MongoDB.
        for column in ["report_date", "cut_off_date"]:
            if pd.isna(record[column]):
                record[column] = None
            elif hasattr(record[column], "to_pydatetime"):
                record[column] = record[column].to_pydatetime()

        # Origin is intentionally null for Robusta because it is
        # not available in the source report.
        if pd.isna(record["origin"]):
            record["origin"] = None

        record["quantity"] = int(record["quantity"])

        filter_document = {
            field: record[field]
            for field in NATURAL_KEY
        }

        # Upsert prevents duplicate records when the same dataset
        # is loaded into MongoDB multiple times.
        operations.append(
            UpdateOne(
                filter_document,
                {"$set": record},
                upsert=True,
            )
        )

    client = MongoClient(mongodb_uri)

    try:
        database = client[mongodb_database]
        collection = database[mongodb_collection]

        # Enforce uniqueness at the database level using the
        # same natural key used by the upsert operation.
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
                f"Inserted: {result.upserted_count:,}"
            )

            print(
                f"Modified: {result.modified_count:,}"
            )

        return len(operations)

    finally:
        # Always close the MongoDB connection after the load.
        client.close()