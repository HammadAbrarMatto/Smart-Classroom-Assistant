from gtts import gTTS
import io

# Languages supported by gTTS (subset of most common)
TTS_LANGUAGES = {
    "English":              "en",
    "Hindi":                "hi",
    "Tamil":                "ta",
    "Telugu":               "te",
    "Malayalam":            "ml",
    "Kannada":              "kn",
    "Bengali":              "bn",
    "Gujarati":             "gu",
    "Marathi":              "mr",
    "Punjabi":              "pa",
    "Urdu":                 "ur",
    "Arabic":               "ar",
    "French":               "fr",
    "German":               "de",
    "Spanish":              "es",
    "Portuguese":           "pt",
    "Russian":              "ru",
    "Japanese":             "ja",
    "Korean":               "ko",
    "Chinese (Simplified)": "zh-CN",
    "Italian":              "it",
    "Dutch":                "nl",
    "Turkish":              "tr",
    "Polish":               "pl",
    "Swedish":              "sv",
    "Indonesian":           "id",
    "Vietnamese":           "vi",
    "Thai":                 "th",
    "Greek":                "el",
    "Ukrainian":            "uk",
    "Filipino":             "tl",
    "Malay":                "ms",
    "Swahili":              "sw",
    "Afrikaans":            "af",
}


def speak_text(text: str, lang_code: str = "en") -> dict:
    """
    Convert text to speech using gTTS and return audio bytes.

    Args:
        text (str): Text to convert.
        lang_code (str): ISO 639-1 language code (e.g. "en", "hi").

    Returns:
        dict: {"success": bool, "audio_bytes": bytes, "error": str or None}
    """
    if not text or not text.strip():
        return {"success": False, "audio_bytes": None, "error": "No text to speak."}

    try:
        tts = gTTS(text=text[:3000], lang=lang_code, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return {"success": True, "audio_bytes": audio_buffer.read(), "error": None}
    except Exception as e:
        return {"success": False, "audio_bytes": None, "error": f"TTS error: {str(e)}"}


def get_tts_languages():
    return TTS_LANGUAGES
