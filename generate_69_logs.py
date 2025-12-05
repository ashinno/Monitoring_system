import requests
import time
import random
import uuid
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def run():
    session = requests.Session()
    session.trust_env = False
    
    # 1. Login
    print("Logging in...")
    try:
        response = session.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin"})
        if response.status_code != 200:
            print(f"Login failed: Status {response.status_code}, Body: {response.text}")
            return
        
        data = response.json()
        token = data.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # 2. Create 69 Logs
    print("Generating 69 logs...")
    
    activities = [
        ("LOGIN_SUCCESS", "INFO", "User logged in successfully", "Method: Password"),
        ("FILE_ACCESS", "INFO", "Accessed confidential document", "File: Q4_Report.pdf"),
        ("SUDO_USAGE", "HIGH", "User used sudo command", "Command: sudo rm -rf /tmp/*"),
        ("MALWARE_DETECTED", "CRITICAL", "Antivirus flagged file", "Path: /tmp/trojan.exe"),
        ("DATA_EXFILTRATION", "CRITICAL", "Large outbound traffic detected", "Dest: 192.168.x.x, Size: 5GB"),
        ("FAILED_LOGIN", "MEDIUM", "Failed login attempt", "IP: 45.22.11.1"),
        ("PORT_SCAN", "HIGH", "Port scan detected", "Source: 10.0.0.5"),
        ("PASSWORD_CHANGE", "INFO", "User changed password", "User: alice"),
        ("ACCOUNT_LOCKED", "MEDIUM", "Account locked due to multiple failures", "User: bob"),
        ("SYSTEM_UPDATE", "INFO", "System update started", "Version: 2.0.1")
    ]
    
    users = ["admin", "alice", "bob", "system", "unknown", "charlie", "dave", "eve", "frank", "grace"]
    
    for i in range(69):
        act = random.choice(activities)
        log = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user": random.choice(users),
            "activity_type": act[0],
            "risk_level": act[1],
            "description": act[2],
            "details": act[3],
            "ip_address": f"192.168.1.{random.randint(10, 200)}",
            "location": "Internal Network"
        }
        
        try:
            res = session.post(f"{BASE_URL}/logs", json=log, headers=headers)
            if res.status_code == 200:
                # Print every 10th to reduce spam, but ensure last one is printed or start/end
                if (i+1) % 10 == 0 or i == 68:
                    print(f"[{i+1}/69] Created log: {log['description']}")
            else:
                print(f"[{i+1}/69] Failed: {res.text}")
        except Exception as e:
            print(f"Error creating log: {e}")
        
        # Minimal delay
        time.sleep(0.05)

if __name__ == "__main__":
    run()
