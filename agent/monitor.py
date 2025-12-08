import psutil
from datetime import datetime

class SystemMonitor:
    def get_metrics(self):
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get active window (Platform specific - complex for cross-platform)
        # For MVP/Thesis, we might skip active window title unless specifically requested or use platform specific libs (pywin32, Quartz, etc.)
        # The proposal mentions "keylogger-based system", but context aware usually needs window title.
        # For now, we stick to resources.
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used // (1024 * 1024),
            "disk_percent": disk.percent
        }

if __name__ == "__main__":
    sm = SystemMonitor()
    print(sm.get_metrics())
