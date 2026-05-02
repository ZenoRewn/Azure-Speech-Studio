"""MAI-Transcribe-1 REST API wrapper (25-language enhanced transcription)."""

import json
import re
import requests


API_VERSION = "2025-10-15"


def call_mai_transcribe(speech_key, speech_region, audio_bytes, audio_filename,
                        locales, enable_diarization=False, max_speakers=4,
                        phrase_list=None):
    """Call Azure MAI-Transcribe-1 model via the Speech-to-Text transcribe endpoint."""
    url = (f"https://{speech_region}.api.cognitive.microsoft.com/"
           f"speechtotext/transcriptions:transcribe?api-version={API_VERSION}")

    definition = {
        "locales": locales,
        "enhancedMode": {
            "enabled": True,
            "task": "transcribe",
            "model": "mai-transcribe-1",
        },
    }
    if enable_diarization:
        definition["diarization"] = {"speakers": {"maxCount": max_speakers}}
    if phrase_list:
        definition["customPhrases"] = [{"phrase": p} for p in phrase_list if p]

    headers = {"Ocp-Apim-Subscription-Key": speech_key}
    files = {
        "audio": (audio_filename or "audio.wav", audio_bytes),
        "definition": (None, json.dumps(definition), "application/json"),
    }
    return requests.post(url, headers=headers, files=files, timeout=300)


_DURATION_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?")


def parse_duration_ms(value):
    """Parse ISO 8601 duration (PT...) or tick count to milliseconds."""
    if not value:
        return 0
    m = _DURATION_RE.fullmatch(str(value))
    if m:
        h = int(m.group(1) or 0)
        minute = int(m.group(2) or 0)
        s = float(m.group(3) or 0)
        return int((h * 3600 + minute * 60 + s) * 1000)
    try:
        return int(int(value) / 10000)
    except (TypeError, ValueError):
        return 0


def normalize_response(data):
    """Flatten MAI-Transcribe response into a uniform segments list."""
    segments = []
    for phrase in data.get("phrases", []) or []:
        segments.append({
            "text": phrase.get("text", ""),
            "offset_ms": parse_duration_ms(phrase.get("offset")),
            "duration_ms": parse_duration_ms(phrase.get("duration")),
            "locale": phrase.get("locale"),
            "confidence": phrase.get("confidence"),
            "speaker": (f"Speaker {phrase['speaker']}"
                        if phrase.get("speaker") is not None else None),
        })
    combined = [c.get("text", "") for c in data.get("combinedPhrases", []) or []]
    return {"segments": segments, "combined_text": " ".join(filter(None, combined))}
