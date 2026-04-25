from deep_translator import GoogleTranslator

# Comprehensive language map (name → ISO 639-1 code)
ALL_LANGUAGES = {
    "Afrikaans": "af", "Albanian": "sq", "Amharic": "am", "Arabic": "ar",
    "Armenian": "hy", "Azerbaijani": "az", "Basque": "eu", "Belarusian": "be",
    "Bengali": "bn", "Bosnian": "bs", "Bulgarian": "bg", "Catalan": "ca",
    "Cebuano": "ceb", "Chinese (Simplified)": "zh-CN", "Chinese (Traditional)": "zh-TW",
    "Croatian": "hr", "Czech": "cs", "Danish": "da", "Dutch": "nl",
    "English": "en", "Esperanto": "eo", "Estonian": "et", "Filipino": "tl",
    "Finnish": "fi", "French": "fr", "Galician": "gl", "Georgian": "ka",
    "German": "de", "Greek": "el", "Gujarati": "gu", "Haitian Creole": "ht",
    "Hausa": "ha", "Hebrew": "iw", "Hindi": "hi", "Hungarian": "hu",
    "Icelandic": "is", "Igbo": "ig", "Indonesian": "id", "Irish": "ga",
    "Italian": "it", "Japanese": "ja", "Javanese": "jw", "Kannada": "kn",
    "Kazakh": "kk", "Khmer": "km", "Korean": "ko", "Kurdish": "ku",
    "Kyrgyz": "ky", "Lao": "lo", "Latin": "la", "Latvian": "lv",
    "Lithuanian": "lt", "Luxembourgish": "lb", "Macedonian": "mk",
    "Malagasy": "mg", "Malay": "ms", "Malayalam": "ml", "Maltese": "mt",
    "Marathi": "mr", "Mongolian": "mn", "Myanmar (Burmese)": "my",
    "Nepali": "ne", "Norwegian": "no", "Odia (Oriya)": "or", "Pashto": "ps",
    "Persian": "fa", "Polish": "pl", "Portuguese": "pt", "Punjabi": "pa",
    "Romanian": "ro", "Russian": "ru", "Samoan": "sm", "Serbian": "sr",
    "Sesotho": "st", "Shona": "sn", "Sindhi": "sd", "Sinhala": "si",
    "Slovak": "sk", "Slovenian": "sl", "Somali": "so", "Spanish": "es",
    "Sundanese": "su", "Swahili": "sw", "Swedish": "sv", "Tajik": "tg",
    "Tamil": "ta", "Tatar": "tt", "Telugu": "te", "Thai": "th",
    "Turkish": "tr", "Turkmen": "tk", "Ukrainian": "uk", "Urdu": "ur",
    "Uyghur": "ug", "Uzbek": "uz", "Vietnamese": "vi", "Welsh": "cy",
    "Xhosa": "xh", "Yiddish": "yi", "Yoruba": "yo", "Zulu": "zu",
}

# Quick-access Indian regional languages
INDIAN_LANGUAGES = {
    "Hindi": "hi", "Tamil": "ta", "Telugu": "te", "Malayalam": "ml",
    "Kannada": "kn", "Bengali": "bn", "Gujarati": "gu", "Marathi": "mr",
    "Punjabi": "pa", "Urdu": "ur", "Odia (Oriya)": "or",
}


def translate_text(text: str, target_lang_code: str, source_lang: str = "auto") -> dict:
    """
    Translate text using deep-translator GoogleTranslator.

    Args:
        text (str): Input text.
        target_lang_code (str): ISO 639-1 code of target language.
        source_lang (str): Source language code or 'auto'.

    Returns:
        dict: {"success": bool, "translated_text": str, "error": str or None}
    """
    if not text or not text.strip():
        return {"success": False, "translated_text": "", "error": "Input text is empty."}

    # Split into chunks of 4500 chars to stay within API limits
    chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
    translated_chunks = []

    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang_code)
        for chunk in chunks:
            translated_chunks.append(translator.translate(chunk))
        return {
            "success": True,
            "translated_text": " ".join(translated_chunks),
            "error": None
        }
    except Exception as e:
        return {"success": False, "translated_text": "", "error": f"Translation failed: {str(e)}"}


def translate_hindi_to_english(hindi_text: str) -> dict:
    """Translate Hindi text to English."""
    return translate_text(hindi_text, target_lang_code="en", source_lang="hi")


def get_target_languages():
    return {k: v for k, v in ALL_LANGUAGES.items() if k != "English"}

def get_indian_languages():
    return INDIAN_LANGUAGES

def get_all_languages():
    return ALL_LANGUAGES
