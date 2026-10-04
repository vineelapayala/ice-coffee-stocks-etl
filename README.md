# ICE Certified Coffee Stocks ETL

## Overview

This project implements an ETL pipeline to retrieve, clean, validate, transform, and consolidate approximately one year of ICE Certified Coffee Stock data for Arabica and Robusta coffee into a single analysis-ready dataset.

The pipeline handles the differences between the two ICE reports, normalizes them into a common schema, performs data-quality validation, identifies duplicate source files, and generates a consolidated CSV dataset together with a data-quality report.

## Objectives

- Retrieve historical ICE Certified Coffee Stock data.
- Process both Arabica and Robusta coffee stock reports.
- Handle the different extraction mechanisms used by the two ICE reports.
- Parse and normalize the source data into a common structure.
- Validate the extracted data.
- Detect duplicate source files.
- Generate an analysis-ready consolidated dataset.
- Generate a data-quality report.
- Provide automated tests for the parsing and validation logic.

## Data Sources

### Arabica

**ICE Report 42 - Stock Figures**

Source: https://www.ice.com/report/42

Arabica historical reports are available as XLS files.

### Robusta

**ICE Report 173 - Stock Figures**

Source: https://www.ice.com/report/173

Robusta reports are dynamically generated through the ICE Market Data API and returned as CSV report URLs.

## Pipeline Architecture

ICE Data Sources
       |
       +-------------------+
       |                   |
   Arabica              Robusta
       |                   |
       v                   v
XLS Extraction       API Discovery
       |                   |
       |              CSV Extraction
       |                   |
       +---------+---------+
                 |
                 v
              Parsing
                 |
                 v
        Schema Normalization
                 |
                 v
          Deduplication
                 |
                 v
             Validation
                 |
                 v
        Consolidated Dataset
          /             \
         v               v
      CSV Output     Quality Report


## Project Structure

ice-coffee-stocks-etl/
|
+-- data/
|   |
|   +-- processed/
|   |
|   +-- quality/
|
+-- src/
|   |
|   +-- extractor.py
|   +-- historical_extractor.py
|   +-- parser.py
|   +-- robusta_extractor.py
|   +-- robusta_parser.py
|   +-- robusta_discovery.py
|   +-- pipeline.py
|   +-- validator.py
|   +-- quality_report.py
|   +-- file_utils.py
|
+-- tests/
|   |
|   +-- test_parser.py
|   +-- test_robusta_parser.py
|   +-- test_validator.py
|
+-- main.py
+-- requirements.txt
+-- .gitignore
+-- README.md


## Technology Stack

* Python
* Pandas
* Requests
* Nodriver
* Pytest
* Excel/XLS processing
* CSV processing
* REST API

## Installation

### 1. Create a virtual environment

```powershell
python -m venv .venv
```

### 2. Activate the virtual environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

## Running the Pipeline

Run the complete ETL pipeline from the project root:

```powershell
python main.py
```

The pipeline:

1. Reads the available Arabica source files.
2. Reads the available Robusta source files.
3. Removes identical duplicate Robusta files.
4. Parses both datasets.
5. Normalizes both datasets into a common schema.
6. Validates the consolidated dataset.
7. Generates the data-quality report.
8. Writes the consolidated CSV.

## Running Tests

Run the test suite using the project's Python interpreter:

```powershell
python -m pytest
```

The current test suite contains 38 tests.

## Output

The pipeline generates:

data/
|
+-- processed/
|   |
|   +-- coffee_stock_consolidated.csv
|
+-- quality/
    |
    +-- data_quality_report.json


The processed CSV is generated output and is excluded from Git.

The quality report is retained as project evidence of the validation results.

## Common Data Schema

The consolidated dataset uses the following fields:

