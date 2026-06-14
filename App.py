import streamlit as st

st.title("Alzheimer's Detection System")

st.write("My Streamlit app is working!")
import streamlit as st

st.title("🧠 Cognitive Screening AI (Prototype)")

# --- IMAGE ---
st.subheader("1. Look at this image")

st.image("image1.jpg", caption="Study Image", use_container_width=True)

# --- QUESTIONS ---
st.subheader("2. Answer the questions")

q1 = st.radio(
    "What did you see in the image?",
    ["People", "Animals", "Objects", "I don't remember"]
)

q2 = st.radio(
    "How clear was your memory of the image?",
    ["Very clear", "Somewhat clear", "Unclear", "Not sure"]
)

q3 = st.text_input("Describe the image in your own words:")

# --- SIMPLE AI LOGIC (placeholder) ---
score = 0

if q1 == "I don't remember":
    score += 2
if q2 in ["Unclear", "Not sure"]:
    score += 2
if len(q3) < 10:
    score += 1

# --- RESULT ---
if st.button("Analyze"):
    if score >= 4:
        st.error("⚠️ High risk: Cognitive decline indicators detected")
    elif score == 2 or score == 3:
        st.warning("🟡 Moderate risk: Some memory issues detected")
    else:
        st.success("🟢 Low risk: No strong indicators detected")
      pip install streamlit-audio-recorder
from audio_recorder_streamlit import audio_recorder

audio_bytes = audio_recorder()

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    st.write("Voice recorded successfully!")
st.image(image2.jpg")
