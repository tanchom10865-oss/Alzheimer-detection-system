import streamlit as st
import speech_recognition as sr
import tempfile
import os
import io

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

FORWARD_SEQUENCE = ["2", "1", "8", "5", "4"]
BACKWARD_SEQUENCE = ["7", "4", "2"]

st.info(
    "**Forward:** Say these numbers in the same order: **2 – 1 – 8 – 5 – 4**\n\n"
    "**Backward:** Say these numbers in reverse order: **7 – 4 – 2** → say **2 – 4 – 7**"
)


def transcribe_audio(audio_bytes: bytes) -> str | None:
    """Write audio bytes to a temp WAV file and return recognised text, or None on failure."""
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


def digits_in_order(text: str, sequence: list) -> bool:
    """Return True if every digit in *sequence* appears in *text* in the correct order."""
    if not text:
        return False
    spoken_digits = [ch for ch in text if ch.isdigit()]
    return spoken_digits == sequence


def score_forward(text: str) -> bool:
    return digits_in_order(text, FORWARD_SEQUENCE)


def score_backward(text: str) -> bool:
    return digits_in_order(text, list(reversed(BACKWARD_SEQUENCE)))


# ── Forward digit span ──────────────────────────────────────────────────────
st.markdown("#### 🔢 Forward Digit Span")
st.write("Record yourself saying: **2 – 1 – 8 – 5 – 4**")

audio_forward = st.audio_input("Forward recording", key="forward_audio")

forward_text = st.session_state.get("forward_text", "")

if audio_forward is not None:
    with st.spinner("Transcribing…"):
        result = transcribe_audio(audio_forward.read())
    if result is not None:
        forward_text = result
        st.session_state["forward_text"] = forward_text
        st.success(f"You said: **{forward_text}**")
        if score_forward(forward_text):
            st.success("✅ Correct order!")
        else:
            st.warning("❌ Digits missing or out of order.")
    else:
        st.error("Could not recognise speech — please try again.")
elif forward_text:
    st.info(f"Last recognised: **{forward_text}**")

# ── Backward digit span ─────────────────────────────────────────────────────
st.markdown("#### 🔁 Backward Digit Span")
st.write("You will hear **7 – 4 – 2**. Record yourself saying them **backwards**: **2 – 4 – 7**")

audio_backward = st.audio_input("Backward recording", key="backward_audio")

backward_text = st.session_state.get("backward_text", "")

if audio_backward is not None:
    with st.spinner("Transcribing…"):
        result = transcribe_audio(audio_backward.read())
    if result is not None:
        backward_text = result
        st.session_state["backward_text"] = backward_text
        st.success(f"You said: **{backward_text}**")
        if score_backward(backward_text):
            st.success("✅ Correct reverse order!")
        else:
            st.warning("❌ Digits missing or wrong order.")
    else:
        st.error("Could not recognise speech — please try again.")
elif backward_text:
    st.info(f"Last recognised: **{backward_text}**")

# ── Vigilance / sustained attention ─────────────────────────────────────────
st.markdown("#### 🎯 Vigilance Task")
st.write(
    "Read the letter sequence below. Say **'yes'** every time you see the letter **A**, "
    "then record your responses."
)
VIGILANCE_SEQUENCE = "F B A C M N A A B C L A F M A K"
st.code(VIGILANCE_SEQUENCE, language=None)
VIGILANCE_A_POSITIONS = [i for i, ch in enumerate(VIGILANCE_SEQUENCE.split()) if ch == "A"]
st.caption(f"There are {len(VIGILANCE_A_POSITIONS)} A's in this sequence.")

audio_vigilance = st.audio_input("Vigilance recording", key="vigilance_audio")

vigilance_text = st.session_state.get("vigilance_text", "")

if audio_vigilance is not None:
    with st.spinner("Transcribing…"):
        result = transcribe_audio(audio_vigilance.read())
    if result is not None:
        vigilance_text = result
        st.session_state["vigilance_text"] = vigilance_text
        st.success(f"You said: **{vigilance_text}**")
        spoken_words = vigilance_text.lower().split()
        tap_count = sum(1 for w in spoken_words if w in {"yes", "yeah", "a", "ay", "yep"})
        st.info(f"Detected ~{tap_count} response(s). Expected {len(VIGILANCE_A_POSITIONS)}.")
    else:
        st.error("Could not recognise speech — please try again.")
elif vigilance_text:
    st.info(f"Last recognised: **{vigilance_text}**")

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
t1 = st.text_input("Train vs Bicycle — what do they have in common?")
t2 = st.text_input("Watch vs Ruler — what do they have in common?")
st.write("---")

# -----------------------------
# 5. DELAYED RECALL
# -----------------------------
st.subheader("5. Final Memory Test")
recall = st.text_input("Type the words you remember from section 1")
st.write("Words were: face, velvet, church, daisy, red")
st.write("---")

# -----------------------------
# SCORING
# -----------------------------
if st.button("Calculate Score"):
    score = 0
    details = []

    fwd = st.session_state.get("forward_text", "")
    bwd = st.session_state.get("backward_text", "")

    if score_forward(fwd):
        score += 1
        details.append("✅ Forward digit span: correct")
    else:
        details.append("❌ Forward digit span: incorrect")

    if score_backward(bwd):
        score += 1
        details.append("✅ Backward digit span: correct")
    else:
        details.append("❌ Backward digit span: incorrect")

    vig_text = st.session_state.get("vigilance_text", "")
    vig_words = vig_text.lower().split() if vig_text else []
    vig_taps = sum(1 for w in vig_words if w in {"yes", "yeah", "a", "ay", "yep"})
    if abs(vig_taps - len(VIGILANCE_A_POSITIONS)) <= 1:
        score += 1
        details.append(f"✅ Vigilance: ~{vig_taps} taps (expected {len(VIGILANCE_A_POSITIONS)})")
    else:
        details.append(f"❌ Vigilance: ~{vig_taps} taps (expected {len(VIGILANCE_A_POSITIONS)})")

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

    if score >= 7:
        st.success("🟢 Good performance (prototype)")
    elif score >= 4:
        st.warning("🟡 Mild concern (prototype)")
    else:
        st.error("🔴 Needs review (prototype)")

    st.caption("⚠️ Not a medical diagnosis tool.")
