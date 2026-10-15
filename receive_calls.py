"""Point your Twilio number at this server so incoming calls are answered by the agent.

Run once after PUBLIC_BASE_URL changes. From then on, anyone who calls TWILIO_PHONE_NUMBER
reaches the same /voice -> /stream flow that outbound calls use.
"""
import sys

from twilio.rest import Client

from app import config

REQUIRED = ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER", "PUBLIC_BASE_URL")

if __name__ == "__main__":
    missing = [k for k in REQUIRED if not getattr(config, k)]
    if missing:
        sys.exit(f"Missing in .env: {', '.join(missing)}")
    client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    numbers = client.incoming_phone_numbers.list(phone_number=config.TWILIO_PHONE_NUMBER)
    if not numbers:
        sys.exit(f"{config.TWILIO_PHONE_NUMBER} not found in this Twilio account")
    voice_url = config.PUBLIC_BASE_URL + "/voice"
    numbers[0].update(voice_url=voice_url, voice_method="POST")
    print(f"Incoming calls to {config.TWILIO_PHONE_NUMBER} now go to {voice_url}")
