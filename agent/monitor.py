import psutil
from datetime import datetime
import threading
import time
from collections import defaultdict
import platform
import subprocess
import json
import hashlib
try:
    from scapy.all import sniff, IP
except ImportError:
    print("Scapy not installed. Network monitoring disabled.")

class SystemMonitor:
    def get_metrics(self):
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used // (1024 * 1024),
            "disk_percent": disk.percent
        }

class NetworkMonitor:
    def __init__(self):
        self.is_running = False
        self.stats = defaultdict(int)
        self.lock = threading.Lock()
        self.thread = None

    def _packet_callback(self, packet):
        if IP in packet:
            src = packet[IP].src
            dst = packet[IP].dst
            # Simple aggregation: Count packets per source-dest pair
            key = f"{src}->{dst}"
            
            with self.lock:
                self.stats[key] += 1

    def _sniff_loop(self):
        # Sniff silently (store=0) to avoid memory issues
        # Filter for IP traffic only
        try:
            sniff(prn=self._packet_callback, store=0, filter="ip", stop_filter=lambda x: not self.is_running)
        except Exception as e:
            print(f"Network sniffer error: {e}")

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._sniff_loop, daemon=True)
        self.thread.start()
        print("Network Monitor started.")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)

    def get_and_reset_stats(self):
        """Returns the current stats and resets the counter."""
        with self.lock:
            # Convert to list of dicts for easier JSON serialization
            data = []
            for k, v in self.stats.items():
                src, dst = k.split("->")
                data.append({"src": src, "dst": dst, "count": v})
            
            self.stats.clear()
            return data

class ClipboardMonitor:
    def __init__(self, max_length=200):
        self.last_hash = None
        self.max_length = max_length

    def _read_clipboard(self):
        system = platform.system()
        try:
            if system == "Darwin":
                result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    return result.stdout
            elif system == "Windows":
                result = subprocess.run(
                    ["powershell", "-Command", "Get-Clipboard"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return result.stdout
            else:
                result = subprocess.run(["xclip", "-o", "-selection", "clipboard"], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    return result.stdout
                result = subprocess.run(["xsel", "-b", "-o"], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    return result.stdout
        except Exception:
            return None
        return None

    def poll(self):
        content = self._read_clipboard()
        if content is None:
            return None
        content = content.strip()
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if content_hash == self.last_hash:
            return None
        self.last_hash = content_hash
        preview = content[: self.max_length]
        return {
            "length": len(content),
            "preview": preview,
            "hash": content_hash
        }

class UsbMonitor:
    def __init__(self):
        self.last_devices = set()

    def _collect_devices_macos(self):
        try:
            result = subprocess.run(["system_profiler", "SPUSBDataType", "-json"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return []
            data = json.loads(result.stdout)
            devices = []
            def walk(obj):
                if isinstance(obj, list):
                    for item in obj:
                        walk(item)
                elif isinstance(obj, dict):
                    name = obj.get("_name")
                    if name and any(k in obj for k in ["vendor_id", "product_id", "serial_num", "manufacturer"]):
                        devices.append({
                            "name": name,
                            "vendor_id": obj.get("vendor_id"),
                            "product_id": obj.get("product_id"),
                            "serial_num": obj.get("serial_num"),
                            "manufacturer": obj.get("manufacturer")
                        })
                    for key in obj.keys():
                        if key in ["_items", "spusb_devices", "items", "_children"]:
                            walk(obj[key])
            walk(data.get("SPUSBDataType", []))
            return devices
        except Exception:
            return []

    def _collect_devices_linux(self):
        try:
            result = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=3)
            if result.returncode != 0:
                return []
            devices = []
            for line in result.stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 6:
                    usb_id = parts[5]
                    name = " ".join(parts[6:]) if len(parts) > 6 else usb_id
                    devices.append({"name": name, "vendor_id": usb_id.split(":")[0], "product_id": usb_id.split(":")[1]})
            return devices
        except Exception:
            return []

    def _collect_devices_windows(self):
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-PnpDevice -Class USB | Select-Object -ExpandProperty FriendlyName"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return []
            devices = []
            for line in result.stdout.strip().splitlines():
                name = line.strip()
                if name:
                    devices.append({"name": name})
            return devices
        except Exception:
            return []

    def _collect_devices(self):
        system = platform.system()
        if system == "Darwin":
            return self._collect_devices_macos()
        if system == "Windows":
            return self._collect_devices_windows()
        return self._collect_devices_linux()

    def poll(self):
        devices = self._collect_devices()
        current = set([d.get("name") for d in devices if d.get("name")])
        added = list(current - self.last_devices)
        removed = list(self.last_devices - current)
        if not added and not removed:
            return None
        self.last_devices = current
        return {
            "added": added,
            "removed": removed,
            "count": len(current)
        }

class CameraMonitor:
    def __init__(self):
        self.last_devices = set()

    def _collect_cameras_macos(self):
        try:
            result = subprocess.run(["system_profiler", "SPCameraDataType", "-json"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return []
            data = json.loads(result.stdout)
            devices = []
            def walk(obj):
                if isinstance(obj, list):
                    for item in obj:
                        walk(item)
                elif isinstance(obj, dict):
                    name = obj.get("_name")
                    if name and any(k in obj for k in ["model_id", "unique_id", "manufacturer"]):
                        devices.append({
                            "name": name,
                            "model_id": obj.get("model_id"),
                            "unique_id": obj.get("unique_id"),
                            "manufacturer": obj.get("manufacturer")
                        })
                    for key in obj.keys():
                        if key in ["_items", "spcamera_devices", "items", "_children"]:
                            walk(obj[key])
            walk(data.get("SPCameraDataType", []))
            return devices
        except Exception:
            return []

    def _collect_cameras_linux(self):
        try:
            result = subprocess.run(["ls", "/dev"], capture_output=True, text=True, timeout=2)
            if result.returncode != 0:
                return []
            devices = []
            for name in result.stdout.strip().splitlines():
                if name.startswith("video"):
                    devices.append({"name": name})
            return devices
        except Exception:
            return []

    def _collect_cameras_windows(self):
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-PnpDevice -Class Camera | Select-Object -ExpandProperty FriendlyName"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return []
            devices = []
            for line in result.stdout.strip().splitlines():
                name = line.strip()
                if name:
                    devices.append({"name": name})
            return devices
        except Exception:
            return []

    def _collect_devices(self):
        system = platform.system()
        if system == "Darwin":
            return self._collect_cameras_macos()
        if system == "Windows":
            return self._collect_cameras_windows()
        return self._collect_cameras_linux()

    def poll(self):
        devices = self._collect_devices()
        current = set([d.get("name") for d in devices if d.get("name")])
        added = list(current - self.last_devices)
        removed = list(self.last_devices - current)
        if not added and not removed:
            return None
        self.last_devices = current
        return {
            "added": added,
            "removed": removed,
            "count": len(current)
        }

if __name__ == "__main__":
    sm = SystemMonitor()
    print(sm.get_metrics())
    
    nm = NetworkMonitor()
    nm.start()
    time.sleep(5)
    print(nm.get_and_reset_stats())
    nm.stop()
