import argparse
import getpass
import json
import os
import sys

import requests


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return config_path, json.load(f)


def save_config(config_path, config):
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def resolve_credentials(
    config, cli_email=None, cli_password=None, non_interactive=False
):
    email = (
        cli_email
        or os.getenv("HRMS_EMAIL")
        or config.get("employee_email")
        or config.get("email")
    )
    password = (
        cli_password
        or os.getenv("HRMS_PASSWORD")
        or config.get("employee_password")
        or config.get("password")
    )

    if email and password:
        return email.strip(), password.strip()

    if non_interactive:
        print(
            "Missing credentials for non-interactive mode. "
            "Provide --email/--password or set HRMS_EMAIL/HRMS_PASSWORD."
        )
        sys.exit(1)

    if not email:
        email = input("Email: ").strip()
    if not password:
        password = getpass.getpass("Password: ").strip()
    return email, password


def main():
    parser = argparse.ArgumentParser(description="Register this device with HRMS.")
    parser.add_argument("--email", help="Employee email for login")
    parser.add_argument("--password", help="Employee password for login")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Fail instead of prompting for credentials",
    )
    args = parser.parse_args()

    config_path, config = load_config()

    server_url = config["server_url"].rstrip("/")
    print(f"==>> server_url: {server_url}")
    device_name = config.get("device_name") or None

    print("Registering device with HRMS...")
    email, password = resolve_credentials(
        config,
        cli_email=args.email,
        cli_password=args.password,
        non_interactive=args.non_interactive,
    )

    login_url = f"{server_url}/superadmin/auth/login/"
    register_url = f"{server_url}/superadmin/device/register/"

    login_resp = requests.post(
        login_url, json={"email": email, "password": password}, timeout=10
    )
    if login_resp.status_code != 200:
        print("Login failed:", login_resp.text)
        sys.exit(1)

    access_token = login_resp.json().get("access")
    if not access_token:
        print("Login response missing access token.")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {access_token}"}
    register_payload = {"device_name": device_name} if device_name else {}

    reg_resp = requests.post(
        register_url, json=register_payload, headers=headers, timeout=10
    )
    if reg_resp.status_code not in (200, 201):
        print("Register failed:", reg_resp.text)
        sys.exit(1)

    tracking_token = reg_resp.json().get("tracking_token")
    if not tracking_token:
        print("Register response missing tracking_token.")
        sys.exit(1)

    config["tracking_token"] = tracking_token
    save_config(config_path, config)
    print("Device registered. tracking_token saved to config.json")


if __name__ == "__main__":
    main()
