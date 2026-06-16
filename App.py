import streamlit as st
import speech_recognition as sr
import tempfile
import os

st.title("🧠 Cognitive Screening Test")

SENTENCE_1 = "I only know that John is the one to help today"
SENTENCE_2 = "The cat always hid under the couch when dogs were in the room"

def transcribe_audio(audio_bytes: bytes) -> str | None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        audio_path = f.name
    try:
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = r.record(source)
        return r.recognize_google(audio_data)
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        st.error(f"Speech service error: {e}")
        return None
    finally:
        os.unlink(audio_path)

def similarity_score(spoken: str, reference: str) -> float:
    ref_words = set(reference.lower().split())
    spoken_words = set(spoken.lower().split())
    if not ref_words:
        return 0.0
    return len(ref_words & spoken_words) / len(ref_words)

# -----------------------------
# 1. WORD MEMORY
# -----------------------------
st.subheader("1. Word Memory Test")
words = ["face", "velvet", "church", "daisy", "red"]
st.write("Memorize these words:")
st.write(words)
st.session_state["words"] = words
st.write("---")

# -----------------------------
# 2. ATTENTION TEST
# -----------------------------
st.subheader("2. Attention Test")
forward = st.text_input("Enter FORWARD numbers (e.g. 2 1 8 5 4)")
backward = st.text_input("Enter BACKWARD numbers (e.g. 2 4 7)")
st.write("---")

# -----------------------------
# 3. LANGUAGE TEST (VOICE)
# -----------------------------
st.subheader("3. Language Repetition")

# ── Sentence 1 ──────────────────────────────────────────────────────────────
st.markdown(f"**Sentence 1:** {SENTENCE_1}")
st.write("Record yourself repeating this sentence:")

audio_lang1 = st.audio_input("🎙 Sentence 1", key="lang1_audio")

# transcribe only when new audio arrives (bytes changed)
if audio_lang1 is not None:
    audio_bytes = audio_lang1.read()
    prev = st.session_state.get("lang1_bytes")
    if audio_bytes != prev:
        st.session_state["lang1_bytes"] = audio_bytes
        with st.spinner("Transcribing…"):
            result = transcribe_audio(audio_bytes)
        if result is not None:
            st.session_state["lang1_text"] = result
            st.session_state["lang1_score"] = similarity_score(result, SENTENCE_1)
        else:
            st.session_state["lang1_text"] = ""
            st.session_state["lang1_score"] = 0.0
            st.error("Could not recognise — please try again.")

if st.session_state.get("lang1_text"):
    st.success(f"You said: **{st.session_state['lang1_text']}**")
    st.progress(st.session_state["lang1_score"],
                text=f"Match: {st.session_state['lang1_score']:.0%}")

# ── Sentence 2 ──────────────────────────────────────────────────────────────
st.markdown(f"**Sentence 2:** {SENTENCE_2}")
st.write("Record yourself repeating this sentence:")

audio_lang2 = st.audio_input("🎙 Sentence 2", key="lang2_audio")

if audio_lang2 is not None:
    audio_bytes = audio_lang2.read()
    prev = st.session_state.get("lang2_bytes")
    if audio_bytes != prev:
        st.session_state["lang2_bytes"] = audio_bytes
        with st.spinner("Transcribing…"):
            result = transcribe_audio(audio_bytes)
        if result is not None:
            st.session_state["lang2_text"] = result
            st.session_state["lang2_score"] = similarity_score(result, SENTENCE_2)
        else:
            st.session_state["lang2_text"] = ""
            st.session_state["lang2_score"] = 0.0
            st.error("Could not recognise — please try again.")

if st.session_state.get("lang2_text"):
    st.success(f"You said: **{st.session_state['lang2_text']}**")
    st.progress(st.session_state["lang2_score"],
                text=f"Match: {st.session_state['lang2_score']:.0%}")

st.write("---")

# -----------------------------
# 4. ABSTRACTION
# -----------------------------
st.subheader("4. Abstraction")
t1 = st.text_input("Train vs Bicycle similarity?")
t2 = st.text_input("Watch vs Ruler similarity?")

# -----------------------------
# 5. DELAYED RECALL
# -----------------------------
st.subheader("5. Final Memory Test")
recall = st.text_input("Type the words you remember")
st.write("Words were: face, velvet, church, daisy, red")
st.write("---")

# -----------------------------
# SCORING
# -----------------------------
if st.button("Calculate Score"):
    score = 0
    details = []

    s1 = st.session_state.get("lang1_score", 0.0)
    s2 = st.session_state.get("lang2_score", 0.0)
    if s1 >= 0.6:
        score += 1
        details.append(f"✅ Sentence 1: {s1:.0%} match")
    else:
        details.append(f"❌ Sentence 1: {s1:.0%} match (need ≥ 60%)")
    if s2 >= 0.6:
        score += 1
        details.append(f"✅ Sentence 2: {s2:.0%} match")
    else:
        details.append(f"❌ Sentence 2: {s2:.0%} match (need ≥ 60%)")

    if len(t1.strip()) > 2:
        score += 1
        details.append("✅ Abstraction 1: answered")
    else:
        details.append("❌ Abstraction 1: no answer")
    if len(t2.strip()) > 2:
        score += 1
        details.append("✅ Abstraction 2: answered")
    else:
        details.append("❌ Abstraction 2: no answer")

    correct_words = st.session_state.get("words", [])
    found = 0
    if recall:
        found = sum(word in recall.lower() for word in correct_words)
        score += found
    details.append(f"🧠 Delayed recall: {found}/{len(correct_words)} words")

    st.subheader("Results")
    for d in details:
        st.write(d)
    st.write(f"**Total Score: {score}**")

    if score >= 5:
        st.success("🟢 Good performance (prototype)")
    elif score >= 3:
        st.warning("🟡 Mild concern (prototype)")
    else:
        st.error("🔴 Needs review (prototype)")

    st.write("⚠️ Not a medical diagnosis tool")
