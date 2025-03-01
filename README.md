# CIS6930SP25 -- Project 1

## Name:

Yash Sarwaiya

## Assignment Description

This project extracts and analyzes public safety data from the City of Gainesville’s open data API. The system fetches data on arrests, traffic crashes, and crime responses, processes them to filter incidents by a given date, and identifies nearby incidents within a 1 km range of the most severe event. The program uses DuckDB for storage and geopy for distance calculations.

## How to Install

Ensure you have Python Python 3.9.21 installed. Then, install the dependencies using Pipenv:

```sh
pipenv install -e .
```

## How to Run

Execute the script using the following command:

```sh
pipenv run python main.py --year 2024 --month 12 --day 12
```

## Example

If you run the following command:

```sh
pipenv run python main.py --year 2024 --month 12 --day 12
```

The expected output (if data is available) will be:

```
5       224018560
4       224018592
3       224018581
3       224018555
2       224018578
2       224018577
2       224018570
2       224018566
2       224018565
2       224018557
2       224018556
2       224018552
1       224018583
```

## Features and Functions

### `main.py`

- **`fetch_all_data(url, params=None, limit=10000)`**: Fetches all records from an API using pagination.
- **`parse_date(date_str)`**: Parses and normalizes different date formats.
- **`clean_record(category, entry, target_date)`**: Cleans raw data entries and extracts relevant fields.
- **`process_data(year, month, day)`**: The main function that fetches, cleans, and analyzes data to find incidents.
- **`store_data_in_duckdb(incidents)`**: Stores incident records in an in-memory DuckDB database.

## Bugs and Assumptions

### Bugs:

- API responses may change in structure, which could break parsing logic.
- Some records may have missing or incorrect geolocation data.
- Network failures might prevent API calls from fetching data.

### Assumptions:

- All timestamps are in the correct format or convertible.
- Case numbers are unique identifiers.
- A distance threshold of strictly less than 1 km is considered for nearby incidents.
- The dataset is assumed to have consistent key names.

## INSTALLATION AND USAGE SUMMARY

1. Clone the Repository
2. Run tests with `pipenv run pytest -v`.
3. Run the application with `pipenv run python main.py --year YYYY --month MM --day DD`.
4. Run tests with `pipenv run pytest -v`.
