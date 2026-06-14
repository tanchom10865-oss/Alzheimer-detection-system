pip install streamlit streamlit-webrtc av librosa numpy scipy
import streamlit as st
import numpy as np
import librosa
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av

st.title("🧠 Alzheimer Cognitive Screening Test (Speech AI Prototype)")

# -----------------------------
# 1. WORD MEMORY TEST
# -----------------------------
st.subheader("1. Word Memory Test")

words = ["face", "velvet", "church", "daisy", "red"]
st.write("Memorize these words:")
st.write(words)

st.session_state["words"] = words

st.write("---")


# -----------------------------
# AUDIO PROCESSOR
# -----------------------------
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.frames.append(audio)
        return frame


ctx = webrtc_streamer(
    key="mic",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)


# -----------------------------
# AUDIO ANALYSIS FUNCTION
# -----------------------------
def analyze(audio, sr=48000):

    y = audio.astype(np.float32)

    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))

    # pitch
    pitches, mags = librosa.piptrack(y=y, sr=sr)
    pitch_vals = []

    for t in range(pitches.shape[1]):
        i = mags[:, t].argmax()
        p = pitches[i, t]
        if p > 0:
            pitch_vals.append(p)

    avg_pitch = np.mean(pitch_vals) if pitch_vals else 0

    # fluency (speech continuity)
    segments = librosa.effects.split(y, top_db=20)
    num_segments = len(segments)

    rms = librosa.feature.rms(y=y)[0]
    fluency = np.mean(rms)

    return avg_pitch, num_segments, fluency


# -----------------------------
# 2–5 TEST SECTIONS
# -----------------------------
st.subheader("2–5. Speak During Tasks")

st.write("👉 Please perform ALL tasks while recording:")
st.write("""
- Say numbers forward: 2 1 8 5 4  
- Say numbers backward: 2 4 7  
- Repeat sentences  
- Recall words at the end  
""")

st.write("---")


# -----------------------------
# ANALYZE BUTTON
# -----------------------------
if st.button("📊 Calculate Cognitive Score"):

    processor = ctx.audio_processor

    if processor is None or len(processor.frames) == 0:
        st.warning("No audio detected. Please record your voice first.")
        st.stop()

    audio = np.concatenate(processor.frames, axis=1).flatten()

    pitch, segments, fluency = analyze(audio)

    st.subheader("📊 Speech Biomarker Results")

    st.write("🎯 Pitch (avg):", round(pitch, 2))
    st.write("🧩 Speech Segments (pauses):", segments)
    st.write("📈 Fluency Score:", round(fluency, 5))

    # -----------------------------
    # SCORING SYSTEM
    # -----------------------------
    score = 0

    # voice indicators
    if pitch < 120:
        score += 1
    if segments > 10:
        score += 1
    if fluency < 0.02:
        score += 1

    # simple cognitive interpretation
    st.subheader("🧠 Cognitive Indicator Result")

    if score == 0:
        st.success("🟢 Low risk cognitive indicators")
    elif score == 1:
        st.warning("🟡 Mild risk indicators")
    else:
        st.error("🔴 Higher risk indicators")

    st.write("---")
    st.write("⚠️ This is a research prototype, not a medical diagnosis")
