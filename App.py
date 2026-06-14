pip install streamlit streamlit-webrtc av librosa scipy numpy
import streamlit as st
import numpy as np
import librosa
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av

st.title("🧠 Cognitive Screening Test (Speech Biomarker AI)")

# -----------------------------
# 1. MEMORY WORDS
# -----------------------------
st.subheader("1. Memorize these words")

words = ["face", "velvet", "church", "daisy", "red"]
st.write(words)

st.session_state["words"] = words


# -----------------------------
# 2. AUDIO CAPTURE (MICROPHONE)
# -----------------------------
st.subheader("2. Speak the words aloud")

audio_buffer = []

class AudioProcessor(AudioProcessorBase):
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        audio_buffer.append(audio)
        return frame


ctx = webrtc_streamer(
    key="mic",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)


# -----------------------------
# 3. ANALYZE AUDIO BUTTON
# -----------------------------
if st.button("📊 Analyze Speech"):

    if len(audio_buffer) == 0:
        st.warning("No audio detected. Please speak first.")
        st.stop()

    # Combine audio chunks
    audio = np.concatenate(audio_buffer, axis=1).flatten()

    sr = 48000  # default browser sample rate

    # Convert to librosa format
    y = audio.astype(np.float32)
    y = y / np.max(np.abs(y)) if np.max(np.abs(y)) > 0 else y


    # -----------------------------
    # PITCH ANALYSIS
    # -----------------------------
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

    pitch_values = []

    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax()
        pitch = pitches[index, t]
        if pitch > 0:
            pitch_values.append(pitch)

    avg_pitch = np.mean(pitch_values) if len(pitch_values) > 0 else 0


    # -----------------------------
    # FLUENCY (PAUSES + ENERGY)
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
    # SIMPLE RISK MODEL
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
