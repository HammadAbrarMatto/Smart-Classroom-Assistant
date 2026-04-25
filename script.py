
# ─── tts_module.py ──────────────────────────────────────────────────
tts_module = '''from gtts import gTTS
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
'''

# ─── speech_module.py (infinite listening + stop) ───────────────────
speech_module_v3 = '''import speech_recognition as sr
import queue
import threading

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
    "Hebrew":                  "iw-IL",
    "Persian (Farsi)":         "fa-IR",
    "Ukrainian":               "uk-UA",
    "Czech":                   "cs-CZ",
    "Romanian":                "ro-RO",
    "Hungarian":               "hu-HU",
    "Finnish":                 "fi-FI",
    "Danish":                  "da-DK",
    "Norwegian":               "no-NO",
    "Filipino":                "fil-PH",
    "Swahili":                 "sw-KE",
    "Afrikaans":               "af-ZA",
}

HINDI_FAMILY = {
    "hi-IN","ta-IN","te-IN","kn-IN","ml-IN",
    "bn-IN","gu-IN","mr-IN","pa-IN","ur-IN"
}


# ── Single-shot capture ──────────────────────────────────────────────
def capture_speech(language="en-IN", timeout=5, phrase_limit=10):
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        text = recognizer.recognize_google(audio, language=language)
        return {"success": True, "text": text, "error": None,
                "raw_language": language,
                "needs_translation": language in HINDI_FAMILY}
    except sr.WaitTimeoutError:
        return {"success": False, "text": "", "needs_translation": False,
                "error": "⏱️ No speech detected. Please try again.", "raw_language": language}
    except sr.UnknownValueError:
        return {"success": False, "text": "", "needs_translation": False,
                "error": "🔇 Could not understand audio. Speak clearly.", "raw_language": language}
    except sr.RequestError as e:
        return {"success": False, "text": "", "needs_translation": False,
                "error": f"🌐 API error: {e}", "raw_language": language}
    except OSError:
        return {"success": False, "text": "", "needs_translation": False,
                "error": "🎙️ Microphone not found.", "raw_language": language}
    except Exception as e:
        return {"success": False, "text": "", "needs_translation": False,
                "error": f"❌ {str(e)}", "raw_language": language}


# ── Continuous (infinite) background listening ───────────────────────
def make_callback(result_queue: queue.Queue, language: str):
    """Factory that creates a background-listener callback."""
    recognizer = sr.Recognizer()

    def callback(_, audio):
        try:
            text = recognizer.recognize_google(audio, language=language)
            if text.strip():
                result_queue.put({
                    "success": True,
                    "text": text,
                    "needs_translation": language in HINDI_FAMILY,
                    "raw_language": language,
                })
        except sr.UnknownValueError:
            pass  # Silence / unclear — ignore silently
        except Exception as e:
            result_queue.put({"success": False, "text": "", "error": str(e),
                              "needs_translation": False, "raw_language": language})
    return callback


def start_continuous_listening(result_queue: queue.Queue, language: str = "en-IN"):
    """
    Start background (infinite) listening.

    Returns a callable stop_fn() that stops the listener when called.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    callback = make_callback(result_queue, language)
    stop_fn = recognizer.listen_in_background(mic, callback, phrase_time_limit=15)
    return stop_fn


def get_supported_input_languages():
    return SUPPORTED_INPUT_LANGUAGES

def get_hindi_family_codes():
    return HINDI_FAMILY
'''

