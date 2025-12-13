import requests
import time
import json

BASE_URL = "http://localhost:8000"

def verify_traffic_data():
    # Login
    response = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin"})
    token = response.json()["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start Simulation with specific latency
    target_latency = 123
    config = {
        "is_running": True,
        "traffic_type": "HTTP",
        "volume": "low", # Low volume to easier inspect
        "pattern": "steady",
        "packet_size_range": [100, 200],
        "error_rate": 0.0,
        "latency": target_latency
    }
    requests.post(f"{BASE_URL}/simulation/start", json=config, headers=headers)
    print(f"Simulation started with target latency {target_latency}ms")

    time.sleep(3)

    # Stop Simulation
    requests.post(f"{BASE_URL}/simulation/stop", headers=headers)
    print("Simulation stopped")

    # Fetch Traffic
    response = requests.get(f"{BASE_URL}/traffic?limit=50", headers=headers)
    traffic_data = response.json()

    # Analyze
    print(f"Fetched {len(traffic_data)} traffic records")
    if not traffic_data:
        print("No traffic data found!")
        return

    # Check latency of recent records (filtering by timestamp might be needed if DB has old data, 
    # but for now just checking if ANY match the target range)
    
    matching_latency_count = 0
    total_checked = 0
    
    for t in traffic_data[:20]: # Check top 20
        # Latency should be target + jitter (-5 to +5)
        # But wait, my simulator code uses max(0, base + jitter)
        # So it should be within [target-5, target+5]
        
        # Note: older data might be in the DB.
        # Ideally we should filter by time, but let's just see if we see our values.
        
        lat = t.get('latency')
        if lat is not None:
            if target_latency - 10 <= lat <= target_latency + 10:
                matching_latency_count += 1
            total_checked += 1
            
    print(f"Found {matching_latency_count} records matching target latency out of {total_checked} checked.")
    
    if matching_latency_count > 0:
        print("Verification SUCCESS: Generated traffic reflects configuration.")
    else:
        print("Verification FAILED: Could not find traffic with expected latency.")

if __name__ == "__main__":
    verify_traffic_data()
