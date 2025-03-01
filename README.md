# CIS6930SP25 -- PROJECT 1  

**Name:** Yash Sarwaiya  

## **ASSIGNMENT DESCRIPTION**  
This project extracts and analyzes public safety data from the City of Gainesville's APIs, including Arrests, Traffic Crashes, and Crime Responses. The goal is to help the **Men in Black (MIB)** identify potential **alien encounters** by analyzing incidents that occurred on a specific date.  

The program:  
1. Retrieves incident data dynamically from Gainesville public safety APIs.  
2. Identifies the **incident involving the most people**.  
3. Filters incidents within **1 kilometer** of this event.  
4. Sorts and displays the results by the number of people involved, then by case number.  

The data is stored in **DuckDB (in-memory)** and queried efficiently to find and analyze incidents.  

---

## **HOW TO INSTALL**  
Ensure you have **Python 3.9+** and **pipenv** installed. Then, run:  

```sh
pipenv install -e .
pipenv install duckdb requests geopy
pipenv run python -c "import duckdb; duckdb.sql('INSTALL SPATIAL; LOAD SPATIAL'); print('Spatial functions installed!')"
```

---

## **HOW TO RUN**  
To run the program, use:  

```sh
pipenv run python main.py --year <YYYY> --month <MM> --day <DD>
```

For example, to retrieve incidents on **February 25, 2025**:  

```sh
pipenv run python main.py --year 2025 --month 2 --day 25
```

---

## **EXAMPLE OUTPUT**  
```
25    223008681
17    225002747
1     223002794
```

This output represents:  
- **25 people involved** in case `223008681`.  
- **17 people involved** in case `225002747`.  
- **1 person involved** in case `223002794`.  

Each row contains **people involved** and the **case number**, separated by a tab (`	`).  

---

## **FEATURES AND FUNCTIONS**  

### **`main.py`**  
- **`fetch_data(url)`** → Fetches JSON data from Gainesville's public safety APIs.  
- **`parse_args()`** → Parses command-line arguments (`--year`, `--month`, `--day`).  
- **`distance(lat1, lon1, lat2, lon2)`** → Uses `geopy` to calculate the geodesic distance between two coordinates.  
- **`store_data(con, incidents)`** → Stores data in an **in-memory DuckDB database**.  
- **`process_data(year, month, day)`** →  
  - Retrieves and filters incidents by date.  
  - Identifies the **incident involving the most people**.  
  - Filters **all incidents within 1 km** of this event.  
  - Sorts and **prints the results**.  

---

## **BUGS AND ASSUMPTIONS**  

### **Known Bugs:**  
- **Missing Latitude/Longitude in Arrests:** Since Arrests data does not include **location coordinates**, they **cannot** be considered when filtering for incidents **within 1 km**.  
- **APIs May Fail:** If an API request fails, the program will skip that dataset but continue processing the remaining data.  

### **Assumptions:**  
- **Arrests Involve 1 Person:** Since the dataset does not specify the number of people per arrest, each arrest is counted as **1 person involved**.  
- **Crime Responses Involve 1 Person:** Crime response data lacks a **people_involved** field, so we assume **1 person per crime**.  
- **Dynamic Data Fetching:** The program **does not store data persistently**; it retrieves the latest data **each time it runs**.  
- **1 km Filtering:** Uses the **geopy library** to calculate distances in **kilometers**.  
- **Sorting:**  
  - **Primary Sort:** **Descending** by number of people involved.  
  - **Secondary Sort:** **Ascending** by case number (lexicographic order).  

---

## **COLLABORATORS**  
This project was completed **individually**. Any external references are listed in **COLLABORATORS.md**.  

---

## **HOW TO TEST**  
Run the tests using:  
```sh
pipenv run python -m pytest -v
```

Example test (`tests/test_geoquery.py`):  
```python
import pytest
from main import distance

def test_distance():
    assert round(distance(29.6516, -82.3248, 29.6520, -82.3245), 2) < 1
```

---

## **SUBMISSION**  
Tag the latest commit before submission:  
```sh
git tag v1.0
git push origin v1.0
```
Then submit via **Gradescope**.  

---

## **FINAL NOTES**  
This project effectively retrieves and processes Gainesville public safety data using **DuckDB**, **geopy**, and **Python**, ensuring efficient querying and analysis. 🚀  
