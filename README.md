# 🎓 Smart Classroom Assistant

[![CI](https://github.com/HammadAbrarMatto/Smart-Classroom-Assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/HammadAbrarMatto/Smart-Classroom-Assistant/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-app-red)
![Gemini](https://img.shields.io/badge/Gemini-optional-8e44ad)

An AI classroom companion that turns **speech, text, web pages, documents and lecture recordings** into accessible learning material: translated into 100+ languages, simplified to a chosen reading level, summarised, turned into a quiz, and read aloud.

Built for multilingual classrooms — a teacher can lecture in Hindi, Tamil or Urdu and students get English text, a simplified version, revision notes and audio.

---

## ✨ Features

| | Feature | How |
|---|---|---|
| 🎙️ | **Speech input** — record in the browser, listen once, or live continuous captioning | SpeechRecognition (Google Web Speech) + noise reduction |
| 🎧 | **Lecture recordings** — upload mp3/wav/m4a/mp4 and transcribe offline | **faster-whisper** (auto language detection, VAD) |
| 🌐 | **Web pages & documents** — URL, PDF, DOCX, TXT, MD | BeautifulSoup, pdfplumber, python-docx |
| 🔤 | **Translation** into 100+ languages; non-English speech is auto-translated to English | deep-translator |
| 💡 | **Simplification** to a reading level (primary, middle, high school, English learner) with key points + glossary | **Gemini** (offline rule-based fallback) |
| 🧾 | **Summaries** as revision notes | Gemini |
| ❓ | **Auto-generated quizzes** with instant marking and explanations | Gemini (structured JSON output) |
| 💬 | **Ask the lecture** — Q&A grounded only in the captured text | Gemini |
| 🔊 | **Text-to-speech** in 30+ languages, any length | gTTS (chunked) |
| 📋 | **Session history** exported as Markdown class notes | — |

The AI features are optional: with no API key the app runs fully on free, keyless services and the rule-based simplifier.

---

## 🆕 What changed in v2

- **New:** Gemini-powered simplification by reading level, summaries, quizzes, and lecture Q&A
- **New:** offline Whisper transcription of uploaded recordings
- **New:** in-browser recording (`st.audio_input`), so speech input works when the app is deployed, not only on the machine running it
- **New:** Markdown notes export; glossary of difficult terms
- **Fixed:** non-English speech was always translated *as Hindi* — Tamil, Bengali, French etc. now use their own source language
- **Fixed:** translation re-ran on every live-caption refresh; results are now cached
- **Fixed:** long sentences were truncated by the simplifier; they are now split, so no content is lost
- **Fixed:** web/PDF text capped at 3,000 characters → configurable (default 20,000), PDF page limit raised
- **Fixed:** HTML injection through history entries; the live listener now belongs to one session instead of a module-level global
- **Cleanup:** removed the `script.py` code generator; modules moved into a `src/` package; dark theme moved from ~140 lines of CSS overrides into `.streamlit/config.toml`; tests + CI added

---

## 📂 Project structure

```
Smart-Classroom-Assistant/
├── app.py                          # Streamlit UI
├── src/classroom_assistant/
│   ├── config.py                   # settings from .env / Streamlit secrets
│   ├── languages.py                # speech / translation / TTS language tables
│   ├── notes.py                    # history + Markdown export
│   ├── result.py                   # uniform Result type
│   └── services/
│       ├── speech.py               # mic, browser recording, live listener, Whisper
│       ├── translation.py          # sentence-aware chunked translation
│       ├── simplify.py             # offline rule-based simplifier
│       ├── llm.py                  # Gemini: simplify · summarise · quiz · ask
│       ├── content.py              # URL / PDF / DOCX / TXT extraction
│       └── tts.py                  # gTTS with chunking
├── tests/                          # pytest (services + headless UI tests)
├── .streamlit/config.toml          # theme
├── .env.example
└── requirements.txt
```

---

## ▶️ Run it

```bash
git clone https://github.com/HammadAbrarMatto/Smart-Classroom-Assistant.git
cd Smart-Classroom-Assistant
python -m venv venv
venv\Scripts\activate                 # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env                # then paste your GEMINI_API_KEY (optional)
streamlit run app.py
```

- Free Gemini key: <https://aistudio.google.com/app/apikey>
- Linux users need PortAudio for the live microphone: `sudo apt install portaudio19-dev`
- The first Whisper transcription downloads the model (`small` ≈ 480 MB). Use `WHISPER_MODEL=base` for a faster, lighter option.

### Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | – | enables AI simplification, summary, quiz, Q&A |
| `GEMINI_MODEL` | `gemini-3.6-flash` | any Gemini text model |
| `WHISPER_MODEL` | `small` | `tiny` … `large-v3`, `turbo` |
| `MAX_INPUT_CHARS` | `20000` | cap on text taken from URLs and files |
| `MAX_PDF_PAGES` | `40` | pages read from a PDF |

---

## ✅ Live check

`python scripts/live_check.py` calls the real services: Google Translate (including a Tamil → English source-language check), gTTS, web fetching, a speech round-trip (gTTS audio → Whisper) and every Gemini feature. It prints PASS / FAIL / SKIP for each.

## 🧪 Tests

```bash
pip install pytest ruff
pytest -q
ruff check .
```

Network services (translation, Gemini) are mocked, so the suite runs offline.

---

## 📌 Use cases

- Live captions + translation for multilingual classrooms
- Turning a recorded lecture into notes and a self-test quiz
- Simplifying reading material for younger students or English learners
- Audio versions of material for visually impaired learners

## 📄 License

MIT
