import json

import firebase_admin
import requests
from firebase_admin import credentials

cred = credentials.Certificate("apps/config/firebase-service-account.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)


def send_fcm_notification(device_token):
    fcm_url = "https://fcm.googleapis.com/v1/projects/hrms-f6b07/messages:send"

    message = {
        "message": {
            "token": device_token,
            "notification": {
                "title": "Test Notification",
                "body": "This is a test notification from Firebase Cloud Messaging.",
            },
        }
    }

    headers = {
        "Authorization": f"Bearer {firebase_admin.credentials.get_access_token()}",
        "Content-Type": "application/json; UTF-8",
    }

    response = requests.post(
        fcm_url, json=message, headers=headers, data=json.dumps(message)
    )

    if response.status_code == 200:
        print("Notification sent successfully.")
    else:
        print(f"Failed to send notification: {response.text}")
