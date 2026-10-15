import os

from dotenv import load_dotenv

load_dotenv()

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
TARGET_PHONE_NUMBER = os.getenv("TARGET_PHONE_NUMBER", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

# LLM
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")  # any OpenAI-compatible API
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")

# Sarvam (verified against docs.sarvam.ai)
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
STT_MODEL = "saaras:v3"
STT_MODE = os.getenv("STT_MODE", "transcribe")  # transcribe | codemix (mixed Hindi/English) | ...
TTS_MODEL = "bulbul:v3"
TTS_SPEAKER = os.getenv("TTS_SPEAKER", "priya")
LANGUAGE = os.getenv("LANGUAGE", "en-IN")  # BCP-47, e.g. en-IN, hi-IN
