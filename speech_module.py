import speech_recognition as sr
import threading
import queue
import numpy as np
import io, wave

# ── Optional noise reduction ─────────────────────────────────────────
try:
    import noisereduce as nr
    _NR = True
except ImportError:
    _NR = False

SUPPORTED_INPUT_LANGUAGES = {
    "English (India)":         "en-IN",
    "English (US)":            "en-US",
    "English (UK)":            "en-GB",
    "Hindi":                   "hi-IN",
    "Tamil":                   "ta-IN",
    "Telugu":                  "te-IN",
    "Kannada":                 "kn-IN",
    "Malayalam":               "ml-IN",
    "Bengali":                 "bn-IN",
    "Gujarati":                "gu-IN",
    "Marathi":                 "mr-IN",
    "Punjabi":                 "pa-IN",
    "Urdu":                    "ur-IN",
    "Arabic":                  "ar-SA",
    "Chinese (Simplified)":    "zh-CN",
    "Chinese (Traditional)":   "zh-TW",
    "French":                  "fr-FR",
    "German":                  "de-DE",
    "Spanish":                 "es-ES",
    "Portuguese":              "pt-PT",
    "Russian":                 "ru-RU",
    "Japanese":                "ja-JP",
    "Korean":                  "ko-KR",
    "Italian":                 "it-IT",
    "Dutch":                   "nl-NL",
    "Turkish":                 "tr-TR",
    "Polish":                  "pl-PL",
    "Swedish":                 "sv-SE",
    "Indonesian":              "id-ID",
    "Vietnamese":              "vi-VN",
    "Thai":                    "th-TH",
    "Greek":                   "el-GR",
    "Ukrainian":               "uk-UA",
    "Filipino":                "fil-PH",
    "Swahili":                 "sw-KE",
    "Afrikaans":               "af-ZA",
}

NON_ENGLISH = {
    "hi-IN","ta-IN","te-IN","kn-IN","ml-IN",
    "bn-IN","gu-IN","mr-IN","pa-IN","ur-IN"
}

# ── Global listener state ────────────────────────────────────────────
_stop_event:  threading.Event  | None = None
_listener_th: threading.Thread | None = None


# ════════════════════════════════════════════════════════════════════
# NOISE REDUCTION HELPER
# ════════════════════════════════════════════════════════════════════
def _denoise_audio(audio: sr.AudioData) -> sr.AudioData:
    """Apply spectral-gating noise reduction to an AudioData object."""
    if not _NR:
        return audio
    try:
        raw   = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32)
        clean = nr.reduce_noise(y=raw, sr=audio.sample_rate,
                                stationary=False, prop_decrease=0.75)
        return sr.AudioData(clean.astype(np.int16).tobytes(),
                            audio.sample_rate, audio.sample_width)
    except Exception:
        return audio          # fall back to original on any error


# ════════════════════════════════════════════════════════════════════
# SINGLE-SHOT CAPTURE
# ════════════════════════════════════════════════════════════════════
def capture_speech(language: str = "en-IN",
                   timeout: int  = 8,
                   phrase_limit: int = 15) -> dict:
    """
    Open mic, wait for speech, record one phrase, denoise, recognise.
    Returns dict with keys: success, text, error, needs_translation, raw_language
    """
    r   = sr.Recognizer()
    r.dynamic_energy_threshold = True
    r.energy_threshold         = 300      # start low; dynamic mode raises it
    r.pause_threshold          = 1.0      # seconds of silence = end of phrase

    try:
        with sr.Microphone(sample_rate=16000) as src:
            # Calibrate for 1 second of ambient noise
            r.adjust_for_ambient_noise(src, duration=1)
            # Listen – wait up to `timeout` s for speech, record up to `phrase_limit` s
            audio = r.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)

        audio   = _denoise_audio(audio)
        text    = r.recognize_google(audio, language=language)
        return {
            "success": True, "text": text, "error": None,
            "needs_translation": language in NON_ENGLISH,
            "raw_language": language,
        }

    except sr.WaitTimeoutError:
        return {"success": False, "text": "",
                "error": "⏱️ No speech detected within timeout. Speak louder or move closer to the mic.",
                "needs_translation": False, "raw_language": language}
    except sr.UnknownValueError:
        return {"success": False, "text": "",
                "error": "🔇 Could not understand. Speak clearly in a quiet environment.",
                "needs_translation": False, "raw_language": language}
    except sr.RequestError as e:
        return {"success": False, "text": "",
                "error": f"🌐 Google API error: {e}",
                "needs_translation": False, "raw_language": language}
    except OSError:
        return {"success": False, "text": "",
                "error": "🎙️ Microphone not found. Check audio input device.",
                "needs_translation": False, "raw_language": language}
    except Exception as e:
        return {"success": False, "text": "",
                "error": f"❌ Unexpected error: {e}",
                "needs_translation": False, "raw_language": language}


