import streamlit as st
import queue, datetime

from streamlit_autorefresh import st_autorefresh
from speech_module import (
    capture_speech, start_continuous_listening,
    stop_continuous_listening, is_listening_active,
    get_supported_input_languages, get_non_english_codes,
)
from translation_module  import translate_text, translate_hindi_to_english, get_all_languages
from simplification_module import simplify_text
from content_fetcher     import fetch_url_content, extract_pdf_text, extract_txt_text, extract_docx_text
from tts_module          import speak_text, get_tts_languages

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Classroom Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ══ SIDEBAR: dark theme to match main app ══ */
  section[data-testid="stSidebar"] {
      min-width: 330px !important;
      max-width: 330px !important;
      width:     330px !important;
      background: #0e1117 !important;
      border-right: 1px solid #2a2d35 !important;
  }
  section[data-testid="stSidebar"] > div:first-child {
      width: 330px !important;
      padding: 1.2rem 1rem !important;
      background: #0e1117 !important;
  }
  /* All text in sidebar white */
  section[data-testid="stSidebar"] * {
      color: #fafafa !important;
  }
  /* Sidebar inputs & selectboxes dark */
  section[data-testid="stSidebar"] .stSelectbox > div,
  section[data-testid="stSidebar"] .stTextInput > div > div,
  section[data-testid="stSidebar"] [data-baseweb="select"] > div {
      background: #1e2129 !important;
      border-color: #3a3d47 !important;
      color: #fafafa !important;
  }
  section[data-testid="stSidebar"] input {
      background: #1e2129 !important;
      color: #fafafa !important;
  }
  /* Radio buttons label text */
  section[data-testid="stSidebar"] label {
      color: #fafafa !important;
  }
  /* Toggle track */
  section[data-testid="stSidebar"] [data-testid="stToggle"] {
      color: #fafafa !important;
  }
  /* Force sidebar visible — fixes collapse-on-rerun */
  section[data-testid="stSidebar"][aria-expanded="false"] {
      margin-left: 0 !important;
      transform: none !important;
  }
  /* Keep collapse toggle accessible */
  [data-testid="collapsedControl"] {
      display: flex !important;
      visibility: visible !important;
  }

  /* ══ MAIN CONTENT ══ */
  .main .block-container {
      padding-top: 1.4rem;
      max-width: 1080px;
  }

  /* ══ HEADER ══ */
  .main-title {
      font-size: 2.3rem;
      font-weight: 800;
      color: #4d9eff;
      text-align: center;
      letter-spacing: -0.5px;
      margin-bottom: 2px;
  }
  .subtitle {
      text-align: center;
      color: #9aa0a6;
      font-size: 0.95rem;
      margin-bottom: 0.4rem;
  }

  /* ══ SIDEBAR SECTION HEADERS ══ */
  .sb-section {
      background: #1e2129 !important;
      border: 1px solid #2a2d35;
      border-radius: 10px;
      padding: 12px 14px 10px 14px;
      margin-bottom: 10px;
  }
  .sb-section-title {
      font-size: 0.78rem;
      font-weight: 700;
      color: #7a8499 !important;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 8px;
  }

  /* ══ SOURCE CARD — dark themed ══ */
  .src-card {
      background: #1a2540;
      border-radius: 10px;
      padding: 10px 16px;
      border-left: 4px solid #4d9eff;
      margin-bottom: 1rem;
      font-size: 0.93rem;
      color: #e8eaed !important;
  }
  .src-card b { color: #4d9eff !important; }

  /* ══ HISTORY ROWS — dark themed ══ */
  .hist-row {
      background: #1e2129;
      border: 1px solid #2a2d35;
      border-radius: 8px;
      padding: 8px 12px;
      margin-bottom: 6px;
      font-size: .86rem;
      line-height: 1.5;
      color: #e8eaed !important;
  }

  /* ══ LIVE BADGE ══ */
  .live-badge {
      display: inline-block;
      background: #e53935;
      color: #fff;
      border-radius: 20px;
      padding: 3px 14px;
      font-size: .82rem;
      font-weight: 700;
      animation: blink 1s infinite;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.25} }

  /* ══ BUTTONS & TABS ══ */
  .stButton > button {
      border-radius: 8px !important;
      font-weight: 600 !important;
  }
  .stTabs [data-baseweb="tab"] {
      font-size: .95rem;
      font-weight: 600;
  }

  /* ══ HIDE STREAMLIT BRANDING ══ */
  #MainMenu { visibility: hidden; }
  footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🎓 Smart Classroom Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Speech · Text · Online Content — Translate · Listen · History</div>', unsafe_allow_html=True)
