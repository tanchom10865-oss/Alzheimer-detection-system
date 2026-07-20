import streamlit as st
import speech_recognition as sr
import tempfile
import os
import datetime
import numpy as np
import pandas as pd

# Optional heavy deps for the Explainable AI (SHAP) section.
# Install with: pip install librosa shap scikit-learn soundfile
try:
    import librosa
    import shap
    from sklearn.ensemble import RandomForestClassifier
    XAI_AVAILABLE = True
except ImportError:
    XAI_AVAILABLE = False

# Optional: Claude API for plain-language interpretation of the numeric results.
# Install with: pip install anthropic
try:
    import anthropic
    ANTHROPIC_SDK_AVAILABLE = True
except ImportError:
    ANTHROPIC_SDK_AVAILABLE = False

# ─────────────────────────────────────────────
# LANGUAGE SELECTION (must happen first)
# ─────────────────────────────────────────────
st.set_page_config(page_title="Cognitive Screening Test / แบบทดสอบคัดกรองสภาวะทางปัญญา")

if "lang" not in st.session_state:
    st.session_state["lang"] = None

if st.session_state["lang"] is None:
    st.title("🧠 Cognitive Screening Test / แบบทดสอบคัดกรองสภาวะทางปัญญา")
    st.write("Please choose your language / กรุณาเลือกภาษา")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🇹🇭 ภาษาไทย", use_container_width=True):
            st.session_state["lang"] = "th"
            st.rerun()
    with col2:
        if st.button("🇬🇧 English", use_container_width=True):
            st.session_state["lang"] = "en"
            st.rerun()
    st.stop()

LANG = st.session_state["lang"]  # "th" or "en"

with st.sidebar:
    st.write("🌐 " + ("ภาษา" if LANG == "th" else "Language") + f": **{'ไทย' if LANG == 'th' else 'English'}**")
    if st.button("🔁 " + ("เปลี่ยนภาษา" if LANG == "th" else "Change language")):
        st.session_state["lang"] = None
        st.rerun()


def T(key: str) -> str:
    """Fetch a localized string."""
    val = STR[key]
    return val[0] if LANG == "th" else val[1]


# ─────────────────────────────────────────────
# STRING TABLE: key -> (thai, english)
# ─────────────────────────────────────────────
STR = {
    "title": ("🧠 แบบทดสอบคัดกรองสภาวะทางปัญญา (Cognitive Screening Test)",
              "🧠 Cognitive Screening Test"),

    "record_btn": ("🎙 บันทึกเสียง", "🎙 Record your answer"),
    "record_btn_answer": ("🎙 บันทึกคำตอบ", "🎙 Record your answer"),
    "transcribing": ("กำลังแปลงเสียงเป็นข้อความ…", "Transcribing…"),
    "transcribe_error": ("ไม่สามารถแปลงเสียงได้ — กรุณาลองอีกครั้ง", "Could not recognise — please try again."),
    "service_error": ("เกิดข้อผิดพลาดของบริการแปลงเสียง: ", "Speech service error: "),
    "you_said": ("คุณพูดว่า:", "You said:"),
    "correct": ("✅ ถูกต้อง!", "✅ Correct!"),
    "incorrect": ("❌ ยังไม่ถูกต้อง", "❌ Not quite."),

    # Section 1
    "sec1_header": ("1. แบบทดสอบความจำคำศัพท์", "1. Word Memory Test"),
    "sec1_instruction": ("กรุณาจดจำคำเหล่านี้:", "Memorize these words:"),

    # Section 1B
    "sec1b_header": ("1B. ทวนคำศัพท์ทันที (Immediate Recall)", "1B. Immediate Recall"),
    "sec1b_instruction": ("พูดทวนคำศัพท์ทั้ง 5 คำที่เพิ่งเห็นด้านบนทันที:",
                           "Repeat back all 5 words you just saw above, right now:"),

    # Section 2
    "sec2_header": ("2. แบบทดสอบสมาธิและความจำใช้งาน", "2. Attention Test"),
    "fwd_label": ("**ความจำตัวเลขแบบเรียงไปข้างหน้า** — พูดตัวเลขต่อไปนี้ตามลำดับเดิม:",
                  "**Forward Digit Span** — say these numbers in the same order:"),
    "bwd_label": ("**ความจำตัวเลขแบบย้อนกลับ** — พูดเลข 7-4-2 โดยเรียงย้อนกลับ:",
                  "**Backward Digit Span** — say 7-4-2 in reverse:"),

    # Section 3
    "sec3_header": ("3. การทวนประโยค (Language Repetition)", "3. Language Repetition"),
    "sentence_label": ("**ประโยคที่ {n}:**", "**Sentence {n}:**"),
    "match_label": ("ความตรงกัน", "Match"),

    # Section 4
    "sec4_header": ("4. การคิดเชิงนามธรรม (Abstraction)", "4. Abstraction"),
    "abs_correct_prefix": ("🎯 ถูกต้อง!", "🎯 Correct!"),
    "abs_incorrect_prefix": ("⚠️ ยังไม่ตรงนัก", "⚠️ Not quite —"),

    # Section 5 (orientation to time)
    "sec5_header": ("5. การรับรู้เรื่องเวลา (Orientation to Time)", "5. Orientation to Time"),
    "ori_day_q": ("**วันนี้วันอะไร?**", "**What day of the week is it today?**"),
    "ori_date_q": ("**วันนี้วันที่เท่าไหร่?**", "**What is today's date (day number)?**"),
    "ori_month_q": ("**เดือนนี้คือเดือนอะไร?**", "**What month is it?**"),
    "ori_year_q": ("**ปีนี้คือปี พ.ศ. อะไร?**", "**What year is it?**"),
    "ori_season_q": ("**ตอนนี้เป็นฤดูอะไร?**", "**What season is it now?**"),
    "actually_is": ("❌ ที่จริงคือ", "❌ It's actually"),

    # Section 6 (orientation to place)
    "sec6_header": ("6. การรับรู้เรื่องสถานที่ (Orientation to Place)", "6. Orientation to Place"),
    "sec6_caption": ("คำตอบข้อนี้จะถูกบันทึกไว้ ผู้ประเมินสามารถตรวจสอบความถูกต้องด้วยตนเอง",
                      "These answers are recorded for a human reviewer to verify, since the app can't confirm your real location."),
    "ori_country_q": ("**ตอนนี้คุณอยู่ประเทศอะไร?**", "**What country are you in right now?**"),
    "ori_province_q": ("**ตอนนี้คุณอยู่จังหวัดอะไร?**", "**What state/province are you in?**"),
    "ori_place_q": ("**ตอนนี้คุณอยู่ที่ไหน (เช่น บ้าน, โรงพยาบาล, คลินิก)?**",
                     "**Where are you right now (e.g. home, hospital, clinic)?**"),
    "ori_floor_q": ("**ตอนนี้คุณอยู่ชั้นไหนของอาคาร?**", "**What floor of the building are you on?**"),
    "ori_city_q": ("**เมืองหรืออำเภอที่คุณอยู่ตอนนี้ชื่ออะไร?**", "**What city or town are you in?**"),

    # Section 7 (fluency)
    "sec7_header": ("7. ความคล่องแคล่วทางภาษา (Verbal Fluency)", "7. Verbal Fluency"),
    "fluency_animals_q": ("**บอกชื่อสัตว์ให้ได้มากที่สุดภายใน 1 นาที**",
                           "**Name as many animals as you can in 1 minute**"),
    "fluency_fruits_q": ("**บอกชื่อผลไม้ให้ได้มากที่สุดภายใน 1 นาที**",
                          "**Name as many fruits as you can in 1 minute**"),
    "fluency_count": ("📊 จำนวนคำที่พูดได้โดยประมาณ:", "📊 Approximate number of words:"),

    # Section 8 (calculation)
    "sec8_header": ("8. การคำนวณ (Calculation)", "8. Calculation"),
    "calc_q": ("**เริ่มจาก 100 แล้วลบ 7 ไปเรื่อยๆ พูดผลลัพธ์ 5 ค่าติดต่อกัน**",
               "**Starting at 100, keep subtracting 7 and say 5 results in a row**"),
    "calc_result": ("📊 ถูกต้อง", "📊 Correct:"),

    # Section 9 (naming)
    "sec9_header": ("9. การเรียกชื่อสิ่งของ (Naming)", "9. Naming"),
    "naming_watch_q": ("**ของใช้ที่ใช้บอกเวลา สวมข้อมือได้ เรียกว่าอะไร?**",
                        "**What do you call the object worn on the wrist that tells time?**"),
    "naming_pen_q": ("**สิ่งที่ใช้ในการเขียนหนังสือ เรียกว่าอะไร?**",
                      "**What do you call the object used for writing?**"),
    "naming_dog_q": ("**สัตว์เลี้ยงที่เห่าและเฝ้าบ้าน เรียกว่าอะไร?**",
                      "**What do you call the pet that barks and guards the house?**"),

    # Section 10 (functional description)
    "sec10_header": ("10. การอธิบายหน้าที่ของสิ่งของ (Functional Description)",
                      "10. Functional Description"),
    "func_hammer_q": ("**ค้อนใช้ทำอะไร?**", "**What is a hammer used for?**"),
    "func_scissors_q": ("**กรรไกรใช้ทำอะไร?**", "**What are scissors used for?**"),

    # Section 11 (proverbs)
    "sec11_header": ("11. การอธิบายความหมายสุภาษิต (Proverb Interpretation)",
                      "11. Proverb Interpretation"),
    "proverb_water_q": ("**\"น้ำขึ้นให้รีบตัก\" หมายความว่าอย่างไร?**",
                         "**What does \"strike while the iron is hot\" mean?**"),
    "proverb_slow_q": ("**\"ช้าๆ ได้พร้าเล่มงาม\" หมายความว่าอย่างไร?**",
                        "**What does \"slow and steady wins the race\" mean?**"),
    "proverb_try_again": ("⚠️ ลองอธิบายอีกครั้งด้วยคำพูดของคุณเอง", "⚠️ Try explaining it again in your own words."),

    # Section 12 (delayed recall)
    "sec12_header": ("12. แบบทดสอบความจำครั้งสุดท้าย (Delayed Recall)", "12. Delayed Recall"),
    "sec12_instruction": ("พูดคำศัพท์ให้ได้มากที่สุดเท่าที่จำได้จากตอนต้น:",
                           "Say as many words as you can remember from the beginning:"),
    "recall_progress": ("ความแม่นยำในการจำคำศัพท์:", "Words Remembered Accuracy:"),
    "recall_score": ("📊 **คะแนน:** จำได้", "📊 **Score:**"),
    "of_words": ("จาก", "out of"),
    "words_label": ("คำ", "words recognized."),

    # Scoring
    "calc_score_btn": ("คำนวณคะแนน (Calculate Score)", "Calculate Score"),
    "results_header": ("ผลการทดสอบ", "Results"),
    "total_score": ("**คะแนนรวม:", "**Total Score:"),
    "good": ("🟢 ผลการทดสอบอยู่ในเกณฑ์ดี (ต้นแบบ/Prototype)", "🟢 Good performance (prototype)"),
    "mild": ("🟡 มีความกังวลเล็กน้อย (ต้นแบบ/Prototype)", "🟡 Mild concern (prototype)"),
    "review": ("🔴 ควรได้รับการตรวจประเมินเพิ่มเติม (ต้นแบบ/Prototype)", "🔴 Needs review (prototype)"),
    "disclaimer": ("⚠️ นี่ไม่ใช่เครื่องมือวินิจฉัยทางการแพทย์ กรุณาปรึกษาแพทย์ผู้เชี่ยวชาญเพื่อการวินิจฉัยที่ถูกต้อง",
                    "⚠️ Not a medical diagnosis tool. Please consult a qualified professional for an accurate diagnosis."),
}

