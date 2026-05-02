"""Whisper Batch transcription via Azure Speech Batch API v3.2 with Whisper model.

Flow: find Whisper base model -> submit job -> poll -> fetch results.
Emits progress events over SocketIO: 'wb:progress' / 'wb:done' / 'wb:error'.
"""

import re
import threading
import time
import requests

from flask import request
from sessions import sessions


POLL_INTERVAL_SEC = 8
MAX_WAIT_SEC = 10 * 60
_DURATION_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?")


def _parse_ms(value):
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


def _base(region):
    return f"https://{region}.api.cognitive.microsoft.com"


def _find_whisper_model(speech_key, speech_region):
    """Paginate Azure base models, return the first Whisper model's self URL."""
    headers = {"Ocp-Apim-Subscription-Key": speech_key}
    next_url = f"{_base(speech_region)}/speechtotext/models/base?api-version=2024-11-15&top=200"

    while next_url:
        resp = requests.get(next_url, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        for model in data.get("values", []) or []:
            name = (model.get("displayName") or "").lower()
            if "whisper" in name:
                return model.get("self"), model.get("displayName")
        next_url = data.get("@nextLink")
    return None, None


def _submit_job(speech_key, speech_region, audio_url, locale, model_self):
    """Submit a new batch transcription job, return its polling URL."""
    url = f"{_base(speech_region)}/speechtotext/v3.2/transcriptions"
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
        "Content-Type": "application/json",
    }
    body = {
        "contentUrls": [audio_url],
        "locale": locale or "en-US",
        "displayName": f"Whisper-{int(time.time())}",
        "model": {"self": model_self},
    }
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json().get("self")


def _fetch_results(speech_key, poll_data):
    """Given a Succeeded job payload, fetch the transcription result file."""
    headers = {"Ocp-Apim-Subscription-Key": speech_key}
    files_url = (poll_data.get("links") or {}).get("files")
    if not files_url:
        return []

    resp = requests.get(files_url, headers=headers, timeout=60)
    resp.raise_for_status()
    for f in resp.json().get("values", []) or []:
        if f.get("kind") == "Transcription":
            content_url = (f.get("links") or {}).get("contentUrl")
            if not content_url:
                continue
            cr = requests.get(content_url, timeout=120)
            cr.raise_for_status()
            result = cr.json()
            segments = []
            for p in result.get("recognizedPhrases", []) or []:
                segments.append({
                    "text": p.get("display", ""),
                    "offset_ms": _parse_ms(p.get("offset")),
                    "duration_ms": _parse_ms(p.get("duration")),
                    "confidence": p.get("confidence"),
                    "speaker": (f"Speaker {p['speaker']}"
                                if p.get("speaker") is not None else None),
                })
            if not segments:
                for c in result.get("combinedRecognizedPhrases", []) or []:
                    if c.get("display"):
                        segments.append({"text": c["display"]})
            return segments
    return []


def _run(socketio, sid, speech_key, speech_region, audio_url, locale, cancel_event):
    def emit(event, payload):
        socketio.emit(event, payload, to=sid)

    try:
        emit("wb:progress", {"phase": "finding_model", "text": "Finding Whisper model..."})
        model_self, model_name = _find_whisper_model(speech_key, speech_region)
        if not model_self:
            emit("wb:error", {"message": "No Whisper model found in this region."})
            return
        emit("wb:progress", {"phase": "found_model", "text": f"Found: {model_name}"})

        if cancel_event.is_set():
            return

        emit("wb:progress", {"phase": "submitting", "text": "Submitting batch job..."})
        job_url = _submit_job(speech_key, speech_region, audio_url, locale, model_self)
        if not job_url:
            emit("wb:error", {"message": "Failed to submit job."})
            return

        headers = {"Ocp-Apim-Subscription-Key": speech_key}
        start = time.time()
        while not cancel_event.is_set() and time.time() - start < MAX_WAIT_SEC:
            time.sleep(POLL_INTERVAL_SEC)
            poll = requests.get(job_url, headers=headers, timeout=60)
            if poll.status_code != 200:
                continue
            data = poll.json()
            status = data.get("status", "")
            emit("wb:progress", {"phase": "polling", "text": f"Status: {status}"})

            if status == "Succeeded":
                emit("wb:progress", {"phase": "fetching", "text": "Downloading results..."})
                segments = _fetch_results(speech_key, data)
                emit("wb:done", {"segments": segments})
                return
            if status == "Failed":
                err = ((data.get("properties") or {}).get("error") or {}).get("message",
                       "Unknown error")
                emit("wb:error", {"message": f"Job failed: {err}"})
                return

        if cancel_event.is_set():
            emit("wb:progress", {"phase": "cancelled", "text": "Cancelled."})
        else:
            emit("wb:error", {"message": "Job timed out after 10 minutes."})
    except requests.HTTPError as e:
        emit("wb:error", {"message": f"HTTP error: {e.response.status_code} {e.response.text[:300]}"})
    except Exception as e:
        emit("wb:error", {"message": f"{type(e).__name__}: {e}"})


def register(socketio):
    @socketio.on("wb:start")
    def on_start(payload):
        sid = request.sid
        speech_key = (payload or {}).get("speech_key", "")
        speech_region = (payload or {}).get("speech_region", "")
        audio_url = (payload or {}).get("audio_url", "").strip()
        locale = (payload or {}).get("locale", "en-US")

        if not speech_key or not speech_region:
            socketio.emit("wb:error", {"message": "Missing Azure credentials."}, to=sid)
            return
        if not audio_url:
            socketio.emit("wb:error", {"message": "Missing audio URL."}, to=sid)
            return

        # Cancel any prior task for this sid
        prev = sessions.pop(sid, "wb_cancel")
        if prev:
            prev.set()

        cancel = threading.Event()
        sessions.set(sid, "wb_cancel", cancel)
        thread = threading.Thread(
            target=_run,
            args=(socketio, sid, speech_key, speech_region, audio_url, locale, cancel),
            daemon=True,
        )
        thread.start()

    @socketio.on("wb:stop")
    def on_stop(_payload=None):
        sid = request.sid
        cancel = sessions.pop(sid, "wb_cancel")
        if cancel:
            cancel.set()
