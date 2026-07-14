import streamlit as st
import speech_recognition as sr
import tempfile
import os
import datetime
import difflib

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
    "bwd_hint": ("ให้พูดว่า: 2 – 4 – 7", "Say: 2 – 4 – 7"),

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
    "calc_q": ("**เริ่มจาก 100 แล้วลบ 7 ไปเรื่อยๆ พูดผลลัพธ์ 5 ค่าติดต่อกัน (เช่น 93, 86, 79, 72, 65)**",
               "**Starting at 100, keep subtracting 7 and say 5 results in a row (e.g. 93, 86, 79, 72, 65)**"),
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
    "not_attempted": ("⚪ ยังไม่ได้ตอบ", "⚪ Not attempted"),
    "coverage_warning": (
        "⚠️ คุณตอบเพียง {done}/{total} ส่วนของแบบทดสอบ ผลลัพธ์นี้อาจไม่สะท้อนภาพรวมที่แม่นยำ กรุณาทำแบบทดสอบให้ครบทุกส่วนเพื่อผลลัพธ์ที่น่าเชื่อถือมากขึ้น",
        "⚠️ You only completed {done}/{total} parts of this test. This result may not be reliable — please complete more sections for an accurate screening.",
    ),
    "score_on_attempted": ("**คะแนน (จากส่วนที่ตอบแล้ว):", "**Score (of sections attempted):"),
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


def digits_in_order(text: str, sequence: list, max_edit_distance: int = 1) -> bool:
    """Check whether the target digit sequence appears (possibly among other
    noise digits, e.g. mis-heard extra digits) in the right order, tolerating
    up to `max_edit_distance` insertions/deletions/substitutions to account
    for imperfect speech-to-text transcription."""
    spoken_digits = [ch for ch in text if ch.isdigit()]

    # Exact match
    if spoken_digits == sequence:
        return True

    # Sequence appears as a contiguous run somewhere in the spoken digits
    n = len(sequence)
    for i in range(len(spoken_digits) - n + 1):
        if spoken_digits[i:i + n] == sequence:
            return True

    # Fuzzy match: allow a small edit distance against the closest-length window
    matcher = difflib.SequenceMatcher(None, spoken_digits, sequence)
    # ratio-based leniency: if the two lists are "close enough", accept it
    if spoken_digits:
        opcodes = matcher.get_opcodes()
        edits = sum(1 for tag, *_ in opcodes if tag != "equal")
        if edits <= max_edit_distance:
            return True

    return False


def contains_any(text: str, keywords: list) -> bool:
    text_l = text.lower()
    return any(k.lower() in text_l for k in keywords)


def attempted(widget_key: str) -> bool:
    """True if the user actually recorded + got a non-empty transcription for
    this widget (as opposed to simply never having answered it)."""
    return bool(st.session_state.get(f"{widget_key}_text"))


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


st.title(T("title"))

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
st.info(T("bwd_hint"))
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
    st.markdown(q_th if LANG == "th" else q_en)
    ans = voice_input(T("record_btn"), f"{key}_widget")
    if ans:
        st.success(f"{T('you_said')} **{ans}**")
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


def _year_match(ans: str) -> bool:
    ans_l = ans.lower()
    if str(ctx["year"]) in ans_l:
        return True
    # tolerate people saying just the last two digits of the year
    last_two = str(ctx["year"])[-2:]
    return bool(last_two) and last_two in ans_l


