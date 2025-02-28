import argparse
import requests
import duckdb
from geopy.distance import geodesic
from datetime import datetime

# Define API Endpoints
API_ENDPOINTS = {
    "arrests": "https://data.cityofgainesville.org/resource/aum6-79zv.json",
    "traffic_crashes": "https://data.cityofgainesville.org/resource/iecn-3sxx.json",
    "crime_responses": "https://data.cityofgainesville.org/resource/gvua-xt9q.json",
}

# Fetch Data from API
def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return []

# Parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Extract and analyze public safety data.")
    parser.add_argument("--year", type=int, required=True, help="Year of incidents")
    parser.add_argument("--month", type=int, required=True, help="Month of incidents")
    parser.add_argument("--day", type=int, required=True, help="Day of incidents")
    return parser.parse_args()

# Convert API Date String to Python Date
def parse_date(date_str):
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    except ValueError:
        return None

# Extract Incident Data
def extract_incidents(year, month, day):
    target_date = datetime(year, month, day).date()
    incidents = []

    # Process each data source
    for category, url in API_ENDPOINTS.items():
        data = fetch_data(url)

        for entry in data:
            try:
                # Extract latitude and longitude
                latitude = float(entry["latitude"])
                longitude = float(entry["longitude"])
                
                # Extract people count based on category
                if category == "arrests":
                    event_date = parse_date(entry.get("arrest_date"))
                    people_count = 1  # Assuming each arrest record involves one person
                    case_number = entry.get("case_number")
                
                elif category == "traffic_crashes":
                    event_date = parse_date(entry.get("accident_date"))
                    people_count = int(entry.get("totalpeopleinvolved", 0))
                    case_number = entry.get("case_number")
                
                elif category == "crime_responses":
                    event_date = parse_date(entry.get("offense_date"))
                    people_count = 1  # Assuming each crime response involves at least one person
                    case_number = entry.get("id")  # Crime responses use "id" instead of "case_number"

                # Check if the event matches the given date
                if event_date == target_date and case_number:
                    incidents.append({
                        "case_number": case_number,
                        "people": people_count,
                        "latitude": latitude,
                        "longitude": longitude,
                    })
            except (ValueError, KeyError):
                continue  # Skip invalid entries

    return incidents

# Store data in DuckDB
def store_data(incidents):
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE incidents (case_number TEXT, people INTEGER, latitude FLOAT, longitude FLOAT)")
    
    for incident in incidents:
        con.execute(
            "INSERT INTO incidents VALUES (?, ?, ?, ?)",
            [incident["case_number"], incident["people"], incident["latitude"], incident["longitude"]],
        )
    return con

# Calculate distance using geopy
def distance(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).km

# Process data
def process_data(year, month, day):
    incidents = extract_incidents(year, month, day)
    
    if not incidents:
        return  # No data, so print nothing

    # Store in DuckDB
    db_conn = store_data(incidents)

    # Identify the incident with the most people
    max_incident = max(incidents, key=lambda x: x["people"])

    # Find all incidents within 1 km
    nearby_incidents = [
        incident
        for incident in incidents
        if distance(
            max_incident["latitude"], max_incident["longitude"],
            incident["latitude"], incident["longitude"]
        ) <= 1
    ]

    # Sort and print results
    nearby_incidents.sort(key=lambda x: (-x["people"], x["case_number"]))
    for incident in nearby_incidents:
        print(f"{incident['people']}\t{incident['case_number']}")

# Run the script
if __name__ == "__main__":
    args = parse_args()
    process_data(args.year, args.month, args.day)
