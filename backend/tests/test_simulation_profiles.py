import requests
import uuid

BASE_URL = "http://127.0.0.1:8000"

def test_simulation_profiles():
    print("Testing Simulation Profiles...")
    
    # 1. Create a profile
    profile_data = {
        "name": f"Test Profile {uuid.uuid4().hex[:8]}",
        "description": "A test profile",
        "trafficType": "HTTP",
        "volume": "high",
        "pattern": "bursty",
        "packetSizeRange": [100, 2000],
        "errorRate": 0.05
    }
    
    # We need a token if auth is enforced, but based on code, depends(auth.get_current_user) is used.
    # So we need to login first.
    print("Logging in...")
    login_data = {"username": "admin", "password": "admin"} # Default seeded admin
    
    # Use no proxies to avoid localhost issues
    proxies = {"http": None, "https": None}
    
    response = requests.post(f"{BASE_URL}/token", data=login_data, proxies=proxies)
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
        return
    
    token = response.json()["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Creating profile...")
    response = requests.post(f"{BASE_URL}/simulation/profiles", json=profile_data, headers=headers, proxies=proxies)
    if response.status_code != 200:
        print(f"Failed to create profile: {response.text}")
        return
    
    created_profile = response.json()
    print(f"Profile created: {created_profile['name']} (ID: {created_profile['id']})")
    
    # 2. List profiles
    print("Listing profiles...")
    response = requests.get(f"{BASE_URL}/simulation/profiles", headers=headers, proxies=proxies)
    if response.status_code != 200:
        print(f"Failed to list profiles: {response.text}")
        return
        
    profiles = response.json()
    print(f"Found {len(profiles)} profiles")
    found = False
    for p in profiles:
        if p['id'] == created_profile['id']:
            found = True
            break
    
    if found:
        print("Created profile found in list.")
    else:
        print("Created profile NOT found in list!")
        
    # 3. Delete profile
    print("Deleting profile...")
    response = requests.delete(f"{BASE_URL}/simulation/profiles/{created_profile['id']}", headers=headers, proxies=proxies)
    if response.status_code == 200:
        print("Profile deleted successfully.")
    else:
        print(f"Failed to delete profile: {response.text}")

    # 4. Verify deletion
    response = requests.get(f"{BASE_URL}/simulation/profiles", headers=headers, proxies=proxies)
    profiles = response.json()
    found = False
    for p in profiles:
        if p['id'] == created_profile['id']:
            found = True
            break
            
    if not found:
        print("Profile successfully removed from list.")
    else:
        print("Profile still exists after deletion!")

if __name__ == "__main__":
    test_simulation_profiles()
