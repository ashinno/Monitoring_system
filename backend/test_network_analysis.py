import requests
import uuid
import datetime

BASE_URL = "http://127.0.0.1:8000"

def get_token():
    session = requests.Session()
    session.trust_env = False
    response = session.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin"})
    if response.status_code == 200:
        # Note: Response uses camelCase due to Pydantic alias generator
        return response.json().get("accessToken")
    else:
        print(f"Failed to login: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def create_traffic_data(token):
    session = requests.Session()
    session.trust_env = False
    headers = {"Authorization": f"Bearer {token}"}
    
    # Normal traffic
    for _ in range(5):
        data = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now().isoformat(),
            "source_ip": "192.168.1.10",
            "destination_ip": "142.250.190.46",
            "port": 443,
            "protocol": "TCP",
            "bytes_transferred": 500,
            "packet_count": 10,
            "is_anomalous": False
        }
        session.post(f"{BASE_URL}/traffic", json=data, headers=headers)

    # Anomaly 1: High Data Transfer
    data_high_transfer = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now().isoformat(),
        "source_ip": "192.168.1.20",
        "destination_ip": "10.0.0.5",
        "port": 22,
        "protocol": "TCP",
        "bytes_transferred": 200 * 1024 * 1024, # 200MB
        "packet_count": 5000,
        "is_anomalous": False
    }
    session.post(f"{BASE_URL}/traffic", json=data_high_transfer, headers=headers)

    # Anomaly 2: Port Scan (Multiple ports from same IP)
    scanner_ip = "192.168.1.66"
    for port in range(20, 35):
        data_scan = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now().isoformat(),
            "source_ip": scanner_ip,
            "destination_ip": "192.168.1.100",
            "port": port,
            "protocol": "TCP",
            "bytes_transferred": 64,
            "packet_count": 1,
            "is_anomalous": False
        }
        session.post(f"{BASE_URL}/traffic", json=data_scan, headers=headers)

    print("Traffic data seeded.")

def test_analysis(token):
    session = requests.Session()
    session.trust_env = False
    headers = {"Authorization": f"Bearer {token}"}
    response = session.get(f"{BASE_URL}/traffic/analyze", headers=headers)
    
    if response.status_code == 200:
        print("\nAnalysis Result:")
        print(response.json())
    else:
        print(f"Analysis failed: {response.text}")

if __name__ == "__main__":
    token = get_token()
    if token:
        create_traffic_data(token)
        test_analysis(token)
