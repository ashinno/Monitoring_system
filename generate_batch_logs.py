import requests
import time
import random
import uuid

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
        token = data.get("access_token") or data.get("accessToken")
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # 2. Create 6 Logs
    current_time = int(time.time())
    logs = [
        # 1. Normal: API Usage
        {
            "id": f"log-batch-1-{current_time}",
            "timestamp": "2025-11-26T09:30:00",
            "user": "service_account",
            "activity_type": "API_CALL",
            "risk_level": "INFO",
            "description": "Routine data synchronization",
            "details": "Sync endpoint /v1/users",
            "ip_address": "10.0.0.100",
            "location": "Internal"
        },
        # 2. Normal: User Logout
        {
            "id": f"log-batch-2-{current_time}",
            "timestamp": "2025-11-26T17:00:00",
            "user": "alice",
            "activity_type": "LOGOUT",
            "risk_level": "INFO",
            "description": "User logged out",
            "details": "Session duration: 8h",
            "ip_address": "192.168.1.10",
            "location": "New York"
        },
        # 3. High: Brute Force Suspect
        {
            "id": f"log-batch-3-{current_time}",
            "timestamp": "2025-11-26T12:00:00",
            "user": "unknown",
            "activity_type": "AUTH_FAILURE",
            "risk_level": "HIGH",
            "description": "High rate of authentication failures",
            "details": "50 attempts / second",
            "ip_address": "89.200.10.50",
            "location": "Unknown"
        },
        # 4. High: Unexpected Admin Access
        {
            "id": f"log-batch-4-{current_time}",
            "timestamp": "2025-11-26T04:00:00",
            "user": "maintenance",
            "activity_type": "ADMIN_ACCESS",
            "risk_level": "HIGH",
            "description": "Admin panel accessed outside maintenance window",
            "details": "Module: UserManagement",
            "ip_address": "192.168.1.99",
            "location": "Office"
        },
        # 5. Critical: Rootkit
        {
            "id": f"log-batch-5-{current_time}",
            "timestamp": "2025-11-26T23:55:00",
            "user": "root",
            "activity_type": "SYSTEM_INTEGRITY",
            "risk_level": "CRITICAL",
            "description": "System file checksum mismatch",
            "details": "/bin/ls modified",
            "ip_address": "127.0.0.1",
            "location": "Server"
        },
        # 6. Critical: Insider Threat
        {
            "id": f"log-batch-6-{current_time}",
            "timestamp": "2025-11-26T16:30:00",
            "user": "disgruntled_emp",
            "activity_type": "DATA_DESTRUCTION",
            "risk_level": "CRITICAL",
            "description": "Mass deletion of customer records",
            "details": "DELETE * FROM customers",
            "ip_address": "192.168.1.45",
            "location": "Office"
        }
    ]

    print("Creating 6 logs...")
    for log in logs:
        try:
            res = session.post(f"{BASE_URL}/logs", json=log, headers=headers)
            if res.status_code == 200:
                print(f"Created log {log['id']} ({log['risk_level']})")
            else:
                print(f"Failed to create log {log['id']}: {res.text}")
        except Exception as e:
             print(f"Error creating log {log['id']}: {e}")

    # 3. Analyze
    print("Requesting analysis...")
    try:
        res = session.post(f"{BASE_URL}/analyze", headers=headers)
        if res.status_code == 200:
            data = res.json()
            print("Analysis complete.")
            print(f"Threat Score: {data.get('threat_score')}")
            explanations = data.get("explanations", {})
            print(f"Explanations found: {len(explanations)}")
            
            # Print specific explanations for our new logs
            for log in logs:
                if log['id'] in explanations:
                    print(f"Explanation for {log['id']}: {explanations[log['id']]}")
        else:
            print(f"Analysis failed: {res.text}")
    except Exception as e:
        print(f"Analysis request error: {e}")

if __name__ == "__main__":
    run()
