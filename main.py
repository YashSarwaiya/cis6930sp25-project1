#!/usr/bin/env python3
import argparse
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests
import duckdb
from geopy.distance import geodesic

# Configure logging to STDERR then disable logging output so STDOUT contains only final results.
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
logging.disable(logging.CRITICAL)

# API endpoints for retrieving data
API_ENDPOINTS = {
    "arrests": "https://data.cityofgainesville.org/resource/aum6-79zv.json",
    "traffic_crashes": "https://data.cityofgainesville.org/resource/iecn-3sxx.json",
    "crime_responses": "https://data.cityofgainesville.org/resource/gvua-xt9q.json",
}

def parse_date(date_str: str) -> Optional[str]:
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",  
        "%Y-%m-%dT%H:%M:%S",     
        "%Y-%m-%d",              
        "%m/%d/%y %H:%M",        
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def fetch_data(url: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []

def fetch_all_data(url: str, params: Optional[Dict[str, Any]] = None, limit: int = 10000) -> List[Dict[str, Any]]:
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
            break 
        offset += limit
    return all_data

def get_date_str(year: int, month: int, day: int) -> str:
    """
    Format the provided date as YYYY-MM-DD.
    """
    return f"{year:04d}-{month:02d}-{day:02d}"

def is_valid_coordinate(lat: float, lon: float) -> bool:
    return -90 <= lat <= 90 and -180 <= lon <= 180

def clean_record(category: str, entry: Dict[str, Any], target_date: str) -> Optional[Dict[str, Any]]:
    try:
        if category == "arrests":
            raw_date = entry.get("arrest_date", "")
            parsed_date = parse_date(raw_date)
            if parsed_date != target_date:
                return None
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
                return None
            return {
                "case_number": entry["case_number"].strip(),
                "people": people,
                "latitude": lat,
                "longitude": lon
            }
        elif category == "crime_responses":
            # Use report_date for filtering.
            raw_date = entry.get("report_date", "")
            parsed_date = parse_date(raw_date)
            if parsed_date != target_date:
                return None
            lat = float(entry.get("latitude", "").strip())
            lon = float(entry.get("longitude", "").strip())
            if not is_valid_coordinate(lat, lon):
                return None
            return {
                "case_number": entry["id"].strip(),
                "people": 1,
                "latitude": lat,
                "longitude": lon
            }
        else:
            return None
    except (KeyError, ValueError, AttributeError):
        return None

def store_data_in_duckdb(incidents: List[Dict[str, Any]]) -> duckdb.DuckDBPyConnection:
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
    target_date = get_date_str(year, month, day)
    incidents: List[Dict[str, Any]] = []

    for category, url in API_ENDPOINTS.items():
        raw_data = fetch_all_data(url)
        for entry in raw_data:
            cleaned = clean_record(category, entry, target_date)
            if cleaned is not None:
                incidents.append(cleaned)

    if not incidents:
        return

    # Use only records with valid geolocation.
    incidents_with_loc = [inc for inc in incidents if inc["latitude"] is not None and inc["longitude"] is not None]
    if not incidents_with_loc:
        return

    max_incident = max(incidents_with_loc, key=lambda inc: inc["people"])

    nearby_incidents: List[Dict[str, Any]] = []
    for inc in incidents_with_loc:
        try:
            dist = geodesic(
                (max_incident["latitude"], max_incident["longitude"]),
                (inc["latitude"], inc["longitude"])
            ).km
            if dist < 1:
                nearby_incidents.append(inc)
        except Exception:
            continue

    # Sort first by descending people, then by descending case number.
    nearby_incidents.sort(key=lambda inc: (-inc["people"], -int(inc["case_number"])))
    store_data_in_duckdb(incidents_with_loc)

    for inc in nearby_incidents:
        print(f"{inc['people']}\t{inc['case_number']}", flush=True)

def parse_args() -> argparse.Namespace:
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
