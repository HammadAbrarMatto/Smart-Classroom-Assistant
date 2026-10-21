"""Smart Classroom Assistant — Streamlit front-end.

Run:  streamlit run app.py
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from classroom_assistant.config import settings  # noqa: E402
from classroom_assistant.languages import (  # noqa: E402
    SPEECH_LANGUAGES,
    TRANSLATION_LANGUAGES,
    TTS_LANGUAGES,
    is_english,
    speech_to_translation_code,
    tts_code_for,
)
from classroom_assistant.notes import Entry, to_markdown  # noqa: E402
from classroom_assistant.services import content, llm, speech, translation, tts  # noqa: E402
from classroom_assistant.services import simplify as rules  # noqa: E402

st.set_page_config(page_title="Smart Classroom Assistant", page_icon="🎓", layout="wide")
st.markdown(
    """<style>
    .block-container{max-width:1100px;padding-top:1.5rem}
    .src-card{border-left:4px solid #4d9eff;background:rgba(77,158,255,.08);border-radius:8px;
              padding:.6rem 1rem;margin:.4rem 0 1rem}
    .live{display:inline-block;background:#e53935;color:#fff;border-radius:20px;padding:2px 12px;
          font-weight:700;font-size:.8rem;animation:b 1s infinite}@keyframes b{50%{opacity:.3}}
    </style>""",
    unsafe_allow_html=True,
)

# ── State ────────────────────────────────────────────────────────────────────
DEFAULTS = {"text": "", "original": "", "source": "", "history": [], "listener": None, "quiz": None}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def load_text(text: str, source: str, original: str | None = None) -> None:
    st.session_state.text = text
    st.session_state.original = original or text
    st.session_state.source = source
    st.session_state.quiz = None
    st.session_state.history.append(Entry(source=source, original=original or text, text=text))


# ── Cached service calls (Streamlit reruns the script on every interaction) ─
@st.cache_data(show_spinner=False, ttl=3600)
def cached_translate(text: str, target: str, source: str = "auto"):
    return translation.translate(text, target, source)


@st.cache_data(show_spinner=False, ttl=3600)
def cached_simplify(text: str, level: str, use_llm: bool):
    if use_llm:
        res = llm.simplify(text, level)
        if res.ok:
            return res
    return rules.simplify(text)


@st.cache_data(show_spinner=False, ttl=3600)
def cached_summary(text: str):
    return llm.summarize(text)


@st.cache_data(show_spinner=False, ttl=3600)
def cached_tts(text: str, lang: str):
    return tts.synthesize(text, lang)


def to_english(text: str, locale: str) -> str:
    if is_english(locale):
        return text
    res = cached_translate(text, "en", speech_to_translation_code(locale))
    return res.text if res.ok else text


def speak_button(text: str, lang: str, key: str, label: str = "🔊 Listen") -> None:
    if st.button(label, key=key, width="stretch"):
        with st.spinner("Generating audio…"):
            res, audio = cached_tts(text, lang)
        if res.ok:
            st.audio(audio, format="audio/mp3")
            if res.meta.get("truncated"):
                st.caption("Audio covers the first part of a long text.")
        else:
            st.error(res.error)


# ── Header ───────────────────────────────────────────────────────────────────
st.title("🎓 Smart Classroom Assistant")
st.caption("Capture a lecture by voice, text, web page, document or recording → translate · simplify · "
           "summarise · quiz · listen")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Controls")
    mode = st.radio("Input", ["🎙️ Speech", "✏️ Text", "🌐 Web / Document", "🎧 Recording"], key="mode")

    speech_lang = st.selectbox("Spoken language", list(SPEECH_LANGUAGES), key="speech_lang")
    locale = SPEECH_LANGUAGES[speech_lang]

    st.divider()
    target_name = st.selectbox(
        "Translate to", sorted(n for n in TRANSLATION_LANGUAGES if n != "English"),
        index=sorted(n for n in TRANSLATION_LANGUAGES if n != "English").index("Hindi"),
    )
    target_code = TRANSLATION_LANGUAGES[target_name]

    level = st.selectbox("Reading level", list(llm.READING_LEVELS), index=1)
    use_llm = st.toggle("Use Gemini AI", value=llm.available(), disabled=not llm.available(),
                        help="Set GEMINI_API_KEY in .env to enable AI simplification, summaries and quizzes.")
    if not llm.available():
        st.caption("🔑 No `GEMINI_API_KEY` — using offline rule-based simplification.")

    st.divider()
    hist: list[Entry] = st.session_state.history
    st.subheader(f"📋 History ({len(hist)})")
    if hist:
        c1, c2 = st.columns(2)
        if c1.button("🗑️ Clear", width="stretch"):
            st.session_state.history = []
            st.rerun()
        c2.download_button("⬇️ Notes", to_markdown(hist), "class_notes.md", width="stretch")
        with st.expander("View entries"):
            for e in reversed(hist[-30:]):
                st.markdown(f"**{html.escape(e.source)}** · `{e.time}`  \n{html.escape(e.text[:140])}"
                            f"{'…' if len(e.text) > 140 else ''}")

# ── Input modes ──────────────────────────────────────────────────────────────
if mode == "🎙️ Speech":
    st.subheader("🎙️ Speech input")
    tab_browser, tab_live = st.tabs(["Record in browser", "Live microphone (local only)"])

    with tab_browser:
        st.caption("Works anywhere, including when the app is deployed. Record, then stop to transcribe.")
        rec = st.audio_input("Record a phrase", key="audio_in")
        if rec is not None and st.button("📝 Transcribe recording", type="primary"):
            with st.spinner("Transcribing…"):
                res = speech.transcribe_wav(rec.getvalue(), locale)
            if res.ok:
                load_text(to_english(res.text, locale), f"🎙️ {speech_lang}", res.text)
                st.success(f"Recognised: {res.text[:160]}")
            else:
                st.error(res.error)

    with tab_live:
        listener: speech.LiveListener | None = st.session_state.listener
        live = listener is not None and listener.active

        @st.fragment(run_every=1.5 if live else None)
        def live_panel() -> None:
            lst: speech.LiveListener | None = st.session_state.listener
            if lst is None:
                st.info(f"Language: **{speech_lang}** · uses the microphone of the machine running the app.")
                return
            for res in lst.drain():
                if res.ok:
                    load_text(to_english(res.text, lst.language), f"🔴 Live · {speech_lang}", res.text)
                else:
                    st.warning(res.error)
            badge = '<span class="live">● LIVE</span> ' if lst.active else ""
            status = "listening — speak anytime" if lst.ready else "calibrating microphone…"
            st.markdown(f"{badge}{status}", unsafe_allow_html=True)
            if st.session_state.text:
                st.success(st.session_state.text[-400:])

        c1, c2, c3 = st.columns(3)
        if c1.button("⚡ Listen once", width="stretch", disabled=live):
            with st.spinner("Listening… (up to 8 s)"):
                res = speech.capture_once(locale)
            if res.ok:
                load_text(to_english(res.text, locale), f"⚡ {speech_lang}", res.text)
            else:
                st.error(res.error)
        if c2.button("🔴 Start live", type="primary", width="stretch", disabled=live):
            st.session_state.listener = speech.LiveListener(locale).start()
            st.rerun()
        if c3.button("⏹️ Stop", width="stretch", disabled=not live):
            listener.stop()
            for res in listener.drain():
                if res.ok:
                    load_text(to_english(res.text, listener.language), f"🔴 Live · {speech_lang}", res.text)
            st.session_state.listener = None
            st.rerun()
        live_panel()

elif mode == "✏️ Text":
    st.subheader("✏️ Text input")
    typed = st.text_area("Lecture text", height=180, placeholder="Type or paste lecture content…",
                         label_visibility="collapsed")
    if st.button("▶️ Process", type="primary"):
        if typed.strip():
            load_text(typed.strip(), "✏️ Typed text")
        else:
            st.warning("Please enter some text first.")

elif mode == "🌐 Web / Document":
    st.subheader("🌐 Web page or document")
    t_url, t_file = st.tabs(["🔗 URL", "📁 Upload"])
    with t_url:
        url = st.text_input("URL", placeholder="https://en.wikipedia.org/wiki/Photosynthesis")
        if st.button("🌐 Fetch", type="primary") and url:
            with st.spinner("Fetching…"):
                res = content.fetch_url(url)
            if res.ok:
                load_text(res.text, f"🔗 {res.meta['title']}")
                st.success(f"**{res.meta['title']}** — {len(res.text.split()):,} words")
                if res.meta.get("truncated"):
                    st.caption(f"Trimmed to the first {settings.max_input_chars:,} characters.")
            else:
                st.error(res.error)
    with t_file:
        up = st.file_uploader("PDF, DOCX, TXT or MD", type=["pdf", "docx", "txt", "md"])
        if up and st.button("📄 Extract", type="primary"):
            with st.spinner("Extracting…"):
                res = content.extract_file(up.name, up.getvalue())
            if res.ok:
                load_text(res.text, f"📁 {up.name}")
                pages = f" from {res.meta['pages']} pages" if "pages" in res.meta else ""
                st.success(f"{len(res.text.split()):,} words extracted{pages}")
            else:
                st.error(res.error)

else:
    st.subheader("🎧 Lecture recording")
    if not speech.whisper_available():
        st.info("Install the offline transcriber to use this mode:  `pip install faster-whisper`")
    up = st.file_uploader("Audio / video", type=["mp3", "wav", "m4a", "ogg", "webm", "mp4"])
    auto = st.checkbox("Auto-detect language", value=True)
    if up and st.button("📝 Transcribe", type="primary", disabled=not speech.whisper_available()):
        with st.spinner(f"Transcribing with Whisper ({settings.whisper_model})… this can take a while"):
            lang = None if auto else speech_to_translation_code(locale)
            res = speech.transcribe_file(up.getvalue(), Path(up.name).suffix, language=lang)
        if res.ok:
            detected = res.meta.get("language", "en")
            load_text(to_english(res.text, detected), f"🎧 {up.name}", res.text)
            st.success(f"{res.meta.get('duration', '?')} s of audio · detected language: {detected}")
        else:
            st.error(res.error)

# ── Output dashboard ─────────────────────────────────────────────────────────
text = st.session_state.text
if not text:
    st.info("👈 Choose an input mode to get started.")
    st.stop()

st.divider()
st.markdown(f'<div class="src-card">📌 <b>Source:</b> {html.escape(st.session_state.source)}</div>',
            unsafe_allow_html=True)
tabs = st.tabs(["📝 Text", "🌐 Translation", "💡 Simplified", "🧾 Summary", "❓ Quiz", "💬 Ask"])

with tabs[0]:
    st.text_area("Captured text", text, height=220, disabled=True, label_visibility="collapsed")
    st.caption(f"{len(text.split()):,} words · {len(text):,} characters")
    if st.session_state.original != text:
        with st.expander("Original (before translation to English)"):
            st.write(st.session_state.original)
    c1, c2 = st.columns(2)
    c1.download_button("⬇️ Download .txt", text, "lecture.txt", width="stretch")
    with c2:
        speak_button(text, "en", "tts_text")

with tabs[1]:
    with st.spinner(f"Translating to {target_name}…"):
        tr = cached_translate(text, target_code)
    if tr.ok:
        st.text_area("Translation", tr.text, height=220, disabled=True, label_visibility="collapsed")
        c1, c2 = st.columns(2)
        c1.download_button(f"⬇️ {target_name} .txt", tr.text,
                           f"translation_{target_code}.txt", width="stretch")
        if target_name in TTS_LANGUAGES:
            with c2:
                speak_button(tr.text, tts_code_for(target_name), "tts_tr", f"🔊 Listen in {target_name}")
    else:
        st.error(tr.error)

with tabs[2]:
    with st.spinner("Simplifying…"):
        simp = cached_simplify(text, level, use_llm)
    if simp.ok:
        engine = "Gemini" if simp.meta.get("engine") == "gemini" else "rule-based"
        st.caption(f"Engine: {engine} · level: {level if engine == 'Gemini' else 'n/a'}")
        st.info(simp.text)
        if simp.meta.get("bullets"):
            st.markdown("**📌 Key points**")
            st.markdown("\n".join(f"- {b}" for b in simp.meta["bullets"]))
        if simp.meta.get("glossary"):
            st.markdown("**📖 Glossary**")
            st.markdown("\n".join(f"- **{k}** — {v}" for k, v in simp.meta["glossary"].items()))
        speak_button(simp.text, "en", "tts_simp")
    else:
        st.error(simp.error)

with tabs[3]:
    if not use_llm:
        st.info("Summaries need Gemini — add `GEMINI_API_KEY` to your `.env`.")
    else:
        with st.spinner("Summarising…"):
            summ = cached_summary(text)
        if summ.ok:
            st.markdown(summ.text)
            st.download_button("⬇️ Summary .md", summ.text, "summary.md")
        else:
            st.error(summ.error)

with tabs[4]:
    if not use_llm:
        st.info("Quizzes need Gemini — add `GEMINI_API_KEY` to your `.env`.")
    else:
        c1, c2, c3 = st.columns([1, 1, 2])
        n = c1.number_input("Questions", 3, 15, 5)
        diff = c2.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
        if c3.button("🎲 Generate quiz", type="primary", width="stretch"):
            with st.spinner("Writing questions…"):
                res, quiz = llm.make_quiz(text, int(n), diff)
            if res.ok:
                st.session_state.quiz = quiz
            else:
                st.error(res.error)
        quiz = st.session_state.quiz
        if quiz:
            with st.form("quiz"):
                picks = [st.radio(f"**Q{i}.** {q.question}", q.options, index=None, key=f"q{i}")
                         for i, q in enumerate(quiz.questions, 1)]
                submitted = st.form_submit_button("Check answers")
            if submitted:
                score = 0
                for i, (q, pick) in enumerate(zip(quiz.questions, picks, strict=True), 1):
                    correct = q.options[q.answer_index]
                    if pick == correct:
                        score += 1
                        st.success(f"Q{i}: correct — {q.explanation}")
                    else:
                        st.error(f"Q{i}: answer is **{correct}** — {q.explanation}")
                st.metric("Score", f"{score}/{len(quiz.questions)}")

with tabs[5]:
    if not use_llm:
        st.info("Q&A needs Gemini — add `GEMINI_API_KEY` to your `.env`.")
    else:
        q = st.text_input("Ask a question about this lecture")
        if q:
            with st.spinner("Thinking…"):
                ans = llm.ask(text, q)
            if ans.ok:
                st.markdown(ans.text)
            else:
                st.error(ans.error)
