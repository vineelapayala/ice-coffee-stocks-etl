# ICE Certified Coffee Stocks ETL

An end-to-end Python ETL pipeline for extracting, cleaning, validating, transforming, and consolidating approximately one year of ICE Certified Arabica and Robusta coffee stock data into a single analysis-ready dataset.

The project handles the differences between the two ICE reporting systems, including different source formats, extraction mechanisms, report structures, stock categories, units, and date representations.

The final dataset is stored as a normalized CSV file and can optionally be loaded into MongoDB Atlas.

---

## Table of Contents

- [Overview](#overview)
- [Objectives](#objectives)
- [Architecture](#architecture)
- [Data Sources](#data-sources)
- [End-to-End Data Flow](#end-to-end-data-flow)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [Step 1 - Extract Arabica Data](#step-1---extract-arabica-data)
- [Step 2 - Discover Robusta Reports](#step-2---discover-robusta-reports)
- [Step 3 - Extract Robusta Data](#step-3---extract-robusta-data)
- [Step 4 - Parse the Source Data](#step-4---parse-the-source-data)
- [Step 5 - Schema Normalization](#step-5---schema-normalization)
- [Step 6 - Duplicate Handling](#step-6---duplicate-handling)
- [Step 7 - Data Quality Validation](#step-7---data-quality-validation)
- [Step 8 - Generate the Quality Report](#step-8---generate-the-quality-report)
- [Step 9 - Generate the Consolidated Dataset](#step-9---generate-the-consolidated-dataset)
- [Step 10 - MongoDB Integration](#step-10---mongodb-integration)
- [Common Data Schema](#common-data-schema)
- [Current Results](#current-results)
- [Testing](#testing)
- [Configuration](#configuration)
- [Reproducibility](#reproducibility)
- [Git and Repository Workflow](#git-and-repository-workflow)
- [Future Improvements](#future-improvements)

---

## Overview

This project implements an end-to-end ETL pipeline for ICE Certified Coffee Stock data.

The objective is to retrieve approximately one year of historical stock reports for:

- Certified Arabica coffee
- Certified Robusta coffee

The two ICE reports use different data delivery mechanisms:

- Arabica reports are available as XLS files through a deterministic URL pattern.
- Robusta reports are dynamically generated through the ICE Market Data API and returned as CSV report URLs.

Because the source structures are different, the pipeline performs source-specific extraction and parsing before transforming both datasets into a common analytical schema.

The pipeline then:

1. Extracts the source data.
2. Parses the source-specific report structures.
3. Normalizes both datasets into a common schema.
4. Detects identical duplicate Robusta source files.
5. Validates individual reports.
6. Consolidates Arabica and Robusta records.
7. Performs final dataset validation.
8. Generates a data-quality report.
9. Writes the final consolidated CSV.
10. Optionally loads the dataset into MongoDB Atlas.

---

## Objectives

The main objectives of the project are:

- Retrieve historical ICE Certified Coffee Stock data.
- Process both Arabica and Robusta reports.
- Handle different source extraction mechanisms.
- Parse different report structures.
- Preserve important source dimensions.
- Normalize both datasets into a common schema.
- Validate source-level and consolidated data.
- Detect duplicate Robusta source files.
- Validate source totals where available.
- Generate a consolidated analysis-ready dataset.
- Generate a machine-readable data-quality report.
- Provide automated tests for parsing and validation.
- Support optional MongoDB Atlas integration.
- Make the ETL process reproducible and maintainable.

---

# Architecture

The overall architecture is:

```text
                         ICE Certified Coffee Reports
                                    |
                    +---------------+---------------+
                    |                               |
                    v                               v
                 Arabica                         Robusta
                Report 42                       Report 173
                    |                               |
                    v                               v
            Deterministic XLS              API Report Discovery
                    |                               |
                    v                               v
          Historical Extraction               CSV URL Discovery
                    |                               |
                    |                               v
                    |                         CSV Extraction
                    |                               |
                    +---------------+---------------+
                                    |
                                    v
                              Source Parsing
                                    |
                                    v
                            Schema Normalization
                                    |
                                    v
                         Robusta Duplicate Handling
                                    |
                                    v
                           Individual Validation
                                    |
                                    v
                           Dataset Consolidation
                                    |
                                    v
                         Final Dataset Validation
                                    |
                         +----------+----------+
                         |                     |
                         v                     v
                 Consolidated CSV       Quality Report
                         |
                         v
                    MongoDB Atlas
                       (Optional)
```

---

# Data Sources

## Arabica

ICE Report 42 - Stock Figures

Source:

https://www.ice.com/report/42

Arabica historical certified stock reports are available as XLS files.

The report contains warehouse-level certified stock information and a source-level total.

The pipeline uses the `TOTAL BAGS CERTIFIED` section.

### Arabica Characteristics

- Source format: XLS
- Report type: Stock Figures
- Unit: bags
- Grain: report date + warehouse + stock category
- Source total available for reconciliation
- Warehouse/location codes are preserved
- The aggregate `Total` column is not treated as a physical warehouse

---

## Robusta

ICE Report 173 - Stock Figures

Source:

https://www.ice.com/report/173

Robusta reports are dynamically generated through the ICE Market Data API.

The report results are requested through:

```text
/marketdata/api/reports/173/results
```

The request uses the `Stock Figures` report type and a date range.

The API response contains dynamically generated CSV report URLs.

Because the generated URLs contain timestamp information, the final report URL is discovered from the API response instead of being manually constructed.

### Robusta Characteristics

- Source format: CSV
- Report type: Stock Figures
- Unit: lots
- Location information is available through `PortId`
- Coffee origin is not provided by the source
- `GrandTotal` is treated as an aggregate and excluded from location-level records
- Report date is extracted from the generated filename
- Cut-off date is extracted from the source data

---

# End-to-End Data Flow

The complete pipeline can be summarized as:

```text
ICE Sources
    |
    +---- Arabica XLS
    |
    +---- Robusta API / CSV
             |
             v
        Raw Source Files
             |
             v
           Parsers
             |
             v
      Common Data Schema
             |
             v
      Duplicate Detection
             |
             v
        Data Validation
             |
             v
      Consolidated DataFrame
             |
         +---+---+
         |       |
         v       v
        CSV   Quality Report
         |
         v
    MongoDB Atlas
       (optional)
```

---

# Project Structure

```text
ice-coffee-stocks-etl/
│
├── data/
│   ├── raw/
│   │   ├── arabica/
│   │   ├── robusta/
│   │   └── robusta_discovery/
│   │
│   └── quality/
│       └── data_quality_report.json
│
├── src/
│   ├── __init__.py
│   │
│   ├── extractor.py
│   ├── historical_extractor.py
│   ├── robusta_extractor.py
│   ├── robusta_discovery.py
│   ├── run_arabica.py
│   ├── run_robusta.py
│   │
│   ├── parser.py
│   ├── robusta_parser.py
│   │
│   ├── pipeline.py
│   ├── validator.py
│   ├── quality_report.py
│   ├── mongodb_loader.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py
│       └── http_utils.py
│
├── tests/
│   ├── test_parser.py
│   ├── test_robusta_parser.py
│   └── test_validator.py
│
├── coffee_stock_consolidated.csv
├── main.py
├── requirements.txt
├── .gitignore
├── README.md
└── CLONE_AND_RUN.md
```

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | Main pipeline orchestration |
| `extractor.py` | Arabica report downloading |
| `historical_extractor.py` | Iterates over the requested Arabica date range |
| `run_arabica.py` | Entry point for Arabica historical extraction |
| `robusta_discovery.py` | Discovers dynamically generated Robusta report URLs |
| `run_robusta.py` | Entry point for Robusta report extraction |
| `robusta_extractor.py` | Downloads Robusta CSV reports |
| `parser.py` | Parses Arabica XLS reports |
| `robusta_parser.py` | Parses Robusta CSV reports |
| `pipeline.py` | Coordinates parsing, deduplication, validation, and consolidation |
| `validator.py` | Performs data-quality validation |
| `quality_report.py` | Generates the JSON data-quality report |
| `mongodb_loader.py` | Loads the consolidated dataset into MongoDB |
| `utils/file_utils.py` | Shared file utilities and SHA-256 hashing |
| `utils/http_utils.py` | Shared HTTP session and retry utilities |
| `tests/` | Automated tests |

---

# Technology Stack

- Python
- Pandas
- Requests
- Nodriver
- Pytest
- PyMongo
- Python-dotenv
- xlrd
- Excel/XLS processing
- CSV processing
- REST API
- MongoDB Atlas
- Git / GitHub

---

# Installation

## 1. Clone the Repository

```powershell
git clone https://github.com/vineelapayala/ice-coffee-stocks-etl.git
cd ice-coffee-stocks-etl
```

For a complete setup guide, see:

```text
CLONE_AND_RUN.md
```

The main pipeline performs the following operations:

```text
1. Discover local Arabica XLS files
2. Discover local Robusta CSV files
3. Deduplicate identical Robusta files
4. Parse Arabica reports
5. Parse Robusta reports
6. Validate individual reports
7. Combine both datasets
8. Standardize data types
9. Validate the consolidated dataset
10. Generate the quality report
11. Write the consolidated CSV
12. Load into MongoDB if configured
13. Print pipeline summary
```

MongoDB is optional. If `MONGODB_URI` is not configured, the pipeline skips the MongoDB loading step.

---

# Step 1 - Extract Arabica Data

Arabica reports follow a deterministic XLS URL pattern.

For each requested date, the extractor:

1. Builds the expected report URL.
2. Sends an HTTP request.
3. Handles unavailable reports.
4. Handles HTTP `429 Too Many Requests`.
5. Uses retry and exponential backoff.
6. Honors the `Retry-After` header when available.
7. Validates that the response is an XLS file.
8. Skips files that already exist locally.
9. Saves valid reports under:

```text
data/raw/arabica/
```

The historical extractor iterates through the requested date range and calls the Arabica downloader for each date.

---

# Step 2 - Discover Robusta Reports

Robusta is different from Arabica because its report URLs are dynamically generated.

The discovery process uses the ICE Market Data API through a browser session.

The relevant API endpoint is:

```text
/marketdata/api/reports/173/results
```

The request uses:

```text
reportType=Stock Figures
startDate=<date>
endDate=<date>
```

The API response contains dynamically generated CSV report URLs.

The discovery process:

1. Connects to the existing browser session using Nodriver.
2. Sends/observes the required report request.
3. Captures the ICE Market Data API response.
4. Extracts available CSV report URLs.
5. Extracts report dates and filenames.
6. Stores the discovered metadata.

Discovery output is stored under:

```text
data/raw/robusta_discovery/
```

The discovery process requires manual CAPTCHA completion when ICE presents a CAPTCHA.

The automation does not attempt to bypass or solve the CAPTCHA.

---

# Step 3 - Extract Robusta Data

Once report metadata has been discovered, the Robusta extractor downloads the corresponding CSV files.

The extractor:

1. Reads the discovered report metadata.
2. Downloads each CSV report.
3. Skips files that already exist.
4. Validates the HTTP response.
5. Handles HTTP `429` responses.
6. Uses retry and exponential backoff.
7. Honors `Retry-After` when available.
8. Waits between requests.
9. Saves reports under:

```text
data/raw/robusta/
```

---

# Step 4 - Parse the Source Data

## Arabica Parser

The Arabica parser processes the XLS structure.

The parser:

1. Reads the XLS file.
2. Extracts the report date.
3. Locates the `TOTAL BAGS CERTIFIED` section.
4. Identifies warehouse columns.
5. Extracts the source total.
6. Excludes the aggregate `Total` column from warehouse-level records.
7. Converts warehouse columns into rows.
8. Removes invalid or zero quantities.
9. Validates the parsed total against the source total.
10. Adds the normalized schema fields.

The Arabica unit is:

```text
bags
```

The source `Total` represents an aggregate and is therefore not treated as a physical warehouse.

---

## Robusta Parser

The Robusta parser processes the dynamically generated CSV files.

The source contains fields such as:

```text
Commodity
CutOffDate
PortId
LotsWithValCert
LotsNonTend
LotsSuspended
```

The parser:

1. Reads the CSV.
2. Validates expected source columns.
3. Validates the commodity.
4. Separates the `GrandTotal` row from location-level rows.
5. Extracts the report date from the filename.
6. Extracts the cut-off date from the source.
7. Converts stock quantities to numeric values.
8. Converts the wide source structure into a long structure.
9. Maps source stock columns to normalized stock categories.
10. Validates the parsed totals against the source `GrandTotal`.
11. Adds the common schema fields.

The source stock categories are mapped as follows:

| Source Column | Normalized Category |
|---|---|
| `LotsWithValCert` | `VALID_CERTIFICATE` |
| `LotsNonTend` | `NON_TENDERABLE` |
| `LotsSuspended` | `SUSPENDED` |

The Robusta unit is:

```text
lots
```

The Robusta source does not provide coffee origin, so:

```text
origin = null
```

for Robusta records.

---

# Step 5 - Schema Normalization

Arabica and Robusta have different source structures.

To make them analyzable together, both are transformed into the following common schema:

```text
report_date
cut_off_date
coffee_type
origin
location_code
stock_category
quantity
unit
```

This allows the final dataset to contain both coffee types while preserving source-specific dimensions where available.

---

# Common Data Schema

| Column | Description |
|---|---|
| `report_date` | Date associated with the ICE report |
| `cut_off_date` | Stock cut-off date where provided by the source |
| `coffee_type` | `Arabica` or `Robusta` |
| `origin` | Coffee origin where available |
| `location_code` | Warehouse or port/location code |
| `stock_category` | Type of certified stock |
| `quantity` | Stock quantity |
| `unit` | Unit of measurement |

### Units

| Coffee Type | Unit |
|---|---|
| Arabica | bags |
| Robusta | lots |

---

# Step 6 - Duplicate Handling

Robusta report URLs contain generated timestamp values.

Therefore, multiple files can exist for the same report date even when their contents are identical.

The pipeline handles this using SHA-256 file hashing.

For each Robusta file, the pipeline records:

- Report date
- Report timestamp
- File path
- SHA-256 hash

Files are grouped by report date.

If multiple files have:

1. The same report date, and
2. The same SHA-256 hash

they are considered identical duplicates.

The file with the latest timestamp is retained.

Different files with different content for the same report date are not silently discarded. The pipeline raises an error because the difference requires investigation.

This prevents accidental duplication while avoiding silent loss of potentially meaningful source changes.

---

# Step 7 - Data Quality Validation

Validation occurs at two levels:

1. Individual parsed reports
2. Final consolidated dataset

## Individual Report Validation

Each parsed report is checked for:

- Schema
- Required fields
- Coffee type
- Units
- Quantities
- Dates
- Duplicate records

## Consolidated Dataset Validation

The final dataset is checked for:

- Non-empty dataset
- Expected schema
- Required fields
- Valid coffee types
- Valid units
- Coffee-type/unit consistency
- Numeric quantities
- Non-negative quantities
- Duplicate natural grain

### Coffee Type Validation

Only the following values are allowed:

```text
Arabica
Robusta
```

### Unit Validation

Allowed units are:

```text
bags
lots
```

with the following relationship:

```text
Arabica → bags
Robusta → lots
```

### Quantity Validation

Quantities must:

- Be numeric
- Not be null
- Not be negative

### Duplicate Validation

The expected natural grain is:

```text
report_date
cut_off_date
coffee_type
origin
location_code
stock_category
unit
```

Duplicate records at this grain are rejected.

### Calendar Date Coverage

Missing calendar dates are reported in the quality report for completeness analysis.

They are not automatically treated as validation failures because ICE reports may not be published on every calendar day.

---

# Step 8 - Generate the Quality Report

After successful validation, the pipeline generates:

```text
data/quality/data_quality_report.json
```

The report contains:

### Source File Statistics

- Arabica files found
- Robusta files found
- Robusta files selected for parsing
- Identical duplicate groups

### Dataset Statistics

- Total rows
- Arabica rows
- Robusta rows
- Overall date range

### Date Coverage

Separate coverage information for:

- Arabica
- Robusta

Including:

- Distinct report dates
- Start date
- End date
- Missing calendar dates

### Distributions

- Coffee type
- Stock category
- Unit
- Location

### Null Checks

- Null count by column
- Null quantity count

### Duplicate Checks

- Duplicate row count

### Quantity Checks

- Negative quantity count
- Zero quantity count

### Quality Status

The report records whether the expected validation checks passed.

---

# Step 9 - Generate the Consolidated Dataset

After parsing and validation, the Arabica and Robusta DataFrames are concatenated into one DataFrame.

The pipeline then standardizes:

- Report dates
- Cut-off dates
- Quantities

The final dataset is sorted by:

```text
report_date
coffee_type
location_code
stock_category
origin
```

The final output is:

```text
coffee_stock_consolidated.csv
```

This is the primary analysis-ready deliverable of the project.

---

# Step 10 - MongoDB Integration

MongoDB Atlas integration is optional.

When a MongoDB connection string is configured, the consolidated CSV is loaded into MongoDB after successful validation and CSV generation.

## Configuration

Create a `.env` file in the project root:

```text
MONGODB_URI=<your MongoDB connection string>
MONGODB_DATABASE=ice_coffee_stocks
MONGODB_COLLECTION=coffee_stock
```

The `.env` file is excluded from Git and must never be committed.

## MongoDB Destination

Default database:

```text
ice_coffee_stocks
```

Default collection:

```text
coffee_stock
```

## Idempotent Loading

The MongoDB loader uses `upsert=True`.

Records are uniquely identified using the same natural key used by the dataset:

```text
report_date
cut_off_date
coffee_type
origin
location_code
stock_category
unit
```

A unique compound MongoDB index is also created on these fields.

This provides two levels of duplicate protection:

```text
Application level
       ↓
UpdateOne + upsert
       ↓
Database level
       ↓
Unique compound index
```

As a result, rerunning the pipeline with the same source data does not create duplicate MongoDB documents.

---

# Current Results

The current historical extraction produced:

| Metric | Result |
|---|---:|
| Arabica source files | 252 |
| Robusta source files | 254 |
| Identical Robusta duplicate groups | 1 |
| Robusta files selected for parsing | 253 |
| Consolidated rows | 11,579 |
| Arabica rows | 10,020 |
| Robusta rows | 1,559 |
| Duplicate rows in final dataset | 0 |
| Negative quantities | 0 |
| Null quantities | 0 |

The consolidated dataset currently covers:

```text
2025-10-03 → 2026-10-02
```

These figures represent the current extracted dataset and may change if the source data or extraction period is updated.

---

# Testing

The project contains automated tests covering:

- Arabica parsing
- Robusta parsing
- Schema validation
- Required-field validation
- Coffee-type validation
- Unit validation
- Quantity validation
- Date validation
- Duplicate validation

Run the complete test suite with:

```powershell
python -m pytest
```

Current test suite:

```text
35 tests
```

Expected result:

```text
35 passed
```

---

# Configuration

The project does not require MongoDB to run the core ETL pipeline.

Without MongoDB configuration:

```text
Extraction
    ↓
Parsing
    ↓
Validation
    ↓
Quality Report
    ↓
CSV
```

With MongoDB configuration:

```text
Extraction
    ↓
Parsing
    ↓
Validation
    ↓
Quality Report
    ↓
CSV
    ↓
MongoDB Atlas
```

MongoDB configuration is loaded using `python-dotenv`.

---

# Reproducibility

The repository contains the code required for:

- Arabica extraction
- Robusta report discovery
- Robusta extraction
- Source parsing
- Schema normalization
- Duplicate detection
- Data validation
- Quality reporting
- CSV generation
- MongoDB loading

Raw ICE source files are intentionally excluded from Git because they are downloaded source data.

The following directories are ignored:

```text
data/raw/
.venv/
.pytest_cache/
```

The final consolidated CSV and quality report are retained as project outputs.

For complete clone and setup instructions, see:

```text
CLONE_AND_RUN.md
```

---

# Important Notes

## Raw Source Data

Raw ICE reports are not committed to the repository.

Arabica raw files are stored locally under:

```text
data/raw/arabica/
```

Robusta raw files are stored locally under:

```text
data/raw/robusta/
```

Robusta discovery artifacts are stored under:

```text
data/raw/robusta_discovery/
```

These directories are excluded through `.gitignore`.

## Credentials

MongoDB credentials must be stored in:

```text
.env
```

Never commit credentials or connection strings to GitHub.

## CAPTCHA

Robusta report discovery may require manual CAPTCHA completion.

The project does not attempt to bypass or solve the CAPTCHA.

## Source Totals

The parsers use source-level totals where available to validate that the extracted location-level records reconcile with the source report.

This provides an additional data-quality check beyond schema and field validation.

---

# Git and Repository Workflow

The repository follows a feature-based Git workflow:

```text
feature/<feature>
       |
       | Pull Request
       v
      dev
       |
       | Pull Request
       v
     main
```

The intended roles are:

- `feature/*` → isolated development
- `dev` → integration and testing branch
- `main` → final stable branch

Changes should be tested before merging into `dev`, and `main` should contain stable, reviewed code.

---

# Future Improvements

Potential future enhancements include:

- Add GitHub Actions CI/CD.
- Add additional data-quality checks.
- Add more extraction integration tests.
- Improve test fixtures so tests do not depend on local raw-data files.
- Make extraction date ranges configurable through CLI arguments or environment variables.
- Add structured logging instead of relying entirely on console output.
- Add automated scheduling for periodic ICE stock updates.
- Add monitoring and alerting for source-report changes.
- Add analytical visualizations or a dashboard on top of the consolidated dataset.

---

# Summary

This project demonstrates a complete data-engineering workflow for heterogeneous external data sources.

The pipeline combines:

```text
External Data Extraction
        +
API Discovery
        +
File Processing
        +
Data Parsing
        +
Schema Normalization
        +
Duplicate Detection
        +
Data Validation
        +
Quality Reporting
        +
Data Consolidation
        +
Optional Database Loading
```

The result is a validated, analysis-ready time-series/panel dataset containing ICE Certified Arabica and Robusta coffee stock information in a consistent structure.

The primary final deliverable is:

```text
coffee_stock_consolidated.csv
```

with supporting data-quality evidence:

```text
data/quality/data_quality_report.json
```

and optional persistence through:

```text
MongoDB Atlas
```