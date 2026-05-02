"""Azure Personal Voice — Custom Voice project / consent / training workflow."""

import json
import requests

from config import PERSONAL_VOICE_CONSENT_TEMPLATE

API_VERSION = "2024-02-01-preview"


def _base(region):
    return f"https://{region}.api.cognitive.microsoft.com"


def list_models(speech_key, speech_region):
    """List base models available for custom voice training."""
    url = f"{_base(speech_region)}/customvoice/models/base?api-version={API_VERSION}"
    headers = {"Ocp-Apim-Subscription-Key": speech_key}
    resp = requests.get(url, headers=headers, timeout=60)
    return resp


def list_voices(speech_key, speech_region):
    """List existing custom voices (trained / training)."""
    url = f"{_base(speech_region)}/customvoice/voices?api-version={API_VERSION}"
    headers = {"Ocp-Apim-Subscription-Key": speech_key}
    resp = requests.get(url, headers=headers, timeout=60)
    return resp


def get_voice(speech_key, speech_region, voice_id):
    """Poll a custom voice's training status."""
    url = f"{_base(speech_region)}/customvoice/voices/{voice_id}?api-version={API_VERSION}"
    headers = {"Ocp-Apim-Subscription-Key": speech_key}
    return requests.get(url, headers=headers, timeout=60)


def create_project(speech_key, speech_region, project_name, locale, description=""):
    url = f"{_base(speech_region)}/customvoice/projects?api-version={API_VERSION}"
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
        "Content-Type": "application/json",
    }
    body = {
        "displayName": project_name,
        "locale": locale,
        "description": description or f"Custom voice project: {project_name}",
    }
    return requests.post(url, headers=headers, json=body, timeout=60)


def upload_consent(speech_key, speech_region, project_id, voice_name,
                   company_name, locale, consent_audio_bytes, consent_filename):
    """Upload consent audio for the voice talent."""
    url = f"{_base(speech_region)}/customvoice/consents?api-version={API_VERSION}"
    headers = {"Ocp-Apim-Subscription-Key": speech_key}
    consent_statement = PERSONAL_VOICE_CONSENT_TEMPLATE.format(
        voice_talent_name=voice_name, company_name=company_name)
    description = {
        "projectId": project_id,
        "voiceTalentName": voice_name,
        "companyName": company_name,
        "locale": locale,
        "consentStatement": consent_statement,
    }
    files = {
        "audioData": (consent_filename or "consent.wav", consent_audio_bytes),
        "description": (None, json.dumps(description), "application/json"),
    }
    return requests.post(url, headers=headers, files=files, timeout=180)


def create_voice(speech_key, speech_region, project_id, voice_name, model_id,
                 consent_id, locale, training_audio_files, description=""):
    """Kick off training for a custom voice.

    training_audio_files: list of (filename, bytes) tuples.
    """
    url = f"{_base(speech_region)}/customvoice/voices?api-version={API_VERSION}"
    headers = {"Ocp-Apim-Subscription-Key": speech_key}
    desc = {
        "projectId": project_id,
        "displayName": voice_name,
        "modelId": model_id,
        "consentId": consent_id,
        "locale": locale,
        "description": description or f"Custom voice: {voice_name}",
    }
    files = [
        ("audioData", (name, blob)) for name, blob in training_audio_files
    ]
    files.append(("description", (None, json.dumps(desc), "application/json")))
    return requests.post(url, headers=headers, files=files, timeout=600)
