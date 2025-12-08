import subprocess
import sys
import os
import signal
import psutil

class AgentManager:
    def __init__(self):
        self.process = None
        self.log_file = None

    def start_agent(self):
        if self.is_running():
            return {"status": "already_running", "pid": self.process.pid}

        try:
            # Run from project root
            cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            
            # Use the same python executable as the backend
            python_exe = sys.executable
            
            # Script path
            script_path = os.path.join(cwd, "agent", "client.py")
            
            # Open log file
            self.log_file = open(os.path.join(cwd, "agent_runtime.log"), "a")

            # Start subprocess
            # We use python -u for unbuffered output
            self.process = subprocess.Popen(
                [python_exe, "-u", script_path],
                cwd=cwd,
                stdout=self.log_file,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid # Create new process group so we can kill it and children
            )
            
            return {"status": "started", "pid": self.process.pid}
        except Exception as e:
            print(f"Failed to start agent: {e}")
            return {"status": "error", "error": str(e)}

    def stop_agent(self):
        if not self.is_running():
            return {"status": "not_running"}

        try:
            # Kill the process group to ensure children (like pynput threads/processes?) are killed
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait(timeout=3)
        except Exception as e:
            print(f"Error stopping agent: {e}")
            try:
                # Force kill if SIGTERM failed
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except:
                pass
        finally:
            self.process = None
            if self.log_file:
                self.log_file.close()
                self.log_file = None

        return {"status": "stopped"}

    def is_running(self):
        if self.process is None:
            return False
        
        if self.process.poll() is not None:
            # Process has exited
            self.process = None
            return False
            
        return True

    def get_status(self):
        running = self.is_running()
        return {
            "is_running": running,
            "pid": self.process.pid if running else None
        }

# Global instance
agent_manager = AgentManager()
