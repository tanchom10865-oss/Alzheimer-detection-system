```python
import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import tempfile

st.title("🧠 Cognitive Screening Test (Voice Attention Test)")

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
# 2. ATTENTION TEST (VOICE)
# -----------------------------
st.subheader("2. Attention Test")

st.write("Forward numbers: 2 1 8 5 4")
st.write("Backward numbers: 7 4 2")

forward_text = ""
backward_text = ""

# Forward recording
st.write("🎤 Say the FORWARD numbers")

audio_forward = mic_recorder(
    start_prompt="Start Forward Recording",
    stop_prompt="Stop Recording",
    key="forward_audio"
)

if audio_forward:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_forward["bytes"])
        audio_path = f.name

    r = sr.Recognizer()

    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = r.record(source)

        forward_text = r.recognize_google(audio_data)
        st.success(f"You said: {forward_text}")

    except Exception:
        st.error("Could not recognize speech")

# Backward recording
st.write("🎤 Say the BACKWARD numbers")

audio_backward = mic_recorder(
    start_prompt="Start Backward Recording",
    stop_prompt="Stop Recording",
    key="backward_audio"
)

if audio_backward:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_backward["bytes"])
        audio_path = f.name

    r = sr.Recognizer()

    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = r.record(source)

        backward_text = r.recognize_google(audio_data)
        st.success(f"You said: {backward_text}")

    except Exception:
        st.error("Could not recognize speech")

st.write("---")

# -----------------------------
# 3. LANGUAGE TEST
# -----------------------------
st.subheader("3. Language Repetition")

lang1 = st.text_input(
    "Repeat sentence 1: I only know that John is the one to help today"
)

lang2 = st.text_input(
    "Repeat sentence 2: The cat always hid under the couch when dogs were in the room"
)

st.write("---")

# -----------------------------
# 4. ABSTRACTION
# -----------------------------
st.subheader("4. Abstraction")

t1 = st.text_input("Train vs Bicycle similarity?")
t2 = st.text_input("Watch vs Ruler similarity?")

st.write("---")

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

    # Attention scoring
    if (
        "2" in forward_text
        and "1" in forward_text
        and "8" in forward_text
        and "5" in forward_text
        and "4" in forward_text
    ):
        score += 1

    if (
        "2" in backward_text
        and "4" in backward_text
        and "7" in backward_text
    ):
        score += 1

    # Abstraction scoring
    if len(t1.strip()) > 2:
        score += 1

    if len(t2.strip()) > 2:
        score += 1

    # Recall scoring
    correct_words = st.session_state.get("words", [])

    if recall:
        found = sum(word in recall.lower() for word in correct_words)
        score += found

    st.subheader("Results")

    st.write(f"Score: {score}")

    if score >= 5:
        st.success("🟢 Good performance (prototype)")
    elif score >= 3:
        st.warning("🟡 Mild concern (prototype)")
    else:
        st.error("🔴 Needs review (prototype)")

    st.write("⚠️ Not a medical diagnosis tool")
```
