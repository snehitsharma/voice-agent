"""Start an outbound call. Twilio rings TARGET_PHONE_NUMBER, then asks our server (/voice) what to do."""
import sys

from twilio.rest import Client

from app import config

REQUIRED = ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER", "TARGET_PHONE_NUMBER", "PUBLIC_BASE_URL")

if __name__ == "__main__":
    missing = [k for k in REQUIRED if not getattr(config, k)]
    if missing:
        sys.exit(f"Missing in .env: {', '.join(missing)}")
    call = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN).calls.create(
        to=config.TARGET_PHONE_NUMBER,
        from_=config.TWILIO_PHONE_NUMBER,
        url=config.PUBLIC_BASE_URL + "/voice",
    )
    print("Call started:", call.sid)
