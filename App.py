pip install streamlit streamlit-webrtc av librosa scipy numpy
import streamlit as st
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from io import BytesIO

st.title("🧠 Cognitive Screening Test (Voice Enabled)")

# -----------------------------
# WORD MEMORY
# -----------------------------
st.subheader("1. Memorize these words")

words = ["face", "velvet", "church", "daisy", "red"]
st.write(words)

st.session_state["words"] = words

st.write("---")


# -----------------------------
# FUNCTION: AUDIO → TEXT
# -----------------------------
def audio_to_text(audio_bytes):
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(BytesIO(audio_bytes))
    
    with audio_file as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
        return text.lower()
    except:
        return ""


# -----------------------------
# 2. ATTENTION TEST
# -----------------------------
st.subheader("2. Attention Test (Speak answers)")

audio_forward = mic_recorder(
    start_prompt="🎤 Speak FORWARD numbers",
    stop_prompt="⏹ Stop"
)

audio_backward = mic_recorder(
    start_prompt="🎤 Speak BACKWARD numbers",
    stop_prompt="⏹ Stop"
)


forward_text = ""
backward_text = ""

if audio_forward:
    forward_text = audio_to_text(audio_forward["bytes"])
    st.write("You said (forward):", forward_text)

if audio_backward:
    backward_text = audio_to_text(audio_backward["bytes"])
    st.write("You said (backward):", backward_text)

st.write("Expected forward: 2 1 8 5 4")
st.write("Expected backward: 2 4 7")

st.write("---")


# -----------------------------
# 3. LANGUAGE TEST
# -----------------------------
st.subheader("3. Language Repetition")

audio_lang1 = mic_recorder(
    start_prompt="🎤 Repeat sentence 1",
    stop_prompt="⏹ Stop",
    key="lang1"
)

audio_lang2 = mic_recorder(
    start_prompt="🎤 Repeat sentence 2",
    stop_prompt="⏹ Stop",
    key="lang2"
)

lang1_text = ""
lang2_text = ""

if audio_lang1:
    lang1_text = audio_to_text(audio_lang1["bytes"])
    st.write("Sentence 1:", lang1_text)

if audio_lang2:
    lang2_text = audio_to_text(audio_lang2["bytes"])
    st.write("Sentence 2:", lang2_text)

st.write("---")


# -----------------------------
# 4. ABSTRACTION (VOICE OPTIONAL, TEXT HERE)
# -----------------------------
st.subheader("4. Abstraction")

t1 = st.text_input("Train vs Bicycle similarity?")
t2 = st.text_input("Watch vs Ruler similarity?")


# -----------------------------
# 5. DELAYED RECALL (VOICE)
# -----------------------------
st.subheader("5. Final Memory Test")

audio_recall = mic_recorder(
    start_prompt="🎤 Recall the words",
    stop_prompt="⏹ Stop",
    key="recall"
)

recall_text = ""

if audio_recall:
    recall_text = audio_to_text(audio_recall["bytes"])
    st.write("You said:", recall_text)

st.write("Words were: face, velvet, church, daisy, red")


# -----------------------------
# SCORING
# -----------------------------
if st.button("Calculate Score"):

    score = 0

    # abstraction
    if len(t1) > 2:
        score += 1
    if len(t2) > 2:
        score += 1

    # recall scoring
    correct_words = st.session_state.get("words", [])

    if recall_text:
        found = sum(word in recall_text for word in correct_words)
        score += found


    st.subheader("Results")

    if score >= 5:
        st.success("🟢 Good performance (prototype)")
    elif score >= 3:
        st.warning("🟡 Mild concern (prototype)")
    else:
        st.error("🔴 Needs review (prototype)")

    st.write("⚠️ Not a medical diagnosis tool")
