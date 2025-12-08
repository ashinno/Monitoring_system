import time
import requests
import uuid
import platform
import socket
from datetime import datetime
from config import Config
from encryption import Encryptor
from logger_service import KeyLogger
from monitor import SystemMonitor

class SentinelAgent:
    def __init__(self):
        self.base_url = Config.BASE_URL
        self.token = None
        self.encryptor = Encryptor()
        self.keylogger = KeyLogger()
        self.monitor = SystemMonitor()
        self.host_name = socket.gethostname()
        self.ip_address = self._get_ip()

    def _get_ip(self):
        try:
            return socket.gethostbyname(self.host_name)
        except:
            return "127.0.0.1"

    def login(self):
        print(f"Authenticating as {Config.USERNAME}...")
        try:
            # Note: backend expects form data for OAuth2
            data = {
                "username": Config.USERNAME,
                "password": Config.PASSWORD
            }
            response = requests.post(f"{self.base_url}/token", data=data)
            if response.status_code == 200:
                resp_json = response.json()
                self.token = resp_json.get("access_token") or resp_json.get("accessToken")
                print("Authentication successful.")
                return True
            else:
                print(f"Authentication failed: {response.text}")
                return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def send_log(self, activity_type, description, details, risk_level="INFO"):
        if not self.token:
            print("Not authenticated. Skipping send.")
            return

        # Encrypt sensitive data
        # We encrypt description (keystrokes)
        encrypted_desc = self.encryptor.encrypt(description)
        
        # For KEYLOG, if details is a dict (counts), we send it as 'activity_summary' (unencrypted metadata for heatmap)
        # and keep 'details' encrypted or generic.
        # The backend schema has 'activity_summary' field? Let's check schemas.py. 
        # Yes, added in migrate_context.py: add_context_columns adds current_activity and activity_summary.
        
        activity_summary = None
        encrypted_details = ""
        
        if isinstance(details, dict) and activity_type == "KEYLOG":
            # Pass counts as unencrypted summary for heatmap
            import json
            activity_summary = json.dumps(details)
            encrypted_details = self.encryptor.encrypt("Key metrics attached in summary")
        else:
            encrypted_details = self.encryptor.encrypt(str(details))
        
        log_data = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user": Config.USERNAME,
            "activity_type": activity_type,
            "risk_level": risk_level,
            "description": f"[ENCRYPTED] {encrypted_desc}", 
            "details": f"[ENCRYPTED] {encrypted_details}",
            "activity_summary": activity_summary, # New field for unencrypted metadata
            "ip_address": self.ip_address,
            "location": "Agent-Monitored-Device"
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(f"{self.base_url}/logs", json=log_data, headers=headers)
            if response.status_code != 200:
                print(f"Failed to send log: {response.text}")
            else:
                print(f"Sent {activity_type} log.")
        except Exception as e:
            print(f"Error sending log: {e}")

    def run(self):
        if not self.login():
            return

        print("Starting monitoring agent...")
        self.keylogger.start()
        
        try:
            while True:
                time.sleep(Config.FLUSH_INTERVAL)
                
                # 1. Process Keystrokes
                keystrokes, counts = self.keylogger.flush()
                if keystrokes:
                    print(f"Captured {len(keystrokes)} keystrokes. Sending...")
                    
                    # Encrypt detailed logs
                    # But send counts as JSON in details for realtime heatmap (Privacy trade-off for feature)
                    # Or we could send counts as a separate non-encrypted metadata if we define a schema for it.
                    # Current schema puts everything in 'details'.
                    # Let's put the counts in 'details' as unencrypted JSON string for the backend to parse easily for the heatmap.
                    # Wait, 'details' is currently encrypted in send_log.
                    # I should modify send_log to accept raw_details or metadata.
                    
                    self.send_log(
                        activity_type="KEYLOG",
                        description=keystrokes,
                        details=counts, # Dictionary of counts
                        risk_level="INFO"
                    )

                # 2. Process System Metrics
                metrics = self.monitor.get_metrics()
                self.send_log(
                    activity_type="SYSTEM_METRIC",
                    description=f"CPU: {metrics['cpu_percent']}%, RAM: {metrics['memory_percent']}%",
                    details=metrics,
                    risk_level="INFO"
                )
                
        except KeyboardInterrupt:
            print("\nStopping agent...")
            self.keylogger.stop()

if __name__ == "__main__":
    agent = SentinelAgent()
    agent.run()