ori_time_qs = [
    ("ori_day_q", "ori_day_name", lambda a: ctx["weekday"].replace("วัน", "").lower() in a.lower(), ctx["weekday"]),
    ("ori_date_q", "ori_date", lambda a: str(ctx["day"]) in a, ctx["day"]),
    ("ori_month_q", "ori_month", lambda a: ctx["month"].lower() in a.lower(), ctx["month"]),
    ("ori_year_q", "ori_year", _year_match, ctx["year"]),
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
    st.markdown(T(label_key))
    ans = voice_input(T("record_btn_answer"), key)
    if ans:
        st.success(f"{T('you_said')} **{ans}**")
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
    st.markdown(T(label_key))
    ans = voice_input(T("record_btn_answer"), key)
    if ans:
        st.success(f"{T('you_said')} **{ans}**")
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
    st.markdown(T(label_key))
    ans = voice_input(T("record_btn_answer"), key)
    if ans:
        st.success(f"{T('you_said')} **{ans}**")
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
# SCORING
# ─────────────────────────────────────────────
if st.button(T("calc_score_btn")):
    score = 0.0
    possible = 0.0
    details = []
    attempted_items = 0
    total_items = 0

    def add_partial(label: str, earned: float, max_points: float, widget_key: str):
        global score, possible, attempted_items, total_items
        total_items += 1
        if not attempted(widget_key):
            details.append(f"{T('not_attempted')} — {label}")
            return
        attempted_items += 1
        possible += max_points
        score += earned
        icon = "✅" if earned >= max_points else ("➖" if earned > 0 else "❌")
        details.append(f"{icon} {label}: {earned}/{max_points}")

    def add_result(label: str, ok: bool, widget_key: str, points: float = 1):
        add_partial(label, points if ok else 0, points, widget_key)

    # 1B. Immediate recall
    imm = st.session_state.get("immediate_recall_count", 0)
    add_partial(T("sec1b_header"), imm, len(WORDS), "immediate_recall")

    # 2. Attention
    add_result(T("fwd_label"), st.session_state.get("fwd_ok", False), "fwd")
    add_result(T("bwd_label"), st.session_state.get("bwd_ok", False), "bwd")

    # 3. Language repetition
    for i in range(1, 5):
        s = st.session_state.get(f"lang{i}_score", 0.0)
        label = T("sentence_label").format(n=i)
        add_result(label, s >= 0.6, f"lang{i}")

    # 4. Abstraction
    for i in range(1, 5):
        label = f"{T('sec4_header')} #{i}"
        add_result(label, st.session_state.get(f"abs{i}_correct", False), f"abs{i}_widget")

    # 5. Orientation to time
    for label_key, key, _check_fn, _truth in ori_time_qs:
        add_result(T(label_key), st.session_state.get(f"{key}_ok", False), key)

    # 6. Orientation to place (self-report; credited for answering, flagged for human review)
    for label_key, key in place_qs:
        label = f"{T(label_key)}"
        if attempted(key):
            attempted_items += 1
            total_items += 1
            possible += 1
            score += 1
            details.append(f"✅ {label} (recorded — please verify)")
        else:
            total_items += 1
            details.append(f"{T('not_attempted')} — {label}")

    # 7. Verbal fluency
    add_result(T("fluency_animals_q"), st.session_state.get("fluency_animals_count", 0) >= 8, "fluency_animals")
    add_result(T("fluency_fruits_q"), st.session_state.get("fluency_fruits_count", 0) >= 8, "fluency_fruits")

    # 8. Calculation
    calc_correct = st.session_state.get("calc_correct_count", 0)
    add_partial(T("sec8_header"), calc_correct, 5, "calc_serial7")

    # 9. Naming
    for label_key, key, _kw in naming_qs:
        add_result(T(label_key), st.session_state.get(f"{key}_ok", False), key)

    # 10. Functional description
    for label_key, key, _kw in func_qs:
        add_result(T(label_key), st.session_state.get(f"{key}_ok", False), key)

    # 11. Proverbs
    for label_key, key, _kw in proverb_qs:
        add_result(T(label_key), st.session_state.get(f"{key}_ok", False), key)

    # 12. Delayed recall
    found = st.session_state.get("recall_score_count", 0)
    add_partial(T("sec12_header"), found, len(WORDS), "recall_widget")

    st.subheader(T("results_header"))
    for d in details:
        st.write(d)

    if total_items:
        coverage = attempted_items / total_items
        if coverage < 1.0:
            st.info(T("coverage_warning").format(done=attempted_items, total=total_items))

    if possible > 0:
        pct_final = score / possible
        st.write(f"{T('score_on_attempted')} {score:.1f} / {possible:.0f}** ({pct_final:.0%})")

        if pct_final >= 0.7:
            st.success(T("good"))
        elif pct_final >= 0.4:
            st.warning(T("mild"))
        else:
            st.error(T("review"))
    else:
        st.warning(T("coverage_warning").format(done=0, total=total_items))

    st.caption(T("disclaimer"))
