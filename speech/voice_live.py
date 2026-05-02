"""Tab 5: Voice Live — SocketIO event handlers."""

import threading
import asyncio
import base64
import traceback

from sessions import sessions

# Voice Live SDK (optional)
try:
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.voicelive.aio import connect as vl_connect
    from azure.ai.voicelive.models import (
        AudioEchoCancellation,
        AudioInputTranscriptionOptions,
        AudioNoiseReduction,
        AzureStandardVoice,
        InputAudioFormat,
        Modality,
        OutputAudioFormat,
        RequestSession as VLRequestSession,
        ServerEventType,
        ServerVad,
    )
    import aiohttp
    import aiohttp.resolver
    from azure.ai.voicelive.aio._patch import _VoiceLiveConnectionManager

    # Monkey-patch: aiodns resolver fails on some networks; force system DNS
    if not hasattr(_VoiceLiveConnectionManager, '_orig_aenter'):
        _VoiceLiveConnectionManager._orig_aenter = _VoiceLiveConnectionManager.__aenter__

        async def _patched_aenter(self):
            connector = aiohttp.TCPConnector(resolver=aiohttp.resolver.ThreadedResolver())
            self._patched_connector = connector
            _orig_cs = aiohttp.ClientSession

            def _patched_cs(**kwargs):
                kwargs.setdefault("connector", connector)
                return _orig_cs(**kwargs)

            aiohttp.ClientSession = _patched_cs
            try:
                return await _VoiceLiveConnectionManager._orig_aenter(self)
            finally:
                aiohttp.ClientSession = _orig_cs

        _VoiceLiveConnectionManager.__aenter__ = _patched_aenter

    VOICELIVE_AVAILABLE = True
except ImportError:
    VOICELIVE_AVAILABLE = False


def _run_voice_live_session(socketio, sid, endpoint, api_key, model, voice,
                            instructions, shutdown_event, mic_audio_queue,
                            voice_provider="OpenAI", target_language="",
                            asr_model="azure-speech"):
    """Run Voice Live session in a background thread with browser audio I/O."""

    async def _session():
        credential = AzureKeyCredential(api_key)
        event_count = 0
        loop = asyncio.get_event_loop()

        try:
            socketio.emit("vl:status", {
                "type": "info",
                "message": f"Connecting to {endpoint} (model={model})..."
            }, to=sid)

            async with vl_connect(
                endpoint=endpoint, credential=credential, model=model,
            ) as connection:
                # Determine voice config
                if voice_provider == "Azure Neural":
                    voice_cfg = AzureStandardVoice(name=voice)
                else:
                    voice_cfg = voice

                # Build audio input transcription options
                transcription_opts = AudioInputTranscriptionOptions(
                    model=asr_model,
                )
                if target_language:
                    transcription_opts.language = target_language

                session_config = VLRequestSession(
                    modalities=[Modality.TEXT, Modality.AUDIO],
                    instructions=instructions,
                    voice=voice_cfg,
                    input_audio_format=InputAudioFormat.PCM16,
                    output_audio_format=OutputAudioFormat.PCM16,
                    turn_detection=ServerVad(
                        threshold=0.5,
                        prefix_padding_ms=300,
                        silence_duration_ms=500,
                    ),
                    input_audio_echo_cancellation=AudioEchoCancellation(),
                    input_audio_noise_reduction=AudioNoiseReduction(
                        type="azure_deep_noise_suppression"
                    ),
                    input_audio_transcription=transcription_opts,
                )
                await connection.session.update(session=session_config)
                socketio.emit("vl:status", {
                    "type": "success", "message": "Connected! Start speaking..."
                }, to=sid)

                # Start mic audio forwarding task
                async def forward_mic_audio():
                    while not shutdown_event.is_set():
                        try:
                            audio_data = await asyncio.wait_for(
                                loop.run_in_executor(None, mic_audio_queue.get),
                                timeout=0.1)
                            if audio_data is None:
                                break
                            audio_b64 = base64.b64encode(audio_data).decode("utf-8")
                            await connection.input_audio_buffer.append(audio=audio_b64)
                        except asyncio.TimeoutError:
                            continue
                        except Exception:
                            break

                mic_task = asyncio.create_task(forward_mic_audio())

                assistant_transcript = []

                async for event in connection:
                    event_count += 1
                    if shutdown_event.is_set():
                        break

                    if event.type == ServerEventType.SESSION_UPDATED:
                        socketio.emit("vl:status", {
                            "type": "success",
                            "message": "Session ready. Microphone active."
                        }, to=sid)

                    elif event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
                        socketio.emit("vl:skip_audio", {}, to=sid)
                        socketio.emit("vl:status", {
                            "type": "info", "message": "Listening..."
                        }, to=sid)

                    elif event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED:
                        socketio.emit("vl:status", {
                            "type": "info", "message": "Processing..."
                        }, to=sid)

                    elif event.type == ServerEventType.RESPONSE_CREATED:
                        assistant_transcript = []

                    elif event.type == ServerEventType.RESPONSE_AUDIO_DELTA:
                        # Send audio to browser for playback
                        audio_b64 = base64.b64encode(event.delta).decode("utf-8")
                        socketio.emit("vl:playback_audio", {
                            "audio": audio_b64,
                        }, to=sid)

                    elif event.type == ServerEventType.RESPONSE_AUDIO_DONE:
                        socketio.emit("vl:status", {
                            "type": "info", "message": "Assistant speaking..."
                        }, to=sid)

                    elif event.type == ServerEventType.RESPONSE_DONE:
                        if assistant_transcript:
                            socketio.emit("vl:transcript", {
                                "role": "assistant",
                                "text": "".join(assistant_transcript),
                            }, to=sid)
                            assistant_transcript = []

                        # Extract and emit usage stats
                        response = getattr(event, "response", None)
                        usage = getattr(response, "usage", None) if response else None
                        if usage:
                            input_details = getattr(usage, "input_token_details", None)
                            output_details = getattr(usage, "output_token_details", None)
                            usage_data = {
                                "total_tokens": getattr(usage, "total_tokens", 0),
                                "input_tokens": getattr(usage, "input_tokens", 0),
                                "output_tokens": getattr(usage, "output_tokens", 0),
                                "input_token_details": {
                                    "text_tokens": getattr(input_details, "text_tokens", 0),
                                    "audio_tokens": getattr(input_details, "audio_tokens", 0),
                                    "cached_tokens": getattr(input_details, "cached_tokens", 0),
                                } if input_details else {},
                                "output_token_details": {
                                    "text_tokens": getattr(output_details, "text_tokens", 0),
                                    "audio_tokens": getattr(output_details, "audio_tokens", 0),
                                } if output_details else {},
                            }
                            socketio.emit("vl:usage", usage_data, to=sid)

                        socketio.emit("vl:status", {
                            "type": "success",
                            "message": "Ready — speak to continue"
                        }, to=sid)

                    elif event.type == ServerEventType.ERROR:
                        msg = event.error.message
                        if "Cancellation failed" not in msg:
                            socketio.emit("vl:transcript", {
                                "role": "error",
                                "text": f"Error: {msg}",
                            }, to=sid)

                    elif event.type == ServerEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA:
                        delta = getattr(event, "delta", None) or ""
                        if delta:
                            assistant_transcript.append(delta)

                    elif event.type == ServerEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED:
                        transcript = getattr(event, "transcript", None) or ""
                        if transcript:
                            socketio.emit("vl:transcript", {
                                "role": "user",
                                "text": transcript,
                            }, to=sid)

                mic_task.cancel()

                if event_count == 0 and not shutdown_event.is_set():
                    socketio.emit("vl:status", {
                        "type": "error",
                        "message": "Connection closed immediately without receiving any events. "
                                   "Please check your Endpoint, API Key, and Model."
                    }, to=sid)

        except Exception as e:
            tb = traceback.format_exc()
            socketio.emit("vl:status", {
                "type": "error",
                "message": f"Voice Live error: {e}\n\n{tb}"
            }, to=sid)
        finally:
            socketio.emit("vl:stopped", {
                "message": f"Session ended. (received {event_count} events)"
            }, to=sid)

    asyncio.run(_session())


