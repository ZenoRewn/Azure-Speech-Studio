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
    MAI_TRANSCRIBE_LANGUAGES, MULTI_TALKER_PRESETS,
    VOICE_CHANGER_TARGETS, VOICE_CHANGER_REGIONS,
    VIDEO_TRANSLATION_LOCALES,
    PERSONAL_VOICE_LOCALES, PERSONAL_VOICE_MODELS, PERSONAL_VOICE_CONSENT_TEMPLATE,
    PODCAST_REGIONS, PODCAST_STYLES, PODCAST_LENGTHS, PODCAST_HOST_TYPES,
    PODCAST_LOCALES, AZURE_SPEECH_REGIONS,
)
from speech import llm_speech
from speech import tts as tts_module
from speech import mai_transcribe, multi_talker_tts, voice_changer, voice_creation

# Register SocketIO event handlers from each tab module
from speech import realtime_stt, fast_transcription, speech_translate
from speech import live_interpreter, voice_live
from speech import whisper_batch, video_translation, podcast_agent, voice_live_translator

realtime_stt.register(socketio)
fast_transcription.register(socketio)
speech_translate.register(socketio)
live_interpreter.register(socketio)
voice_live.register(socketio)
voice_live_translator.register(socketio)
whisper_batch.register(socketio)
video_translation.register(socketio)
podcast_agent.register(socketio)


# --- HTTP Routes ---

@app.route("/healthz")
def healthz():
    """Kubernetes liveness/readiness probe."""
    return jsonify({"status": "ok"}), 200


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
                           tts_voices=TTS_VOICE_OPTIONS,
                           mai_transcribe_languages=MAI_TRANSCRIBE_LANGUAGES,
                           multi_talker_presets=MULTI_TALKER_PRESETS,
                           voice_changer_targets=VOICE_CHANGER_TARGETS,
                           voice_changer_regions=VOICE_CHANGER_REGIONS,
                           video_translation_locales=VIDEO_TRANSLATION_LOCALES,
                           personal_voice_locales=PERSONAL_VOICE_LOCALES,
                           personal_voice_models=PERSONAL_VOICE_MODELS,
                           personal_voice_consent_template=PERSONAL_VOICE_CONSENT_TEMPLATE,
                           podcast_regions=PODCAST_REGIONS,
                           podcast_styles=PODCAST_STYLES,
                           podcast_lengths=PODCAST_LENGTHS,
                           podcast_host_types=PODCAST_HOST_TYPES,
                           podcast_locales=PODCAST_LOCALES,
                           azure_speech_regions=AZURE_SPEECH_REGIONS)


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


# --- MAI-Transcribe ---

@app.route("/api/mai-transcribe", methods=["POST"])
def mai_transcribe_route():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    speech_key = request.form.get("speech_key", "")
    speech_region = request.form.get("speech_region", "")
    locales_raw = request.form.get("locales", "")
    locales = [x.strip() for x in locales_raw.split(",") if x.strip()]
    enable_diarization = request.form.get("enable_diarization") == "true"
    max_speakers = int(request.form.get("max_speakers", "4") or 4)
    phrase_list_raw = request.form.get("phrase_list", "")
    phrase_list = [p.strip() for p in phrase_list_raw.split(",") if p.strip()]

    if not speech_key or not speech_region:
        return jsonify({"error": "Missing Azure credentials"}), 400
    if not locales:
        return jsonify({"error": "At least one locale is required"}), 400

    resp = mai_transcribe.call_mai_transcribe(
        speech_key, speech_region,
        f.read(), f.filename,
        locales=locales,
        enable_diarization=enable_diarization,
        max_speakers=max_speakers,
        phrase_list=phrase_list or None,
    )
    if resp.status_code == 200:
        return jsonify(mai_transcribe.normalize_response(resp.json()))
    return jsonify({"error": resp.text}), resp.status_code


# --- Multi-Talker TTS ---

@app.route("/api/multi-talker-tts/synthesize", methods=["POST"])
def multi_talker_synthesize():
    data = request.get_json() or {}
    speech_key = data.get("speech_key", "")
    speech_region = data.get("speech_region", "")
    content = data.get("content", "")
    voice_name = data.get("voice_name", "")
    locale = data.get("locale", "en-US")
    custom_ssml = data.get("ssml", "")

    if not speech_key or not speech_region:
        return jsonify({"error": "Missing Azure credentials"}), 400
    if not (content or custom_ssml):
        return jsonify({"error": "Missing content"}), 400
    if not voice_name and not custom_ssml:
        return jsonify({"error": "Missing voice_name"}), 400

    ssml = custom_ssml or multi_talker_tts.build_ssml(content, voice_name, locale)
    audio, err = multi_talker_tts.synthesize(speech_key, speech_region, ssml)
    if audio:
        import io
        return send_file(
            io.BytesIO(audio), mimetype="audio/wav",
            as_attachment=True, download_name="multi_talker.wav")
    return jsonify({"error": err or "Synthesis failed"}), 500