st.divider()

# ── Session state ────────────────────────────────────────────────────
_defaults = dict(
    original_text="", display_text="", content_source="",
    is_listening=False, speech_queue=None, stop_event=None,
    mic_ready=False, session_history=[], last_transcript="",
    sel_lang_name="English (India)", sel_lang_code="en-IN",
)
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.is_listening:
    st_autorefresh(interval=1500, key="live_tick")

# ── Helpers ───────────────────────────────────────────────────────────
def _hist(src, orig, disp):
    st.session_state.session_history.append({
        "time":     datetime.datetime.now().strftime("%H:%M:%S"),
        "source":   src,
        "original": orig,
        "display":  disp,
    })

# ── Queue drain (runs every autorefresh tick) ─────────────────────────
def _drain():
    q = st.session_state.speech_queue
    if not q:
        return
    new_text = None
    while True:
        try:
            item = q.get_nowait()
        except queue.Empty:
            break
        if item.get("status") == "ready":
            st.session_state.mic_ready = True
            continue
        if item.get("success"):
            raw  = item["text"]
            disp = raw
            if item.get("needs_translation"):
                tr   = translate_hindi_to_english(raw)
                disp = tr["translated_text"] if tr["success"] else raw
            new_text = disp
            _hist(item.get("raw_language", "🎙️"), raw, disp)
        elif item.get("error"):
            # Surface API errors to the user during live listening
            st.session_state._live_error = item["error"]
    if new_text:
        st.session_state.original_text   = new_text
        st.session_state.display_text    = new_text
        st.session_state.last_transcript = new_text

_drain()

# ── Language data ────────────────────────────────────────────────────
ALL_LANGS  = get_all_languages()
LANG_NAMES = sorted(k for k in ALL_LANGS if k != "English")
TTS_LANGS  = get_tts_languages()
INPUT_LANGS = get_supported_input_languages()

