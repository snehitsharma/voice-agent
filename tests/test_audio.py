import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import audioop

from app import audio


def test_mulaw_8k_to_pcm_16k():
    n = 4000  # 0.5 s at 8 kHz
    pcm8 = b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / 8000))) for i in range(n))
    mulaw = audioop.lin2ulaw(pcm8, 2)

    pcm16, _ = audio.mulaw8k_to_pcm16k(mulaw)

    assert abs(len(pcm16) - 2 * 2 * n) <= 16  # twice the samples, 2 bytes each
    samples = struct.unpack(f"<{len(pcm16) // 2}h", pcm16)
    assert max(abs(s) for s in samples) < 32767  # no clipping
    assert abs(audioop.rms(pcm16, 2) - audioop.rms(pcm8, 2)) < 0.15 * audioop.rms(pcm8, 2)
