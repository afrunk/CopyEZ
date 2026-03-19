import urllib.request
import json

try:
    url = "http://127.0.0.1:5000/api/logs"
    with urllib.request.urlopen(url, timeout=5) as response:
        data = json.loads(response.read().decode())
        events = data.get("events", data) if isinstance(data, dict) else data
        if not isinstance(events, list):
            events = []
        print(f"Total records: {len(events)}")
        print("First 3 records:")
        for r in events[:3]:
            print(f"  - {r.get('at', 'N/A')} | {r.get('ip_address', 'N/A')} | {r.get('action_type', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")