@app.route("/api/multi-talker-tts/ssml-preview", methods=["POST"])
def multi_talker_ssml_preview():
    data = request.get_json() or {}
    ssml = multi_talker_tts.build_ssml(
        data.get("content", ""),
        data.get("voice_name", ""),
        data.get("locale", "en-US"),
    )
    return jsonify({"ssml": ssml})


# --- Voice Changer ---

@app.route("/api/voice-changer", methods=["POST"])
def voice_changer_route():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    speech_key = request.form.get("speech_key", "")
    speech_region = request.form.get("speech_region", "")
    target_voice = request.form.get("target_voice", "")

    if not speech_key or not speech_region:
        return jsonify({"error": "Missing Azure credentials"}), 400
    if not target_voice:
        return jsonify({"error": "Missing target_voice"}), 400

    audio, err = voice_changer.convert(
        speech_key, speech_region, f.read(), f.filename, target_voice)
    if audio:
        import io
        return send_file(
            io.BytesIO(audio), mimetype="audio/mpeg",
            as_attachment=True, download_name="voice_changer.mp3")
    return jsonify({"error": err or "Voice conversion failed"}), 500


# --- Voice Creation (Personal Voice) ---

@app.route("/api/voice-creation/models", methods=["GET"])
def voice_creation_models():
    speech_key = request.args.get("speech_key", "")
    speech_region = request.args.get("speech_region", "")
    if not speech_key or not speech_region:
        return jsonify({"error": "Missing Azure credentials"}), 400
    resp = voice_creation.list_models(speech_key, speech_region)
    if resp.status_code == 200:
        return jsonify(resp.json())
    return jsonify({"error": resp.text}), resp.status_code


@app.route("/api/voice-creation/voices", methods=["GET"])
def voice_creation_list_voices():
    speech_key = request.args.get("speech_key", "")
    speech_region = request.args.get("speech_region", "")
    if not speech_key or not speech_region:
        return jsonify({"error": "Missing Azure credentials"}), 400
    resp = voice_creation.list_voices(speech_key, speech_region)
    if resp.status_code == 200:
        return jsonify(resp.json())
    return jsonify({"error": resp.text}), resp.status_code


@app.route("/api/voice-creation/voices/<voice_id>", methods=["GET"])
def voice_creation_voice_status(voice_id):
    speech_key = request.args.get("speech_key", "")
    speech_region = request.args.get("speech_region", "")
    if not speech_key or not speech_region:
        return jsonify({"error": "Missing Azure credentials"}), 400
    resp = voice_creation.get_voice(speech_key, speech_region, voice_id)
    if resp.status_code == 200:
        return jsonify(resp.json())
    return jsonify({"error": resp.text}), resp.status_code


@app.route("/api/voice-creation/create", methods=["POST"])
def voice_creation_create():
    """Multi-step: create project -> upload consent -> kick off voice training.

    Multipart form fields:
      - speech_key, speech_region
      - project_name, voice_name, company_name, model_id, locale
      - description (optional)
      - consent_audio (file)
      - training_audio (list of files)
    """
    speech_key = request.form.get("speech_key", "")
    speech_region = request.form.get("speech_region", "")
    project_name = request.form.get("project_name", "")
    voice_name = request.form.get("voice_name", "")
    company_name = request.form.get("company_name", project_name)
    model_id = request.form.get("model_id", "")
    locale = request.form.get("locale", "en-US")
    description = request.form.get("description", "")

    consent_audio = request.files.get("consent_audio")
    training_files = request.files.getlist("training_audio")

    missing = [k for k, v in {
        "speech_key": speech_key, "speech_region": speech_region,
        "project_name": project_name, "voice_name": voice_name,
        "model_id": model_id, "consent_audio": consent_audio,
    }.items() if not v]
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400
    if not training_files:
        return jsonify({"error": "At least one training audio file is required"}), 400

    proj_resp = voice_creation.create_project(
        speech_key, speech_region, project_name, locale, description)
    if proj_resp.status_code >= 400 and proj_resp.status_code != 409:
        return jsonify({"error": f"Create project: {proj_resp.text}"}), proj_resp.status_code
    proj = proj_resp.json() if proj_resp.content else {}
    project_id = proj.get("id") or proj.get("self") or project_name

    consent_resp = voice_creation.upload_consent(
        speech_key, speech_region, project_id, voice_name, company_name,
        locale, consent_audio.read(), consent_audio.filename)
    if consent_resp.status_code >= 400:
        return jsonify({"error": f"Upload consent: {consent_resp.text}"}), consent_resp.status_code
    consent = consent_resp.json()

    training_blobs = [(tf.filename, tf.read()) for tf in training_files]
    voice_resp = voice_creation.create_voice(
        speech_key, speech_region, project_id, voice_name, model_id,
        consent.get("id"), locale, training_blobs, description)
    if voice_resp.status_code >= 400:
        return jsonify({"error": f"Create voice: {voice_resp.text}"}), voice_resp.status_code

    voice = voice_resp.json()
    return jsonify({
        "project_id": project_id,
        "consent_id": consent.get("id"),
        "voice_id": voice.get("id"),
        "voice": voice,
    })


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