# ─────────────────────────────────────────────
# CONTENT (word lists, sentences, keywords) PER LANGUAGE
# ─────────────────────────────────────────────
CONTENT = {
    "th": {
        "words": ["ใบหน้า", "กำมะหยี่", "โบสถ์", "เดซี่", "แดง"],
        "sentences": [
            "ฉันรู้เพียงว่าจอห์นคือคนที่จะช่วยเหลือวันนี้",
            "แมวมักจะซ่อนตัวใต้โซฟาเวลาที่มีสุนัขอยู่ในห้อง",
            "เด็กชายวิ่งไปที่สนามเด็กเล่นหลังเลิกเรียนทุกวัน",
            "ฝนตกหนักมากจนถนนหน้าบ้านกลายเป็นแม่น้ำเล็กๆ",
        ],
        "vehicle_kw": ["ยานพาหนะ", "พาหนะ", "เดินทาง", "ล้อ", "ขนส่ง", "ขับ", "นั่ง"],
        "measurement_kw": ["วัด", "เครื่องมือ", "อุปกรณ์", "ตัวเลข", "บอกเวลา", "มาตร"],
        "fruit_kw": ["ผลไม้", "กิน", "รับประทาน", "หวาน", "ผล"],
        "furniture_kw": ["เฟอร์นิเจอร์", "ของใช้", "ไม้", "บ้าน", "เครื่องเรือน"],
        "watch_kw": ["นาฬิกา"],
        "pen_kw": ["ปากกา", "ดินสอ"],
        "dog_kw": ["สุนัข", "หมา"],
        "hammer_kw": ["ตอก", "ตะปู", "ทุบ", "ต่อย"],
        "scissors_kw": ["ตัด", "หนีบ"],
        "proverb_water_kw": ["โอกาส", "รีบ", "ฉวย", "ทัน"],
        "proverb_slow_kw": ["ใจเย็น", "ค่อยเป็นค่อยไป", "ระมัดระวัง", "รอบคอบ"],
        "speech_lang_code": "th-TH",
    },
    "en": {
        "words": ["face", "velvet", "church", "daisy", "red"],
        "sentences": [
            "I only know that John is the one to help today",
            "The cat always hid under the couch when dogs were in the room",
            "The boy runs to the playground after school every day",
            "It rained so hard that the street in front of the house turned into a small river",
        ],
        "vehicle_kw": ["vehicle", "transport", "transportation", "wheels", "ride", "travel", "move"],
        "measurement_kw": ["measure", "measurement", "tool", "instrument", "scale", "tell time", "numbers"],
        "fruit_kw": ["fruit", "eat", "sweet"],
        "furniture_kw": ["furniture", "wood", "sit", "house", "home"],
        "watch_kw": ["watch"],
        "pen_kw": ["pen", "pencil"],
        "dog_kw": ["dog"],
        "hammer_kw": ["hit", "nail", "pound", "strike", "hammer"],
        "scissors_kw": ["cut", "trim", "snip"],
        "proverb_water_kw": ["opportunity", "chance", "act quickly", "seize", "now"],
        "proverb_slow_kw": ["patience", "careful", "steady", "slow", "take your time"],
        "speech_lang_code": "en-US",
    },
}
C = CONTENT[LANG]