# ════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Controls")

    # ── Input Mode ───────────────────────────────────────────────────
    st.markdown('<div class="sb-section"><div class="sb-section-title">📥 Input Mode</div>', unsafe_allow_html=True)
    input_mode = st.radio(
        "input_mode_radio", ["🎙️ Speech Mode", "✏️ Text Mode", "🌐 Online Content"],
        label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Speech Language (only when Speech Mode selected) ─────────────
    if input_mode == "🎙️ Speech Mode":
        st.markdown('<div class="sb-section"><div class="sb-section-title">🗣️ Speech Language</div>', unsafe_allow_html=True)
        sel_lang_name = st.selectbox(
            "speech_lang_select", list(INPUT_LANGS.keys()),
            label_visibility="collapsed",
            key="sel_lang_name",
        )
        sel_lang_code = INPUT_LANGS[sel_lang_name]
        st.session_state.sel_lang_code = sel_lang_code
        st.caption("💡 Non-English speech is auto-translated to English first")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Provide safe defaults so output section never hits NameError
        sel_lang_name = st.session_state.sel_lang_name
        sel_lang_code = st.session_state.sel_lang_code

    # ── Translation ──────────────────────────────────────────────────
    st.markdown('<div class="sb-section"><div class="sb-section-title">🌐 Translation</div>', unsafe_allow_html=True)
    en_tr    = st.toggle("Enable Translation", value=True, key="toggle_tr")
    ls       = st.text_input("Filter languages", placeholder="e.g. French, Tamil…",
                              disabled=not en_tr, label_visibility="collapsed",
                              key="tr_filter")
    filt     = [l for l in LANG_NAMES if ls.strip().lower() in l.lower()] if ls.strip() else LANG_NAMES
    tgt_name = st.selectbox(
        f"Translate to ({len(filt)})",
        filt or LANG_NAMES,
        disabled=not en_tr,
        key="tgt_lang_select",
    )
    tgt_code = ALL_LANGS.get(tgt_name, "hi")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── TTS ───────────────────────────────────────────────────────────
    st.markdown('<div class="sb-section"><div class="sb-section-title">🔊 Text-to-Speech</div>', unsafe_allow_html=True)
    en_tts   = st.toggle("Enable TTS", value=True, key="toggle_tts")
    ts       = st.text_input("Filter TTS", placeholder="e.g. Hindi, Arabic…",
                              disabled=not en_tts, label_visibility="collapsed",
                              key="tts_filter")
    ftts     = [l for l in TTS_LANGS if ts.strip().lower() in l.lower()] if ts.strip() else list(TTS_LANGS)
    tts_name = st.selectbox(
        f"Speak in ({len(ftts)})",
        ftts or list(TTS_LANGS),
        disabled=not en_tts,
        key="tts_lang_select",
    )
    tts_code = TTS_LANGS.get(tts_name, "en")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Simplification ────────────────────────────────────────────────
    st.markdown('<div class="sb-section"><div class="sb-section-title">💡 Simplification</div>', unsafe_allow_html=True)
    en_simp = st.toggle("Enable Simplification", value=True, key="toggle_simp")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Session History ───────────────────────────────────────────────
    st.markdown('<div class="sb-section"><div class="sb-section-title">📋 Session History</div>', unsafe_allow_html=True)
    hist = st.session_state.session_history
    st.caption(f"{len(hist)} entr{'y' if len(hist)==1 else 'ies'} recorded")

    if hist:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🗑️ Clear", use_container_width=True, key="hist_clear"):
                st.session_state.session_history = []
                st.rerun()
        with col_b:
            htxt = "\n\n".join(
                f'[{e["time"]}] {e["source"]}\n{e["display"]}' for e in hist
            )
            st.download_button("⬇️ Export", htxt, "history.txt",
                               use_container_width=True, key="hist_export")

        with st.expander(f"📖 View {len(hist)} entries"):
            for i, e in enumerate(reversed(hist)):
                st.markdown(
                    f'<div class="hist-row">'
                    f'<b>#{len(hist)-i}</b> · <code>{e["time"]}</code> — <b>{e["source"]}</b><br>'
                    f'<span style="color:#444">{e["display"][:100]}{"…" if len(e["display"])>100 else ""}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="text-align:center;color:#7a8499;font-size:0.78rem;padding-top:4px">'
        f'🌍 {len(LANG_NAMES)+1} translation languages &nbsp;·&nbsp; 🔊 {len(TTS_LANGS)} TTS languages'
        f'</div>',
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════
# SPEECH MODE
# ════════════════════════════════════════════════════════════════════
if input_mode == "🎙️ Speech Mode":
    st.subheader("🎙️ Speech Input")

    hc1, hc2 = st.columns([5, 1])
    with hc1:
        if st.session_state.is_listening:
            if st.session_state.mic_ready:
                st.success("🎙️ Microphone open — speak anytime! Transcript updates automatically.", icon="📡")
            else:
                st.warning("⏳ Calibrating microphone, please wait a moment…", icon="🔧")
        else:
            st.info(f"Language: **{sel_lang_name}** · Noise Isolation: ✅ · Ready to listen", icon="🎙️")
    with hc2:
        if st.session_state.is_listening:
            st.markdown(
                '<div style="padding-top:6px;text-align:right">'
                '<span class="live-badge">● LIVE</span></div>',
                unsafe_allow_html=True,
            )

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        once  = st.button("⚡ Listen Once", use_container_width=True, type="primary",
                          disabled=st.session_state.is_listening)
    with b2:
        start = st.button("🔴 Start Live", use_container_width=True, type="primary",
                          disabled=st.session_state.is_listening)
    with b3:
        stop  = st.button("⏹️ Stop Live", use_container_width=True,
                          disabled=not st.session_state.is_listening)
    with b4:
        if st.button("🗑️ Clear", use_container_width=True, key="speech_clear"):
            st.session_state.original_text   = ""
            st.session_state.display_text    = ""
            st.session_state.content_source  = ""
            st.session_state.last_transcript = ""
            st.rerun()

    # -- Listen Once --
    if once:
        bar = st.progress(0, "⏳ Calibrating mic…")
        bar.progress(20, "🎙️ Waiting for voice…")
        res = capture_speech(language=sel_lang_code, timeout=8, phrase_limit=15)
        bar.progress(70, "🔊 Processing audio…")
        if res["success"]:
            raw = res["text"]
            if res.get("needs_translation"):
                bar.progress(85, "🔄 Translating…")
                tr   = translate_hindi_to_english(raw)
                disp = tr["translated_text"] if tr["success"] else raw
            else:
                disp = raw
            bar.progress(100, "✅ Done!")
            st.session_state.original_text  = raw
            st.session_state.display_text   = disp
            st.session_state.content_source = f"⚡ {sel_lang_name}"
            _hist(sel_lang_name, raw, disp)
            st.success(f"✅ **Recognised:** {disp[:120]}{'…' if len(disp)>120 else ''}")
        else:
            bar.empty()
            st.error(res["error"])

    # -- Start Live --
    if start:
        try:
            q = queue.Queue()
            stop_ev = start_continuous_listening(q, language=sel_lang_code)
            st.session_state.speech_queue   = q
            st.session_state.stop_event     = stop_ev
            st.session_state.is_listening   = True
            st.session_state.mic_ready      = False
            st.session_state.content_source = f"🔴 Live · {sel_lang_name}"
            st.rerun()
        except OSError:
            st.error("🎙️ Microphone not accessible. Check your audio input device.")
        except Exception as e:
            st.error(f"❌ Could not start: {e}")

    # -- Stop Live --
    if stop:
        stop_continuous_listening()
        q = st.session_state.speech_queue
        if q:
            while True:
                try:
                    item = q.get_nowait()
                    if item.get("success") and item.get("text", "").strip():
                        raw  = item["text"]
                        disp = raw
                        if item.get("needs_translation"):
                            tr   = translate_hindi_to_english(raw)
                            disp = tr["translated_text"] if tr["success"] else raw
                        st.session_state.original_text  = raw
                        st.session_state.display_text   = disp
                        _hist(item.get("raw_language", "🎙️"), raw, disp)
                except queue.Empty:
                    break
        st.session_state.is_listening  = False
        st.session_state.speech_queue  = None
        st.session_state.stop_event    = None
        st.session_state.mic_ready     = False
        st.info("⏹️ Live listening stopped.")
        st.rerun()

    # -- Live transcript display --
    if st.session_state.is_listening:
        st.markdown("---")
        st.markdown("#### 📡 Live Transcript *(auto-updates every 1.5 s)*")
        if st.session_state.last_transcript:
            st.success(f"🗣️  {st.session_state.last_transcript}")
        elif st.session_state.mic_ready:
            st.info("🎙️ Mic is open — start speaking!")
        else:
            st.warning("⏳ Calibrating mic, please wait…")

# ════════════════════════════════════════════════════════════════════
# TEXT MODE
# ════════════════════════════════════════════════════════════════════
elif input_mode == "✏️ Text Mode":
    st.subheader("✏️ Text Input")
    manual = st.text_area("text_input_area", placeholder="Type or paste lecture content here…",
                          height=160, label_visibility="collapsed")
    ca, cb, _ = st.columns([1, 1, 3])
    with ca:
        if st.button("▶️ Process", type="primary", use_container_width=True):
            if manual.strip():
                st.session_state.original_text  = manual.strip()
                st.session_state.display_text   = manual.strip()
                st.session_state.content_source = "✏️ Manual"
                _hist("✏️ Manual", manual.strip(), manual.strip())
                st.success("✅ Loaded!")
            else:
                st.warning("Please enter some text first.")
    with cb:
        if st.button("🗑️ Clear", use_container_width=True, key="text_clear"):
            st.session_state.original_text  = ""
            st.session_state.display_text   = ""
            st.session_state.content_source = ""
            st.rerun()

# ════════════════════════════════════════════════════════════════════
# ONLINE CONTENT
# ════════════════════════════════════════════════════════════════════
else:
    st.subheader("🌐 Online Content")
    utab, ftab = st.tabs(["🔗 Fetch from URL", "📁 Upload File"])

    with utab:
        url = st.text_input("url_input", placeholder="https://en.wikipedia.org/wiki/Photosynthesis",
                            label_visibility="collapsed")
        if st.button("🌐 Fetch Content", type="primary"):
            if url.strip():
                with st.spinner("Fetching…"):
                    r = fetch_url_content(url.strip())
                if r["success"]:
                    st.session_state.original_text  = r["text"]
                    st.session_state.display_text   = r["text"]
                    st.session_state.content_source = f"🔗 {r['title']}"
                    _hist(f"🔗 {r['title']}", r["text"], r["text"])
                    st.success(f"✅ **{r['title']}** — {len(r['text'].split()):,} words fetched")
                else:
                    st.error(r["error"])
            else:
                st.warning("Please enter a URL.")
        st.markdown("**📌 Try these:**")
        for ex in [
            "https://en.wikipedia.org/wiki/Photosynthesis",
            "https://en.wikipedia.org/wiki/Newton%27s_laws_of_motion",
        ]:
            st.code(ex, language=None)

    with ftab:
        uf = st.file_uploader("file_upload", type=["pdf", "txt", "docx"],
                               label_visibility="collapsed")
        if uf and st.button("📄 Extract Text", type="primary"):
            fb  = uf.read()
            ext = uf.name.rsplit(".", 1)[-1].lower()
            with st.spinner("Extracting…"):
                if ext == "pdf":
                    r    = extract_pdf_text(fb)
                    xtra = f" · {r.get('pages', '?')} pages"
                elif ext == "txt":
                    r    = extract_txt_text(fb)
                    xtra = ""
                else:
                    r    = extract_docx_text(fb)
                    xtra = ""
            if r["success"]:
                st.session_state.original_text  = r["text"]
                st.session_state.display_text   = r["text"]
                st.session_state.content_source = f"📁 {uf.name}"
                _hist(f"📁 {uf.name}", r["text"], r["text"])
                st.success(f"✅ {len(r['text'].split()):,} words extracted{xtra}")
            else:
                st.error(r["error"])

# ════════════════════════════════════════════════════════════════════
# OUTPUT DASHBOARD
# ════════════════════════════════════════════════════════════════════
if st.session_state.display_text:
    st.divider()
    st.markdown(
        f'<div class="src-card">📌 <b>Source:</b> {st.session_state.content_source}</div>',
        unsafe_allow_html=True,
    )
    st.subheader("📊 Output Dashboard")
    t1, t2, t3 = st.tabs(["📝 Captured Text", "🌐 Translation", "💡 Simplified"])

    # ── Tab 1: Captured text ─────────────────────────────────────────
    with t1:
        st.info("**🔤 Captured / Source Text**", icon="📝")
        st.text_area("captured_text_out", value=st.session_state.display_text,
                     height=200, disabled=True, label_visibility="collapsed")
        st.caption(
            f"📏 {len(st.session_state.display_text.split()):,} words · "
            f"{len(st.session_state.display_text):,} chars"
        )
        ca, cb = st.columns(2)
        with ca:
            st.download_button("⬇️ Download (.txt)", st.session_state.display_text,
                               "original.txt", use_container_width=True)
        with cb:
            if en_tts and st.button(f"🔊 Speak in {tts_name}", use_container_width=True, key="tts1"):
                with st.spinner("Generating audio…"):
                    r = speak_text(st.session_state.display_text, tts_code)
                if r["success"]:
                    st.audio(r["audio_bytes"], format="audio/mp3")
                else:
                    st.error(r["error"])

    # ── Tab 2: Translation ───────────────────────────────────────────
    with t2:
        if en_tr:
            with st.spinner(f"Translating to {tgt_name}…"):
                tr = translate_text(st.session_state.display_text, tgt_code)
            if tr["success"]:
                st.success(f"✅ Translated to **{tgt_name}**")
                st.text_area("translated_out", value=tr["translated_text"],
                             height=200, disabled=True, label_visibility="collapsed")
                st.caption(f"📏 {len(tr['translated_text'].split()):,} words")
                ca, cb = st.columns(2)
                with ca:
                    st.download_button(
                        f"⬇️ {tgt_name} (.txt)",
                        tr["translated_text"],
                        f"translated_{tgt_name.lower().replace(' ', '_')}.txt",
                        use_container_width=True,
                    )
                with cb:
                    if en_tts:
                        tc2 = TTS_LANGS.get(tgt_name, tts_code)
                        if st.button(f"🔊 Speak {tgt_name}", use_container_width=True, key="tts2"):
                            with st.spinner("Generating…"):
                                r2 = speak_text(tr["translated_text"], tc2)
                            if r2["success"]:
                                st.audio(r2["audio_bytes"], format="audio/mp3")
                            else:
                                st.error(r2["error"])
            else:
                st.error(tr["error"])
        else:
            st.warning("Translation is disabled — enable it in the sidebar.", icon="🔕")

    # ── Tab 3: Simplification ────────────────────────────────────────
    with t3:
        if en_simp:
            with st.spinner("Simplifying…"):
                s = simplify_text(st.session_state.display_text)
            if s["success"]:
                st.success("✅ Simplified Version")
                st.info(s["simplified_text"])
                if len(s["bullet_points"]) > 1:
                    st.markdown("**📌 Key Points:**")
                    for i, pt in enumerate(s["bullet_points"], 1):
                        st.markdown(f"**{i}.** {pt}")
                if en_tts and st.button("🔊 Speak Simplified", key="tts3"):
                    with st.spinner("Generating…"):
                        r3 = speak_text(s["simplified_text"], "en")
                    if r3["success"]:
                        st.audio(r3["audio_bytes"], format="audio/mp3")
                    else:
                        st.error(r3["error"])
            else:
                st.error(s["error"])
        else:
            st.warning("Simplification is disabled — enable it in the sidebar.", icon="🔕")

# ── Empty state ──────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem;color:#9aa0a6;">
        <div style="font-size:3rem;margin-bottom:0.5rem;">👆</div>
        <h3 style="color:#5f6368;margin-bottom:0.5rem;">Choose an input mode to get started</h3>
        <p style="font-size:0.95rem;">🎙️ Speech &nbsp;|&nbsp; ✏️ Text &nbsp;|&nbsp; 🌐 Online Content</p>
    </div>
    """, unsafe_allow_html=True)