| Column           | Description                                     |
| ---------------- | ----------------------------------------------- |
| `report_date`    | Date associated with the ICE report             |
| `cut_off_date`   | Stock cut-off date where provided by the source |
| `coffee_type`    | Arabica or Robusta                              |
| `origin`         | Coffee origin where available                   |
| `location_code`  | Warehouse or port/location code                 |
| `stock_category` | Type of certified stock                         |
| `quantity`       | Stock quantity                                  |
| `unit`           | Unit of measurement                             |

## Data Handling

### Arabica

Arabica source files are XLS reports.

The parser extracts the `TOTAL BAGS CERTIFIED` section and converts the warehouse-level data into a normalized structure.

The source `Total` column represents an aggregate and is not treated as a physical warehouse location.

The Arabica unit is bags.

### Robusta

Robusta reports are CSV files generated dynamically by ICE.

The pipeline first discovers the available report URLs and then downloads the corresponding CSV files.

The Robusta source contains different stock categories:

* Valid certificate
* Non-tenderable
* Suspended

These categories are transformed into rows in the normalized dataset.

The Robusta unit is lots.

The Robusta source does not provide coffee origin, so the `origin` field is null for Robusta records.

## Robusta API Discovery

The Robusta report uses a dynamically generated API endpoint.

The API request uses:

/marketdata/api/reports/173/results


The request uses the Stock Figures report type together with a date range.

The API response contains dynamically generated CSV report URLs.

Because the URLs contain generated timestamp values, the pipeline does not attempt to construct the final report URLs manually.

Instead, the discovery process identifies the available report URLs and stores the discovered metadata before extraction.

The discovery process uses Nodriver to connect to an existing browser session.

Manual CAPTCHA completion was required during the discovery process.

The automation does not attempt to bypass or solve the CAPTCHA.

## Arabica Extraction

Arabica historical reports follow a deterministic XLS URL pattern.

The extractor:

1. Builds the report URL for each requested date.
2. Sends an HTTP request.
3. Handles HTTP 404 responses for unavailable dates.
4. Handles HTTP 429 responses using retry and backoff logic.
5. Honors the `Retry-After` response header when available.
6. Validates the downloaded file.
7. Skips files that already exist locally.
8. Saves valid XLS files to the raw-data directory.

The historical extractor loops through the requested date range and reuses a requests Session.

## Robusta Extraction

The Robusta extractor:

1. Reads the discovered report metadata.
2. Downloads each CSV report.
3. Skips files that already exist.
4. Validates the response.
5. Handles HTTP 429 responses.
6. Uses retry and exponential backoff logic.
7. Honors `Retry-After` when available.
8. Waits between requests to reduce request frequency.
9. Saves the CSV reports locally.

## Parsing

### Arabica Parser

The Arabica parser:

1. Reads the XLS report.
2. Extracts the report date.
3. Locates the `TOTAL BAGS CERTIFIED` section.
4. Identifies the warehouse columns.
5. Extracts the source total.
6. Excludes the aggregate `Total` column from warehouse-level records.
7. Converts the warehouse columns into rows.
8. Removes invalid or zero quantities.
9. Validates the parsed total against the source total.
10. Adds the common schema fields.

### Robusta Parser

The Robusta parser:

1. Reads the CSV report.
2. Validates the expected source columns.
3. Validates the commodity code.
4. Separates the `GrandTotal` row from location-level rows.
5. Extracts the report date from the filename.
6. Extracts the cut-off date from the source.
7. Converts stock quantities to numeric values.
8. Converts the wide source structure into a long structure.
9. Maps source stock columns to normalized stock categories.
10. Validates the parsed totals against the source `GrandTotal`.
11. Adds the common schema fields.

The parser supports different source date formats by using mixed date parsing.

## Schema Normalization

Both coffee types are transformed into the same eight-column schema:

* `report_date`
* `cut_off_date`
* `coffee_type`
* `origin`
* `location_code`
* `stock_category`
* `quantity`
* `unit`

This allows Arabica and Robusta data to be analyzed together while preserving source-specific dimensions where available.

## Duplicate Handling

Robusta report URLs can contain generated timestamp values.

As a result, different files can represent identical report content.

