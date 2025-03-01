'''
API_ENDPOINTS = {
    "arrests": "https://data.cityofgainesville.org/resource/aum6-79zv.json",
    "traffic_crashes": "https://data.cityofgainesville.org/resource/iecn-3sxx.json",
    "crime_responses": "https://data.cityofgainesville.org/resource/gvua-xt9q.json",
}
'''
#!/usr/bin/env python3
import argparse
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests
import duckdb
from geopy.distance import geodesic

# Configure logging for debugging and advanced error tracking
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# API endpoints for retrieving data
API_ENDPOINTS = {
    "arrests": "https://data.cityofgainesville.org/resource/aum6-79zv.json",
    "traffic_crashes": "https://data.cityofgainesville.org/resource/iecn-3sxx.json",
    "crime_responses": "https://data.cityofgainesville.org/resource/gvua-xt9q.json",
}

def parse_date(date_str: str) -> Optional[str]:
    """
    Attempt to parse a date string using multiple formats.
    Returns the date formatted as 'YYYY-MM-DD' if successful, otherwise None.
    """
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO with microseconds
        "%Y-%m-%dT%H:%M:%S",     # ISO without microseconds
        "%Y-%m-%d",              # Simple ISO
        "%m/%d/%y %H:%M",        # e.g., "12/12/24 21:00"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    logging.debug(f"Unable to parse date: {date_str}")
    return None

