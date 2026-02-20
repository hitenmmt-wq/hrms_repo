#!/usr/bin/env python3
"""
HRMS Agent Test Script
Tests connectivity and configuration before full deployment
"""

import json
import os
import platform
import sys


def test_dependencies():
    """Test if required Python packages are installed"""
    print("Testing dependencies...")
    try:
        import requests

        print("  ✓ requests installed", requests.__version__)
    except ImportError:
        print("  ✗ requests NOT installed - run: pip install requests")
        return False

    try:
        import pynput

        print("  ✓ pynput installed", pynput.__version__)
    except ImportError:
        print("  ✗ pynput NOT installed - run: pip install pynput")
        return False

    return True


def test_config():
    """Test if config.json exists and is valid"""
    print("\nTesting configuration...")

    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"  ✗ config.json not found in {os.getcwd()}")
        return False, None

    print("  ✓ config.json found")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print("  ✓ config.json is valid JSON")
    except json.JSONDecodeError as e:
        print(f"  ✗ config.json is invalid JSON: {e}")
        return False, None

    # Check required fields
    required = ["server_url", "tracking_token"]
    for field in required:
        if field not in config:
            print(f"  ✗ Missing required field: {field}")
            return False, None
        print(f"  ✓ {field}: {config[field]}")

    if config.get("tracking_token") == "PUT-DEVICE-TOKEN-HERE":
        print("  ⚠ tracking_token not set - device needs registration")

    return True, config


def test_connectivity(config):
    """Test connectivity to HRMS server"""
    print("\nTesting server connectivity...")

    import requests

    server_url = config["server_url"].rstrip("/")
    activity_endpoint = config.get("activity_endpoint", "/superadmin/activity-log/")
    activity_url = f"{server_url}{activity_endpoint}"

    print(f"  Testing: {activity_url}")

    try:
        # Test with dummy data
        response = requests.post(
            activity_url,
            json={
                "tracking_token": config["tracking_token"],
                "is_active": True,
                "idle_seconds": 0,
            },
            timeout=5,
        )

        if response.status_code == 200:
            print(f" Server responded: {response.status_code}")
            return True
        elif response.status_code == 401:
            print(" Authentication failed ")
            return False
        elif response.status_code == 404:
            print(" Endpoint not found ")
            return False
        else:
            print(f" Server responded with: {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(" Connection failed - server unreachable")
        return False
    except requests.exceptions.Timeout:
        print(" Connection timeout")
        return False
    except Exception as e:
        print(f" Error: {e}")
        return False


def test_input_monitoring():
    """Test if input monitoring works"""
    print("\nTesting input monitoring...")

    try:
        from pynput import keyboard, mouse

        # Try to create listeners
        mouse.Listener(on_move=lambda x, y: None)
        keyboard.Listener(on_press=lambda key: None)

        print(" Input listeners created successfully")

        # Check platform-specific requirements
        system = platform.system()
        if system == "Darwin":
            print(
                " macOS: Ensure Accessibility & Input Monitoring permissions are granted"
            )
        elif system == "Linux":
            print(" Linux: Ensure running in graphical session (not SSH)")

        return True

    except Exception as e:
        print(f" Input monitoring failed: {e}")
        return False


def main():
    print("=" * 60)
    print("HRMS Desktop Agent - Installation Test")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Working Directory: {os.getcwd()}")
    print()

    # Run tests
    deps_ok = test_dependencies()
    config_ok, config = test_config()

    if not deps_ok or not config_ok:
        print("\n" + "=" * 60)
        print("checks FAILED")
        print("=" * 60)
        sys.exit(1)

    connectivity_ok = test_connectivity(config)
    input_ok = test_input_monitoring()

    print("\n" + "=" * 60)
    if deps_ok and config_ok and connectivity_ok and input_ok:
        print("All tests PASSED - Agent ready to run!")
    else:
        print("Some tests FAILED - Review errors above")
    print("=" * 60)

    if connectivity_ok:
        print("\nTo start the agent:")
        if platform.system() == "Windows":
            print("python agent.py")
        else:
            print("python3 agent.py")


if __name__ == "__main__":
    main()
