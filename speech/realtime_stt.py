"""Tab 1: Real-time Speech to Text — SocketIO event handlers."""

import azure.cognitiveservices.speech as speechsdk
from sessions import sessions
from speech.audio_utils import format_recognition_line


def _build_recognizer(speech_key, speech_region, language, diarization,
                      lang_detect_mode, selected_languages, audio_config,
                      phrase_list=None):
    """Build recognizer or transcriber based on options."""
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=speech_region)
    speech_config.speech_recognition_language = language

    auto_detect_config = None
    if selected_languages:
        if lang_detect_mode == "Continuous":
            speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
                "Continuous")
        auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
            languages=selected_languages)

    kwargs = dict(speech_config=speech_config, audio_config=audio_config)
    if auto_detect_config:
        kwargs["auto_detect_source_language_config"] = auto_detect_config

    if diarization:
        recognizer = speechsdk.transcription.ConversationTranscriber(**kwargs)
        is_diarization = True
    else:
        recognizer = speechsdk.SpeechRecognizer(**kwargs)
        is_diarization = False

    # Apply phrase list
    if phrase_list:
        phrase_grammar = speechsdk.PhraseListGrammar.from_recognizer(recognizer)
        for phrase in phrase_list:
            phrase_grammar.addPhrase(phrase)

    return recognizer, is_diarization


def register(socketio):
    """Register realtime STT SocketIO events."""

    @socketio.on("rt:start_mic")
    def handle_start_mic(data):
        sid = data.get("sid") or socketio.server.environ.get("REMOTE_ADDR", "")
        from flask import request
        sid = request.sid

        config = data.get("config", {})
        speech_key = config.get("speech_key", "")
        speech_region = config.get("speech_region", "")
        language = config.get("language", "zh-CN")
        diarization = config.get("diarization", False)
        lang_detect_mode = config.get("lang_detect", "At Start")
        selected_languages = config.get("languages", [language])

        if not speech_key or not speech_region:
            socketio.emit("rt:status", {
                "type": "error", "message": "Missing Azure Speech Key or Region."
            }, to=sid)
            return

        # Create PushAudioInputStream for browser mic audio
        push_stream = speechsdk.audio.PushAudioInputStream(
            stream_format=speechsdk.audio.AudioStreamFormat(
                samples_per_second=16000, bits_per_sample=16, channels=1))
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

        phrase_list = config.get("phrase_list", [])
        recognizer, is_diarization = _build_recognizer(
            speech_key, speech_region, language, diarization,
            lang_detect_mode, selected_languages, audio_config,
            phrase_list=phrase_list)

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
                detected_lang = evt.result.properties.get(
                    speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult, "") or None
                speaker_id = getattr(evt.result, 'speaker_id', None) if is_diarization else None
                line = format_recognition_line(
                    evt.result.offset, evt.result.text,
                    speaker_id=speaker_id, detected_lang=detected_lang)
                socketio.emit("rt:result", {"line": line, "final": True}, to=sid)

        if is_diarization:
            recognizer.transcribed.connect(on_recognized)
            recognizer.start_transcribing_async()
        else:
            recognizer.recognized.connect(on_recognized)
            recognizer.start_continuous_recognition()

        state = sessions.get(sid)
        state["rt_recognizer"] = recognizer
        state["rt_recognizer_is_diarization"] = is_diarization
        state["rt_push_stream"] = push_stream

        socketio.emit("rt:status", {
            "type": "info", "message": "Listening from microphone..."
        }, to=sid)

    @socketio.on("rt:mic_audio")
    def handle_mic_audio(data):
        from flask import request
        sid = request.sid
        state = sessions.get(sid)
        push_stream = state.get("rt_push_stream")
        if push_stream and isinstance(data, (bytes, bytearray)):
            push_stream.write(bytes(data))

    @socketio.on("rt:stop_mic")
    def handle_stop_mic():
        from flask import request
        sid = request.sid
        state = sessions.get(sid)

        push_stream = state.pop("rt_push_stream", None)
        if push_stream:
            push_stream.close()

        recognizer = state.pop("rt_recognizer", None)
        is_diarization = state.pop("rt_recognizer_is_diarization", False)
        if recognizer:
            try:
                if is_diarization:
                    recognizer.stop_transcribing_async().get()
                else:
                    recognizer.stop_continuous_recognition()
            except Exception:
                pass

        socketio.emit("rt:status", {
            "type": "success", "message": "Transcription stopped."
        }, to=sid)

    @socketio.on("rt:start_file")
    def handle_start_file(data):
        from flask import request
        sid = request.sid

        config = data.get("config", {})
        speech_key = config.get("speech_key", "")
        speech_region = config.get("speech_region", "")
        language = config.get("language", "zh-CN")
        diarization = config.get("diarization", False)
        lang_detect_mode = config.get("lang_detect", "At Start")
        selected_languages = config.get("languages", [language])
        temp_id = data.get("temp_id", "")

        if not speech_key or not speech_region:
            socketio.emit("rt:status", {
                "type": "error", "message": "Missing Azure Speech Key or Region."
            }, to=sid)
            return

        import os
        from sessions import UPLOAD_DIR
        file_path = os.path.join(UPLOAD_DIR, temp_id)
        if not os.path.exists(file_path):
            socketio.emit("rt:status", {
                "type": "error", "message": "Uploaded file not found."
            }, to=sid)
            return

        phrase_list = config.get("phrase_list", [])
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        recognizer, is_diarization = _build_recognizer(
            speech_key, speech_region, language, diarization,
            lang_detect_mode, selected_languages, audio_config,
            phrase_list=phrase_list)

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
                detected_lang = evt.result.properties.get(
                    speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult, "") or None
                speaker_id = getattr(evt.result, 'speaker_id', None) if is_diarization else None
                line = format_recognition_line(
                    evt.result.offset, evt.result.text,
                    speaker_id=speaker_id, detected_lang=detected_lang)
                socketio.emit("rt:result", {"line": line, "final": True}, to=sid)

        def on_done(evt):
            socketio.emit("rt:done", {}, to=sid)
            socketio.emit("rt:status", {
                "type": "success", "message": "File processing complete."
            }, to=sid)
            # Cleanup session state
            state = sessions.get(sid)
            state.pop("rt_recognizer", None)
            state.pop("rt_recognizer_is_diarization", None)
            # Cleanup temp file
            try:
                os.unlink(file_path)
            except Exception:
                pass

        # Store recognizer in session to prevent garbage collection
        state = sessions.get(sid)
        state["rt_recognizer"] = recognizer
        state["rt_recognizer_is_diarization"] = is_diarization

        if is_diarization:
            recognizer.transcribed.connect(on_recognized)
            recognizer.session_stopped.connect(on_done)
            recognizer.canceled.connect(on_done)
            recognizer.start_transcribing_async()
        else:
            recognizer.recognized.connect(on_recognized)
            recognizer.session_stopped.connect(on_done)
            recognizer.canceled.connect(on_done)
            recognizer.start_continuous_recognition()

        socketio.emit("rt:status", {
            "type": "info", "message": "Processing file..."
        }, to=sid)

