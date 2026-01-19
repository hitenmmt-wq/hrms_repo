import psutil


def check_idle_detector_running():
    """Check if HRMS Idle Detector is running"""
    print("🔍 Checking HRMS Idle Detector Status")
    print("=" * 50)

    detector_found = False

    # Check for Python process running idle_detector.py
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            if cmdline and any("idle_detector" in str(cmd).lower() for cmd in cmdline):
                print("✅ Idle Detector is RUNNING")
                print(f"   PID: {proc.info['pid']}")
                print(f"   Name: {proc.info['name']}")
                print(f"   Command: {' '.join(cmdline)}")
                detector_found = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not detector_found:
        print("❌ Idle Detector is NOT RUNNING")
        print("\n💡 To start it, run:")
        print("   python idle_detector.py")

    print("=" * 50)
    return detector_found


if __name__ == "__main__":
    check_idle_detector_running()
    input("\nPress Enter to exit...")
