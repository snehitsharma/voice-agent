"""Twilio sends 8 kHz mulaw; Sarvam speech-to-text wants 16 kHz PCM16."""
import audioop  # on Python 3.13+ this comes from the audioop-lts package

TWILIO_RATE = 8000
STT_RATE = 16000


def mulaw8k_to_pcm16k(mulaw: bytes, state=None):
    """Returns (pcm, resample_state); pass the state back in with the next chunk."""
    pcm8 = audioop.ulaw2lin(mulaw, 2)
    return audioop.ratecv(pcm8, 2, 1, TWILIO_RATE, STT_RATE, state)
