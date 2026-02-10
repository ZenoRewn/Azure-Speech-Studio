"""Tab 4: Live Interpreter — SocketIO event handlers."""

import os
import base64
import azure.cognitiveservices.speech as speechsdk
from sessions import sessions, UPLOAD_DIR
from config import TRANSLATION_TARGET_LANGUAGES, LI_STANDARD_VOICES
from speech.audio_utils import create_wav, apply_fade_in, apply_crossfade


def _build_translation_config(speech_key, speech_region, target_code,
                               voice_mode, standard_voices):
    """Build TranslationConfig for Live Interpreter."""
    v2_endpoint = f"wss://{speech_region}.stt.speech.microsoft.com/speech/universal/v2"
    translation_config = speechsdk.translation.SpeechTranslationConfig(
        endpoint=v2_endpoint, subscription=speech_key)
    translation_config.add_target_language(target_code)
    if voice_mode.startswith("Personal Voice"):
        translation_config.voice_name = "personal-voice"
    else:
        translation_config.voice_name = standard_voices.get(
            target_code, "en-US-AvaMultilingualNeural")
    return translation_config


def register(socketio):
    """Register live interpreter SocketIO events."""

    @socketio.on("li:start_mic")
    def handle_start_mic(data):
        from flask import request
        sid = request.sid

        config = data.get("config", {})
        speech_key = config.get("speech_key", "")
        speech_region = config.get("speech_region", "")
        target_language = config.get("target_language", "English")
        voice_mode = config.get("voice_mode", "Standard TTS Voice")

        if not speech_key or not speech_region:
            socketio.emit("li:status", {
                "type": "error", "message": "Missing Azure Speech Configuration."
            }, to=sid)
            return

        target_code = TRANSLATION_TARGET_LANGUAGES.get(target_language, "en")

        translation_config = _build_translation_config(
            speech_key, speech_region, target_code, voice_mode, LI_STANDARD_VOICES)
        auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig()

        # PushAudioInputStream for browser mic
        push_stream = speechsdk.audio.PushAudioInputStream(
            stream_format=speechsdk.audio.AudioStreamFormat(
                samples_per_second=16000, bits_per_sample=16, channels=1))
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

        recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=translation_config,
            audio_config=audio_config,
            auto_detect_source_language_config=auto_detect_config)

        # Audio buffers for WAV download
        audio_buffers = []
        state = sessions.get(sid)
        state["li_synth_audio"] = audio_buffers

        def on_recognizing(evt):
            if evt.result.reason == speechsdk.ResultReason.TranslatingSpeech:
                auto_lang = evt.result.properties.get(
                    speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult, "")
                socketio.emit("li:result", {
                    "type": "interim",
                    "language": auto_lang,
                    "text": evt.result.text,
                    "translations": dict(evt.result.translations),
                }, to=sid)

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                auto_lang = evt.result.properties.get(
                    speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult, "")
                socketio.emit("li:result", {
                    "type": "final",
                    "language": auto_lang,
                    "text": evt.result.text,
                    "translations": dict(evt.result.translations),
                }, to=sid)

        def on_synthesizing(evt):
            if evt.result.audio and len(evt.result.audio) > 0:
                audio_buffers.append(evt.result.audio)
                # Send audio to browser for playback
                audio_b64 = base64.b64encode(evt.result.audio).decode("utf-8")
                socketio.emit("li:synth_audio", {
                    "audio": audio_b64,
                    "sample_rate": 16000,
                }, to=sid)

        def on_canceled(evt):
            if evt.result.reason == speechsdk.ResultReason.Canceled:
                cancellation = evt.result.cancellation_details
                socketio.emit("li:result", {
                    "type": "error",
                    "text": f"Canceled: {cancellation.reason} — {cancellation.error_details}",
                }, to=sid)

        recognizer.recognizing.connect(on_recognizing)
        recognizer.recognized.connect(on_recognized)
        recognizer.synthesizing.connect(on_synthesizing)
        recognizer.canceled.connect(on_canceled)
        recognizer.start_continuous_recognition()

        state["li_recognizer"] = recognizer
        state["li_push_stream"] = push_stream

        socketio.emit("li:status", {
            "type": "info",
            "message": "Listening... Speak in any language. Auto-detecting source language."
        }, to=sid)

    @socketio.on("li:mic_audio")
    def handle_mic_audio(data):
        from flask import request
        sid = request.sid
        state = sessions.get(sid)
        push_stream = state.get("li_push_stream")
        if push_stream and isinstance(data, (bytes, bytearray)):
            push_stream.write(bytes(data))

    @socketio.on("li:pause")
    def handle_pause():
        from flask import request
        sid = request.sid
        state = sessions.get(sid)
        recognizer = state.get("li_recognizer")
        if recognizer:
            recognizer.stop_continuous_recognition()
        socketio.emit("li:status", {
            "type": "warning", "message": "Paused — microphone muted."
        }, to=sid)

    @socketio.on("li:resume")
    def handle_resume():
        from flask import request
        sid = request.sid
        state = sessions.get(sid)
        recognizer = state.get("li_recognizer")
        if recognizer:
            recognizer.start_continuous_recognition()
        socketio.emit("li:status", {
            "type": "info",
            "message": "Resumed — listening..."
        }, to=sid)

    @socketio.on("li:stop_mic")
    def handle_stop_mic():
        from flask import request
        sid = request.sid
        state = sessions.get(sid)

        push_stream = state.pop("li_push_stream", None)
        if push_stream:
            push_stream.close()

        recognizer = state.pop("li_recognizer", None)
        if recognizer:
            try:
                recognizer.stop_continuous_recognition()
            except Exception:
                pass

        socketio.emit("li:status", {
            "type": "success", "message": "Live interpreter stopped."
        }, to=sid)

    @socketio.on("li:download_audio")
    def handle_download_audio():
        """Build WAV from accumulated synth audio and send download URL."""
        from flask import request
        sid = request.sid
        state = sessions.get(sid)
        audio_buffers = state.get("li_synth_audio", [])

        if not audio_buffers:
            socketio.emit("li:status", {
                "type": "warning", "message": "No synthesized audio available."
            }, to=sid)
            return

        # Apply crossfade
        combined = apply_fade_in(audio_buffers[0])
        for chunk in audio_buffers[1:]:
            combined = apply_crossfade(combined, chunk)

        if len(combined) > 0:
            wav_bytes = create_wav(combined)
            wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")
            socketio.emit("li:download_ready", {
                "audio": wav_b64,
                "filename": "translated_audio.wav",
            }, to=sid)

    @socketio.on("li:start_file")
    def handle_start_file(data):
        from flask import request
        sid = request.sid

        config = data.get("config", {})
        speech_key = config.get("speech_key", "")
        speech_region = config.get("speech_region", "")
        target_language = config.get("target_language", "English")
        voice_mode = config.get("voice_mode", "Standard TTS Voice")
        temp_id = data.get("temp_id", "")

        if not speech_key or not speech_region:
            socketio.emit("li:status", {
                "type": "error", "message": "Missing Azure Speech Configuration."
            }, to=sid)
            return

        file_path = os.path.join(UPLOAD_DIR, temp_id)
        if not os.path.exists(file_path):
            socketio.emit("li:status", {
                "type": "error", "message": "Uploaded file not found."
            }, to=sid)
            return

        target_code = TRANSLATION_TARGET_LANGUAGES.get(target_language, "en")

        translation_config = _build_translation_config(
            speech_key, speech_region, target_code, voice_mode, LI_STANDARD_VOICES)
        auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig()
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)

        recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=translation_config,
            audio_config=audio_config,
            auto_detect_source_language_config=auto_detect_config)

        audio_buffers = []

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                auto_lang = evt.result.properties.get(
                    speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult, "")
                socketio.emit("li:result", {
                    "type": "final",
                    "language": auto_lang,
                    "text": evt.result.text,
                    "translations": dict(evt.result.translations),
                }, to=sid)

        def on_synthesizing(evt):
            if evt.result.audio and len(evt.result.audio) > 0:
                audio_buffers.append(evt.result.audio)
                audio_b64 = base64.b64encode(evt.result.audio).decode("utf-8")
                socketio.emit("li:synth_audio", {
                    "audio": audio_b64,
                    "sample_rate": 16000,
                }, to=sid)

        def on_canceled(evt):
            if evt.result.reason == speechsdk.ResultReason.Canceled:
                cancellation = evt.result.cancellation_details
                socketio.emit("li:result", {
                    "type": "error",
                    "text": f"Canceled: {cancellation.reason} — {cancellation.error_details}",
                }, to=sid)

        def on_done(evt):
            # Build WAV from audio buffers
            if audio_buffers:
                combined = apply_fade_in(audio_buffers[0])
                for chunk in audio_buffers[1:]:
                    combined = apply_crossfade(combined, chunk)
                if len(combined) > 0:
                    wav_bytes = create_wav(combined)
                    wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")
                    socketio.emit("li:download_ready", {
                        "audio": wav_b64,
                        "filename": "translated_audio.wav",
                    }, to=sid)

            socketio.emit("li:done", {}, to=sid)
            socketio.emit("li:status", {
                "type": "success", "message": "Translation complete."
            }, to=sid)
            # Cleanup session state
            state = sessions.get(sid)
            state.pop("li_recognizer", None)
            try:
                os.unlink(file_path)
            except Exception:
                pass

        # Store recognizer in session to prevent garbage collection
        state = sessions.get(sid)
        state["li_recognizer"] = recognizer

        recognizer.recognized.connect(on_recognized)
        recognizer.synthesizing.connect(on_synthesizing)
        recognizer.canceled.connect(on_canceled)
        recognizer.session_stopped.connect(on_done)
        recognizer.canceled.connect(on_done)
        recognizer.start_continuous_recognition()

        socketio.emit("li:status", {
            "type": "info", "message": "Translating file..."
        }, to=sid)
