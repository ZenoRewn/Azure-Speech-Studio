"""Audio utility functions: WAV creation, crossfade, fade-in."""

import io
import struct
import numpy as np
from datetime import timedelta


def format_time(ticks):
    """Format Azure SDK offset ticks to HH:MM:SS string."""
    seconds = ticks / 10000000
    return str(timedelta(seconds=seconds)).split('.')[0]


def format_recognition_line(offset, text, speaker_id=None, detected_lang=None):
    """Format a single recognition result line."""
    timestamp = format_time(offset)
    line = f"[{timestamp}]"
    if detected_lang:
        line += f" [{detected_lang}]"
    if speaker_id is not None:
        line += f" Speaker {speaker_id}:"
    else:
        line += ":"
    return f"{line} {text}"


def create_wav(audio_data, sample_rate=16000, bits_per_sample=16, channels=1):
    """Create a WAV file from raw PCM audio data."""
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    buf = io.BytesIO()
    buf.write(b'RIFF')
    buf.write(struct.pack('<I', 36 + len(audio_data)))
    buf.write(b'WAVE')
    buf.write(b'fmt ')
    buf.write(struct.pack('<I', 16))
    buf.write(struct.pack('<H', 1))  # PCM
    buf.write(struct.pack('<H', channels))
    buf.write(struct.pack('<I', sample_rate))
    buf.write(struct.pack('<I', byte_rate))
    buf.write(struct.pack('<H', block_align))
    buf.write(struct.pack('<H', bits_per_sample))
    buf.write(b'data')
    buf.write(struct.pack('<I', len(audio_data)))
    buf.write(audio_data)
    return buf.getvalue()


def apply_fade_in(audio_data, fade_samples=1600):
    """Apply fade-in to eliminate initial clicking (1600 samples = 100ms at 16kHz)."""
    if len(audio_data) < fade_samples * 2:
        return audio_data
    samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float64)
    for i in range(fade_samples):
        p = i / fade_samples
        samples[i] *= p * p * (3.0 - 2.0 * p)  # smoothstep
    return np.clip(samples, -32768, 32767).astype(np.int16).tobytes()


def apply_crossfade(existing, new_audio, crossfade_samples=2400):
    """Apply crossfade between audio chunks (2400 samples = 150ms at 16kHz)."""
    cf_bytes = crossfade_samples * 2
    if len(existing) < cf_bytes or len(new_audio) < cf_bytes:
        return existing + new_audio
    ex = np.frombuffer(existing, dtype=np.int16)
    nw = np.frombuffer(new_audio, dtype=np.int16)
    out_len = len(ex) + len(nw) - crossfade_samples
    out = np.zeros(out_len, dtype=np.float64)
    out[:len(ex) - crossfade_samples] = ex[:-crossfade_samples]
    for i in range(crossfade_samples):
        p = i / crossfade_samples
        sp = p * p * (3.0 - 2.0 * p)
        fade_out = np.cos(sp * np.pi / 2.0)
        fade_in = np.sin(sp * np.pi / 2.0)
        idx = len(ex) - crossfade_samples + i
        out[idx] = ex[idx] * fade_out + nw[i] * fade_in
    out[len(ex):] = nw[crossfade_samples:]
    return np.clip(out, -32768, 32767).astype(np.int16).tobytes()
