import json


def create_config():
    print("🔧 HRMS Config Generator")
    print("=" * 30)

    config = {}

    config["api_url"] = (
        input("Enter API URL (default: http://localhost:8000): ").strip()
        or "http://localhost:8000"
    )
    config["employee_token"] = input("Enter employee access token: ").strip()
    config["refresh_token"] = input("Enter refresh token (optional): ").strip()
    config["employee_id"] = int(input("Enter employee ID: ").strip())
    config["employee_name"] = input("Enter employee name: ").strip()
    config["employee_email"] = input("Enter employee email: ").strip()
    config["idle_threshold"] = int(
        input("Enter idle threshold in seconds (default: 600): ").strip() or "600"
    )

    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("\n✅ config.json created successfully!")
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    create_config()
