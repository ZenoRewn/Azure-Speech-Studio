"""Constants and configuration maps extracted from the Streamlit app."""

LANGUAGE_OPTIONS = {
    "zh-CN": "中文 (简体)",
    "en-US": "English (US)",
    "ja-JP": "日本語",
    "ko-KR": "한국어",
    "fr-FR": "Français",
    "de-DE": "Deutsch",
    "id-ID": "Bahasa Indonesia",
    "hi-IN": "हिन्दी (Hindi)",
    "ta-IN": "தமிழ் (Tamil)",
    "te-IN": "తెలుగు (Telugu)",
    "bn-IN": "বাংলা (Bengali)",
    "mr-IN": "मराठी (Marathi)",
    "gu-IN": "ગુજરાતી (Gujarati)",
    "kn-IN": "ಕನ್ನಡ (Kannada)",
    "ml-IN": "മലയാളം (Malayalam)",
    "pa-IN": "ਪੰਜਾਬੀ (Punjabi)",
    "ur-IN": "اردو (Urdu)",
}

# Speech Translation target languages
TRANSLATION_TARGET_LANGUAGES = {
    "English": "en",
    "Chinese (Simplified)": "zh-Hans",
    "Chinese (Traditional)": "zh-Hant",
    "Japanese": "ja",
    "Korean": "ko",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Arabic": "ar",
}

# LLM Speech target language codes
LLM_TARGET_LANG_MAP = {
    "English": "en",
    "Chinese (Simplified)": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "Portuguese": "pt",
}

# TTS locale mapping for LLM Speech "Read Aloud"
TTS_LOCALE_MAP = {
    "English": "en-US",
    "Chinese (Simplified)": "zh-CN",
    "Japanese": "ja-JP",
    "Korean": "ko-KR",
    "French": "fr-FR",
    "German": "de-DE",
    "Spanish": "es-ES",
    "Italian": "it-IT",
    "Portuguese": "pt-BR",
}

# Live Interpreter standard voices
LI_STANDARD_VOICES = {
    "en": "en-US-AvaMultilingualNeural",
    "zh-Hans": "zh-CN-XiaoxiaoMultilingualNeural",
    "zh-Hant": "zh-CN-XiaoxiaoMultilingualNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "es": "es-ES-ElviraNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "ar": "ar-SA-ZariyahNeural",
}

# Voice Live model tiers
VL_MODEL_TIERS = {
    "Pro": ["gpt-realtime", "gpt-4o", "gpt-4.1", "gpt-5", "gpt-5-chat"],
    "Basic": ["gpt-realtime-mini", "gpt-4o-mini", "gpt-4.1-mini", "gpt-5-mini"],
    "Lite": ["gpt-5-nano", "phi4-mm-realtime", "phi4-mini"],
}

# Voice Live voice providers
VL_VOICE_PROVIDERS = {
    "OpenAI": {
        "Alloy": "alloy", "Ash": "ash", "Ballad": "ballad",
        "Coral": "coral", "Echo": "echo", "Sage": "sage",
        "Shimmer": "shimmer", "Verse": "verse", "Marin": "marin", "Cedar": "cedar",
    },
    "Azure Neural": {
        "Ava (en-US, DragonHD)": "en-US-Ava:DragonHDLatestNeural",
        "Andrew (en-US, DragonHD)": "en-US-Andrew:DragonHDLatestNeural",
        "Emma (en-US, DragonHD)": "en-US-Emma:DragonHDLatestNeural",
        "Brian (en-US, DragonHD)": "en-US-Brian:DragonHDLatestNeural",
        "Ava Multilingual (en-US)": "en-US-AvaMultilingualNeural",
        "Andrew Multilingual (en-US)": "en-US-AndrewMultilingualNeural",
        "Xiaoxiao Multilingual (zh-CN)": "zh-CN-XiaoxiaoMultilingualNeural",
        "Nanami (ja-JP)": "ja-JP-NanamiNeural",
        "SunHi (ko-KR)": "ko-KR-SunHiNeural",
        "Denise (fr-FR)": "fr-FR-DeniseNeural",
        "Katja (de-DE)": "de-DE-KatjaNeural",
    },
}

# Voice Live ASR models
VL_ASR_MODELS = ["azure-speech", "gpt-4o-mini-transcribe", "gpt-4o-transcribe", "whisper-1"]

# Voice Live target languages
VL_TARGET_LANGUAGES = {
    "Auto-detect": "", "English (US)": "en-US", "English": "en",
    "Chinese": "zh", "Chinese + English": "en,zh", "Japanese": "ja",
    "Korean": "ko", "French": "fr", "German": "de", "Spanish": "es",
    "Italian": "it", "Portuguese": "pt", "Russian": "ru", "Arabic": "ar", "Hindi": "hi",
}

# TTS voice options for Text-to-Speech tab
TTS_VOICE_OPTIONS = {
    "zh-CN Xiaoxiao (Female)": "zh-CN-XiaoxiaoNeural",
    "zh-CN Yunxi (Male)": "zh-CN-YunxiNeural",
    "zh-CN Xiaoyi (Female)": "zh-CN-XiaoyiNeural",
    "en-US Ava Multilingual (Female)": "en-US-AvaMultilingualNeural",
    "en-US Andrew Multilingual (Male)": "en-US-AndrewMultilingualNeural",
    "en-US Jenny (Female)": "en-US-JennyNeural",
    "ja-JP Nanami (Female)": "ja-JP-NanamiNeural",
    "ja-JP Keita (Male)": "ja-JP-KeitaNeural",
    "ko-KR SunHi (Female)": "ko-KR-SunHiNeural",
    "ko-KR InJoon (Male)": "ko-KR-InJoonNeural",
    "fr-FR Denise (Female)": "fr-FR-DeniseNeural",
    "fr-FR Henri (Male)": "fr-FR-HenriNeural",
    "de-DE Katja (Female)": "de-DE-KatjaNeural",
    "de-DE Conrad (Male)": "de-DE-ConradNeural",
}
