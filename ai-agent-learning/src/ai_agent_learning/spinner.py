import sys
import time
import threading

class Spinner:
    """A simple terminal spinner that runs in a separate thread."""
    
    def __init__(self, message="Thinking"):
        self.message = message
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.running = False
        self.thread = None
    
    def _spin(self):
        idx = 0
        while self.running:
            char = self.spinner_chars[idx % len(self.spinner_chars)]
            sys.stdout.write(f"\r{char}  {self.message}...")
            sys.stdout.flush()
            time.sleep(0.1)
            idx += 1
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()