"""Text-to-Speech synthesis using Azure Speech SDK."""

import azure.cognitiveservices.speech as speechsdk


def synthesize_text(speech_key, speech_region, text, voice_name):
    """Synthesize plain text to WAV audio bytes."""
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=speech_region)
    speech_config.speech_synthesis_voice_name = voice_name

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    return None


def synthesize_ssml(speech_key, speech_region, ssml):
    """Synthesize SSML to WAV audio bytes. Voice is specified within the SSML."""
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=speech_region)

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_ssml_async(ssml).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    return None

