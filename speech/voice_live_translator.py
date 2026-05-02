"""Voice Live Translator — reuses voice_live session with translation instructions.

Registers a parallel event set (`vlt:*`) so the Translator tab and the main
Voice Live tab can coexist without cross-talk. Delegates the actual session
loop to `voice_live._run_voice_live_session` through a SocketIO emit proxy
that renames `vl:*` events to `vlt:*` on the fly.
"""

import queue
import threading

from flask import request
from sessions import sessions
from speech import voice_live


class _PrefixedSocketIO:
    """Proxy a Flask-SocketIO instance, rewriting event name prefixes on emit."""

    def __init__(self, socketio, old_prefix="vl", new_prefix="vlt"):
        self._io = socketio
        self._old = old_prefix + ":"
        self._new = new_prefix + ":"

    def emit(self, event, *args, **kwargs):
        if event.startswith(self._old):
            event = self._new + event[len(self._old):]
        return self._io.emit(event, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._io, name)


def _build_instructions(target_language, user_override):
    if user_override and user_override.strip():
        return user_override.strip()
    lang = target_language or "English"
    return (
        f"You are a real-time interpreter. Listen to the user speaking and "
        f"translate everything they say into {lang}. Respond only with the "
        f"translation in a natural, conversational tone. Do not add commentary."
    )


def register(socketio):
    @socketio.on("vlt:start")
    def handle_start(data):
        sid = request.sid

        if not voice_live.VOICELIVE_AVAILABLE:
            socketio.emit("vlt:status", {
                "type": "error",
                "message": "Voice Live SDK not installed on server.",
            }, to=sid)
            return

        config = (data or {}).get("config", {})
        endpoint = config.get("vl_endpoint", "")
        api_key = config.get("api_key", "")
        model = config.get("model", "gpt-4o-mini")
        voice = config.get("voice", "alloy")
        voice_provider = config.get("voice_provider", "OpenAI")
        target_language = config.get("target_language", "English")
        asr_model = config.get("asr_model", "azure-speech")
        instructions = _build_instructions(
            target_language, config.get("instructions", ""))

        if not endpoint or not api_key:
            socketio.emit("vlt:status", {
                "type": "error",
                "message": "Please provide Voice Live Endpoint and API Key.",
            }, to=sid)
            return

        shutdown_event = threading.Event()
        mic_queue = queue.Queue()

        state = sessions.get(sid)
        state["vlt_shutdown_event"] = shutdown_event
        state["vlt_mic_queue"] = mic_queue

        # Route internal vl:* events to vlt:* on the client
        proxied_io = _PrefixedSocketIO(socketio, "vl", "vlt")

        thread = threading.Thread(
            target=voice_live._run_voice_live_session,
            args=(proxied_io, sid, endpoint, api_key, model, voice,
                  instructions, shutdown_event, mic_queue),
            kwargs={"voice_provider": voice_provider,
                    "target_language": "",  # server_vad handles turn detection
                    "asr_model": asr_model},
            daemon=True,
        )
        thread.start()
        state["vlt_thread"] = thread

    @socketio.on("vlt:mic_audio")
    def handle_mic_audio(data):
        sid = request.sid
        state = sessions.get(sid)
        mic_queue = state.get("vlt_mic_queue")
        if mic_queue and isinstance(data, (bytes, bytearray)):
            mic_queue.put(bytes(data))

    @socketio.on("vlt:stop")
    def handle_stop():
        sid = request.sid
        state = sessions.get(sid)

        shutdown_event = state.pop("vlt_shutdown_event", None)
        if shutdown_event:
            shutdown_event.set()

        mic_queue = state.pop("vlt_mic_queue", None)
        if mic_queue:
            mic_queue.put(None)  # sentinel

        thread = state.pop("vlt_thread", None)
        if thread and thread.is_alive():
            thread.join(timeout=3.0)

        socketio.emit("vlt:status", {
            "type": "info",
            "message": "Voice Live Translator stopped.",
        }, to=sid)
