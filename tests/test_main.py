import io
import sys
import main  # import our main module

def fake_fetch_all_data(url, params=None, limit=10000):
    # For "crime_responses", return sample data; for others, return empty lists.
    if "crimereports" in url:
        return [
            {
                "id": "225000033",
                "report_date": "12/12/24 00:00",
                "latitude": "29.66000",
                "longitude": "-82.32000"
            },
            {
                "id": "225000026",
                "report_date": "12/12/24 00:00",
                "latitude": "29.66000",
                "longitude": "-82.32000"
            },
            {
                "id": "225000024",
                "report_date": "12/12/24 00:00",
                "latitude": "29.66000",
                "longitude": "-82.32000"
            },
            {
                "id": "225000023",
                "report_date": "12/12/24 00:00",
                "latitude": "29.66000",
                "longitude": "-82.32000"
            },
            {
                "id": "225000013",
                "report_date": "12/12/24 00:00",
                "latitude": "29.66000",
                "longitude": "-82.32000"
            }
        ]
    else:
        return []

def test_process_data(monkeypatch):
    # Monkeypatch the fetch_all_data function in our main module.
    monkeypatch.setattr(main, "fetch_all_data", fake_fetch_all_data)
    
    # Capture STDOUT.
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    # Call process_data with target date 2024-12-12.
    main.process_data(2024, 12, 12)
    
    # Restore STDOUT.
    sys.stdout = sys.__stdout__
    output = captured_output.getvalue().strip()
    
    # Expected output order (each record printed as "1\t<case_number>").
    expected_lines = [
        "1\t225000033",
        "1\t225000026",
        "1\t225000024",
        "1\t225000023",
        "1\t225000013"
    ]
    output_lines = output.splitlines()
    assert output_lines == expected_lines
