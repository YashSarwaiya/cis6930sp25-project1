import sys
import os
import io
import pytest
import main

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def fake_fetch_all_data(url, params=None, limit=10000):
    if "gvua-xt9q" in url:
        return [
            {"id": "225000033", "report_date": "2024-12-12T00:00:00", "latitude": "29.65100", "longitude": "-82.32300"},
            {"id": "225000026", "report_date": "2024-12-12T00:00:00", "latitude": "29.65200", "longitude": "-82.32200"},
            {"id": "225000024", "report_date": "2024-12-12T00:00:00", "latitude": "29.65300", "longitude": "-82.32100"},
            {"id": "225000023", "report_date": "2024-12-12T00:00:00", "latitude": "29.65400", "longitude": "-82.32000"},
            {"id": "225000013", "report_date": "2024-12-12T00:00:00", "latitude": "29.65500", "longitude": "-82.31900"},
        ]
    elif "iecn-3sxx" in url:
        return [
            {"case_number": "225000101", "accident_date": "2024-12-12T00:00:00", "totalpeopleinvolved": "5",
             "latitude": "29.65000", "longitude": "-82.32500"},
            {"case_number": "225000102", "accident_date": "2024-12-12T00:00:00", "totalpeopleinvolved": "3",
             "latitude": "29.65050", "longitude": "-82.32450"}
        ]
    elif "aum6-79zv" in url:
        return [
            {"case_number": "225000201", "arrest_date": "2024-12-12T00:00:00"},
            {"case_number": "225000202", "arrest_date": "2024-12-12T00:00:00"}
        ]
    return []

def fake_fetch_far_events(url, params=None, limit=10000):
    if "gvua-xt9q" in url:
        return [
            {"id": "225000033", "report_date": "2024-12-12T00:00:00", "latitude": "30.00000", "longitude": "-83.00000"},
            {"id": "225000034", "report_date": "2024-12-12T00:00:00", "latitude": "29.00000", "longitude": "-82.00000"}
        ]
    return []

def fake_fetch_missing_geo(url, params=None, limit=10000):
    if "gvua-xt9q" in url:
        return [{"id": "225000033", "report_date": "2024-12-12T00:00:00"}]
    return []

def fake_fetch_invalid_date(url, params=None, limit=10000):
    if "gvua-xt9q" in url:
        return [{"id": "225000033", "report_date": "12-12-2024", "latitude": "29.66000", "longitude": "-82.32000"}]
    return []

def fake_fetch_high_people(url, params=None, limit=10000):
    if "iecn-3sxx" in url:
        return [
            {"case_number": "225000401", "accident_date": "2024-12-12T00:00:00", "totalpeopleinvolved": "10",
             "latitude": "29.66000", "longitude": "-82.32000"},
            {"case_number": "225000402", "accident_date": "2024-12-12T00:00:00", "totalpeopleinvolved": "8",
             "latitude": "29.66100", "longitude": "-82.32100"}
        ]
    return []


def run_and_capture(year, month, day):
    captured_output = io.StringIO()
    sys.stdout = captured_output
    main.process_data(year, month, day)
    sys.stdout = sys.__stdout__
    return captured_output.getvalue().strip().splitlines()


def test_process_data(monkeypatch):
    monkeypatch.setattr(main, "fetch_all_data", fake_fetch_all_data)
    output_lines = run_and_capture(2024, 12, 12)
    
    expected_lines = [
        "5\t225000101",
        "3\t225000102",
        "1\t225000033",
        "1\t225000026",
        "1\t225000024",
        "1\t225000023",
        "1\t225000013"
    ]
    assert output_lines == expected_lines

def test_far_away_events(monkeypatch):
    monkeypatch.setattr(main, "fetch_all_data", fake_fetch_far_events)
    output_lines = run_and_capture(2024, 12, 12)
    expected = ["1\t225000033"]
    assert output_lines == expected

def test_missing_lat_lon(monkeypatch):
    monkeypatch.setattr(main, "fetch_all_data", fake_fetch_missing_geo)
    output_lines = run_and_capture(2024, 12, 12)
    # Expecting no valid output since no record has geolocation
    assert output_lines == []

def test_invalid_date_format():
    assert main.parse_date("12-12-2024") is None

def test_most_people_involved(monkeypatch):
    monkeypatch.setattr(main, "fetch_all_data", fake_fetch_high_people)
    output_lines = run_and_capture(2024, 12, 12)
    expected = [
        "10\t225000401",
        "8\t225000402"
    ]
    assert output_lines == expected

def test_invalid_lat_lon():
    assert not main.is_valid_coordinate(91, 0)
    assert not main.is_valid_coordinate(-91, 0)
    assert not main.is_valid_coordinate(0, 181)
    assert not main.is_valid_coordinate(0, -181)
    assert main.is_valid_coordinate(29.65, -82.32)
