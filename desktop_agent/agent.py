import getpass
import json
import os
import sys
import time

import requests
from pynput import keyboard, mouse


def is_truthy(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def get_config_path():
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(os.path.dirname(sys.executable), "config.json"))
        if hasattr(sys, "_MEIPASS"):
            candidates.append(os.path.join(sys._MEIPASS, "config.json"))
    else:
        candidates.append(os.path.join(os.path.dirname(__file__), "config.json"))

    for config_path in candidates:
        if os.path.exists(config_path):
            return config_path

    raise FileNotFoundError("Missing config.json. Place it next to the app executable.")


def load_config(config_path=None):
    path = config_path or get_config_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config, config_path=None):
    path = config_path or get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def resolve_registration_credentials(config):
    email = (
        os.getenv("HRMS_EMAIL") or config.get("employee_email") or config.get("email")
    )
    password = (
        os.getenv("HRMS_PASSWORD")
        or config.get("employee_password")
        or config.get("password")
    )

    if email and password:
        return email.strip(), password.strip()

    if not sys.stdin or not sys.stdin.isatty():
        raise RuntimeError(
            "Missing credentials for auto-register in background mode. "
            "Set tracking_token in config.json or provide HRMS_EMAIL/HRMS_PASSWORD."
        )

    print("First run detected. Please login to register this device.")
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ").strip()
    return email, password


def register_device(config):
    server_url = config["server_url"].rstrip("/")
    device_name = config.get("device_name") or None

    email, password = resolve_registration_credentials(config)

    login_url = f"{server_url}/superadmin/auth/login/"
    register_url = f"{server_url}/superadmin/device/register/"

    login_resp = requests.post(
        login_url, json={"email": email, "password": password}, timeout=10
    )
    if login_resp.status_code != 200:
        raise RuntimeError(f"Login failed: {login_resp.text}")

    access_token = login_resp.json().get("access")
    if not access_token:
        raise RuntimeError("Login response missing access token.")

    headers = {"Authorization": f"Bearer {access_token}"}
    register_payload = {"device_name": device_name} if device_name else {}

    reg_resp = requests.post(
        register_url, json=register_payload, headers=headers, timeout=10
    )
    if reg_resp.status_code not in (200, 201):
        raise RuntimeError(f"Register failed: {reg_resp.text}")

    tracking_token = reg_resp.json().get("tracking_token")
    if not tracking_token:
        raise RuntimeError("Register response missing tracking_token.")

    config["tracking_token"] = tracking_token
    save_config(config)
    print("Device registered. tracking_token saved to config.json")
    return config


def get_int_setting(config, key, default_value, previous=None):
    value = config.get(key, None)
    if value is None and previous is not None:
        return previous
    if value is None:
        return int(default_value)
    return int(value)


def get_setting(config, key, default_value, previous=None, overrides=None):
    if overrides and key in overrides and overrides.get(key) is not None:
        return overrides.get(key)
    if key in config and config.get(key) is not None:
        return config.get(key)
    if previous is not None and key in previous:
        return previous.get(key)
    return default_value


def build_runtime_settings(config, previous=None, overrides=None):
    previous = previous or {}

    server_url = (config.get("server_url") or previous.get("server_url") or "").rstrip(
        "/"
    )
    if not server_url:
        raise RuntimeError("server_url is required in config.json")

    tracking_token = (
        config.get("tracking_token")
        or previous.get("tracking_token")
        or "PUT-DEVICE-TOKEN-HERE"
    )
    if tracking_token == "PUT-DEVICE-TOKEN-HERE":
        raise RuntimeError("tracking_token is required in config.json")

    activity_endpoint = get_setting(
        config,
        "activity_endpoint",
        "/superadmin/activity-log/",
        previous=previous,
        overrides=overrides,
    )
    if not activity_endpoint.startswith("/"):
        activity_endpoint = f"/{activity_endpoint}"

    remote_config_endpoint = get_setting(
        config,
        "remote_config_endpoint",
        "/superadmin/device/config/",
        previous=previous,
        overrides=overrides,
    )
    if not remote_config_endpoint.startswith("/"):
        remote_config_endpoint = f"/{remote_config_endpoint}"

    return {
        "server_url": server_url,
        "tracking_token": tracking_token,
        "activity_endpoint": activity_endpoint,
        "activity_url": f"{server_url}{activity_endpoint}",
        "remote_config_endpoint": remote_config_endpoint,
        "remote_config_url": f"{server_url}{remote_config_endpoint}",
        "remote_config_enabled": is_truthy(
            get_setting(
                config,
                "remote_config_enabled",
                True,
                previous=previous,
                overrides=overrides,
            ),
            default=True,
        ),
        "idle_threshold": get_int_setting(
            overrides or config,
            "idle_threshold_seconds",
            60,
            previous.get("idle_threshold"),
        ),
        "heartbeat_seconds": get_int_setting(
            overrides or config,
            "heartbeat_seconds",
            60,
            previous.get("heartbeat_seconds"),
        ),
        "send_interval": get_int_setting(
            overrides or config,
            "send_interval_seconds",
            5,
            previous.get("send_interval"),
        ),
        "timeout_seconds": get_int_setting(
            overrides or config,
            "timeout_seconds",
            5,
            previous.get("timeout_seconds"),
        ),
        "config_reload_seconds": get_int_setting(
            overrides or config,
            "config_reload_seconds",
            30,
            previous.get("config_reload_seconds"),
        ),
        "remote_config_refresh_seconds": get_int_setting(
            overrides or config,
            "remote_config_refresh_seconds",
            60,
            previous.get("remote_config_refresh_seconds"),
        ),
    }


