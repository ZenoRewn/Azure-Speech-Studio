"""Flask + SocketIO entry point for Azure Speech Studio."""

import os
import uuid
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()

socketio = SocketIO(app, async_mode="threading", max_http_buffer_size=10 * 1024 * 1024)


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


from sessions import sessions, UPLOAD_DIR
from config import (
    LANGUAGE_OPTIONS, TRANSLATION_TARGET_LANGUAGES,
    LLM_TARGET_LANG_MAP, TTS_LOCALE_MAP,
    LI_STANDARD_VOICES, VL_VOICE_PROVIDERS, VL_MODEL_TIERS,
    VL_ASR_MODELS, VL_TARGET_LANGUAGES,
    TTS_VOICE_OPTIONS,
)
from speech import llm_speech
from speech import tts as tts_module

# Register SocketIO event handlers from each tab module
from speech import realtime_stt, fast_transcription, speech_translate
from speech import live_interpreter, voice_live

realtime_stt.register(socketio)
fast_transcription.register(socketio)
speech_translate.register(socketio)
live_interpreter.register(socketio)
voice_live.register(socketio)


# --- HTTP Routes ---

@app.route("/")
def index():
    """Serve the single-page application."""
    env_defaults = {
        "speech_key": os.getenv("ASIA_SPEECH_KEY", ""),
        "speech_region": os.getenv("ASIA_SPEECH_REGION", ""),
        "aoai_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
        "aoai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        "aoai_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-35-turbo"),
        "aoai_version": os.getenv("AZURE_OPENAI_VERSION", "2025-04-01-preview"),
        "vl_endpoint": os.getenv("AZURE_VOICELIVE_ENDPOINT", ""),
    }
    return render_template("index.html",
                           env_defaults=env_defaults,
                           language_options=LANGUAGE_OPTIONS,
                           translation_targets=TRANSLATION_TARGET_LANGUAGES,
                           llm_targets=LLM_TARGET_LANG_MAP,
                           vl_voice_providers=VL_VOICE_PROVIDERS,
                           vl_model_tiers=VL_MODEL_TIERS,
                           vl_asr_models=VL_ASR_MODELS,
                           vl_target_languages=VL_TARGET_LANGUAGES,
                           tts_voices=TTS_VOICE_OPTIONS)


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads, return a temp_id for later reference."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400
    ext = f.filename.rsplit(".", 1)[-1] if "." in f.filename else "wav"
    temp_id = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, temp_id)
    f.save(save_path)
    return jsonify({"temp_id": temp_id, "filename": f.filename})


@app.route("/api/llm-speech/transcribe", methods=["POST"])
def llm_transcribe():
    """LLM Speech transcription endpoint."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    speech_key = request.form.get("speech_key", "")
    speech_region = request.form.get("speech_region", "")
    prompt_text = request.form.get("prompt", "")

    if not speech_key or not speech_region:
        return jsonify({"error": "Missing Azure credentials"}), 400

    resp = llm_speech.call_llm_speech_api(
        speech_key, speech_region,
        f.read(), f.filename,
        task="transcribe",
        prompt_text=prompt_text if prompt_text else None)

    if resp.status_code == 200:
        return jsonify(resp.json())
    return jsonify({"error": resp.text}), resp.status_code


@app.route("/api/llm-speech/translate", methods=["POST"])
def llm_translate():
    """LLM Speech translation endpoint."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    speech_key = request.form.get("speech_key", "")
    speech_region = request.form.get("speech_region", "")
    target_language = request.form.get("target_language", "English")
    prompt_text = request.form.get("prompt", "")

    if not speech_key or not speech_region:
        return jsonify({"error": "Missing Azure credentials"}), 400

    lang_code = LLM_TARGET_LANG_MAP.get(target_language, "en")

    resp = llm_speech.call_llm_speech_api(
        speech_key, speech_region,
        f.read(), f.filename,
        task="translate",
        target_language_code=lang_code,
        prompt_text=prompt_text if prompt_text else None)

    if resp.status_code == 200:
        return jsonify(resp.json())
    return jsonify({"error": resp.text}), resp.status_code


@app.route("/api/llm-speech/synthesize", methods=["POST"])
def llm_synthesize():
    """Synthesize text to speech and return WAV audio."""
    data = request.get_json()
    speech_key = data.get("speech_key", "")
    speech_region = data.get("speech_region", "")
    text = data.get("text", "")
    language_label = data.get("language_label", "English")

    if not speech_key or not speech_region or not text:
        return jsonify({"error": "Missing parameters"}), 400

    audio_data = llm_speech.synthesize_speech(
        speech_key, speech_region, text, language_label)

    if audio_data:
        import io
        return send_file(
            io.BytesIO(audio_data),
            mimetype="audio/wav",
            as_attachment=True,
            download_name="speech.wav")
    return jsonify({"error": "Synthesis failed"}), 500


@app.route("/api/tts/synthesize", methods=["POST"])
def tts_synthesize():
    """Synthesize text or SSML to speech and return WAV audio."""
    data = request.get_json()
    speech_key = data.get("speech_key", "")
    speech_region = data.get("speech_region", "")
    text = data.get("text", "")
    voice = data.get("voice", "")
    mode = data.get("mode", "text")

    if not speech_key or not speech_region or not text:
        return jsonify({"error": "Missing parameters"}), 400

    if mode == "ssml":
        audio_data = tts_module.synthesize_ssml(speech_key, speech_region, text)
    else:
        if not voice:
            return jsonify({"error": "Missing voice parameter"}), 400
        audio_data = tts_module.synthesize_text(
            speech_key, speech_region, text, voice)

    if audio_data:
        import io
        return send_file(
            io.BytesIO(audio_data),
            mimetype="audio/wav",
            as_attachment=True,
            download_name="tts_output.wav")
    return jsonify({"error": "Synthesis failed"}), 500


# --- SocketIO lifecycle ---

@socketio.on("connect")
def handle_connect():
    pass


@socketio.on("disconnect")
def handle_disconnect():
    from flask import request
    sessions.cleanup(request.sid)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True,
                 allow_unsafe_werkzeug=True)
