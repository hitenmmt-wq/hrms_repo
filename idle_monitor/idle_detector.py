import ctypes
import json
import os
import time
from ctypes import wintypes
from datetime import datetime

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ConfigHandler(FileSystemEventHandler):
    def __init__(self, idle_detector):
        self.idle_detector = idle_detector

    def on_modified(self, event):
        if event.src_path.endswith("config.json"):
            print("🔄 Config file updated, reloading...")
            self.idle_detector.reload_config()


class IdleDetector:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.api_url = None
        self.employee_token = None
        self.employee_id = None
        self.idle_threshold = 600
        self.is_idle = False
        self.is_running = True
        self.is_configured = False

        # Windows API setup
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

        # Load initial config
        self.load_config()

        # Setup file watcher
        self.setup_file_watcher()

    def setup_file_watcher(self):
        """Setup file watcher for config changes"""
        event_handler = ConfigHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=".", recursive=False)
        self.observer.start()

    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)

                self.api_url = config.get("api_url", "http://localhost:8000")
                self.employee_token = config.get("employee_token", "")
                self.employee_id = config.get("employee_id", "")
                self.idle_threshold = config.get("idle_threshold", 600)

                if self.employee_token and self.employee_id:
                    self.is_configured = True
                    print(
                        f"✅ Configuration loaded for employee ID: {self.employee_id}"
                    )
                else:
                    self.is_configured = False
                    print("⏳ Waiting for employee login...")
            else:
                self.create_empty_config()

        except Exception as e:
            print(f"⚠️ Config load error: {e}")
            self.is_configured = False

    def create_empty_config(self):
        """Create empty config file"""
        config = {
            "api_url": "http://localhost:8000",
            "employee_token": "",
            "refresh_token": "",
            "employee_id": "",
            "employee_name": "",
            "employee_email": "",
            "idle_threshold": 600,
        }

        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def reload_config(self):
        """Reload configuration when file changes"""
        old_configured = self.is_configured
        self.load_config()

        if not old_configured and self.is_configured:
            print("🚀 Employee logged in! Starting idle monitoring...")
            self.check_connection()
        elif old_configured and not self.is_configured:
            print("👋 Employee logged out! Pausing monitoring...")

    def get_last_input_time(self):
        """Get the time of last input using Windows API"""

        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.UINT),
                ("dwTime", wintypes.DWORD),
            ]

        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)

        if self.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = self.kernel32.GetTickCount() - lii.dwTime
            return millis / 1000.0
        return 0

    def send_idle_status(self, is_idle):
        """Send idle status to Django backend"""
        if not self.is_configured:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.employee_token}",
                "Content-Type": "application/json",
            }

            data = {
                "is_idle": is_idle,
                "timestamp": datetime.now().isoformat(),
                "idle_duration": self.get_last_input_time() if is_idle else 0,
            }

            response = requests.post(
                f"{self.api_url}/attendance/idle-status/",
                headers=headers,
                json=data,
                timeout=10,
            )

            if response.status_code == 200:
                print(f"✓ Idle status sent: {'IDLE' if is_idle else 'ACTIVE'}")
                return True
            else:
                print(f"✗ Failed to send status: {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ Error sending idle status: {e}")
            return False

    def check_connection(self):
        """Check connection to HRMS portal"""
        if not self.is_configured:
            return False

        try:
            headers = {"Authorization": f"Bearer {self.employee_token}"}
            response = requests.get(
                f"{self.api_url}/attendance/idle-health/", headers=headers, timeout=5
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                print(f"✅ Connected to HRMS: {data.get('employee_name')}")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    def monitor_activity(self):
        """Main monitoring loop"""
        print("🔍 HRMS Idle Detector Service Started")
        print("⏳ Waiting for employee login...")

        # Check connection on startup
        if self.is_configured:
            self.check_connection()

        while self.is_running:
            try:
                if not self.is_configured:
                    print("📴 No employee logged in, waiting...", end="\r")
                    time.sleep(5)
                    continue

                idle_time = self.get_last_input_time()

                # Check if user became idle
                if not self.is_idle and idle_time >= self.idle_threshold:
                    self.is_idle = True
                    print(f"😴 User is IDLE (inactive for {idle_time:.1f}s)")
                    self.send_idle_status(True)

                # Check if user became active
                elif self.is_idle and idle_time < 5:  # 5 seconds grace period
                    self.is_idle = False
                    print("⚡ User is ACTIVE")
                    self.send_idle_status(False)

                # Status update every 30 seconds
                if int(time.time()) % 30 == 0:
                    status = "IDLE" if self.is_idle else "ACTIVE"
                    print(f"📊 Status: {status} | Idle time: {idle_time:.1f}s")

                time.sleep(1)

            except KeyboardInterrupt:
                print("\n🛑 Stopping idle detector...")
                self.is_running = False
                break
            except Exception as e:
                print(f"✗ Monitor error: {e}")
                time.sleep(5)

        # Cleanup
        if hasattr(self, "observer"):
            self.observer.stop()
            self.observer.join()


def main():
    print("🚀 HRMS Idle Detector Service v2.0")
    print("=" * 40)

    detector = IdleDetector()

    try:
        detector.monitor_activity()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
