import time
import requests
import uuid
import platform
import socket
import subprocess
import os
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
        self.settings = {}
        self.warning_shown = False

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

    def fetch_settings(self):
        if not self.token:
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/settings", headers=headers)
            if response.status_code == 200:
                self.settings = response.json()
                # Handle camelCase vs snake_case keys (API returns camelCase)
                limit = self.settings.get('screenTimeLimit') if 'screenTimeLimit' in self.settings else self.settings.get('screen_time_limit')
                duration = self.settings.get('screenTimeDurationMinutes') if 'screenTimeDurationMinutes' in self.settings else self.settings.get('screen_time_duration_minutes')
                
                print(f"DEBUG: Settings updated. Screen Time Limit: {limit}, Duration: {duration}m")
            else:
                print(f"Failed to fetch settings: {response.text}")
        except Exception as e:
            print(f"Error fetching settings: {e}")

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

    def manage_screen_time(self):
        # Handle camelCase (API) or snake_case
        limit_enabled = self.settings.get('screenTimeLimit')
        if limit_enabled is None:
             limit_enabled = self.settings.get('screen_time_limit')

        if not limit_enabled:
             self.warning_shown = False
             return

        try:
             val = self.settings.get('screenTimeDurationMinutes')
             if val is None:
                 val = self.settings.get('screen_time_duration_minutes', 120)
             limit_minutes = int(val)
        except:
             limit_minutes = 120
            
        limit_seconds = limit_minutes * 60
        warning_seconds = limit_seconds - 300 # 5 minutes before

        # Ensure warning_seconds is positive
        if warning_seconds < 0:
            warning_seconds = 0

        last_activity = self.keylogger.last_activity_time
        inactive_seconds = (datetime.now() - last_activity).total_seconds()

        if inactive_seconds > limit_seconds:
            print(f"DEBUG: Inactivity ({inactive_seconds}s) > Limit ({limit_seconds}s). Triggering sleep...")
            self.send_log("SYSTEM_ACTION", "Screen Time Limit Reached", "Initiating Sleep Mode", "INFO")
            
            # Reset warning flag
            self.warning_shown = False
            
            # Sleep Command
            try:
                if platform.system() == "Darwin":
                     # Try System Events first, it's often more reliable
                     cmd = ["osascript", "-e", 'tell application "System Events" to sleep']
                     result = subprocess.run(cmd, capture_output=True, text=True)
                     if result.returncode != 0:
                         print(f"System Events sleep failed: {result.stderr}. Trying Finder...")
                         res2 = subprocess.run(["osascript", "-e", 'tell application "Finder" to sleep'], capture_output=True, text=True)
                         if res2.returncode != 0:
                             print(f"Finder sleep failed: {res2.stderr}. Trying pmset...")
                             subprocess.run(["pmset", "sleepnow"])
                elif platform.system() == "Windows":
                     # Hibernation off, Suspend on
                     subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            except Exception as e:
                print(f"Failed to sleep: {e}")
            
        elif inactive_seconds > warning_seconds:
             # Debug print every 60s
             if int(inactive_seconds) % 60 == 0:
                 print(f"DEBUG: Inactivity: {int(inactive_seconds)}s / Limit: {int(limit_seconds)}s")

             if not self.warning_shown:
                 msg = f"System will sleep in {int((limit_seconds - inactive_seconds)/60) + 1} minutes due to inactivity. Move mouse to cancel."
                 print(f"WARNING: {msg}")
                 
                 try:
                     if platform.system() == "Darwin":
                         subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "Screen Time Warning"'])
                 except:
                     pass
                 
                 self.warning_shown = True
        else:
            # Activity detected, reset warning
            self.warning_shown = False

    def run(self):
        if not self.login():
            return

        print("Starting monitoring agent...")
        self.fetch_settings()
        self.keylogger.start()
        
        loops = 0
        try:
            while True:
                time.sleep(Config.FLUSH_INTERVAL)
                loops += 1

                # Refresh settings every 60s (assuming 2s interval)
                if loops % 30 == 0:
                    self.fetch_settings()
                
                # Check Screen Time Limits
                self.manage_screen_time()
                
                # 1. Process Keystrokes
                keystrokes, summary = self.keylogger.flush()
                if keystrokes:
                    print(f"Captured activity. Sending...")
                    
                    self.send_log(
                        activity_type="KEYLOG",
                        description=keystrokes,
                        details=summary, # Dictionary with metadata
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
