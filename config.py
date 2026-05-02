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

# MAI-Transcribe-1 supported locales
MAI_TRANSCRIBE_LANGUAGES = [
    "ar-SA", "zh-CN", "cs-CZ", "da-DK", "nl-NL", "en-US", "fi-FI", "fr-FR",
    "de-DE", "hi-IN", "hu-HU", "id-ID", "it-IT", "ja-JP", "ko-KR", "nb-NO",
    "pl-PL", "pt-BR", "ro-RO", "ru-RU", "es-ES", "sv-SE", "th-TH", "tr-TR",
    "vi-VN",
]

# Multi-Talker (DragonHD mstts:dialog) presets per locale
MULTI_TALKER_PRESETS = {
    "en-US": {
        "voiceName": "en-us-multitalker-ava-andrew:DragonHDLatestNeural",
        "speakers": ["Ava", "Andrew"],
        "sample": "Ava: Good morning! How can I help you today?\nAndrew: Hi, I'd like to know more about your speech services.",
    },
    "zh-CN": {
        "voiceName": "zh-cn-multitalker-xiaochen-yunhan:DragonHDLatestNeural",
        "speakers": ["Xiaochen", "Yunhan"],
        "sample": "Xiaochen: 早上好!今天我可以为你做什么?\nYunhan: 你好,我想了解一下你们的语音服务。",
    },
    "ja-JP": {
        "voiceName": "ja-jp-multitalker-nanami-keita:DragonHDLatestNeural",
        "speakers": ["Nanami", "Keita"],
        "sample": "Nanami: おはようございます!何かお手伝いできることはありますか?\nKeita: 多人対話合成について教えてください。",
    },
    "ko-KR": {
        "voiceName": "ko-kr-multitalker-sunhi-injoon:DragonHDLatestNeural",
        "speakers": ["SunHi", "InJoon"],
        "sample": "SunHi: 안녕하세요, 무엇을 도와드릴까요?\nInJoon: 음성 서비스에 대해 알고 싶습니다.",
    },
    "fr-FR": {
        "voiceName": "fr-fr-multitalker-denise-henri:DragonHDLatestNeural",
        "speakers": ["Denise", "Henri"],
        "sample": "Denise: Bonjour ! Comment puis-je vous aider ?\nHenri: Je voudrais en savoir plus sur vos services vocaux.",
    },
    "de-DE": {
        "voiceName": "de-de-multitalker-katja-conrad:DragonHDLatestNeural",
        "speakers": ["Katja", "Conrad"],
        "sample": "Katja: Guten Morgen! Wie kann ich Ihnen helfen?\nConrad: Ich möchte mehr über Ihre Sprachdienste erfahren.",
    },
    "es-ES": {
        "voiceName": "es-es-multitalker-elvira-alvaro:DragonHDLatestNeural",
        "speakers": ["Elvira", "Alvaro"],
        "sample": "Elvira: ¡Buenos días! ¿En qué puedo ayudarle?\nAlvaro: Quisiera saber más sobre sus servicios de voz.",
    },
    "it-IT": {
        "voiceName": "it-it-multitalker-elsa-diego:DragonHDLatestNeural",
        "speakers": ["Elsa", "Diego"],
        "sample": "Elsa: Buongiorno! Come posso aiutarla?\nDiego: Vorrei saperne di più sui vostri servizi vocali.",
    },
    "pt-BR": {
        "voiceName": "pt-br-multitalker-francisca-antonio:DragonHDLatestNeural",
        "speakers": ["Francisca", "Antonio"],
        "sample": "Francisca: Bom dia! Como posso ajudá-lo?\nAntonio: Gostaria de saber mais sobre seus serviços de voz.",
    },
}

# Voice Changer target voices (regions limited to eastus/westeurope/southeastasia)
VOICE_CHANGER_TARGETS = {
    "en-US Ava": "en-US-AvaNeural",
    "en-US Andrew": "en-US-AndrewNeural",
    "en-US Emma": "en-US-EmmaNeural",
    "en-US Brian": "en-US-BrianNeural",
    "en-US Jenny": "en-US-JennyNeural",
    "en-US Aria": "en-US-AriaNeural",
    "en-US Guy": "en-US-GuyNeural",
}
VOICE_CHANGER_REGIONS = ["eastus", "westeurope", "southeastasia"]

# Video Translation supported locales
VIDEO_TRANSLATION_LOCALES = [
    "en-US", "en-GB", "zh-CN", "zh-TW", "ja-JP", "ko-KR", "es-ES", "es-MX",
    "fr-FR", "de-DE", "it-IT", "pt-BR", "pt-PT", "ru-RU", "ar-SA", "hi-IN",
    "th-TH", "vi-VN", "id-ID", "ms-MY", "nl-NL", "pl-PL", "tr-TR", "sv-SE",
    "da-DK", "fi-FI", "nb-NO", "uk-UA", "cs-CZ", "he-IL",
]

# Personal Voice (Voice Creation)
PERSONAL_VOICE_LOCALES = [
    "en-US", "en-GB", "zh-CN", "ja-JP", "ko-KR", "de-DE", "fr-FR",
    "es-ES", "it-IT", "pt-BR",
]
PERSONAL_VOICE_MODELS = ["DragonLatestNeural", "PhoenixLatestNeural"]
PERSONAL_VOICE_CONSENT_TEMPLATE = (
    "I {voice_talent_name} am aware that recordings of my voice will be used by "
    "{company_name} to create and use a synthetic version of my voice."
)

# Podcast Agent
PODCAST_REGIONS = [
    "westeurope", "centralus", "eastus", "eastus2", "northcentralus",
    "southcentralus", "westcentralus", "westus", "westus2", "westus3",
]
PODCAST_STYLES = ["Default", "Professional", "Casual"]
PODCAST_LENGTHS = ["VeryShort", "Short", "Medium", "Long", "VeryLong"]
PODCAST_HOST_TYPES = ["OneHost", "TwoHosts"]
PODCAST_LOCALES = [
    "en-US", "en-GB", "zh-CN", "ja-JP", "ko-KR", "fr-FR", "de-DE",
    "es-ES", "it-IT", "pt-BR",
]

# Azure regions (for region selectors)
AZURE_SPEECH_REGIONS = [
    "eastus", "eastus2", "westus", "westus2", "westus3", "centralus",
    "northcentralus", "southcentralus", "canadacentral", "brazilsouth",
    "northeurope", "westeurope", "uksouth", "francecentral", "germanywestcentral",
    "swedencentral", "switzerlandnorth", "eastasia", "southeastasia",
    "japaneast", "japanwest", "koreacentral", "australiaeast", "centralindia",
]