def fetch_remote_config(runtime):
    if not runtime.get("remote_config_enabled"):
        return None

    response = requests.get(
        runtime["remote_config_url"],
        params={"tracking_token": runtime["tracking_token"]},
        timeout=runtime["timeout_seconds"],
    )
    response.raise_for_status()
    payload = response.json()
    remote_config = payload.get("config")
    if not isinstance(remote_config, dict):
        return None
    remote_version = payload.get("version")
    return {"version": remote_version, "config": remote_config}


def main():
    config_path = get_config_path()
    config = load_config(config_path)
    if (
        not config.get("tracking_token")
        or config.get("tracking_token") == "PUT-DEVICE-TOKEN-HERE"
    ):
        try:
            config = register_device(config)
        except Exception as exc:
            print("Auto-register failed:", exc)
            return

    runtime = build_runtime_settings(config)
    remote_state = {"version": None, "config": {}}
    last_config_mtime = os.path.getmtime(config_path)
    last_config_check_at = time.time()
    last_remote_fetch_at = 0

    last_activity_time = time.time()
    last_send_time = 0
    last_state = None

    def update_activity(*_args, **_kwargs):
        nonlocal last_activity_time
        last_activity_time = time.time()

    mouse.Listener(on_move=update_activity, on_click=update_activity).start()
    keyboard.Listener(on_press=update_activity).start()

    print("Activity agent started.")
    print(f"Server: {runtime['server_url']}")
    print(f"Activity URL: {runtime['activity_url']}")
    print(f"Remote Config URL: {runtime['remote_config_url']}")
    print(f"Config path: {config_path}")

    while True:
        now = time.time()
        if now - last_config_check_at >= runtime["config_reload_seconds"]:
            last_config_check_at = now
            try:
                current_mtime = os.path.getmtime(config_path)
                if current_mtime != last_config_mtime:
                    reloaded = load_config(config_path)
                    config = reloaded
                    updated_runtime = build_runtime_settings(
                        config, runtime, overrides=remote_state["config"]
                    )
                    changed_keys = [
                        key
                        for key in updated_runtime
                        if updated_runtime[key] != runtime[key]
                    ]
                    runtime = updated_runtime
                    last_config_mtime = current_mtime
                    if changed_keys:
                        print(f"Config reloaded. Updated: {', '.join(changed_keys)}")
            except Exception as exc:
                print("Config reload error:", exc)

        if now - last_remote_fetch_at >= runtime["remote_config_refresh_seconds"]:
            last_remote_fetch_at = now
            try:
                remote_data = fetch_remote_config(runtime)
                if remote_data:
                    needs_update = (
                        remote_data["version"] != remote_state["version"]
                        or remote_data["config"] != remote_state["config"]
                    )
                    if needs_update:
                        updated_runtime = build_runtime_settings(
                            config, runtime, overrides=remote_data["config"]
                        )
                        changed_keys = [
                            key
                            for key in updated_runtime
                            if updated_runtime[key] != runtime[key]
                        ]
                        runtime = updated_runtime
                        remote_state = remote_data
                        if changed_keys:
                            print(
                                f"Remote config applied (v{remote_state['version']}). "
                                f"Updated: {', '.join(changed_keys)}"
                            )
            except Exception as exc:
                print("Remote config fetch error:", exc)

        idle_seconds = int(time.time() - last_activity_time)
        is_active = idle_seconds < runtime["idle_threshold"]

        should_send = (
            last_state is None
            or is_active != last_state
            or (time.time() - last_send_time) >= runtime["heartbeat_seconds"]
        )

        if should_send:
            payload = {
                "tracking_token": runtime["tracking_token"],
                "is_active": is_active,
                "idle_seconds": idle_seconds,
            }
            try:
                requests.post(
                    runtime["activity_url"],
                    json=payload,
                    timeout=runtime["timeout_seconds"],
                )
                last_state = is_active
                last_send_time = time.time()
                print("Sent:", payload)
            except Exception as exc:
                print("Send error:", exc)

        time.sleep(runtime["send_interval"])


if __name__ == "__main__":
    main()
