"""Tab 6: LLM Speech (Transcribe & Translate) — REST API handlers."""

import json
import requests
import azure.cognitiveservices.speech as speechsdk
from config import LLM_TARGET_LANG_MAP, TTS_LOCALE_MAP


def call_llm_speech_api(speech_key, speech_region, audio_bytes, audio_filename,
                        task, target_language_code=None, prompt_text=None):
    """Call the Azure LLM Speech REST API for transcribe or translate."""
    url = (f"https://{speech_region}.api.cognitive.microsoft.com/"
           f"speechtotext/transcriptions:transcribe?api-version=2025-10-15")

    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
    }

    enhanced_mode = {
        "enabled": True,
        "task": task,
    }
    if task == "translate" and target_language_code:
        enhanced_mode["targetLanguage"] = target_language_code
    if prompt_text:
        enhanced_mode["prompt"] = [prompt_text]

    definition = {
        "enhancedMode": enhanced_mode,
    }

    files = {
        "audio": (audio_filename, audio_bytes),
        "definition": (None, json.dumps(definition), "application/json"),
    }

    response = requests.post(url, headers=headers, files=files)
    return response


def synthesize_speech(speech_key, speech_region, text, language_label):
    """Synthesize text to WAV audio bytes using Azure TTS."""
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=speech_region)
    tts_locale = TTS_LOCALE_MAP.get(language_label, "en-US")
    speech_config.speech_synthesis_language = tts_locale

    # Synthesize to memory
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    return None
