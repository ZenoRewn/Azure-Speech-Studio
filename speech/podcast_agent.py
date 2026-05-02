"""Podcast Agent via Azure Podcast API.

PUT /podcast/generations/{id} -> poll operation-location -> fetch output.
Emits 'pa:progress' / 'pa:done' / 'pa:error' over SocketIO.
"""

import threading
import time
import uuid
import requests

from flask import request
from sessions import sessions


API_VERSION = "2026-01-01-preview"
POLL_INTERVAL_SEC = 10
MAX_WAIT_SEC = 30 * 60  # 30 minutes


def _base(region):
    return f"https://{region}.api.cognitive.microsoft.com"


def _run(socketio, sid, speech_key, speech_region, config, cancel_event):
    def emit(event, payload):
        socketio.emit(event, payload, to=sid)

    podcast_id = f"podcast-{uuid.uuid4().hex[:12]}"
    try:
        url = f"{_base(speech_region)}/podcast/generations/{podcast_id}?api-version={API_VERSION}"
        headers = {
            "Ocp-Apim-Subscription-Key": speech_key,
            "Content-Type": "application/json",
            "Operation-Id": str(uuid.uuid4()),
        }

        body = {
            "locale": config.get("locale", "en-US"),
            "host": config.get("host_type", "TwoHosts"),
            "content": {
                "text": config.get("content", ""),
                "fileFormat": "Txt",
            },
            "displayName": config.get("title") or podcast_id,
            "scriptGeneration": {
                "style": config.get("style", "Default"),
                "length": config.get("length", "Medium"),
            },
        }

        emit("pa:progress", {"text": "Submitting podcast generation..."})
        resp = requests.put(url, headers=headers, json=body, timeout=120)
        if resp.status_code >= 400:
            emit("pa:error", {"message": f"Submit failed: {resp.status_code} {resp.text[:300]}"})
            return

        operation_url = resp.headers.get("operation-location")
        emit("pa:progress", {"text": "Podcast generation in progress...", "podcast_id": podcast_id})
        start = time.time()
        poll_headers = {"Ocp-Apim-Subscription-Key": speech_key}

        while not cancel_event.is_set() and time.time() - start < MAX_WAIT_SEC:
            time.sleep(POLL_INTERVAL_SEC)
            if operation_url:
                op = requests.get(operation_url, headers=poll_headers, timeout=60)
                if op.status_code >= 400:
                    continue
                data = op.json()
                status = (data.get("status") or "").lower()
                emit("pa:progress", {"text": f"Status: {status}"})
                if status == "succeeded":
                    break
                if status == "failed":
                    emit("pa:error", {"message": f"Generation failed: {data}"})
                    return
            else:
                poll = requests.get(url, headers=poll_headers, timeout=60)
                if poll.status_code >= 400:
                    continue
                data = poll.json()
                status = (data.get("status") or "").lower()
                emit("pa:progress", {"text": f"Status: {status}"})
                if status == "succeeded":
                    break
                if status == "failed":
                    emit("pa:error", {"message": f"Generation failed: {data}"})
                    return

        if cancel_event.is_set():
            emit("pa:progress", {"text": "Cancelled."})
            return

        # Fetch final result
        gen = requests.get(url, headers=poll_headers, timeout=60)
        if gen.status_code < 400:
            data = gen.json()
            output = data.get("output") or {}
            emit("pa:done", {
                "podcast_id": podcast_id,
                "audio_url": output.get("audioFileUrl"),
                "transcript_url": output.get("transcriptUrl"),
                "script_url": output.get("scriptUrl"),
            })
        else:
            emit("pa:error", {"message": f"Fetch result failed: {gen.status_code}"})
    except Exception as e:
        emit("pa:error", {"message": f"{type(e).__name__}: {e}"})


def register(socketio):
    @socketio.on("pa:start")
    def on_start(payload):
        sid = request.sid
        payload = payload or {}
        speech_key = payload.get("speech_key", "")
        speech_region = payload.get("speech_region", "")
        content = (payload.get("content") or "").strip()

        if not speech_key or not speech_region:
            socketio.emit("pa:error", {"message": "Missing Azure credentials."}, to=sid)
            return
        if not content:
            socketio.emit("pa:error", {"message": "Missing content."}, to=sid)
            return

        prev = sessions.pop(sid, "pa_cancel")
        if prev:
            prev.set()
        cancel = threading.Event()
        sessions.set(sid, "pa_cancel", cancel)

        config = {
            "content": content,
            "locale": payload.get("locale", "en-US"),
            "host_type": payload.get("host_type", "TwoHosts"),
            "style": payload.get("style", "Default"),
            "length": payload.get("length", "Medium"),
            "title": payload.get("title"),
        }
        threading.Thread(
            target=_run,
            args=(socketio, sid, speech_key, speech_region, config, cancel),
            daemon=True,
        ).start()

    @socketio.on("pa:stop")
    def on_stop(_payload=None):
        sid = request.sid
        cancel = sessions.pop(sid, "pa_cancel")
        if cancel:
            cancel.set()
