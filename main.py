from pathlib import Path

from src.mongodb_loader import load_to_mongodb
from src.pipeline import build_consolidated_dataset
from src.quality_report import generate_quality_report


ARABICA_DIR = Path("data/raw/arabica")
ROBUSTA_DIR = Path("data/raw/robusta")

PROCESSED_DIR = Path("data/processed")
QUALITY_DIR = Path("data/quality")

OUTPUT_FILE = PROCESSED_DIR / "coffee_stock_consolidated.csv"
QUALITY_REPORT_FILE = QUALITY_DIR / "data_quality_report.json"


def main():
    print("=" * 60)
    print("ICE COFFEE STOCKS - FULL PIPELINE")
    print("=" * 60)

    df, pipeline_stats = build_consolidated_dataset(
        arabica_dir=ARABICA_DIR,
        robusta_dir=ROBUSTA_DIR,
    )

    generate_quality_report(
        df=df,
        arabica_file_count=pipeline_stats["arabica_files_found"],
        robusta_file_count=pipeline_stats["robusta_files_found"],
        robusta_selected_file_count=pipeline_stats[
            "robusta_files_selected_for_parsing"
        ],
        duplicate_groups_count=pipeline_stats[
            "identical_duplicate_groups"
        ],
        output_path=QUALITY_REPORT_FILE,
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    output_df = df.copy()

    output_df["report_date"] = output_df["report_date"].dt.strftime("%Y-%m-%d")
    output_df["cut_off_date"] = output_df["cut_off_date"].dt.strftime("%Y-%m-%d")

    output_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nConsolidated dataset saved to: {OUTPUT_FILE}")

    load_to_mongodb(OUTPUT_FILE)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    print(f"\nTotal rows: {len(df):,}")

    print("\nRows by coffee type:")
    print(df["coffee_type"].value_counts().to_string())

    print("\nRows by stock category:")
    print(df["stock_category"].value_counts().to_string())

    print("\nDate range:")
    print(
        f"{df['report_date'].min().date()} -> "
        f"{df['report_date'].max().date()}"
    )

    print("\nUnits:")
    print(df["unit"].value_counts().to_string())

    print("\nSample:")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()