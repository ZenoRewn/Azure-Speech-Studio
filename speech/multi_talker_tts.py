"""Multi-Talker TTS via Azure DragonHD mstts:dialog SSML."""

from xml.sax.saxutils import escape as _xml_escape
import azure.cognitiveservices.speech as speechsdk


def build_ssml(content, voice_name, locale="en-US"):
    """Build multi-speaker SSML from 'Speaker: text' lines."""
    turns = []
    for raw_line in (content or "").splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        speaker, text = line.split(":", 1)
        speaker = speaker.strip()
        text = text.strip()
        if not speaker or not text:
            continue
        turns.append(
            f'      <mstts:turn speaker="{_xml_escape(speaker)}">'
            f'{_xml_escape(text)}</mstts:turn>'
        )

    turns_xml = "\n".join(turns) if turns else ""
    return (
        '<speak version="1.0" '
        'xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:mstts="http://www.w3.org/2001/mstts" '
        f'xml:lang="{_xml_escape(locale)}">\n'
        f'  <voice name="{_xml_escape(voice_name)}">\n'
        '    <mstts:dialog>\n'
        f'{turns_xml}\n'
        '    </mstts:dialog>\n'
        '  </voice>\n'
        '</speak>'
    )


def synthesize(speech_key, speech_region, ssml):
    """Synthesize multi-talker SSML to WAV audio bytes."""
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=speech_region)
    # DragonHD voices support high-quality output
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_ssml_async(ssml).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data, None

    details = "unknown"
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        details = f"{cancellation.reason}: {cancellation.error_details}"
    return None, details
