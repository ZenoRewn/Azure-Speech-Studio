"""Tab 2: Fast Transcription (file only) — uses Azure Fast Transcription REST API."""

import os
import json
import requests
from sessions import sessions, UPLOAD_DIR


def _call_fast_transcription(speech_key, speech_region, file_path,
                              locales, diarization, max_speakers,
                              phrase_list=None):
    """Call Azure Fast Transcription REST API."""
    url = (f"https://{speech_region}.api.cognitive.microsoft.com/"
           f"speechtotext/transcriptions:transcribe?api-version=2025-10-15")

    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
    }

    definition = {}
    if locales:
        definition["locales"] = locales
    if diarization:
        definition["diarization"] = {
            "enabled": True,
            "maxSpeakers": max_speakers,
        }
    if phrase_list:
        definition["phraseList"] = {"phrases": phrase_list}

    with open(file_path, "rb") as audio_file:
        files = {
            "audio": (os.path.basename(file_path), audio_file),
            "definition": (None, json.dumps(definition), "application/json"),
        }
        response = requests.post(url, headers=headers, files=files, timeout=600)

    return response


def _format_phrase_line(phrase, diarization):
    """Format a single phrase from the API response into a display line."""
    offset_s = (phrase.get("offsetMilliseconds", 0)) / 1000
    duration_s = (phrase.get("durationMilliseconds", 0)) / 1000
    end_s = offset_s + duration_s

    # Format timestamp
    def fmt_time(s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = int(s % 60)
        return f"{h}:{m:02d}:{sec:02d}"

    line = f"[{fmt_time(offset_s)} - {fmt_time(end_s)}]"

    locale = phrase.get("locale", "")
    if locale:
        line += f" [{locale}]"

    if diarization:
        speaker = phrase.get("speaker")
        if speaker is not None:
            line += f" Speaker {speaker}:"
        else:
            line += ":"
    else:
        line += ":"

    confidence = phrase.get("confidence")
    text = phrase.get("text", "")
    line += f" {text}"
    if confidence is not None:
        line += f" ({confidence:.0%})"

    return line


def register(socketio):
    """Register fast transcription SocketIO events."""

    @socketio.on("ft:start_file")
    def handle_start_file(data):
        from flask import request
        sid = request.sid

        config = data.get("config", {})
        speech_key = config.get("speech_key", "")
        speech_region = config.get("speech_region", "")
        language = config.get("language", "zh-CN")
        diarization = config.get("diarization", False)
        max_speakers = config.get("max_speakers", 4)
        lang_detect_mode = config.get("lang_detect", "Off")
        selected_languages = config.get("languages", [language])
        phrase_list = config.get("phrase_list", [])
        temp_id = data.get("temp_id", "")

        if not speech_key or not speech_region:
            socketio.emit("ft:status", {
                "type": "error", "message": "Missing Azure Speech Key or Region."
            }, to=sid)
            return

        file_path = os.path.join(UPLOAD_DIR, temp_id)
        if not os.path.exists(file_path):
            socketio.emit("ft:status", {
                "type": "error", "message": "Uploaded file not found."
            }, to=sid)
            return

        # Determine locales for the API
        if lang_detect_mode != "Off" and selected_languages:
            locales = selected_languages
        else:
            locales = [language]

        socketio.emit("ft:status", {
            "type": "info", "message": "Calling Fast Transcription API..."
        }, to=sid)

        def _run():
            try:
                resp = _call_fast_transcription(
                    speech_key, speech_region, file_path,
                    locales, diarization, max_speakers,
                    phrase_list=phrase_list)

                if resp.status_code != 200:
                    error_msg = resp.text
                    try:
                        error_data = resp.json()
                        error_msg = error_data.get("error", {}).get("message", resp.text)
                    except Exception:
                        pass
                    socketio.emit("ft:status", {
                        "type": "error",
                        "message": f"API error ({resp.status_code}): {error_msg}"
                    }, to=sid)
                    return

                result = resp.json()

                # Emit each phrase as a result line
                phrases = result.get("phrases", [])
                for phrase in phrases:
                    line = _format_phrase_line(phrase, diarization)
                    socketio.emit("ft:result", {
                        "line": line, "final": True
                    }, to=sid)

                # Emit combined text
                combined = result.get("combinedPhrases", [])
                if combined:
                    combined_text = combined[0].get("text", "")
                    socketio.emit("ft:combined", {
                        "text": combined_text
                    }, to=sid)

                duration_ms = result.get("durationMilliseconds", 0)
                duration_s = duration_ms / 1000
                socketio.emit("ft:done", {}, to=sid)
                socketio.emit("ft:status", {
                    "type": "success",
                    "message": f"Transcription complete. (duration: {duration_s:.1f}s, {len(phrases)} phrases)"
                }, to=sid)

            except requests.exceptions.Timeout:
                socketio.emit("ft:status", {
                    "type": "error", "message": "Request timed out."
                }, to=sid)
            except Exception as e:
                socketio.emit("ft:status", {
                    "type": "error", "message": f"Error: {e}"
                }, to=sid)
            finally:
                try:
                    os.unlink(file_path)
                except Exception:
                    pass

        # Run in background to avoid blocking the SocketIO handler
        socketio.start_background_task(_run)