def register(socketio):
    """Register Voice Live SocketIO events."""

    @socketio.on("vl:start")
    def handle_start(data):
        from flask import request
        sid = request.sid

        if not VOICELIVE_AVAILABLE:
            socketio.emit("vl:status", {
                "type": "error",
                "message": "Voice Live SDK not installed on server."
            }, to=sid)
            return

        config = data.get("config", {})
        endpoint = config.get("vl_endpoint", "")
        api_key = config.get("api_key", "")
        model = config.get("model", "gpt-4o-mini")
        voice = config.get("voice", "alloy")
        voice_provider = config.get("voice_provider", "OpenAI")
        target_language = config.get("target_language", "")
        asr_model = config.get("asr_model", "azure-speech")
        instructions = config.get("instructions", "You are a helpful AI assistant.")

        if not endpoint or not api_key:
            socketio.emit("vl:status", {
                "type": "error",
                "message": "Please provide Voice Live Endpoint and API Key."
            }, to=sid)
            return

        import queue
        shutdown_event = threading.Event()
        mic_audio_queue = queue.Queue()

        state = sessions.get(sid)
        state["vl_shutdown_event"] = shutdown_event
        state["vl_mic_queue"] = mic_audio_queue

        thread = threading.Thread(
            target=_run_voice_live_session,
            args=(socketio, sid, endpoint, api_key, model, voice,
                  instructions, shutdown_event, mic_audio_queue),
            kwargs={"voice_provider": voice_provider,
                    "target_language": target_language,
                    "asr_model": asr_model},
            daemon=True,
        )
        thread.start()
        state["vl_thread"] = thread

    @socketio.on("vl:mic_audio")
    def handle_mic_audio(data):
        from flask import request
        sid = request.sid
        state = sessions.get(sid)
        mic_queue = state.get("vl_mic_queue")
        if mic_queue and isinstance(data, (bytes, bytearray)):
            mic_queue.put(bytes(data))

    @socketio.on("vl:stop")
    def handle_stop():
        from flask import request
        sid = request.sid
        state = sessions.get(sid)

        shutdown_event = state.pop("vl_shutdown_event", None)
        if shutdown_event:
            shutdown_event.set()

        mic_queue = state.pop("vl_mic_queue", None)
        if mic_queue:
            mic_queue.put(None)  # sentinel

        thread = state.pop("vl_thread", None)
        if thread and thread.is_alive():
            thread.join(timeout=3.0)

        socketio.emit("vl:status", {
            "type": "info", "message": "Voice Live stopped."
        }, to=sid)