def fetch_data(url: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Retrieve JSON data from the API endpoint.
    """
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Fetched {len(data)} records from {url} with params {params}")
        return data
    except requests.RequestException as e:
        logging.error(f"Error fetching data from {url}: {e}")
        return []

def fetch_all_data(url: str, params: Optional[Dict[str, Any]] = None, limit: int = 10000) -> List[Dict[str, Any]]:
    """
    Fetch all records from the API endpoint using pagination.
    Uses '$limit' and '$offset' parameters to retrieve all available data.
    """
    all_data = []
    offset = 0
    while True:
        qparams = params.copy() if params else {}
        qparams["$limit"] = limit
        qparams["$offset"] = offset
        batch = fetch_data(url, qparams)
        if not batch:
            break
        all_data.extend(batch)
        if len(batch) < limit:
            break  # No more records available.
        offset += limit
    logging.info(f"Total records fetched from {url}: {len(all_data)}")
    return all_data

def get_date_str(year: int, month: int, day: int) -> str:
    """
    Format the provided date as YYYY-MM-DD.
    """
    return f"{year:04d}-{month:02d}-{day:02d}"

def is_valid_coordinate(lat: float, lon: float) -> bool:
    """
    Validate latitude and longitude ranges.
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180

def clean_record(category: str, entry: Dict[str, Any], target_date: str) -> Optional[Dict[str, Any]]:
    """
    Clean and convert an entry record from a given category if it matches the target date.
    Returns a dictionary with keys: case_number, people, latitude, longitude.
    Returns None if the record is invalid or does not match the target date.
    """
    try:
        if category == "arrests":
            raw_date = entry.get("arrest_date", "")
            parsed_date = parse_date(raw_date)
            if parsed_date != target_date:
                return None
            # Arrest records assume 1 person and typically lack geolocation.
            return {
                "case_number": entry["case_number"].strip(),
                "people": 1,
                "latitude": None,
                "longitude": None
            }

        elif category == "traffic_crashes":
            raw_date = entry.get("accident_date", "")
            parsed_date = parse_date(raw_date)
            if parsed_date != target_date:
                return None
            people_str = entry.get("totalpeopleinvolved", "0").strip()
            people = int(people_str) if people_str.isdigit() else 0
            lat = float(entry.get("latitude", "").strip())
            lon = float(entry.get("longitude", "").strip())
            if not is_valid_coordinate(lat, lon):
                logging.debug(f"Invalid coordinate in traffic crash: {lat}, {lon}")
                return None
            return {
                "case_number": entry["case_number"].strip(),
                "people": people,
                "latitude": lat,
                "longitude": lon
            }

        elif category == "crime_responses":
            # Use report_date for filtering, not offense_date.
            raw_date = entry.get("report_date", "")
            parsed_date = parse_date(raw_date)
            if parsed_date != target_date:
                return None
            lat = float(entry.get("latitude", "").strip())
            lon = float(entry.get("longitude", "").strip())
            if not is_valid_coordinate(lat, lon):
                logging.debug(f"Invalid coordinate in crime response: {lat}, {lon}")
                return None
            return {
                "case_number": entry["id"].strip(),
                "people": 1,
                "latitude": lat,
                "longitude": lon
            }
        else:
            return None
    except (KeyError, ValueError, AttributeError) as e:
        logging.debug(f"Error cleaning record for category {category}: {e}")
        return None

def store_data_in_duckdb(incidents: List[Dict[str, Any]]) -> duckdb.DuckDBPyConnection:
    """
    Store valid incident records in an in-memory DuckDB database.
    Only incidents with valid location data are inserted.
    """
    conn = duckdb.connect(database=":memory:")
    conn.execute("""
        CREATE TABLE incidents (
            case_number TEXT,
            people INTEGER,
            latitude DOUBLE,
            longitude DOUBLE
        )
    """)
    for inc in incidents:
        if inc["latitude"] is not None and inc["longitude"] is not None:
            conn.execute(
                "INSERT INTO incidents VALUES (?, ?, ?, ?)",
                (inc["case_number"], inc["people"], inc["latitude"], inc["longitude"])
            )
    return conn

def process_data(year: int, month: int, day: int) -> None:
    """
    Main processing routine:
      - Fetches and cleans data from arrests, traffic crashes, and crime responses using pagination.
      - Filters by the provided target date.
      - Stores incidents with valid coordinates in DuckDB.
      - Identifies the incident (with valid coordinates) involving the most people.
      - Filters all such incidents to those within strictly less than 1 km of that event.
      - Outputs sorted results: number of people then case_number, separated by a tab.
    """
    target_date = get_date_str(year, month, day)
    incidents: List[Dict[str, Any]] = []

    # Process each data source using pagination and the cleaning function.
    for category, url in API_ENDPOINTS.items():
        raw_data = fetch_all_data(url)
        for entry in raw_data:
            cleaned = clean_record(category, entry, target_date)
            if cleaned is not None:
                incidents.append(cleaned)

    if not incidents:
        logging.info("No incidents found for the specified date.")
        return

    # Use only records with valid geolocation for distance-based filtering.
    incidents_with_loc = [inc for inc in incidents if inc["latitude"] is not None and inc["longitude"] is not None]
    if not incidents_with_loc:
        logging.info("No incidents with valid location data available for distance calculation.")
        return

    # Identify the incident with the maximum 'people' count among those with geolocation.
    max_incident = max(incidents_with_loc, key=lambda inc: inc["people"])
    logging.info(f"Incident with maximum people: {max_incident}")

    # Select incidents within strictly less than 1 km of the max_incident.
    nearby_incidents: List[Dict[str, Any]] = []
    for inc in incidents_with_loc:
        try:
            dist = geodesic(
                (max_incident["latitude"], max_incident["longitude"]),
                (inc["latitude"], inc["longitude"])
            ).km
            if dist < 1:
                nearby_incidents.append(inc)
        except Exception as e:
            logging.debug(f"Error calculating distance: {e}")
            continue

    # Sort the nearby incidents by descending people count, then by descending numerical case number.
    nearby_incidents.sort(key=lambda inc: (-inc["people"], -int(inc["case_number"])))
    
    # Optionally store data in DuckDB for debugging; not used further.
    store_data_in_duckdb(incidents_with_loc)

    # Output the results exactly as required: number of people, then a tab, then the case number.
    for inc in nearby_incidents:
        print(f"{inc['people']}\t{inc['case_number']}")

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Extract and analyze Gainesville public safety data."
    )
    parser.add_argument("--year", type=int, required=True, help="Year of incidents")
    parser.add_argument("--month", type=int, required=True, help="Month of incidents")
    parser.add_argument("--day", type=int, required=True, help="Day of incidents")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    process_data(args.year, args.month, args.day)

if __name__ == "__main__":
    main()