# ─── app.py  (full update) ───────────────────────────────────────────
app_v4 = '''import streamlit as st
import queue
import datetime

from streamlit_autorefresh import st_autorefresh

from speech_module import (
    capture_speech, start_continuous_listening,
    get_supported_input_languages, get_hindi_family_codes,
)
from translation_module import (
    translate_text, translate_hindi_to_english,
    get_all_languages, get_indian_languages,
)
from simplification_module import simplify_text
from content_fetcher import (
    fetch_url_content, extract_pdf_text,
    extract_txt_text, extract_docx_text,
)
from tts_module import speak_text, get_tts_languages

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Classroom Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title { font-size:2.4rem; font-weight:700; color:#1a73e8; text-align:center; }
    .subtitle   { text-align:center; color:#5f6368; font-size:1rem; margin-bottom:1.5rem; }
    .source-card {
        background:#f1f3f4; border-radius:10px; padding:10px 16px;
        border-left:4px solid #1a73e8; margin-bottom:1rem;
    }
    .history-entry {
        background:#ffffff; border:1px solid #e0e0e0; border-radius:8px;
        padding:10px 14px; margin-bottom:8px; font-size:0.88rem;
    }
    .live-dot {
        display:inline-block; width:10px; height:10px;
        background:red; border-radius:50%;
        animation: blink 1s infinite;
    }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }
    div[data-testid="stSidebar"] { background-color:#f8f9fa; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────
st.markdown(\'<div class="main-title">🎓 Smart Classroom Assistant</div>\', unsafe_allow_html=True)
st.markdown(\'<div class="subtitle">Speech · Text · Online Content — Translate · Listen · History</div>\', unsafe_allow_html=True)
st.divider()

# ── Session State Init ───────────────────────────────────────────────
DEFAULTS = {
    "original_text":    "",
    "display_text":     "",
    "content_source":   "",
    "is_listening":     False,
    "stop_fn":          None,
    "speech_queue":     None,
    "session_history":  [],       # list of dicts {time, source, original, display}
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Auto-refresh when continuous listening is active ─────────────────
if st.session_state.is_listening:
    st_autorefresh(interval=2000, key="live_refresh")

# ── Poll speech queue ────────────────────────────────────────────────
def poll_speech_queue():
    """Drain one item from the speech queue and update session state."""
    q = st.session_state.speech_queue
    if q is None:
        return False
    try:
        result = q.get_nowait()
    except Exception:
        return False

    if result.get("success"):
        raw = result["text"]
        if result.get("needs_translation"):
            tr = translate_hindi_to_english(raw)
            display = tr["translated_text"] if tr["success"] else raw
        else:
            display = raw

        st.session_state.original_text = raw
        st.session_state.display_text  = display

        # Add to session history
        add_to_history(
            source=f"🎙️ Live ({result.get(\'raw_language\',\'\')})",
            original=raw,
            display=display
        )
        return True
    return False

def add_to_history(source: str, original: str, display: str):
    """Append an entry to session history."""
    st.session_state.session_history.append({
        "time":     datetime.datetime.now().strftime("%H:%M:%S"),
        "source":   source,
        "original": original,
        "display":  display,
    })

# Poll queue on every rerun
poll_speech_queue()

# ── Build language lists ──────────────────────────────────────────────
ALL_LANGS  = get_all_languages()
LANG_NAMES = sorted([k for k in ALL_LANGS if k != "English"])
TTS_LANGS  = get_tts_languages()

# ════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("⚙️ Controls")
    st.markdown("---")

    # ── Input Mode ───────────────────────────────────────────────────
    st.subheader("📥 Input Mode")
    input_mode = st.radio(
        "Choose input source:",
        ["🎙️ Speech Mode", "✏️ Text Mode", "🌐 Online Content"],
        index=0
    )

    st.markdown("---")

    # ── Speech Language ───────────────────────────────────────────────
    if input_mode == "🎙️ Speech Mode":
        st.subheader("🗣️ Speech Language")
        input_langs = get_supported_input_languages()
        sel_lang_name = st.selectbox("Language spoken:", list(input_langs.keys()))
        sel_lang_code = input_langs[sel_lang_name]
        st.caption("Non-English input → auto-translated to English.")
        st.markdown("---")

    # ── Translation ──────────────────────────────────────────────────
    st.subheader("🌐 Translation")
    enable_translation = st.toggle("Enable Translation", value=True)

    lang_search = st.text_input(
        "🔍 Search language",
        placeholder="e.g. French, Arabic...",
        disabled=not enable_translation
    )
    filtered_langs = (
        [l for l in LANG_NAMES if lang_search.strip().lower() in l.lower()]
        if lang_search.strip() else LANG_NAMES
    )

    if enable_translation and filtered_langs:
        target_lang_name = st.selectbox(
            f"Translate to ({len(filtered_langs)} shown):", filtered_langs
        )
        target_lang_code = ALL_LANGS[target_lang_name]
    else:
        target_lang_name, target_lang_code = "Hindi", "hi"
        st.selectbox(f"Translate to ({len(LANG_NAMES)} languages):", LANG_NAMES, disabled=True)

    st.markdown("---")

    # ── TTS ───────────────────────────────────────────────────────────
    st.subheader("🔊 Text-to-Speech")
    enable_tts = st.toggle("Enable TTS", value=True)

    tts_lang_search = st.text_input(
        "🔍 Search TTS language",
        placeholder="e.g. Hindi, French...",
        disabled=not enable_tts
    )
    tts_lang_names  = list(TTS_LANGS.keys())
    filtered_tts    = (
        [l for l in tts_lang_names if tts_lang_search.strip().lower() in l.lower()]
        if tts_lang_search.strip() else tts_lang_names
    )
    tts_lang_name   = st.selectbox(
        f"Speak in ({len(filtered_tts)} shown):",
        filtered_tts if filtered_tts else tts_lang_names,
        disabled=not enable_tts
    )
    tts_lang_code   = TTS_LANGS.get(tts_lang_name, "en")

    st.markdown("---")

    # ── Simplification ────────────────────────────────────────────────
    st.subheader("💡 Simplification")
    enable_simplification = st.toggle("Enable Simplification", value=True)

    st.markdown("---")

    # ── Session History ───────────────────────────────────────────────
    st.subheader("📋 Session History")
    hist = st.session_state.session_history
    st.caption(f"{len(hist)} entries recorded this session")

    if hist:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.session_history = []
            st.rerun()

        with st.expander(f"📖 View all {len(hist)} entries", expanded=False):
            for i, entry in enumerate(reversed(hist), 1):
                st.markdown(
                    f\'<div class="history-entry">\' +
                    f\'<b>#{len(hist)-i+1}</b> · <code>{entry["time"]}</code> · {entry["source"]}<br>\' +
                    f\'<small>{entry["display"][:120]}{"..." if len(entry["display"])>120 else ""}</small>\' +
                    \'</div>\',
                    unsafe_allow_html=True
                )

        # Download full history as TXT
        history_txt = "\\n\\n".join([
            f"[{e[\'time\']}] {e[\'source\']}\\n{e[\'display\']}"
            for e in hist
        ])
        st.download_button(
            "⬇️ Download History (.txt)",
            data=history_txt,
            file_name="session_history.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.caption("No history yet — start capturing!")

    st.markdown("---")
    st.caption(f"🌍 {len(LANG_NAMES)+1} translation languages · {len(TTS_LANGS)} TTS languages")


# ════════════════════════════════════════════════════════════════════
# INPUT PANELS
# ════════════════════════════════════════════════════════════════════

# ── Speech Mode ──────────────────────────────────────────────────────
if input_mode == "🎙️ Speech Mode":
    st.subheader("🎙️ Speech Input")

    col_info, col_status = st.columns([3, 1])
    with col_info:
        st.info(f"**Language:** {sel_lang_name}  |  **Mode:** {'🔴 Infinite (Live)' if st.session_state.is_listening else '⚡ Single-shot'}", icon="ℹ️")
    with col_status:
        if st.session_state.is_listening:
            st.markdown(\'<div style="padding-top:12px;"><span class="live-dot"></span> &nbsp;<b style="color:red">LIVE</b></div>\', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    # Single-shot listen
    with c1:
        single_btn = st.button(
            "⚡ Listen Once",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.is_listening
        )
    # Start infinite
    with c2:
        start_btn = st.button(
            "🔴 Start Live",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.is_listening
        )
    # Stop infinite
    with c3:
        stop_btn = st.button(
            "⏹️ Stop Live",
            use_container_width=True,
            disabled=not st.session_state.is_listening
        )
    # Clear current
    with c4:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.original_text = ""
            st.session_state.display_text  = ""
            st.session_state.content_source = ""
            st.rerun()

    # ── Single-shot handler ───────────────────────────────────────────
    if single_btn:
        with st.spinner("🎙️ Listening once... Please speak."):
            result = capture_speech(language=sel_lang_code, timeout=8, phrase_limit=15)
        if result["success"]:
            raw = result["text"]
            if result.get("needs_translation"):
                with st.spinner("🔄 Translating to English..."):
                    tr = translate_hindi_to_english(raw)
                display = tr["translated_text"] if tr["success"] else raw
            else:
                display = raw
            st.session_state.original_text  = raw
            st.session_state.display_text   = display
            st.session_state.content_source = f"🎙️ Single-shot ({sel_lang_name})"
            add_to_history(f"🎙️ {sel_lang_name}", raw, display)
            st.success(f"✅ Captured: *{display[:80]}...*" if len(display) > 80 else f"✅ Captured: *{display}*")
        else:
            st.error(result["error"])

    # ── Start infinite handler ────────────────────────────────────────
    if start_btn:
        try:
            q = queue.Queue()
            stop_fn = start_continuous_listening(q, language=sel_lang_code)
            st.session_state.speech_queue  = q
            st.session_state.stop_fn       = stop_fn
            st.session_state.is_listening  = True
            st.session_state.content_source = f"🔴 Live ({sel_lang_name})"
            st.success("🔴 Live listening started! Speak anytime — results appear automatically.")
            st.rerun()
        except OSError:
            st.error("🎙️ Microphone not accessible. Check your audio input device.")
        except Exception as e:
            st.error(f"❌ Could not start listener: {e}")

    # ── Stop infinite handler ─────────────────────────────────────────
    if stop_btn:
        if st.session_state.stop_fn:
            st.session_state.stop_fn(wait_for_stop=False)
        st.session_state.is_listening  = False
        st.session_state.stop_fn       = None
        st.session_state.speech_queue  = None
        st.success("⏹️ Live listening stopped.")
        st.rerun()

    # ── Live transcript ticker ────────────────────────────────────────
    if st.session_state.is_listening:
        st.markdown("---")
        st.markdown("**📡 Live Transcript** — new speech appears below automatically:")
        if st.session_state.display_text:
            st.success(f"🗣️ *{st.session_state.display_text}*")
        else:
            st.info("Waiting for speech...")

# ── Text Mode ────────────────────────────────────────────────────────
elif input_mode == "✏️ Text Mode":
    st.subheader("✏️ Text Input")
    manual = st.text_area(
        "Enter lecture text:",
        placeholder="Type or paste content here...",
        height=150,
        label_visibility="collapsed"
    )
    c1, c2, _ = st.columns([1,1,3])
    with c1:
        if st.button("▶️  Process", type="primary", use_container_width=True):
            if manual.strip():
                st.session_state.original_text  = manual.strip()
                st.session_state.display_text   = manual.strip()
                st.session_state.content_source = "✏️ Manual Input"
                add_to_history("✏️ Manual Input", manual.strip(), manual.strip())
                st.success("✅ Text loaded!")
            else:
                st.warning("⚠️ Please enter some text first.")
    with c2:
        if st.button("🗑️ Clear", use_container_width=True):
            for k in ["original_text","display_text","content_source"]:
                st.session_state[k] = ""
            st.rerun()

# ── Online Content Mode ──────────────────────────────────────────────
else:
    st.subheader("🌐 Online Content")
    online_tab, upload_tab = st.tabs(["🔗 Fetch from URL", "📁 Upload a File"])

    with online_tab:
        st.markdown("Paste any webpage URL — news article, Wikipedia, blog, etc.")
        url_input = st.text_input("URL", placeholder="https://en.wikipedia.org/wiki/Photosynthesis", label_visibility="collapsed")
        col_a, _ = st.columns([1,4])
        with col_a:
            fetch_btn = st.button("🌐 Fetch", type="primary", use_container_width=True)
        if fetch_btn:
            if not url_input.strip():
                st.warning("⚠️ Enter a URL first.")
            else:
                with st.spinner("Fetching..."):
                    result = fetch_url_content(url_input.strip())
                if result["success"]:
                    st.session_state.original_text  = result["text"]
                    st.session_state.display_text   = result["text"]
                    st.session_state.content_source = f"🔗 {result[\'title\']}"
                    add_to_history(f"🔗 {result[\'title\']}", result["text"], result["text"])
                    st.success(f"✅ Fetched: **{result[\'title\']}** — {len(result[\'text\'].split())} words")
                else:
                    st.error(result["error"])
        st.markdown("**📌 Example URLs:**")
        for ex in ["https://en.wikipedia.org/wiki/Photosynthesis",
                   "https://en.wikipedia.org/wiki/Newton%27s_laws_of_motion"]:
            st.code(ex, language=None)

    with upload_tab:
        st.markdown("Upload a **PDF**, **TXT**, or **DOCX** file.")
        uploaded_file = st.file_uploader("Upload", type=["pdf","txt","docx"], label_visibility="collapsed")
        if uploaded_file:
            col_x, _ = st.columns([1,3])
            with col_x:
                extract_btn = st.button("📄 Extract", type="primary", use_container_width=True)
            if extract_btn:
                fb = uploaded_file.read()
                ext = uploaded_file.name.split(".")[-1].lower()
                with st.spinner("Extracting..."):
                    if ext=="pdf":   result=extract_pdf_text(fb);     extra=f" | {result.get(\'pages\',\'?\')} pages"
                    elif ext=="txt": result=extract_txt_text(fb);     extra=""
                    else:            result=extract_docx_text(fb);    extra=""
                if result["success"]:
                    st.session_state.original_text  = result["text"]
                    st.session_state.display_text   = result["text"]
                    st.session_state.content_source = f"📁 {uploaded_file.name}"
                    add_to_history(f"📁 {uploaded_file.name}", result["text"], result["text"])
                    st.success(f"✅ {len(result[\'text\'].split())} words extracted{extra}")
                else:
                    st.error(result["error"])


# ════════════════════════════════════════════════════════════════════
# OUTPUT DASHBOARD
# ════════════════════════════════════════════════════════════════════
if st.session_state.display_text:
    st.divider()
    if st.session_state.content_source:
        st.markdown(
            f\'<div class="source-card">📌 <b>Source:</b> {st.session_state.content_source}</div>\',
            unsafe_allow_html=True
        )

    st.subheader("📊 Output Dashboard")
    tab1, tab2, tab3 = st.tabs(["📝 Captured Text", "🌐 Translation", "💡 Simplified"])

    # ── Tab 1: Captured Text + TTS ────────────────────────────────────
    with tab1:
        st.info("**🔤 Source / Captured Text**", icon="📝")
        st.text_area("Source", value=st.session_state.display_text, height=200,
                     disabled=True, label_visibility="collapsed")
        wc = len(st.session_state.display_text.split())
        st.caption(f"📏 {wc:,} words · {len(st.session_state.display_text):,} characters")

        col_dl, col_tts = st.columns([1,2])
        with col_dl:
            st.download_button("⬇️ Download (.txt)", data=st.session_state.display_text,
                               file_name="original_text.txt", mime="text/plain", use_container_width=True)
        with col_tts:
            if enable_tts:
                if st.button(f"🔊 Speak Original ({tts_lang_name})", use_container_width=True, key="tts_orig"):
                    with st.spinner("🔊 Generating audio..."):
                        tts_result = speak_text(st.session_state.display_text, tts_lang_code)
                    if tts_result["success"]:
                        st.audio(tts_result["audio_bytes"], format="audio/mp3")
                    else:
                        st.error(tts_result["error"])

    # ── Tab 2: Translation + TTS ──────────────────────────────────────
    with tab2:
        if enable_translation:
            st.info(f"Translating to **{target_lang_name}** (`{target_lang_code}`)", icon="🌐")
            with st.spinner(f"🌐 Translating to {target_lang_name}..."):
                trans = translate_text(st.session_state.display_text, target_lang_code)
            if trans["success"]:
                st.success(f"✅ **{target_lang_name}** translation complete!")
                st.text_area("Translation", value=trans["translated_text"], height=200,
                             disabled=True, label_visibility="collapsed")
                st.caption(f"📏 {len(trans[\'translated_text\'].split()):,} words")

                col_dl2, col_tts2 = st.columns([1,2])
                with col_dl2:
                    st.download_button(
                        f"⬇️ Download {target_lang_name} (.txt)",
                        data=trans["translated_text"],
                        file_name=f"translated_{target_lang_name.lower().replace(\' \',\'_\')}.txt",
                        mime="text/plain", use_container_width=True
                    )
                with col_tts2:
                    if enable_tts:
                        # Pick the closest gTTS code for the target language
                        tts_code_for_trans = TTS_LANGS.get(target_lang_name, tts_lang_code)
                        if st.button(f"🔊 Speak Translation ({target_lang_name})", use_container_width=True, key="tts_trans"):
                            with st.spinner("🔊 Generating audio..."):
                                tts2 = speak_text(trans["translated_text"], tts_code_for_trans)
                            if tts2["success"]:
                                st.audio(tts2["audio_bytes"], format="audio/mp3")
                            else:
                                st.error(tts2["error"])
            else:
                st.error(f"❌ {trans[\'error\']}")
        else:
            st.warning("Translation disabled. Enable from sidebar.", icon="🔕")

    # ── Tab 3: Simplified + TTS ───────────────────────────────────────
    with tab3:
        if enable_simplification:
            with st.spinner("💡 Simplifying..."):
                simp = simplify_text(st.session_state.display_text)
            if simp["success"]:
                st.success("✅ Simplified Version", icon="💡")
                st.info(simp["simplified_text"])
                if len(simp["bullet_points"]) > 1:
                    st.markdown("**📌 Key Points:**")
                    for i, pt in enumerate(simp["bullet_points"], 1):
                        st.markdown(f"**{i}.** {pt}")
                if enable_tts:
                    if st.button("🔊 Speak Simplified (English)", use_container_width=False, key="tts_simp"):
                        with st.spinner("🔊 Generating audio..."):
                            tts3 = speak_text(simp["simplified_text"], "en")
                        if tts3["success"]:
                            st.audio(tts3["audio_bytes"], format="audio/mp3")
                        else:
                            st.error(tts3["error"])
            else:
                st.warning(simp["error"])
        else:
            st.warning("Simplification disabled. Enable from sidebar.", icon="🔕")

else:
    st.markdown("""
    <div style="text-align:center; padding:3rem; color:#9aa0a6;">
        <h3>👆 Choose an input mode to get started</h3>
        <p>🎙️ Speech &nbsp;|&nbsp; ✏️ Text &nbsp;|&nbsp; 🌐 Online Content</p>
    </div>
    """, unsafe_allow_html=True)
'''

# ─── Updated requirements.txt ────────────────────────────────────────
req_v3 = """streamlit>=1.32.0
streamlit-autorefresh>=0.0.1
SpeechRecognition>=3.10.0
pyaudio>=0.2.14
deep-translator>=1.11.4
nltk>=3.8.1
requests>=2.31.0
beautifulsoup4>=4.12.0
pdfplumber>=0.10.0
python-docx>=1.1.0
gTTS>=2.5.0
"""

files = {
    "tts_module.py":    tts_module,
    "speech_module.py": speech_module_v3,
    "app.py":           app_v4,
    "requirements.txt": req_v3,
}

for fname, content in files.items():
    with open(fname, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ {fname}  ({len(content):,} chars)")

print("\n🎉 Session History + TTS + Infinite Listening all implemented!")
