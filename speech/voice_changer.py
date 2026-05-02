"""Voice Changer via Azure TTS mstts:voiceconversion SSML.

Flow:
  1. Upload audio to Azure Blob Storage (returns blob URL).
  2. Call TTS endpoint with SSML referencing the blob URL and a target voice.
  3. Return converted audio bytes (MP3).

Region-limited to eastus / westeurope / southeastasia.
"""

import os
import uuid
from xml.sax.saxutils import escape as _xml_escape
import requests

from config import VOICE_CHANGER_REGIONS


class VoiceChangerError(RuntimeError):
    pass


def _get_blob_client(container=None):
    """Build an Azure BlobServiceClient from environment variables."""
    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError as e:
        raise VoiceChangerError(
            "azure-storage-blob is not installed. "
            "Add it to requirements.txt.") from e

    account = os.getenv("AZURE_STORAGE_ACCOUNT", "")
    key = os.getenv("AZURE_STORAGE_KEY", "")
    container_name = container or os.getenv("AZURE_STORAGE_CONTAINER", "speech-studio")

    if not account or not key:
        raise VoiceChangerError(
            "Azure Storage account/key not configured "
            "(set AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_KEY).")

    conn_str = (
        f"DefaultEndpointsProtocol=https;AccountName={account};"
        f"AccountKey={key};EndpointSuffix=core.windows.net"
    )
    service = BlobServiceClient.from_connection_string(conn_str)
    try:
        service.create_container(container_name)
    except Exception:
        # Container already exists
        pass
    return service, container_name


def upload_blob(audio_bytes, filename):
    """Upload audio bytes to Blob Storage, return a temporary SAS URL."""
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    from datetime import datetime, timedelta, timezone

    service, container_name = _get_blob_client()
    blob_name = f"voice-changer/{uuid.uuid4().hex}-{filename or 'audio.wav'}"
    blob_client = service.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(audio_bytes, overwrite=True)

    sas = generate_blob_sas(
        account_name=service.account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=service.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    return f"{blob_client.url}?{sas}"


def convert(speech_key, speech_region, audio_bytes, filename, target_voice):
    """Voice-convert the given audio to the target neural voice.

    Returns (audio_bytes_mp3, error_message_or_None).
    """
    if speech_region not in VOICE_CHANGER_REGIONS:
        return None, (
            f"Voice Changer is only available in {', '.join(VOICE_CHANGER_REGIONS)}. "
            f"Current region: {speech_region}")

    try:
        blob_url = upload_blob(audio_bytes, filename)
    except VoiceChangerError as e:
        return None, str(e)

    ssml = (
        '<speak version="1.0" '
        'xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:mstts="http://www.w3.org/2001/mstts" '
        'xml:lang="en-US">\n'
        f'  <voice name="{_xml_escape(target_voice)}">\n'
        f'    <mstts:voiceconversion url="{_xml_escape(blob_url)}"/>\n'
        '  </voice>\n'
        '</speak>'
    )

    tts_url = f"https://{speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-48khz-192kbitrate-mono-mp3",
        "User-Agent": "speech-studio",
    }
    resp = requests.post(tts_url, headers=headers, data=ssml.encode("utf-8"), timeout=120)
    if resp.status_code == 200:
        return resp.content, None
    return None, f"HTTP {resp.status_code}: {resp.text[:500]}"
