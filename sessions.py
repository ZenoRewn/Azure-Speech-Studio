"""Server-side session state manager keyed by SocketIO session ID."""

import threading
import os
import tempfile


class SessionManager:
    """Manages per-connection state: SDK objects, threads, temp files."""

    def __init__(self):
        self._sessions = {}
        self._lock = threading.Lock()

    def get(self, sid):
        with self._lock:
            if sid not in self._sessions:
                self._sessions[sid] = {}
            return self._sessions[sid]

    def set(self, sid, key, value):
        with self._lock:
            if sid not in self._sessions:
                self._sessions[sid] = {}
            self._sessions[sid][key] = value

    def pop(self, sid, key, default=None):
        with self._lock:
            if sid in self._sessions:
                return self._sessions[sid].pop(key, default)
            return default

    def cleanup(self, sid):
        """Clean up all resources for a disconnected session."""
        with self._lock:
            state = self._sessions.pop(sid, {})

        # Stop recognizers
        for key in ("rt_recognizer", "ft_recognizer", "st_recognizer", "li_recognizer"):
            recognizer = state.get(key)
            if recognizer:
                try:
                    is_diarization = state.get(key + "_is_diarization", False)
                    if is_diarization:
                        recognizer.stop_transcribing_async().get()
                    else:
                        recognizer.stop_continuous_recognition()
                except Exception:
                    pass

        # Close PushAudioInputStream
        for key in ("rt_push_stream", "st_push_stream", "li_push_stream"):
            stream = state.get(key)
            if stream:
                try:
                    stream.close()
                except Exception:
                    pass

        # Signal Voice Live / Translator shutdown
        for ev_key, th_key in (
            ("vl_shutdown_event", "vl_thread"),
            ("vlt_shutdown_event", "vlt_thread"),
        ):
            shutdown_event = state.get(ev_key)
            if shutdown_event:
                shutdown_event.set()
            th = state.get(th_key)
            if th and th.is_alive():
                try:
                    th.join(timeout=3.0)
                except Exception:
                    pass

        # Signal background async pollers
        for key in ("wb_cancel", "vt_cancel", "pa_cancel"):
            ev = state.get(key)
            if ev:
                try:
                    ev.set()
                except Exception:
                    pass

        # Delete temp files
        for key in list(state.keys()):
            if key.startswith("tmp_"):
                path = state[key]
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except Exception:
                        pass


# Singleton
sessions = SessionManager()

# Temp file storage directory
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "speech_studio_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