WORDS = C["words"]
SENTENCE_1, SENTENCE_2, SENTENCE_3, SENTENCE_4 = C["sentences"]
FORWARD_SEQUENCE = ["2", "1", "8", "5", "4"]
BACKWARD_SEQUENCE = ["2", "4", "7"]

THAI_WEEKDAYS = ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"]
THAI_MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
               "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]


def current_context():
    now = datetime.datetime.now()
    if LANG == "th":
        weekday = THAI_WEEKDAYS[now.weekday()]
        month = THAI_MONTHS[now.month - 1]
        year = now.year + 543
        if now.month in (3, 4, 5, 6):
            season = "ฤดูร้อน"
        elif now.month in (7, 8, 9, 10):
            season = "ฤดูฝน"
        else:
            season = "ฤดูหนาว"
    else:
        weekday = now.strftime("%A")
        month = now.strftime("%B")
        year = now.year
        if now.month in (12, 1, 2):
            season = "winter"
        elif now.month in (3, 4, 5):
            season = "spring"
        elif now.month in (6, 7, 8):
            season = "summer"
        else:
            season = "fall"
    return {"day": now.day, "weekday": weekday, "month": month, "year": year, "season": season}


def transcribe_audio(audio_bytes: bytes) -> str | None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        audio_path = f.name
    try:
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = r.record(source)
        return r.recognize_google(audio_data, language=C["speech_lang_code"])
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        st.error(T("service_error") + str(e))
        return None
    finally:
        os.unlink(audio_path)


def similarity_score(spoken: str, reference: str) -> float:
    matches = 0
    spoken_clean = spoken.lower().replace(" ", "")
    for w in reference.split():
        if w.lower() in spoken_clean:
            matches += 1
    return matches / max(len(reference.split()), 1)


def digits_in_order(text: str, sequence: list) -> bool:
    spoken_digits = [ch for ch in text if ch.isdigit()]
    return spoken_digits == sequence


def contains_any(text: str, keywords: list) -> bool:
    """
    Fallback keyword check (used only when AI grading is unavailable).
    Matches whole words/phrases with boundaries, not raw substrings — so "cut" won't
    incorrectly match inside "cutting". Thai has no spaces between words, so plain
    substring matching is kept for Thai keywords.
    """
    import re
    text_l = text.lower()
    for k in keywords:
        k_l = k.lower()
        if any(ord(ch) > 0x0E00 and ord(ch) < 0x0E7F for ch in k_l):
            # Thai keyword: no word boundaries available, fall back to substring
            if k_l in text_l:
                return True
        else:
            if re.search(r"\b" + re.escape(k_l) + r"\b", text_l):
                return True
    return False


def voice_input(label: str, key: str):
    audio = st.audio_input(label, key=key)
    if audio is not None:
        audio_bytes = audio.read()
        if audio_bytes != st.session_state.get(f"{key}_bytes"):
            st.session_state[f"{key}_bytes"] = audio_bytes
            with st.spinner(T("transcribing")):
                result = transcribe_audio(audio_bytes)
            st.session_state[f"{key}_text"] = result if result else ""
            if result is None:
                st.error(T("transcribe_error"))
    return st.session_state.get(f"{key}_text", "")


# ─────────────────────────────────────────────
# EXPLAINABLE AI (SHAP) HELPERS
# ─────────────────────────────────────────────
FEATURE_NAMES = [
    "pitch_mean", "pitch_std", "jitter", "shimmer",
    "energy_mean", "zero_crossing_rate", "mfcc_mean",
    "speaking_rate", "pause_duration", "pause_frequency", "vocabulary_diversity",
]

FEATURE_LABELS = {
    "pitch_mean": ("ระดับเสียงเฉลี่ย (Pitch เฉลี่ย)", "Mean pitch (F0)"),
    "pitch_std": ("ความแปรปรวนของระดับเสียง", "Pitch variability"),
    "jitter": ("ความสั่นของความถี่เสียง (Jitter)", "Jitter (frequency perturbation)"),
    "shimmer": ("ความสั่นของความดังเสียง (Shimmer)", "Shimmer (amplitude perturbation)"),
    "energy_mean": ("พลังงานเสียงเฉลี่ย", "Mean energy (RMS)"),
    "zero_crossing_rate": ("อัตราการตัดผ่านศูนย์ (ความคมของเสียง)", "Zero-crossing rate"),
    "mfcc_mean": ("ค่าเฉลี่ย MFCC (ลักษณะเสียงพูด)", "Mean MFCC (timbre)"),
    "speaking_rate": ("อัตราความเร็วในการพูด (คำ/นาที)", "Speaking rate (words/min)"),
    "pause_duration": ("ความยาวเฉลี่ยของการหยุดพูด (วินาที)", "Mean pause duration (sec)"),
    "pause_frequency": ("ความถี่ของการหยุดพูด (ครั้ง/นาที)", "Pause frequency (pauses/min)"),
    "vocabulary_diversity": ("ความหลากหลายของคำศัพท์ (Type-Token Ratio)", "Vocabulary diversity (type-token ratio)"),
}


def extract_acoustic_features(audio_bytes: bytes, transcript: str = "") -> dict | None:
    """Extract acoustic + pause + vocabulary features from a recorded voice clip using librosa."""
    if not XAI_AVAILABLE:
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        path = f.name
    try:
        y, srate = librosa.load(path, sr=16000)
        duration = max(librosa.get_duration(y=y, sr=srate), 0.01)

        f0, _, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7")
        )
        f0_voiced = f0[~np.isnan(f0)] if f0 is not None else np.array([])
        pitch_mean = float(np.mean(f0_voiced)) if len(f0_voiced) else 0.0
        pitch_std = float(np.std(f0_voiced)) if len(f0_voiced) else 0.0
        if len(f0_voiced) > 1:
            periods = 1.0 / f0_voiced
            jitter = float(np.mean(np.abs(np.diff(periods))) / np.mean(periods))
        else:
            jitter = 0.0

        rms = librosa.feature.rms(y=y)[0]
        energy_mean = float(np.mean(rms))
        shimmer = float(np.std(rms) / np.mean(rms)) if np.mean(rms) > 0 else 0.0
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)[0]))
        mfcc = librosa.feature.mfcc(y=y, sr=srate, n_mfcc=13)
        mfcc_mean = float(np.mean(mfcc))

        # ── Pause detection ──
        # top_db: how many dB below peak counts as silence. Lower = more sensitive to soft pauses.
        intervals = librosa.effects.split(y, top_db=30)  # array of [start_sample, end_sample] non-silent chunks
        if len(intervals) > 0:
            speaking_samples = sum(end - start for start, end in intervals)
            speaking_duration = speaking_samples / srate
            # gaps between consecutive non-silent chunks = pauses (ignore leading/trailing silence)
            pause_lengths = []
            for i in range(len(intervals) - 1):
                gap_samples = intervals[i + 1][0] - intervals[i][1]
                gap_sec = gap_samples / srate
                if gap_sec > 0.15:  # ignore tiny sub-150ms gaps (not perceptible pauses)
                    pause_lengths.append(gap_sec)
            pause_duration = float(np.mean(pause_lengths)) if pause_lengths else 0.0
            pause_frequency = len(pause_lengths) / (duration / 60.0)  # pauses per minute
        else:
            speaking_duration = 0.0
            pause_duration = 0.0
            pause_frequency = 0.0

        word_count = len(transcript.split()) if transcript else 0
        # words per minute of actual speaking time (excludes long silences), falls back to total duration
        effective_time = speaking_duration if speaking_duration > 0.1 else duration
        speaking_rate = (word_count / effective_time) * 60.0

        # ── Vocabulary diversity: type-token ratio ──
        words = transcript.lower().split() if transcript else []
        vocabulary_diversity = (len(set(words)) / len(words)) if words else 0.0

        return {
            "pitch_mean": pitch_mean, "pitch_std": pitch_std, "jitter": jitter,
            "shimmer": shimmer, "energy_mean": energy_mean, "zero_crossing_rate": zcr,
            "mfcc_mean": mfcc_mean, "speaking_rate": speaking_rate,
            "pause_duration": pause_duration, "pause_frequency": pause_frequency,
            "vocabulary_diversity": vocabulary_diversity,
        }
    except Exception as e:
        st.error(f"Feature extraction failed: {e}")
        return None
    finally:
        os.unlink(path)


