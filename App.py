import streamlit as st

st.title("🧠 Cognitive Screening Test (Prototype)")

# -----------------------------
# 1. WORD MEMORY (ENCODING)
# -----------------------------
st.subheader("1. Memorize these words")

words = ["face", "velvet", "church", "daisy", "red"]
st.write("Remember these words:")
st.write(words)

st.session_state["words"] = words

st.write("---")

# -----------------------------
# 2. ATTENTION TEST
# -----------------------------
st.subheader("2. Attention Test")

forward = st.text_input("Repeat numbers FORWARD: 2 1 8 5 4")
backward = st.text_input("Repeat numbers BACKWARD: 7 4 2")

st.write("---")

# -----------------------------
# 3. LANGUAGE TEST
# -----------------------------
st.subheader("3. Language Repetition")

lang1 = st.text_input("Repeat: I only know that John is the one to help today")
lang2 = st.text_input("Repeat: The cat always hides under the couch when dogs are in the room")

st.write("---")

# -----------------------------
# 4. ABSTRACTION TEST
# -----------------------------
st.subheader("4. Abstraction")

t1 = st.text_input("What is similar between: train and bicycle?")
t2 = st.text_input("What is similar between: watch and ruler?")

st.write("---")

# -----------------------------
# 5. DELAYED RECALL
# -----------------------------
st.subheader("5. Final Memory Test")

recall = st.text_input("Recall the words from the beginning (separate with spaces)")

# -----------------------------
# SCORING (simple prototype)
# -----------------------------
if st.button("Calculate Score"):

    score = 0

    # word recall scoring
    correct_words = st.session_state.get("words", [])
    user_words = recall.lower().split()

    for w in correct_words:
        if w in user_words:
            score += 1

    # attention scoring (very simple check)
    if forward.strip() == "2 1 8 5 4":
        score += 1
    if backward.strip() == "2 4 7":
        score += 1

    # language (basic check)
    if len(lang1) > 10:
        score += 1
    if len(lang2) > 10:
        score += 1

    # abstraction (basic check)
    if len(t1) > 3:
        score += 1
    if len(t2) > 3:
        score += 1

    # -----------------------------
    # RESULTS
    # -----------------------------
    st.subheader("Results")

    if score >= 8:
        st.success(f"🟢 Good cognitive performance (Score: {score})")
    elif score >= 5:
        st.warning(f"🟡 Moderate performance (Score: {score})")
    else:
        st.error(f"🔴 Low performance (Score: {score})")

    st.write("⚠️ This is a prototype screening tool, not a medical diagnosis.")
import streamlit as st
from streamlit_mic_recorder import mic_recorder

st.title("🎤 Mic Test")

st.write("If this works, you will see a record button below.")

audio = mic_recorder(
    start_prompt="🎤 Start recording",
    stop_prompt="⏹ Stop recording"
)

if audio:
    st.success("Audio recorded ✔")
    st.audio(audio["bytes"])
