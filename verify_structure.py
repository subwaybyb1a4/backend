import requests
import json
import sys

def verify():
    url = "http://localhost:8000/api/v1/routes"
    params = {"departure": "서울역", "arrival": "강남역"}
    try:
        print(f"Calling {url} with {params}...")
        resp = requests.get(url, params=params)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("Response Keys:", list(data.keys()))
            
            print("\n=== Min Time Route Segments ===")
            min_time = data.get("min_time")
            if min_time:
                for seg in min_time.get('segments', []):
                    print(f"Type: {seg['type']}, Label: {seg['label']}")
                    if seg['type'] == 'subway':
                        print(f"  > Start: {seg.get('start_station_name')}")
                        print(f"  > End:   {seg.get('end_station_name')}")
            
            print("\nValidation Successful!")
        else:
            print("Error Response:", resp.text)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    verify()
