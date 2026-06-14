import streamlit as st
import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile
import numpy as np
import librosa

st.title("🧠 Cognitive Screening Test (Speech Biomarker Version)")

# -----------------------------
# 1. WORD MEMORY
# -----------------------------
st.subheader("1. Memorize these words")

words = ["face", "velvet", "church", "daisy", "red"]
st.write(words)

st.session_state["words"] = words


# -----------------------------
# 2. RECORD SPEECH
# -----------------------------
st.subheader("2. Speak the words aloud")

duration = st.slider("Recording time (seconds)", 3, 10, 5)

if st.button("🎤 Start Recording"):

    fs = 44100
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    # save audio file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        wav.write(tmp.name, fs, audio)

        st.audio(tmp.name)


        # -----------------------------
        # LOAD AUDIO FOR ANALYSIS
        # -----------------------------
        y, sr = librosa.load(tmp.name)


        # -----------------------------
        # 3. PITCH ANALYSIS
        # -----------------------------
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

        pitch_values = []

        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)

        avg_pitch = np.mean(pitch_values) if len(pitch_values) > 0 else 0

        st.subheader("📊 Speech Analysis Results")

        st.write("🎯 Average Pitch:", round(avg_pitch, 2))


        # -----------------------------
        # 4. FLUENCY ANALYSIS (PAUSES + ENERGY)
        # -----------------------------
        intervals = librosa.effects.split(y, top_db=20)

        num_speech_segments = len(intervals)

        rms = librosa.feature.rms(y=y)[0]
        fluency_score = np.mean(rms)

        st.write("🧩 Speech Segments (pauses indicator):", num_speech_segments)
        st.write("📈 Fluency Score:", round(fluency_score, 5))


        # -----------------------------
        # 5. SIMPLE RISK LOGIC (BASIC MODEL)
        # -----------------------------
        risk = 0

        # low pitch variation (very simplified rule)
        if avg_pitch < 120:
            risk += 1

        # too many pauses
        if num_speech_segments > 10:
            risk += 1

        # low fluency energy
        if fluency_score < 0.02:
            risk += 1


        st.subheader("🧠 Cognitive Indicator Score")

        if risk == 0:
            st.success("Low risk indicators")
        elif risk == 1:
            st.warning("Mild risk indicators")
        else:
            st.error("Higher risk indicators")
