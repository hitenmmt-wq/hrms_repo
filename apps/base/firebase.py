import os

import firebase_admin
from firebase_admin import credentials, messaging

FIREBASE_CRED_PATH = os.getenv(
    "FIREBASE_CREDENTIAL_PATH",
    "apps/config/firebase-service-account.json",
)

if os.path.exists(FIREBASE_CRED_PATH):
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
else:
    print("Firebase credentials not found. Firebase disabled.")


def send_fcm_notification(message):
    if not firebase_admin._apps:
        print("Firebase not initialized. Skipping notification.")
        return

    try:
        response = messaging.send(message)
        print(f"Notification sent successfully: {response}")
    except Exception as exc:
        print(f"Failed to send notification: {exc}")
