"""Video Translation via Azure Video Translation REST API.

Flow: PUT /videotranslation/translations/{id} -> poll -> report output URLs.
Emits 'vt:progress' / 'vt:done' / 'vt:error' over SocketIO.
"""

import threading
import time
import uuid
import requests

from flask import request
from sessions import sessions


API_VERSION = "2024-05-20-preview"
POLL_INTERVAL_SEC = 10
MAX_WAIT_SEC = 60 * 60  # 1 hour


def _base(region):
    return f"https://{region}.api.cognitive.microsoft.com"


def _submit(speech_key, speech_region, translation_id, body):
    url = f"{_base(speech_region)}/videotranslation/translations/{translation_id}?api-version={API_VERSION}"
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
        "Content-Type": "application/json",
    }
    resp = requests.put(url, headers=headers, json=body, timeout=120)
    return url, resp


def _poll(speech_key, url):
    headers = {"Ocp-Apim-Subscription-Key": speech_key}
    return requests.get(url, headers=headers, timeout=60)


def _run(socketio, sid, speech_key, speech_region, video_url, config, cancel_event):
    def emit(event, payload):
        socketio.emit(event, payload, to=sid)

    translation_id = f"vt-{uuid.uuid4().hex[:12]}"
    try:
        emit("vt:progress", {"text": f"Submitting translation {translation_id}..."})

        body = {
            "displayName": translation_id,
            "input": {
                "sourceUrl": video_url,
                "sourceLocale": config.get("source_locale"),
                "targetLocale": config.get("target_locale"),
                "voiceKind": config.get("voice_kind") or "PlatformVoice",
            },
            "properties": {},
        }
        if config.get("speaker_count"):
            body["speakerCount"] = int(config["speaker_count"])
        if config.get("subtitle_max_chars"):
            body["subtitleMaxCharCountPerSegment"] = int(config["subtitle_max_chars"])
        if "export_subtitle_in_video" in config:
            body["exportSubtitleInVideo"] = bool(config["export_subtitle_in_video"])

        url, resp = _submit(speech_key, speech_region, translation_id, body)
        if resp.status_code >= 400:
            emit("vt:error", {"message": f"Submit failed: {resp.status_code} {resp.text[:300]}"})
            return

        emit("vt:progress", {"text": "Translation in progress..."})
        start = time.time()
        while not cancel_event.is_set() and time.time() - start < MAX_WAIT_SEC:
            time.sleep(POLL_INTERVAL_SEC)
            poll = _poll(speech_key, url)
            if poll.status_code >= 400:
                emit("vt:error", {"message": f"Poll failed: {poll.status_code} {poll.text[:300]}"})
                return
            data = poll.json()
            status = (data.get("status") or "").lower()
            emit("vt:progress", {"text": f"Status: {status}"})

            if status == "succeeded":
                output = data.get("output") or {}
                emit("vt:done", {
                    "translation_id": translation_id,
                    "video_url": output.get("translatedVideoUrl"),
                    "subtitle_url": output.get("translatedSubtitleUrl"),
                    "source_locale": config.get("source_locale"),
                    "target_locale": config.get("target_locale"),
                })
                return
            if status == "failed":
                err = data.get("error") or (data.get("properties") or {}).get("error")
                emit("vt:error", {"message": f"Translation failed: {err}"})
                return

        if cancel_event.is_set():
            emit("vt:progress", {"text": "Cancelled."})
        else:
            emit("vt:error", {"message": "Translation timed out."})
    except Exception as e:
        emit("vt:error", {"message": f"{type(e).__name__}: {e}"})


def register(socketio):
    @socketio.on("vt:start")
    def on_start(payload):
        sid = request.sid
        payload = payload or {}
        speech_key = payload.get("speech_key", "")
        speech_region = payload.get("speech_region", "")
        video_url = payload.get("video_url", "").strip()

        if not speech_key or not speech_region:
            socketio.emit("vt:error", {"message": "Missing Azure credentials."}, to=sid)
            return
        if not video_url:
            socketio.emit("vt:error", {"message": "Missing video URL."}, to=sid)
            return
        if not payload.get("source_locale") or not payload.get("target_locale"):
            socketio.emit("vt:error", {"message": "Missing source/target locale."}, to=sid)
            return

        prev = sessions.pop(sid, "vt_cancel")
        if prev:
            prev.set()
        cancel = threading.Event()
        sessions.set(sid, "vt_cancel", cancel)

        config = {
            "source_locale": payload["source_locale"],
            "target_locale": payload["target_locale"],
            "voice_kind": payload.get("voice_kind", "PlatformVoice"),
            "speaker_count": payload.get("speaker_count"),
            "subtitle_max_chars": payload.get("subtitle_max_chars"),
            "export_subtitle_in_video": payload.get("export_subtitle_in_video"),
        }
        threading.Thread(
            target=_run,
            args=(socketio, sid, speech_key, speech_region, video_url, config, cancel),
            daemon=True,
        ).start()

    @socketio.on("vt:stop")
    def on_stop(_payload=None):
        sid = request.sid
        cancel = sessions.pop(sid, "vt_cancel")
        if cancel:
            cancel.set()