# ════════════════════════════════════════════════════════════════════
# CONTINUOUS LISTENER WORKER
# ════════════════════════════════════════════════════════════════════
def _worker(result_q: queue.Queue, stop_ev: threading.Event, language: str):
    """
    Background thread: mic stays open, we call listen(timeout=1) in a loop.
    - timeout=1  → raises WaitTimeoutError every second if silence,
                   letting us check stop_ev without blocking forever.
    - phrase_time_limit=20 → max 20 s per phrase
    """
    r   = sr.Recognizer()
    r.dynamic_energy_threshold = True
    r.energy_threshold         = 300
    r.pause_threshold          = 0.9

    try:
        with sr.Microphone(sample_rate=16000) as src:
            r.adjust_for_ambient_noise(src, duration=1)
            result_q.put({"status": "ready"})      # signal: mic is open

            while not stop_ev.is_set():
                try:
                    audio = r.listen(src, timeout=1, phrase_time_limit=20)
                except sr.WaitTimeoutError:
                    continue           # silence tick — loop back & check stop_ev

                # We have audio — process it
                audio = _denoise_audio(audio)
                try:
                    text = r.recognize_google(audio, language=language)
                    if text.strip():
                        result_q.put({
                            "success": True,
                            "text": text,
                            "needs_translation": language in NON_ENGLISH,
                            "raw_language": language,
                        })
                except sr.UnknownValueError:
                    pass               # unclear audio — ignore silently
                except sr.RequestError as e:
                    result_q.put({"success": False, "text": "",
                                  "error": f"API error: {e}",
                                  "needs_translation": False,
                                  "raw_language": language})

    except OSError as e:
        result_q.put({"success": False, "text": "",
                      "error": f"🎙️ Mic error: {e}",
                      "needs_translation": False, "raw_language": language})
    except Exception as e:
        result_q.put({"success": False, "text": "",
                      "error": f"❌ Listener crashed: {e}",
                      "needs_translation": False, "raw_language": language})


# ════════════════════════════════════════════════════════════════════
# PUBLIC: start / stop continuous
# ════════════════════════════════════════════════════════════════════
def start_continuous_listening(result_q: queue.Queue,
                                language: str = "en-IN") -> threading.Event:
    """
    Spin up the background listener thread.
    Returns the stop_event — set it to stop listening.
    """
    global _stop_event, _listener_th

    # Kill any previous listener
    if _stop_event:
        _stop_event.set()
    if _listener_th and _listener_th.is_alive():
        _listener_th.join(timeout=3)

    _stop_event  = threading.Event()
    _listener_th = threading.Thread(
        target=_worker,
        args=(result_q, _stop_event, language),
        daemon=True,
        name="SpeechListener",
    )
    _listener_th.start()
    return _stop_event


def stop_continuous_listening():
    """Signal the listener thread to stop."""
    global _stop_event
    if _stop_event:
        _stop_event.set()


def is_listening_active() -> bool:
    return bool(_listener_th and _listener_th.is_alive()
                and _stop_event and not _stop_event.is_set())


def get_supported_input_languages():
    return SUPPORTED_INPUT_LANGUAGES

def get_non_english_codes():
    return NON_ENGLISH
