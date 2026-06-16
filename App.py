import streamlit as st
import speech_recognition as sr
import tempfile
import os

st.title("🧠 Cognitive Screening Test")

SENTENCE_1 = "I only know that John is the one to help today"
SENTENCE_2 = "The cat always hid under the couch when dogs were in the room"
WORDS = ["face", "velvet", "church", "daisy", "red"]
FORWARD_SEQUENCE = ["2", "1", "8", "5", "4"]
BACKWARD_SEQUENCE = ["2", "4", "7"]


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


def digits_in_order(text: str, sequence: list) -> bool:
    spoken_digits = [ch for ch in text if ch.isdigit()]
    return spoken_digits == sequence


def voice_input(label: str, key: str):
    """Show audio recorder, transcribe only when new bytes arrive. Returns transcript string."""
    audio = st.audio_input(label, key=key)
    if audio is not None:
        audio_bytes = audio.read()
        if audio_bytes != st.session_state.get(f"{key}_bytes"):
            st.session_state[f"{key}_bytes"] = audio_bytes
            with st.spinner("Transcribing…"):
                result = transcribe_audio(audio_bytes)
            st.session_state[f"{key}_text"] = result if result else ""
            if result is None:
                st.error("Could not recognise — please try again.")
    return st.session_state.get(f"{key}_text", "")


# ─────────────────────────────────────────────
# 1. WORD MEMORY
# ─────────────────────────────────────────────
st.subheader("1. Word Memory Test")
st.write("Memorize these words:")
st.info("  ·  ".join(WORDS))
st.session_state["words"] = WORDS
st.write("---")

# ─────────────────────────────────────────────
# 2. ATTENTION TEST — voice
# ─────────────────────────────────────────────
st.subheader("2. Attention Test")

st.markdown("**Forward Digit Span** — say these numbers in the same order:")
st.info("2 – 1 – 8 – 5 – 4")
fwd = voice_input("🎙 Record forward numbers", "fwd")
if fwd:
    st.success(f"You said: **{fwd}**")
    fwd_ok = digits_in_order(fwd, FORWARD_SEQUENCE)
    st.write("✅ Correct!" if fwd_ok else "❌ Not quite.")
    st.session_state["fwd_ok"] = fwd_ok

st.markdown("**Backward Digit Span** — say **7 – 4 – 2** in reverse:")
st.info("Say: 2 – 4 – 7")
bwd = voice_input("🎙 Record backward numbers", "bwd")
if bwd:
    st.success(f"You said: **{bwd}**")
    bwd_ok = digits_in_order(bwd, BACKWARD_SEQUENCE)
    st.write("✅ Correct!" if bwd_ok else "❌ Not quite.")
    st.session_state["bwd_ok"] = bwd_ok

st.write("---")

# ─────────────────────────────────────────────
# 3. LANGUAGE REPETITION — voice
# ─────────────────────────────────────────────
st.subheader("3. Language Repetition")

st.markdown(f"**Sentence 1:** {SENTENCE_1}")
lang1 = voice_input("🎙 Record sentence 1", "lang1")
if lang1:
    sc = similarity_score(lang1, SENTENCE_1)
    st.success(f"You said: **{lang1}**")
    st.progress(sc, text=f"Match: {sc:.0%}")
    st.session_state["lang1_score"] = sc

st.markdown(f"**Sentence 2:** {SENTENCE_2}")
lang2 = voice_input("🎙 Record sentence 2", "lang2")
if lang2:
    sc = similarity_score(lang2, SENTENCE_2)
    st.success(f"You said: **{lang2}**")
    st.progress(sc, text=f"Match: {sc:.0%}")
    st.session_state["lang2_score"] = sc

st.write("---")

# ─────────────────────────────────────────────
# 4. ABSTRACTION — voice
# ─────────────────────────────────────────────
st.subheader("4. Abstraction")

# --- Question 1 ---
st.markdown("**How are a Train and a Bicycle similar?**")

# Notice we changed the widget key name to "abs1_widget" to avoid the collision
abs1 = voice_input("🎙️ Record your answer", "abs1_widget")

if abs1:
    st.success(f"You said: **{abs1}**")
    
    # Normalize text to lowercase for cleaner matching
    answer1_lower = abs1.lower()
    vehicle_keywords = ["vehicle", "transport", "transportation", "wheels", "ride", "travel", "move"]
    
    if any(keyword in answer1_lower for keyword in vehicle_keywords):
        st.info("🎯 Correct! They are both forms of vehicles/transportation.")
    else:
        st.warning("⚠️ That's an interesting answer, but think about how they move people or things!")


# --- Question 2 ---
st.markdown("**How are a Watch and a Ruler similar?**")

# Changed the widget key name to "abs2_widget" to avoid the collision
abs2 = voice_input("🎙️ Record your answer", "abs2_widget")

if abs2:
    st.success(f"You said: **{abs2}**")
    
    # Normalize text to lowercase
    answer2_lower = abs2.lower()
    measurement_keywords = ["measure", "measurement", "tool", "instrument", "scale", "tell time", "numbers"]
    
    if any(keyword in answer2_lower for keyword in measurement_keywords):
        st.info("🎯 Correct! They are both tools used for measurement (time and length).")
    else:
        st.warning("⚠️ Not quite! Think about what both of these objects are used to do.")

st.write("---")

# ─────────────────────────────────────────────
# 5. DELAYED RECALL — voice, NO hint
# ─────────────────────────────────────────────
st.subheader("5. Final Memory Test")
st.write("Say as many words as you can remember from the beginning:")

recall = voice_input("🎙 Record the words you remember", "recall")
if recall:
    st.success(f"You said: **{recall}**")
    st.session_state["recall"] = recall

st.write("---")

# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────
if st.button("Calculate Score"):
    score = 0
    details = []

    # Attention
    if st.session_state.get("fwd_ok"):
        score += 1
        details.append("✅ Forward digit span: correct")
    else:
        details.append("❌ Forward digit span: incorrect")

    if st.session_state.get("bwd_ok"):
        score += 1
        details.append("✅ Backward digit span: correct")
    else:
        details.append("❌ Backward digit span: incorrect")

    # Language
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

    # Abstraction
    if len(st.session_state.get("abs1", "").strip()) > 2:
        score += 1
        details.append("✅ Abstraction 1: answered")
    else:
        details.append("❌ Abstraction 1: no answer")
    if len(st.session_state.get("abs2", "").strip()) > 2:
        score += 1
        details.append("✅ Abstraction 2: answered")
    else:
        details.append("❌ Abstraction 2: no answer")

    # Delayed recall — no hint was shown
    recall_spoken = st.session_state.get("recall", "")
    found = sum(w in recall_spoken.lower() for w in WORDS) if recall_spoken else 0
    score += found
    details.append(f"🧠 Delayed recall: {found}/{len(WORDS)} words")

    st.subheader("Results")
    for d in details:
        st.write(d)

    max_score = 2 + 2 + 2 + len(WORDS)
    st.write(f"**Total Score: {score} / {max_score}**")

    if score >= int(max_score * 0.7):
        st.success("🟢 Good performance (prototype)")
    elif score >= int(max_score * 0.4):
        st.warning("🟡 Mild concern (prototype)")
    else:
        st.error("🔴 Needs review (prototype)")

    st.caption("⚠️ Not a medical diagnosis tool")