The pipeline calculates SHA-256 hashes for Robusta files and identifies identical duplicate files before parsing.

Only one file from each identical duplicate group is selected for processing.

This prevents the same report content from being loaded multiple times into the final dataset.

## Data Quality Validation

The pipeline validates:

* Schema
* Required fields
* Coffee type
* Units
* Quantities
* Dates
* Duplicate rows
* Source totals
* Stock categories

The final dataset must contain valid positive quantities and conform to the expected common schema.

The validation logic also checks that:

* Required fields are populated.
* Coffee types are valid.
* Units match the coffee type.
* Quantities are numeric.
* Quantities are not negative.
* Quantities are not null.
* Duplicate rows are not present.

## Data Quality Report

The pipeline generates a JSON data-quality report containing:

* Source file counts
* Dataset row counts
* Date range
* Coffee-type distribution
* Stock-category distribution
* Unit distribution
* Location distribution
* Null counts
* Duplicate counts
* Quantity checks
* Validation status

## Current Results

The current extraction produced:

* 252 Arabica source files
* 254 Robusta source files
* 1 identical Robusta duplicate group
* 253 Robusta files selected for parsing
* 11,579 consolidated rows
* 10,020 Arabica rows
* 1,559 Robusta rows
* 0 duplicate rows in the final dataset
* 0 negative quantities
* 0 null quantities

The available consolidated dataset covers:


2025-10-03 to 2026-10-02


## Testing

The project contains automated tests for:

* Arabica parsing
* Robusta parsing
* Schema validation
* Required-field validation
* Coffee-type validation
* Unit validation
* Quantity validation
* Date validation
* Duplicate validation

The current test suite contains 38 tests.

Run the tests with:

```powershell
python -m pytest
```

## Important Notes

Raw ICE source files are not committed to the repository.

The following directories are intentionally ignored by Git:


data/raw/
data/processed/
.venv/
.pytest_cache/


The raw data can therefore be regenerated using the extraction scripts.

## MongoDB Integration

The consolidated coffee stock dataset is loaded into MongoDB Atlas after the ETL pipeline completes.

### Configuration

MongoDB connection details are stored in a local `.env` file:

```text
MONGODB_URI=<your MongoDB connection string>
MONGODB_DATABASE=ice_coffee_stocks
MONGODB_COLLECTION=coffee_stock
```

The `.env` file is excluded from Git and must never be committed.

### Collection

The data is stored in:

```text
Database:   ice_coffee_stocks
Collection: coffee_stock
```

### Idempotent Loading

The MongoDB loader uses `upsert=True` with the following natural key:

```text
report_date
cut_off_date
coffee_type
origin
location_code
stock_category
unit
```

A unique compound index is created on these fields to prevent duplicate records.

This makes the MongoDB load idempotent. Running the pipeline multiple times with the same source data does not create duplicate documents.

For example, a subsequent pipeline run processes the existing 11,579 records without inserting duplicates:

```text
MongoDB load complete: 11,579 records processed
Inserted: 0
Modified: 0
```

### MongoDB Pipeline Flow

```text
ICE Reports
    ↓
Extraction
    ↓
Parsing
    ↓
Normalization
    ↓
Validation
    ↓
Consolidated CSV
    ↓
MongoDB Atlas
```

## Environment Setup

Create a `.env` file in the project root before running the MongoDB-enabled pipeline:

```text
MONGODB_URI=<your MongoDB connection string>
MONGODB_DATABASE=ice_coffee_stocks
MONGODB_COLLECTION=coffee_stock
```

Then run:

```powershell
python main.py
```

The pipeline generates the consolidated CSV and loads the records into MongoDB.

## Future Improvements

Potential future enhancements include:

* Loading the consolidated dataset into MongoDB.
* Adding additional automated data-quality checks.
* Adding CI/CD using GitHub Actions.
* Improving test fixtures so tests do not depend on local raw-data files.
* Adding configurable extraction date ranges through environment variables or CLI arguments.
