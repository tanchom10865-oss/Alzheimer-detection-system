pip install streamlit streamlit-webrtc av librosa scipy numpy
import streamlit as st
import numpy as np
import librosa
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av

st.title("🧠 Cognitive Speech Test (Stable Version)")

# -----------------------------
# WORDS
# -----------------------------
st.subheader("1. Memorize these words")
words = ["face", "velvet", "church", "daisy", "red"]
st.write(words)


# -----------------------------
# AUDIO PROCESSOR (FIXED)
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
# ANALYZE BUTTON
# -----------------------------
if st.button("📊 Analyze Speech"):

    processor = ctx.audio_processor

    if processor is None or len(processor.frames) == 0:
        st.warning("No audio recorded yet. Please speak first.")
        st.stop()

    # Combine audio safely
    audio = np.concatenate(processor.frames, axis=1).flatten()

    sr = 48000

    y = audio.astype(np.float32)

    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))


    # -----------------------------
    # PITCH
    # -----------------------------
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

    pitch_values = []
    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax()
        pitch = pitches[index, t]
        if pitch > 0:
            pitch_values.append(pitch)

    avg_pitch = np.mean(pitch_values) if pitch_values else 0


    # -----------------------------
    # FLUENCY
    # -----------------------------
    intervals = librosa.effects.split(y, top_db=20)
    num_segments = len(intervals)

    rms = librosa.feature.rms(y=y)[0]
    fluency = np.mean(rms)


    # -----------------------------
    # RESULTS
    # -----------------------------
    st.subheader("📊 Results")

    st.write("🎯 Average Pitch:", round(avg_pitch, 2))
    st.write("🧩 Speech Segments:", num_segments)
    st.write("📈 Fluency Score:", round(fluency, 5))


    # -----------------------------
    # SIMPLE MODEL
    # -----------------------------
    risk = 0

    if avg_pitch < 120:
        risk += 1
    if num_segments > 10:
        risk += 1
    if fluency < 0.02:
        risk += 1


    st.subheader("🧠 Cognitive Indicator")

    if risk == 0:
        st.success("Low risk indicators")
    elif risk == 1:
        st.warning("Mild risk indicators")
    else:
        st.error("Higher risk indicators")
