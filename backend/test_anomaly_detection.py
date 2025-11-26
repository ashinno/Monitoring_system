import requests
import datetime
import random
import time

BASE_URL = "http://127.0.0.1:8000"

def login():
    session = requests.Session()
    session.trust_env = False
    response = session.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin"})
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None
    # Pydantic with alias_generator=to_camel will return camelCase keys
    return response.json().get("accessToken")

def create_log(token, risk="INFO", hour=10, day=0):
    session = requests.Session()
    session.trust_env = False
    # Construct a timestamp for a specific hour and day
    # day: 0=Monday, 6=Sunday
    # We need a recent date that matches this weekday
    today = datetime.date.today()
    days_behind = (today.weekday() - day) % 7
    target_date = today - datetime.timedelta(days=days_behind)
    
    dt = datetime.datetime.combine(target_date, datetime.time(hour=hour, minute=random.randint(0, 59)))
    
    log_data = {
        "id": f"test-{random.randint(1000, 9999)}",
        "timestamp": dt.isoformat(),
        "user": "test_user",
        "activityType": "LOGIN",
        "riskLevel": risk,
        "description": "Routine login",
        "details": "Nothing special",
        "ipAddress": "192.168.1.1",
        "location": "Office"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = session.post(f"{BASE_URL}/logs", json=log_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error creating log: {response.status_code} - {response.text}")
        # Return a dummy dict to avoid crashing, or raise a more descriptive error
        return {}
        
    try:
        return response.json()
    except Exception as e:
        print(f"JSON Decode Error: {e}")
        print(f"Response text: {response.text}")
        return {}

def run_test():
    token = login()
    if not token:
        return

    print("Generating training data (normal behavior)...")
    # Generate 50 normal logs: 9 AM - 5 PM, Mon-Fri, Risk INFO
    for _ in range(50):
        hour = random.randint(9, 17)
        day = random.randint(0, 4) # Mon-Fri
        create_log(token, risk="INFO", hour=hour, day=day)
    
    print("Triggering training...")
    session = requests.Session()
    session.trust_env = False
    headers = {"Authorization": f"Bearer {token}"}
    resp = session.post(f"{BASE_URL}/ml/train", headers=headers)
    print(resp.json())
    
    # Wait a bit for training to complete (it's synchronous in my code, but good to pause)
    time.sleep(1)
    
    print("Testing anomaly (Sunday 3 AM)...")
    # Sunday (6), 3 AM
    anomaly_log = create_log(token, risk="INFO", hour=3, day=6)
    
    print("Result:")
    print(f"Risk Level: {anomaly_log.get('riskLevel')}") # Should be HIGH if detected
    print(f"Description: {anomaly_log.get('description')}") # Should contain [ML_DETECTED]

    if "ML_DETECTED" in anomaly_log.get('description', ''):
        print("SUCCESS: Anomaly detected!")
    else:
        print("FAILURE: Anomaly NOT detected.")

if __name__ == "__main__":
    run_test()
