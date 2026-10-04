import os
from pathlib import Path

from dotenv import load_dotenv

from src.mongodb_loader import load_to_mongodb
from src.pipeline import build_consolidated_dataset
from src.quality_report import generate_quality_report


# Load environment variables from .env
load_dotenv()


ARABICA_DIR = Path("data/raw/arabica")
ROBUSTA_DIR = Path("data/raw/robusta")

QUALITY_DIR = Path("data/quality")
QUALITY_REPORT_FILE = (
    QUALITY_DIR / "data_quality_report.json"
)

# Final case-study deliverable.
# The consolidated dataset is saved in the repository root.
OUTPUT_FILE = Path(
    "coffee_stock_consolidated.csv"
)


def _save_consolidated_dataset(
    df,
    output_path: Path,
) -> None:
    """
    Save the consolidated dataset as a CSV file.

    Date columns are formatted as YYYY-MM-DD
    before writing the final dataset.
    """

    output_df = df.copy()

    output_df["report_date"] = (
        output_df["report_date"]
        .dt.strftime("%Y-%m-%d")
    )

    output_df["cut_off_date"] = (
        output_df["cut_off_date"]
        .dt.strftime("%Y-%m-%d")
    )

    output_df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nConsolidated dataset saved to: "
        f"{output_path}"
    )


def _print_pipeline_summary(
    df,
) -> None:
    """Print a summary of the completed pipeline."""

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    print(
        f"\nTotal rows: {len(df):,}"
    )

    print("\nRows by coffee type:")
    print(
        df["coffee_type"]
        .value_counts()
        .to_string()
    )

    print("\nRows by stock category:")
    print(
        df["stock_category"]
        .value_counts()
        .to_string()
    )

    print("\nDate range:")
    print(
        f"{df['report_date'].min().date()} "
        f"-> "
        f"{df['report_date'].max().date()}"
    )

    print("\nUnits:")
    print(
        df["unit"]
        .value_counts()
        .to_string()
    )

    print("\nSample:")
    print(
        df.head(10)
        .to_string(index=False)
    )


def main():
    print("=" * 60)
    print("ICE COFFEE STOCKS - FULL PIPELINE")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Extract, parse, normalize and validate the data
    # ---------------------------------------------------------
    df, pipeline_stats = build_consolidated_dataset(
        arabica_dir=ARABICA_DIR,
        robusta_dir=ROBUSTA_DIR,
    )

    # ---------------------------------------------------------
    # 2. Generate data-quality report
    # ---------------------------------------------------------
    generate_quality_report(
        df=df,
        arabica_file_count=pipeline_stats[
            "arabica_files_found"
        ],
        robusta_file_count=pipeline_stats[
            "robusta_files_found"
        ],
        robusta_selected_file_count=pipeline_stats[
            "robusta_files_selected_for_parsing"
        ],
        duplicate_groups_count=pipeline_stats[
            "identical_duplicate_groups"
        ],
        output_path=QUALITY_REPORT_FILE,
    )

    # ---------------------------------------------------------
    # 3. Save consolidated dataset
    # ---------------------------------------------------------
    _save_consolidated_dataset(
        df=df,
        output_path=OUTPUT_FILE,
    )

    # ---------------------------------------------------------
    # 4. Optional MongoDB load
    # ---------------------------------------------------------
    if os.getenv("MONGODB_URI"):
        load_to_mongodb(
            OUTPUT_FILE
        )
    else:
        print(
            "\nMONGODB_URI not configured. "
            "Skipping MongoDB load."
        )

    # ---------------------------------------------------------
    # 5. Pipeline summary
    # ---------------------------------------------------------
    _print_pipeline_summary(
        df
    )


if __name__ == "__main__":
    main()