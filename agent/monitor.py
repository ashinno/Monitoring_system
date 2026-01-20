import psutil
from datetime import datetime
import threading
import time
from collections import defaultdict
try:
    from scapy.all import sniff, IP, TCP, UDP
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

if __name__ == "__main__":
    sm = SystemMonitor()
    print(sm.get_metrics())
    
    nm = NetworkMonitor()
    nm.start()
    time.sleep(5)
    print(nm.get_and_reset_stats())
    nm.stop()
