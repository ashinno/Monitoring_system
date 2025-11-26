import requests
import time
import statistics

BASE_URL = "http://localhost:8000"

def login():
    response = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin"})
    response.raise_for_status()
    return response.json()["accessToken"]

def start_simulation(token, volume="high", latency=0):
    headers = {"Authorization": f"Bearer {token}"}
    config = {
        "is_running": True,
        "traffic_type": "HTTP",
        "volume": volume,
        "pattern": "bursty",
        "packet_size_range": [500, 1500],
        "error_rate": 0.01,
        "latency": latency
    }
    response = requests.post(f"{BASE_URL}/simulation/start", json=config, headers=headers)
    response.raise_for_status()
    print(f"Simulation started with volume={volume}, latency={latency}ms")

def stop_simulation(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/simulation/stop", headers=headers)
    response.raise_for_status()
    print("Simulation stopped")

def measure_api_latency(token, endpoint, iterations=20):
    headers = {"Authorization": f"Bearer {token}"}
    latencies = []
    
    for _ in range(iterations):
        start_time = time.time()
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        if response.status_code == 200:
            latencies.append((time.time() - start_time) * 1000) # ms
        else:
            print(f"Error calling {endpoint}: {response.status_code}")
        time.sleep(0.1) # small delay
        
    return latencies

def run_performance_test():
    print("Starting Performance Test...")
    try:
        token = login()
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # Baseline (no simulation)
    print("\n--- Measuring Baseline Performance (No Simulation) ---")
    baseline_logs = measure_api_latency(token, "/logs")
    baseline_traffic = measure_api_latency(token, "/traffic")
    
    print(f"Baseline /logs: Avg={statistics.mean(baseline_logs):.2f}ms, Max={max(baseline_logs):.2f}ms")
    print(f"Baseline /traffic: Avg={statistics.mean(baseline_traffic):.2f}ms, Max={max(baseline_traffic):.2f}ms")

    # High Volume Simulation
    print("\n--- Starting High Volume Simulation ---")
    start_simulation(token, volume="high", latency=50)
    
    # Allow simulation to warm up
    time.sleep(2)
    
    print("Measuring Performance Under Load...")
    load_logs = measure_api_latency(token, "/logs")
    load_traffic = measure_api_latency(token, "/traffic")
    
    stop_simulation(token)
    
    print(f"Under Load /logs: Avg={statistics.mean(load_logs):.2f}ms, Max={max(load_logs):.2f}ms")
    print(f"Under Load /traffic: Avg={statistics.mean(load_traffic):.2f}ms, Max={max(load_traffic):.2f}ms")
    
    # Calculate Impact
    impact_logs = (statistics.mean(load_logs) - statistics.mean(baseline_logs)) / statistics.mean(baseline_logs) * 100
    impact_traffic = (statistics.mean(load_traffic) - statistics.mean(baseline_traffic)) / statistics.mean(baseline_traffic) * 100
    
    print("\n--- Impact Analysis ---")
    print(f"/logs Impact: {impact_logs:+.2f}%")
    print(f"/traffic Impact: {impact_traffic:+.2f}%")
    
    if impact_logs > 50 or impact_traffic > 50:
        print("WARNING: Significant performance degradation detected (>50%)")
    else:
        print("Performance impact is within acceptable limits.")

if __name__ == "__main__":
    run_performance_test()
