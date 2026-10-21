"""Language tables shared by speech recognition, translation and TTS."""

from __future__ import annotations

# Speech-recognition locales (Google Web Speech API)
SPEECH_LANGUAGES: dict[str, str] = {
    "English (India)": "en-IN", "English (US)": "en-US", "English (UK)": "en-GB",
    "Hindi": "hi-IN", "Urdu": "ur-IN", "Tamil": "ta-IN", "Telugu": "te-IN", "Kannada": "kn-IN",
    "Malayalam": "ml-IN", "Bengali": "bn-IN", "Gujarati": "gu-IN", "Marathi": "mr-IN", "Punjabi": "pa-IN",
    "Arabic": "ar-SA", "Chinese (Simplified)": "zh-CN", "Chinese (Traditional)": "zh-TW",
    "French": "fr-FR", "German": "de-DE", "Spanish": "es-ES", "Portuguese": "pt-PT", "Russian": "ru-RU",
    "Japanese": "ja-JP", "Korean": "ko-KR", "Italian": "it-IT", "Dutch": "nl-NL", "Turkish": "tr-TR",
    "Polish": "pl-PL", "Swedish": "sv-SE", "Indonesian": "id-ID", "Vietnamese": "vi-VN", "Thai": "th-TH",
    "Greek": "el-GR", "Ukrainian": "uk-UA", "Filipino": "fil-PH", "Swahili": "sw-KE", "Afrikaans": "af-ZA",
}

# Translation targets (Google Translate codes via deep-translator)
TRANSLATION_LANGUAGES: dict[str, str] = {
    "Afrikaans": "af", "Albanian": "sq", "Amharic": "am", "Arabic": "ar", "Armenian": "hy",
    "Azerbaijani": "az", "Basque": "eu", "Belarusian": "be", "Bengali": "bn", "Bosnian": "bs",
    "Bulgarian": "bg", "Catalan": "ca", "Cebuano": "ceb", "Chinese (Simplified)": "zh-CN",
    "Chinese (Traditional)": "zh-TW", "Croatian": "hr", "Czech": "cs", "Danish": "da", "Dutch": "nl",
    "English": "en", "Esperanto": "eo", "Estonian": "et", "Filipino": "tl", "Finnish": "fi", "French": "fr",
    "Galician": "gl", "Georgian": "ka", "German": "de", "Greek": "el", "Gujarati": "gu",
    "Haitian Creole": "ht", "Hausa": "ha", "Hebrew": "iw", "Hindi": "hi", "Hungarian": "hu",
    "Icelandic": "is", "Igbo": "ig", "Indonesian": "id", "Irish": "ga", "Italian": "it", "Japanese": "ja",
    "Javanese": "jw", "Kannada": "kn", "Kazakh": "kk", "Khmer": "km", "Korean": "ko", "Kurdish": "ku",
    "Kyrgyz": "ky", "Lao": "lo", "Latin": "la", "Latvian": "lv", "Lithuanian": "lt", "Luxembourgish": "lb",
    "Macedonian": "mk", "Malagasy": "mg", "Malay": "ms", "Malayalam": "ml", "Maltese": "mt", "Marathi": "mr",
    "Mongolian": "mn", "Myanmar (Burmese)": "my", "Nepali": "ne", "Norwegian": "no", "Odia (Oriya)": "or",
    "Pashto": "ps", "Persian": "fa", "Polish": "pl", "Portuguese": "pt", "Punjabi": "pa", "Romanian": "ro",
    "Russian": "ru", "Samoan": "sm", "Serbian": "sr", "Sesotho": "st", "Shona": "sn", "Sindhi": "sd",
    "Sinhala": "si", "Slovak": "sk", "Slovenian": "sl", "Somali": "so", "Spanish": "es", "Sundanese": "su",
    "Swahili": "sw", "Swedish": "sv", "Tajik": "tg", "Tamil": "ta", "Tatar": "tt", "Telugu": "te",
    "Thai": "th", "Turkish": "tr", "Turkmen": "tk", "Ukrainian": "uk", "Urdu": "ur", "Uyghur": "ug",
    "Uzbek": "uz", "Vietnamese": "vi", "Welsh": "cy", "Xhosa": "xh", "Yiddish": "yi", "Yoruba": "yo",
    "Zulu": "zu",
}

# Text-to-speech voices available in gTTS
TTS_LANGUAGES: dict[str, str] = {
    "English": "en", "Hindi": "hi", "Urdu": "ur", "Tamil": "ta", "Telugu": "te", "Malayalam": "ml",
    "Kannada": "kn", "Bengali": "bn", "Gujarati": "gu", "Marathi": "mr", "Punjabi": "pa", "Arabic": "ar",
    "French": "fr", "German": "de", "Spanish": "es", "Portuguese": "pt", "Russian": "ru", "Japanese": "ja",
    "Korean": "ko", "Chinese (Simplified)": "zh-CN", "Italian": "it", "Dutch": "nl", "Turkish": "tr",
    "Polish": "pl", "Swedish": "sv", "Indonesian": "id", "Vietnamese": "vi", "Thai": "th", "Greek": "el",
    "Ukrainian": "uk", "Filipino": "tl", "Malay": "ms", "Swahili": "sw", "Afrikaans": "af",
}

_SPECIAL = {"zh-CN": "zh-CN", "zh-TW": "zh-TW", "fil-PH": "tl"}


def speech_to_translation_code(locale: str) -> str:
    """'hi-IN' → 'hi', 'zh-TW' → 'zh-TW', 'fil-PH' → 'tl'."""
    return _SPECIAL.get(locale, locale.split("-")[0].lower())


def is_english(locale_or_code: str) -> bool:
    return locale_or_code.lower().startswith("en")


def tts_code_for(language_name: str, fallback: str = "en") -> str:
    return TTS_LANGUAGES.get(language_name, fallback)
