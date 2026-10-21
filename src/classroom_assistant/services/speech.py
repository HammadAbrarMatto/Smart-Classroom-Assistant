"""Speech input.

* ``capture_once`` / ``LiveListener`` — microphone → Google Web Speech API
  (SpeechRecognition + PyAudio), with optional spectral noise reduction.
* ``transcribe_file`` — offline transcription of uploaded lecture recordings with
  **faster-whisper** (optional dependency, runs on CPU).
"""

from __future__ import annotations

import queue
import tempfile
import threading
from functools import lru_cache
from pathlib import Path

from ..config import settings
from ..result import Result

try:
    import noisereduce as nr
    import numpy as np

    _HAS_NR = True
except ImportError:  # optional
    _HAS_NR = False


def _denoise(audio):
    if not _HAS_NR:
        return audio
    import speech_recognition as sr

    try:
        raw = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32)
        clean = nr.reduce_noise(y=raw, sr=audio.sample_rate, stationary=False, prop_decrease=0.75)
        return sr.AudioData(clean.astype(np.int16).tobytes(), audio.sample_rate, audio.sample_width)
    except Exception:  # noqa: BLE001 – never lose audio because denoising failed
        return audio


def _recognizer(pause: float = 1.0):
    import speech_recognition as sr

    r = sr.Recognizer()
    r.dynamic_energy_threshold = True
    r.energy_threshold = 300
    r.pause_threshold = pause
    return r


def capture_once(language: str = "en-IN", timeout: int = 8, phrase_limit: int = 20) -> Result:
    """Record a single phrase from the default microphone and transcribe it."""
    try:
        import speech_recognition as sr
    except ImportError:
        return Result.fail("SpeechRecognition is not installed (pip install SpeechRecognition pyaudio).")

    r = _recognizer()
    try:
        with sr.Microphone(sample_rate=16000) as src:
            r.adjust_for_ambient_noise(src, duration=1)
            audio = r.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
        text = r.recognize_google(_denoise(audio), language=language)
        return Result.success(text, language=language)
    except sr.WaitTimeoutError:
        return Result.fail("No speech detected — speak louder or move closer to the mic.")
    except sr.UnknownValueError:
        return Result.fail("Could not understand the audio — try again in a quieter place.")
    except sr.RequestError as e:
        return Result.fail(f"Speech API error: {e}")
    except (OSError, AttributeError):
        return Result.fail("Microphone not found — check your audio input device / PyAudio install.")


class LiveListener:
    """Continuous background transcription. One instance per Streamlit session."""

    def __init__(self, language: str = "en-IN"):
        self.language = language
        self.results: queue.Queue = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="LiveListener")
        self.ready = False

    def start(self) -> LiveListener:
        self._thread.start()
        return self

    def stop(self, timeout: float = 3) -> None:
        self._stop.set()
        self._thread.join(timeout=timeout)

    @property
    def active(self) -> bool:
        return self._thread.is_alive() and not self._stop.is_set()

    def drain(self) -> list[Result]:
        out: list[Result] = []
        while True:
            try:
                out.append(self.results.get_nowait())
            except queue.Empty:
                return out

    def _run(self) -> None:
        try:
            import speech_recognition as sr

            r = _recognizer(pause=0.9)
            with sr.Microphone(sample_rate=16000) as src:
                r.adjust_for_ambient_noise(src, duration=1)
                self.ready = True
                while not self._stop.is_set():
                    try:
                        audio = r.listen(src, timeout=1, phrase_time_limit=20)
                    except sr.WaitTimeoutError:
                        continue
                    try:
                        text = r.recognize_google(_denoise(audio), language=self.language)
                        if text.strip():
                            self.results.put(Result.success(text, language=self.language))
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        self.results.put(Result.fail(f"Speech API error: {e}"))
        except Exception as e:  # noqa: BLE001
            self.results.put(Result.fail(f"Microphone error: {e}"))


def transcribe_wav(data: bytes, language: str = "en-IN") -> Result:
    """Transcribe WAV bytes (e.g. from ``st.audio_input`` in the browser) with Google Web Speech."""
    try:
        import io

        import speech_recognition as sr
    except ImportError:
        return Result.fail("SpeechRecognition is not installed.")
    r = _recognizer()
    try:
        with sr.AudioFile(io.BytesIO(data)) as src:
            audio = r.record(src)
        return Result.success(r.recognize_google(_denoise(audio), language=language), language=language)
    except sr.UnknownValueError:
        return Result.fail("Could not understand the recording — try again closer to the mic.")
    except sr.RequestError as e:
        return Result.fail(f"Speech API error: {e}")
    except Exception as e:  # noqa: BLE001
        return Result.fail(f"Could not read the recording: {e}")


# ── Offline transcription of recordings ─────────────────────────────────────
@lru_cache(maxsize=2)
def _whisper(model_size: str):
    from faster_whisper import WhisperModel

    return WhisperModel(model_size, device="auto", compute_type="int8")


def whisper_available() -> bool:
    try:
        import faster_whisper  # noqa: F401

        return True
    except ImportError:
        return False


def transcribe_file(data: bytes, suffix: str = ".wav", language: str | None = None,
                    model_size: str | None = None) -> Result:
    """Transcribe an uploaded audio/video file. ``language=None`` → auto-detect."""
    if not whisper_available():
        return Result.fail("faster-whisper is not installed — run: pip install faster-whisper")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        path = Path(tmp.name)
    try:
        model = _whisper(model_size or settings.whisper_model)
        segments, info = model.transcribe(str(path), language=language, vad_filter=True, beam_size=5)
        text = " ".join(s.text.strip() for s in segments).strip()
    except Exception as e:  # noqa: BLE001
        return Result.fail(f"Transcription failed: {e}")
    finally:
        path.unlink(missing_ok=True)
    if not text:
        return Result.fail("No speech found in the recording.")
    return Result.success(text, language=info.language, duration=round(info.duration, 1))
