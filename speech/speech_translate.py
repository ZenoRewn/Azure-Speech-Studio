"""Tab 3: Speech Translation — SocketIO event handlers."""

import os
import azure.cognitiveservices.speech as speechsdk
from sessions import sessions, UPLOAD_DIR
from config import TRANSLATION_TARGET_LANGUAGES


def register(socketio):
    """Register speech translation SocketIO events."""

    @socketio.on("st:start_mic")
    def handle_start_mic(data):
        from flask import request
        sid = request.sid

        config = data.get("config", {})
        speech_key = config.get("speech_key", "")
        speech_region = config.get("speech_region", "")
        source_lang = config.get("language", "zh-CN")
        target_langs = config.get("target_languages", ["English"])

        if not speech_key or not speech_region:
            socketio.emit("st:status", {
                "type": "error", "message": "Missing Azure Speech Key or Region."
            }, to=sid)
            return

        target_codes = [TRANSLATION_TARGET_LANGUAGES[t] for t in target_langs
                        if t in TRANSLATION_TARGET_LANGUAGES]
        if not target_codes:
            socketio.emit("st:status", {
                "type": "error", "message": "No valid target languages selected."
            }, to=sid)
            return

        translation_config = speechsdk.translation.SpeechTranslationConfig(
            subscription=speech_key, region=speech_region,
            speech_recognition_language=source_lang,
            target_languages=target_codes)

        # PushAudioInputStream for browser mic
        push_stream = speechsdk.audio.PushAudioInputStream(
            stream_format=speechsdk.audio.AudioStreamFormat(
                samples_per_second=16000, bits_per_sample=16, channels=1))
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

        recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=translation_config, audio_config=audio_config)

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                socketio.emit("st:result", {
                    "text": evt.result.text,
                    "translations": dict(evt.result.translations),
                    "final": True,
                }, to=sid)

        recognizer.recognized.connect(on_recognized)
        recognizer.start_continuous_recognition()

        state = sessions.get(sid)
        state["st_recognizer"] = recognizer
        state["st_push_stream"] = push_stream

        socketio.emit("st:status", {
            "type": "info", "message": "Listening... Speak now."
        }, to=sid)

    @socketio.on("st:mic_audio")
    def handle_mic_audio(data):
        from flask import request
        sid = request.sid
        state = sessions.get(sid)
        push_stream = state.get("st_push_stream")
        if push_stream and isinstance(data, (bytes, bytearray)):
            push_stream.write(bytes(data))

    @socketio.on("st:stop_mic")
    def handle_stop_mic():
        from flask import request
        sid = request.sid
        state = sessions.get(sid)

        push_stream = state.pop("st_push_stream", None)
        if push_stream:
            push_stream.close()

        recognizer = state.pop("st_recognizer", None)
        if recognizer:
            try:
                recognizer.stop_continuous_recognition()
            except Exception:
                pass

        socketio.emit("st:status", {
            "type": "success", "message": "Translation stopped."
        }, to=sid)

    @socketio.on("st:start_file")
    def handle_start_file(data):
        from flask import request
        sid = request.sid

        config = data.get("config", {})
        speech_key = config.get("speech_key", "")
        speech_region = config.get("speech_region", "")
        source_lang = config.get("language", "zh-CN")
        target_langs = config.get("target_languages", ["English"])
        temp_id = data.get("temp_id", "")

        if not speech_key or not speech_region:
            socketio.emit("st:status", {
                "type": "error", "message": "Missing Azure Speech Key or Region."
            }, to=sid)
            return

        file_path = os.path.join(UPLOAD_DIR, temp_id)
        if not os.path.exists(file_path):
            socketio.emit("st:status", {
                "type": "error", "message": "Uploaded file not found."
            }, to=sid)
            return

        target_codes = [TRANSLATION_TARGET_LANGUAGES[t] for t in target_langs
                        if t in TRANSLATION_TARGET_LANGUAGES]

        translation_config = speechsdk.translation.SpeechTranslationConfig(
            subscription=speech_key, region=speech_region,
            speech_recognition_language=source_lang,
            target_languages=target_codes)

        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=translation_config, audio_config=audio_config)

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                socketio.emit("st:result", {
                    "text": evt.result.text,
                    "translations": dict(evt.result.translations),
                    "final": True,
                }, to=sid)

        def on_done(evt):
            socketio.emit("st:done", {}, to=sid)
            socketio.emit("st:status", {
                "type": "success", "message": "Translation complete."
            }, to=sid)
            # Cleanup session state
            state = sessions.get(sid)
            state.pop("st_recognizer", None)
            try:
                os.unlink(file_path)
            except Exception:
                pass

        # Store recognizer in session to prevent garbage collection
        state = sessions.get(sid)
        state["st_recognizer"] = recognizer

        recognizer.recognized.connect(on_recognized)
        recognizer.session_stopped.connect(on_done)
        recognizer.canceled.connect(on_done)
        recognizer.start_continuous_recognition()

        socketio.emit("st:status", {
            "type": "info", "message": "Translating file..."
        }, to=sid)