@st.cache_resource
def train_demo_model():
    """
    Trains a small RandomForest on SYNTHETIC data as a demonstration model.
    This is NOT trained on real clinical data and NOT validated — it exists purely
    to illustrate how SHAP-based explainability could work once a real labeled
    Thai speech dataset is available (see the data-collection guideline below).
    """
    rng = np.random.default_rng(42)
    n = 300
    # "typical" class: stable pitch, fewer/shorter pauses, faster speech, richer vocabulary
    typical = {
        "pitch_mean": rng.normal(180, 20, n // 2),
        "pitch_std": rng.normal(15, 4, n // 2),
        "jitter": rng.normal(0.01, 0.004, n // 2),
        "shimmer": rng.normal(0.05, 0.015, n // 2),
        "energy_mean": rng.normal(0.05, 0.01, n // 2),
        "zero_crossing_rate": rng.normal(0.08, 0.02, n // 2),
        "mfcc_mean": rng.normal(0, 5, n // 2),
        "speaking_rate": rng.normal(140, 20, n // 2),
        "pause_duration": rng.normal(0.4, 0.15, n // 2),
        "pause_frequency": rng.normal(6, 2, n // 2),
        "vocabulary_diversity": rng.normal(0.75, 0.08, n // 2),
    }
    # "possible concern" class: more jitter/shimmer, longer & more frequent pauses,
    # slower speech, less varied vocabulary (word-finding difficulty)
    concern = {
        "pitch_mean": rng.normal(170, 25, n // 2),
        "pitch_std": rng.normal(25, 6, n // 2),
        "jitter": rng.normal(0.025, 0.008, n // 2),
        "shimmer": rng.normal(0.09, 0.02, n // 2),
        "energy_mean": rng.normal(0.035, 0.012, n // 2),
        "zero_crossing_rate": rng.normal(0.07, 0.02, n // 2),
        "mfcc_mean": rng.normal(-2, 5, n // 2),
        "speaking_rate": rng.normal(90, 20, n // 2),
        "pause_duration": rng.normal(0.9, 0.25, n // 2),
        "pause_frequency": rng.normal(12, 3, n // 2),
        "vocabulary_diversity": rng.normal(0.55, 0.1, n // 2),
    }
    X = pd.DataFrame({k: np.concatenate([typical[k], concern[k]]) for k in FEATURE_NAMES})
    y = np.array([0] * (n // 2) + [1] * (n // 2))
    model = RandomForestClassifier(n_estimators=150, max_depth=5, random_state=42)
    model.fit(X, y)
    return model, X


def get_anthropic_api_key():
    """Look for the API key in Streamlit secrets first, then environment variables."""
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def ai_grade_answer(question_text: str, spoken_answer: str) -> tuple[bool | None, str]:
    """
    Uses Claude to judge whether a spoken answer is a reasonable, valid answer to the
    question — accepting synonyms and alternative correct answers (e.g. "charcoal" for
    a writing-tool question), not just one expected keyword.
    Returns (is_correct, note). is_correct is None if Claude is unavailable/unconfigured;
    the caller should fall back to keyword matching in that case.
    """
    if not ANTHROPIC_SDK_AVAILABLE:
        return None, "sdk_missing"
    api_key = get_anthropic_api_key()
    if not api_key:
        return None, "no_key"
    if not spoken_answer.strip():
        return False, "empty"
    prompt = f"""You are grading one short spoken answer in a voice-based cognitive
screening quiz. Judge only whether the answer is a reasonable, valid answer to the
question — accept synonyms, alternative correct answers, and answers in Thai or English,
not just one single expected word. Be generous with genuinely valid alternatives, but
reject answers that are simply wrong or unrelated.

Question: "{question_text}"
Spoken answer: "{spoken_answer}"

Reply with exactly one word first — YES or NO — then a very short reason (under 12 words)."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        is_correct = text.upper().startswith("YES")
        return is_correct, text
    except Exception as e:
        return None, str(e)


def get_claude_interpretation(feats: dict, transcript: str, proba: float) -> tuple[str | None, str | None]:
    """
    Sends the already-computed librosa metrics (not raw audio) + transcript to Claude
    and asks for a plain-language interpretation. Returns (text, error).
    """
    if not ANTHROPIC_SDK_AVAILABLE:
        return None, "sdk_missing"
    api_key = get_anthropic_api_key()
    if not api_key:
        return None, "no_key"

    lang_instruction = (
        "ตอบเป็นภาษาไทยเท่านั้น ใช้ภาษาที่เข้าใจง่ายสำหรับผู้ที่ไม่ใช่แพทย์"
        if LANG == "th" else
        "Respond in English only, in plain language for a non-clinician reader."
    )
    feature_lines = "\n".join(f"- {k}: {v:.3f}" for k, v in feats.items())
    prompt = f"""You are helping describe the results of a prototype voice-based cognitive
screening exercise. You are given already-computed numeric speech metrics (extracted with
signal processing, not by you) and a speech transcript. Write a short, plain-language,
neutral description (4-6 sentences) of what these numbers show about the speech sample —
e.g. pace, pausing, vocabulary variety, pitch stability — without stating or implying any
diagnosis, and without claiming clinical validity. End with a one-sentence reminder that this
is a non-validated prototype and not a medical assessment. {lang_instruction}

Metrics:
{feature_lines}

Model's demo classification probability (synthetic, non-clinical model) for "possible concern" group: {proba:.0%}

Transcript of what was said: "{transcript}"
"""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text, None
    except Exception as e:
        return None, str(e)


st.title(T("title"))

_ai_ready = ANTHROPIC_SDK_AVAILABLE and bool(get_anthropic_api_key())
if _ai_ready:
    st.caption(
        "🤖 " + ("การให้คะแนนด้วย AI (Claude) กำลังทำงาน" if LANG == "th" else "AI (Claude) grading is active")
    )
else:
    reason = (
        ("ไม่พบไลบรารี anthropic" if not ANTHROPIC_SDK_AVAILABLE else "ไม่พบ ANTHROPIC_API_KEY")
        if LANG == "th" else
        ("anthropic library not installed" if not ANTHROPIC_SDK_AVAILABLE else "ANTHROPIC_API_KEY not found")
    )
    st.caption(
        f"⚠️ {'ยังไม่ได้เปิดใช้ AI grading (' + reason + ') — ใช้การจับคำสำคัญแบบพื้นฐานแทน ดูวิธีตั้งค่าในข้อ 13' if LANG == 'th' else 'AI grading is OFF (' + reason + ') — using basic keyword matching instead. See setup steps in section 13'}"
    )

# ─────────────────────────────────────────────
# 1. WORD MEMORY
# ─────────────────────────────────────────────
st.subheader(T("sec1_header"))
st.write(T("sec1_instruction"))
st.info("  ·  ".join(WORDS))
st.session_state["words"] = WORDS
st.write("---")

# ─────────────────────────────────────────────
# 1B. IMMEDIATE RECALL
# ─────────────────────────────────────────────
st.subheader(T("sec1b_header"))
st.write(T("sec1b_instruction"))
immediate = voice_input(T("record_btn"), "immediate_recall")
if immediate:
    st.success(f"{T('you_said')} **{immediate}**")
    found_now = [w for w in WORDS if w.lower() in immediate.lower()]
    st.write(f"📊 {len(found_now)} / {len(WORDS)}")
    st.session_state["immediate_recall_count"] = len(found_now)
st.write("---")

# ─────────────────────────────────────────────
# 2. ATTENTION TEST
# ─────────────────────────────────────────────
st.subheader(T("sec2_header"))

st.markdown(T("fwd_label"))
st.info("2 – 1 – 8 – 5 – 4")
fwd = voice_input(T("record_btn"), "fwd")
if fwd:
    st.success(f"{T('you_said')} **{fwd}**")
    fwd_ok = digits_in_order(fwd, FORWARD_SEQUENCE)
    st.write(T("correct") if fwd_ok else T("incorrect"))
    st.session_state["fwd_ok"] = fwd_ok

st.markdown(T("bwd_label"))
bwd = voice_input(T("record_btn"), "bwd")
if bwd:
    st.success(f"{T('you_said')} **{bwd}**")
    bwd_ok = digits_in_order(bwd, BACKWARD_SEQUENCE)
    st.write(T("correct") if bwd_ok else T("incorrect"))
    st.session_state["bwd_ok"] = bwd_ok

st.write("---")

# ─────────────────────────────────────────────
# 3. LANGUAGE REPETITION
# ─────────────────────────────────────────────
st.subheader(T("sec3_header"))

for i, sentence in enumerate([SENTENCE_1, SENTENCE_2, SENTENCE_3, SENTENCE_4], start=1):
    st.markdown(f"{T('sentence_label').format(n=i)} {sentence}")
    ans = voice_input(T("record_btn"), f"lang{i}")
    if ans:
        sc = similarity_score(ans, sentence)
        st.success(f"{T('you_said')} **{ans}**")
        st.progress(sc, text=f"{T('match_label')}: {sc:.0%}")
        st.session_state[f"lang{i}_score"] = sc

st.write("---")

# ─────────────────────────────────────────────
# 4. ABSTRACTION
# ─────────────────────────────────────────────
st.subheader(T("sec4_header"))

abstraction_qs = [
    (("**รถไฟกับจักรยานเหมือนกันอย่างไร?**", "**How are a Train and a Bicycle similar?**"), "abs1", C["vehicle_kw"]),
    (("**นาฬิกากับไม้บรรทัดเหมือนกันอย่างไร?**", "**How are a Watch and a Ruler similar?**"), "abs2", C["measurement_kw"]),
    (("**ส้มกับกล้วยเหมือนกันอย่างไร?**", "**How are an Orange and a Banana similar?**"), "abs3", C["fruit_kw"]),
    (("**โต๊ะกับเก้าอี้เหมือนกันอย่างไร?**", "**How are a Table and a Chair similar?**"), "abs4", C["furniture_kw"]),
]
for (q_th, q_en), key, keywords in abstraction_qs:
    q_text = q_th if LANG == "th" else q_en
    st.markdown(q_text)
    ans = voice_input(T("record_btn"), f"{key}_widget")
    if ans:
        st.success(f"{T('you_said')} **{ans}**")
        ok, note = ai_grade_answer(q_text, ans)
        if ok is None:
            ok = contains_any(ans, keywords)
        if ok:
            st.info(T("abs_correct_prefix"))
        else:
            st.warning(T("abs_incorrect_prefix"))
        st.session_state[f"{key}_correct"] = ok

st.write("---")

# ─────────────────────────────────────────────
# 5. ORIENTATION TO TIME
# ─────────────────────────────────────────────
st.subheader(T("sec5_header"))
ctx = current_context()

ori_time_qs = [
    ("ori_day_q", "ori_day_name", lambda a: ctx["weekday"].replace("วัน", "").lower() in a.lower(), ctx["weekday"]),
    ("ori_date_q", "ori_date", lambda a: str(ctx["day"]) in a, ctx["day"]),
    ("ori_month_q", "ori_month", lambda a: ctx["month"].lower() in a.lower(), ctx["month"]),
    ("ori_year_q", "ori_year", lambda a: str(ctx["year"]) in a, ctx["year"]),
    ("ori_season_q", "ori_season", lambda a: ctx["season"].replace("ฤดู", "").lower() in a.lower(), ctx["season"]),
]
for label_key, key, check_fn, truth in ori_time_qs:
    st.markdown(T(label_key))
    ans = voice_input(T("record_btn_answer"), key)
    if ans:
        st.success(f"{T('you_said')} **{ans}**")
        ok = check_fn(ans)
        st.write(T("correct") if ok else f"{T('actually_is')} {truth}")
        st.session_state[f"{key}_ok"] = ok

st.write("---")

# ─────────────────────────────────────────────
# 6. ORIENTATION TO PLACE
# ─────────────────────────────────────────────
st.subheader(T("sec6_header"))
st.caption(T("sec6_caption"))

place_qs = [
    ("ori_country_q", "ori_country"),
    ("ori_province_q", "ori_province"),
    ("ori_place_q", "ori_place"),
    ("ori_floor_q", "ori_floor"),
    ("ori_city_q", "ori_city"),
]
for label_key, key in place_qs:
    st.markdown(T(label_key))
    ans = voice_input(T("record_btn_answer"), key)
    if ans:
        st.success(f"{T('you_said')} **{ans}**")
        st.session_state[f"{key}_answered"] = True

st.write("---")

# ─────────────────────────────────────────────
# 7. VERBAL FLUENCY
# ─────────────────────────────────────────────
st.subheader(T("sec7_header"))

st.markdown(T("fluency_animals_q"))
fluency_animals = voice_input(T("record_btn"), "fluency_animals")
if fluency_animals:
    st.success(f"{T('you_said')} **{fluency_animals}**")
    words_count = len(set(fluency_animals.lower().split()))
    st.write(f"{T('fluency_count')} {words_count}")
    st.session_state["fluency_animals_count"] = words_count

st.markdown(T("fluency_fruits_q"))
fluency_fruits = voice_input(T("record_btn"), "fluency_fruits")
if fluency_fruits:
    st.success(f"{T('you_said')} **{fluency_fruits}**")
    words_count = len(set(fluency_fruits.lower().split()))
    st.write(f"{T('fluency_count')} {words_count}")
    st.session_state["fluency_fruits_count"] = words_count

st.write("---")

# ─────────────────────────────────────────────
# 8. CALCULATION
# ─────────────────────────────────────────────
st.subheader(T("sec8_header"))
st.markdown(T("calc_q"))
calc = voice_input(T("record_btn"), "calc_serial7")
if calc:
    st.success(f"{T('you_said')} **{calc}**")
    expected = ["93", "86", "79", "72", "65"]
    spoken_numbers = [tok for tok in calc.replace(",", " ").split() if tok.isdigit()]
    correct_count = sum(1 for e in expected if e in spoken_numbers)
    st.write(f"{T('calc_result')} {correct_count} / {len(expected)}")
    st.session_state["calc_correct_count"] = correct_count

st.write("---")

# ─────────────────────────────────────────────
# 9. NAMING
# ─────────────────────────────────────────────
st.subheader(T("sec9_header"))

naming_qs = [
    ("naming_watch_q", "naming_watch", C["watch_kw"]),
    ("naming_pen_q", "naming_pen", C["pen_kw"]),
    ("naming_dog_q", "naming_dog", C["dog_kw"]),
]
for label_key, key, keywords in naming_qs:
    q_text = T(label_key)
    st.markdown(q_text)
    ans = voice_input(T("record_btn_answer"), key)
    if ans:
        st.success(f"{T('you_said')} **{ans}**")
        ok, note = ai_grade_answer(q_text, ans)
        if ok is None:
            ok = contains_any(ans, keywords)
        st.write(T("correct") if ok else T("incorrect"))
        st.session_state[f"{key}_ok"] = ok

st.write("---")

# ─────────────────────────────────────────────
# 10. FUNCTIONAL DESCRIPTION
# ─────────────────────────────────────────────
st.subheader(T("sec10_header"))

func_qs = [
    ("func_hammer_q", "func_hammer", C["hammer_kw"]),
    ("func_scissors_q", "func_scissors", C["scissors_kw"]),
]
for label_key, key, keywords in func_qs:
    q_text = T(label_key)
    st.markdown(q_text)
    ans = voice_input(T("record_btn_answer"), key)
    if ans:
        st.success(f"{T('you_said')} **{ans}**")
        ok, note = ai_grade_answer(q_text, ans)
        if ok is None:
            ok = contains_any(ans, keywords)
        st.write(T("correct") if ok else T("incorrect"))
        st.session_state[f"{key}_ok"] = ok

st.write("---")

# ─────────────────────────────────────────────
# 11. PROVERB INTERPRETATION
# ─────────────────────────────────────────────
st.subheader(T("sec11_header"))

proverb_qs = [
    ("proverb_water_q", "proverb_water", C["proverb_water_kw"]),
    ("proverb_slow_q", "proverb_slow", C["proverb_slow_kw"]),
]
for label_key, key, keywords in proverb_qs:
    q_text = T(label_key)
    st.markdown(q_text)
    ans = voice_input(T("record_btn_answer"), key)
    if ans:
        st.success(f"{T('you_said')} **{ans}**")
        ok, note = ai_grade_answer(q_text, ans)
        if ok is None:
            ok = contains_any(ans, keywords)
        st.write(T("correct") if ok else T("proverb_try_again"))
        st.session_state[f"{key}_ok"] = ok

st.write("---")

# ─────────────────────────────────────────────
# 12. DELAYED RECALL
# ─────────────────────────────────────────────
st.subheader(T("sec12_header"))
st.write(T("sec12_instruction"))

recall = voice_input(T("record_btn"), "recall_widget")
if recall:
    st.success(f"{T('you_said')} **{recall}**")
    spoken_text = recall.lower()
    words_found = [word for word in WORDS if word.lower() in spoken_text]
    score_recall = len(words_found)
    total_words = len(WORDS)
    pct = score_recall / total_words
    st.progress(pct, text=f"{T('recall_progress')} {pct:.0%}")
    st.write(f"{T('recall_score')} {score_recall} {T('of_words')} {total_words} {T('words_label')}")
    st.session_state["recall_score_count"] = score_recall

st.write("---")

# ─────────────────────────────────────────────
# 13. EXPLAINABLE AI — SHAP FEATURE ANALYSIS
# ─────────────────────────────────────────────
st.subheader(
    "13. วิเคราะห์คุณลักษณะเสียงด้วย Explainable AI (SHAP)"
    if LANG == "th" else
    "13. Explainable AI: Which Voice Features Drive the Result (SHAP)"
)
st.caption(
    "⚠️ โมเดลนี้เป็นเพียงต้นแบบสาธิต ฝึกด้วยข้อมูลสังเคราะห์ (synthetic data) ไม่ใช่ข้อมูลผู้ป่วยจริง "
    "ผลลัพธ์นี้ใช้เพื่อสาธิตแนวทางการอธิบายผลเท่านั้น ไม่ใช่การวินิจฉัย"
    if LANG == "th" else
    "⚠️ This model is only a demonstration prototype trained on synthetic data, not real patient "
    "data. Results illustrate how explainability could work — this is not a diagnosis."
)

if not XAI_AVAILABLE:
    st.warning(
        "ต้องติดตั้งไลบรารีเพิ่มเติมก่อนใช้งานส่วนนี้: `pip install librosa shap scikit-learn soundfile`"
        if LANG == "th" else
        "Install extra libraries to use this section: `pip install librosa shap scikit-learn soundfile`"
    )
else:
    # Prefer the delayed-recall clip; fall back to any other recorded clip in this session.
    candidate_keys = ["recall_widget", "immediate_recall", "lang1", "lang2", "fwd", "bwd"]
    chosen_key, chosen_bytes, chosen_text = None, None, ""
    for k in candidate_keys:
        b = st.session_state.get(f"{k}_bytes")
        if b:
            chosen_key, chosen_bytes = k, b
            chosen_text = st.session_state.get(f"{k}_text", "")
            break

    if chosen_bytes is None:
        st.info(
            "บันทึกคำตอบด้วยเสียงอย่างน้อยหนึ่งข้อด้านบนก่อน จึงจะวิเคราะห์ได้"
            if LANG == "th" else
            "Record at least one voice answer above before running this analysis."
        )
    else:
        if st.button(
            "🔍 วิเคราะห์คุณลักษณะเสียง (Run SHAP Analysis)"
            if LANG == "th" else
            "🔍 Run SHAP Analysis"
        ):
            with st.spinner("กำลังสกัดคุณลักษณะเสียงและคำนวณ SHAP…" if LANG == "th" else "Extracting features and computing SHAP…"):
                feats = extract_acoustic_features(chosen_bytes, chosen_text)
                if feats is not None:
                    st.markdown(
                        "**ตัวชี้วัดหลักของรูปแบบการพูด**" if LANG == "th" else
                        "**Key Speech Pattern Metrics**"
                    )
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric(
                        "อัตราการพูด (คำ/นาที)" if LANG == "th" else "Speaking Rate (wpm)",
                        f"{feats['speaking_rate']:.0f}"
                    )
                    m2.metric(
                        "ความยาวหยุดพูดเฉลี่ย (วิ)" if LANG == "th" else "Pause Duration (s)",
                        f"{feats['pause_duration']:.2f}"
                    )
                    m3.metric(
                        "ความถี่การหยุดพูด (ครั้ง/นาที)" if LANG == "th" else "Pause Frequency (/min)",
                        f"{feats['pause_frequency']:.1f}"
                    )
                    m4.metric(
                        "ความหลากหลายคำศัพท์" if LANG == "th" else "Vocabulary Diversity",
                        f"{feats['vocabulary_diversity']:.2f}"
                    )
                    st.caption(
                        "คำนวณจากการตรวจจับช่วงเงียบ (silence detection) ในคลื่นเสียงจริง ไม่ได้ใช้ AI ภาษาช่วยวิเคราะห์"
                        if LANG == "th" else
                        "Computed directly from silence detection on the raw audio waveform — no language model involved."
                    )
                    st.write("---")

                    model, X_train = train_demo_model()
                    x_user = pd.DataFrame([feats])[FEATURE_NAMES]
                    proba = model.predict_proba(x_user)[0][1]

                    explainer = shap.TreeExplainer(model)
                    sv = explainer.shap_values(x_user)
                    # sv can be a list (per-class) or a single array depending on sklearn/shap version
                    if isinstance(sv, list):
                        shap_vals = sv[1][0]
                    else:
                        shap_vals = sv[0]

                    label_idx = 0 if LANG == "th" else 1
                    labels = [FEATURE_LABELS[f][label_idx] for f in FEATURE_NAMES]
                    shap_series = pd.Series(shap_vals, index=labels).sort_values()

                    st.write(
                        f"**ความน่าจะเป็นของกลุ่ม 'ควรตรวจเพิ่มเติม' (ต้นแบบสาธิต):** {proba:.0%}"
                        if LANG == "th" else
                        f"**Model's estimated probability of the 'possible concern' group (demo only):** {proba:.0%}"
                    )
                    st.bar_chart(shap_series)
                    st.caption(
                        "แท่งที่ยื่นไปทางขวา = คุณลักษณะนั้นดันผลไปทาง 'ควรตรวจเพิ่มเติม' / "
                        "แท่งที่ยื่นไปทางซ้าย = ดันผลไปทาง 'ปกติ' — ยิ่งแท่งยาว ยิ่งมีผลมาก"
                        if LANG == "th" else
                        "Bars pointing right push the result toward 'possible concern'; bars pointing "
                        "left push toward 'typical'. Longer bars = more influence on this prediction."
                    )
                    with st.expander("ดูค่าคุณลักษณะดิบ (Raw feature values)"):
                        st.dataframe(pd.DataFrame([feats]).T.rename(columns={0: "value"}))

                    st.write("---")
                    st.markdown(
                        "**🤖 ให้ Claude อธิบายผลเป็นภาษาที่เข้าใจง่าย**" if LANG == "th" else
                        "**🤖 Ask Claude to explain these results in plain language**"
                    )
                    st.caption(
                        "Claude จะอ่านเฉพาะตัวเลขและคำที่ถอดเสียงแล้วเท่านั้น ไม่ได้ฟังไฟล์เสียงโดยตรง "
                        "ต้องตั้งค่า API key ก่อนใช้งาน (ดูคำแนะนำด้านล่าง)"
                        if LANG == "th" else
                        "Claude only reads the computed numbers and transcript below — it does not "
                        "listen to the raw audio directly. Requires an API key (see setup notes below)."
                    )
                    if st.button(
                        "ขอคำอธิบายจาก Claude" if LANG == "th" else "Get Claude's explanation",
                        key="ask_claude_btn",
                    ):
                        with st.spinner("Claude กำลังวิเคราะห์…" if LANG == "th" else "Claude is analyzing…"):
                            text, err = get_claude_interpretation(feats, chosen_text, proba)
                        if err == "sdk_missing":
                            st.warning(
                                "ต้องติดตั้งไลบรารีก่อน: `pip install anthropic`"
                                if LANG == "th" else
                                "Install the SDK first: `pip install anthropic`"
                            )
                        elif err == "no_key":
                            st.warning(
                                "ยังไม่พบ ANTHROPIC_API_KEY กรุณาตั้งค่าใน Streamlit Secrets (ดูคำแนะนำด้านล่าง)"
                                if LANG == "th" else
                                "No ANTHROPIC_API_KEY found. Set it in Streamlit Secrets (see setup notes below)."
                            )
                        elif err:
                            st.error(f"Claude API error: {err}")
                        else:
                            st.info(text)

                    with st.expander(
                        "⚙️ วิธีตั้งค่า Claude API key" if LANG == "th" else "⚙️ How to set up the Claude API key"
                    ):
                        if LANG == "th":
                            st.markdown("""
1. สมัครและสร้าง API key ที่ [console.anthropic.com](https://console.anthropic.com) (มีค่าใช้จ่ายตามการใช้งานจริง แต่ราคาต่อครั้งต่ำมาก)
2. เพิ่ม `anthropic` ในไฟล์ `requirements.txt` ของโปรเจกต์
3. บน Streamlit Community Cloud: ไปที่การตั้งค่าแอปของคุณ → **Secrets** → เพิ่มบรรทัด:
   ```
   ANTHROPIC_API_KEY = "sk-ant-...ของคุณ..."
   ```
4. บันทึกแล้วรอแอป redeploy อัตโนมัติ
""")
                        else:
                            st.markdown("""
1. Sign up and create an API key at [console.anthropic.com](https://console.anthropic.com) (usage-based pricing, but cost per request is very small)
2. Add `anthropic` to your project's `requirements.txt`
3. On Streamlit Community Cloud: go to your app's settings → **Secrets** → add:
   ```
   ANTHROPIC_API_KEY = "sk-ant-...your key..."
   ```
4. Save — the app will redeploy automatically
""")

st.write("---")

# ─────────────────────────────────────────────
# 14. GUIDELINE: COLLECTING A THAI SPEECH DATASET FOR FUTURE RESEARCH
# ─────────────────────────────────────────────
st.subheader(
    "14. แนวทางการเก็บชุดข้อมูลเสียงพูดภาษาไทยสำหรับงานวิจัยในอนาคต"
    if LANG == "th" else
    "14. Guideline: Collecting a Thai Speech Dataset for Future Research"
)

with st.expander(
    "อ่านแนวทางฉบับเต็ม" if LANG == "th" else "Read the full guideline", expanded=False
):
    if LANG == "th":
        st.markdown("""
**1. จริยธรรมและความยินยอม**
- ขอความยินยอมที่เป็นลายลักษณ์อักษร (informed consent) จากผู้เข้าร่วมหรือผู้ดูแลตามกฎหมาย
- ผ่านการรับรองจากคณะกรรมการจริยธรรมการวิจัยในมนุษย์ (IRB/EC) ของสถาบัน
- ปฏิบัติตาม พ.ร.บ. คุ้มครองข้อมูลส่วนบุคคล (PDPA) อย่างเคร่งครัด โดยเฉพาะข้อมูลสุขภาพซึ่งจัดเป็นข้อมูลอ่อนไหว

**2. ความหลากหลายของกลุ่มตัวอย่าง**
- ครอบคลุมช่วงอายุ เพศ ระดับการศึกษา และภูมิภาค (ภาคเหนือ ภาคอีสาน ภาคใต้ ภาคกลาง) เพื่อให้ครอบคลุมสำเนียงถิ่น
- เก็บทั้งกลุ่มปกติและกลุ่มที่ได้รับการวินิจฉัยแล้ว (เช่น MCI, Alzheimer's) โดยแพทย์ผู้เชี่ยวชาญ เพื่อใช้เป็น ground truth
- ควบคุมสัดส่วนเพศ/อายุระหว่างกลุ่มให้ใกล้เคียงกัน (matched design) เพื่อลด confounding

**3. โปรโตคอลการบันทึกเสียง**
- ใช้ไมโครโฟนและอัตราสุ่มสัญญาณเสียง (sampling rate) มาตรฐานเดียวกันทุกจุดเก็บข้อมูล (แนะนำ ≥16kHz, 16-bit)
- บันทึกในสภาพแวดล้อมที่ควบคุมเสียงรบกวนพื้นหลัง หรืออย่างน้อยบันทึกระดับเสียงรบกวนไว้เป็น metadata
- ออกแบบชุดงาน (task) ให้หลากหลาย เช่น การอ่านออกเสียง การพูดต่อเนื่องแบบอิสระ (spontaneous speech) การทวนประโยค การนับเลขถอยหลัง และคำอธิบายภาพ เพื่อดึงลักษณะเสียงที่ต่างกัน

**4. การติดป้ายกำกับข้อมูล (Labeling)**
- เชื่อมโยงกับผลตรวจทางคลินิกมาตรฐาน เช่น MMSE, MoCA, CDR ที่ประเมินโดยแพทย์
- บันทึกวันที่ประเมิน และระยะเวลาห่างจากการบันทึกเสียง เพื่อความถูกต้องของ label
- พิจารณาการเก็บข้อมูลระยะยาว (longitudinal) เพื่อดูการเปลี่ยนแปลงของเสียงพูดตามระยะเวลา

**5. การจัดการและความเป็นส่วนตัวของข้อมูล**
- จัดเก็บไฟล์เสียงและข้อมูลระบุตัวตนแยกจากกัน (de-identification) พร้อมระบบเข้ารหัส
- กำหนดสิทธิ์การเข้าถึงข้อมูลเฉพาะทีมวิจัยที่เกี่ยวข้อง และมีบันทึกการเข้าถึง (access log)
- วางแผนระยะเวลาการเก็บรักษาและการทำลายข้อมูลตามนโยบายของสถาบันและกฎหมาย

**6. คุณภาพและ Metadata**
- บันทึก metadata ครบถ้วน เช่น อุปกรณ์บันทึก อายุ เพศ ระดับการศึกษา สำเนียง โรคประจำตัวที่เกี่ยวข้อง ยาที่ใช้
- ตรวจสอบคุณภาพเสียง (SNR, clipping) ก่อนนำเข้าสู่ชุดข้อมูลหลัก
- เตรียมชุดข้อมูลสำหรับ train/validation/test แยกตามผู้พูด (speaker-independent split) เพื่อป้องกัน data leakage
""")
    else:
        st.markdown("""
**1. Ethics and Consent**
- Obtain written informed consent from participants (or legal guardians where applicable)
- Secure approval from an Institutional Review Board / Ethics Committee
- Comply with Thailand's PDPA (Personal Data Protection Act), treating health data as sensitive data

**2. Sample Diversity**
- Cover a range of ages, genders, education levels, and regions (North, Northeast, South, Central) to capture dialectal variation
- Include both cognitively typical participants and clinically diagnosed participants (e.g., MCI, Alzheimer's) confirmed by specialists, to serve as ground truth
- Match age/gender distribution across groups where possible to reduce confounding

**3. Recording Protocol**
- Use a consistent microphone setup and sampling rate across all collection sites (recommend ≥16kHz, 16-bit)
- Record in an environment with controlled background noise, or log ambient noise level as metadata
- Design varied elicitation tasks: reading aloud, spontaneous speech, sentence repetition, backward counting, and picture description, to capture different acoustic characteristics

**4. Labeling**
- Link each recording to standardized clinical assessments (MMSE, MoCA, CDR) scored by a clinician
- Record the assessment date and its gap from the recording date for label accuracy
- Consider longitudinal collection to track how speech changes over time

**5. Data Management and Privacy**
- Store audio separately from identifying information (de-identification), with encryption
- Restrict access to the research team only, with an access log
- Define a retention and deletion policy in line with institutional and legal requirements

**6. Quality and Metadata**
- Record complete metadata: recording device, age, gender, education, dialect/accent, relevant conditions, medications
- Check audio quality (SNR, clipping) before inclusion in the main dataset
- Use a speaker-independent train/validation/test split to prevent data leakage
""")

st.write("---")

# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────
if st.button(T("calc_score_btn")):
    score = 0
    details = []

    imm = st.session_state.get("immediate_recall_count", 0)
    score += imm
    details.append(f"🧠 {T('sec1b_header')}: {imm}/{len(WORDS)}")

    if st.session_state.get("fwd_ok"):
        score += 1
        details.append(f"✅ {T('fwd_label')}")
    else:
        details.append(f"❌ {T('fwd_label')}")

    if st.session_state.get("bwd_ok"):
        score += 1
        details.append(f"✅ {T('bwd_label')}")
    else:
        details.append(f"❌ {T('bwd_label')}")

    for i in range(1, 5):
        s = st.session_state.get(f"lang{i}_score", 0.0)
        label = T("sentence_label").format(n=i)
        if s >= 0.6:
            score += 1
            details.append(f"✅ {label} {s:.0%}")
        else:
            details.append(f"❌ {label} {s:.0%}")

    for i in range(1, 5):
        if st.session_state.get(f"abs{i}_correct"):
            score += 1
            details.append(f"✅ {T('sec4_header')} #{i}")
        else:
            details.append(f"❌ {T('sec4_header')} #{i}")

    ori_time_keys = ["ori_day_name_ok", "ori_date_ok", "ori_month_ok", "ori_year_ok", "ori_season_ok"]
    for key in ori_time_keys:
        if st.session_state.get(key):
            score += 1
            details.append(f"✅ {T('sec5_header')} ({key})")
        else:
            details.append(f"❌ {T('sec5_header')} ({key})")

    place_keys = ["ori_country_answered", "ori_province_answered", "ori_place_answered",
                  "ori_floor_answered", "ori_city_answered"]
    for key in place_keys:
        if st.session_state.get(key):
            score += 1
            details.append(f"✅ {T('sec6_header')} ({key})")
        else:
            details.append(f"❌ {T('sec6_header')} ({key})")

    for key in ["fluency_animals_count", "fluency_fruits_count"]:
        count = st.session_state.get(key, 0)
        if count >= 8:
            score += 1
            details.append(f"✅ {T('sec7_header')} ({key}): {count}")
        else:
            details.append(f"❌ {T('sec7_header')} ({key}): {count}")

    calc_correct = st.session_state.get("calc_correct_count", 0)
    score += calc_correct
    details.append(f"🧮 {T('sec8_header')}: {calc_correct}/5")

    for key in ["naming_watch_ok", "naming_pen_ok", "naming_dog_ok"]:
        if st.session_state.get(key):
            score += 1
            details.append(f"✅ {T('sec9_header')} ({key})")
        else:
            details.append(f"❌ {T('sec9_header')} ({key})")

    for key in ["func_hammer_ok", "func_scissors_ok"]:
        if st.session_state.get(key):
            score += 1
            details.append(f"✅ {T('sec10_header')} ({key})")
        else:
            details.append(f"❌ {T('sec10_header')} ({key})")

    for key in ["proverb_water_ok", "proverb_slow_ok"]:
        if st.session_state.get(key):
            score += 1
            details.append(f"✅ {T('sec11_header')} ({key})")
        else:
            details.append(f"❌ {T('sec11_header')} ({key})")

    found = st.session_state.get("recall_score_count", 0)
    score += found
    details.append(f"🧠 {T('sec12_header')}: {found}/{len(WORDS)}")

    st.subheader(T("results_header"))
    for d in details:
        st.write(d)

    max_score = len(WORDS) + 2 + 4 + 4 + 5 + 5 + 2 + 5 + 3 + 2 + 2 + len(WORDS)
    st.write(f"{T('total_score')} {score} / {max_score}**")

    if score >= int(max_score * 0.7):
        st.success(T("good"))
    elif score >= int(max_score * 0.4):
        st.warning(T("mild"))
    else:
        st.error(T("review"))

    st.caption(T("disclaimer"))
