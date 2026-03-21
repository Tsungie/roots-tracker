import os
import requests
from dotenv import load_dotenv

# Load the keys from your hidden .env file
load_dotenv()

ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# The number you want to send the message TO (your verified test number)
RECIPIENT_NUMBER = "263776844533"  


def send_test_message():
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # We use Meta's pre-approved 'hello_world' template for the test
    payload = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT_NUMBER,
        "type": "template",
        "template": {"name": "hello_world", "language": {"code": "en_US"}},
    }

    print(f"Sending message to {RECIPIENT_NUMBER}...")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print("✅ SUCCESS! Check your phone!")
    else:
        print("❌ FAILED!")
        print(response.text)


if __name__ == "__main__":
    send_test_message()
