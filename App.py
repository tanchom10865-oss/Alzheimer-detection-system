import streamlit as st
import speech_recognition as sr
import tempfile
import os
import datetime

st.title("🧠 แบบทดสอบคัดกรองสภาวะทางปัญญา (Cognitive Screening Test)")

# ─────────────────────────────────────────────
# CONSTANTS (Thai)
# ─────────────────────────────────────────────
WORDS = ["ใบหน้า", "กำมะหยี่", "โบสถ์", "เดซี่", "แดง"]
SENTENCE_1 = "ฉันรู้เพียงว่าจอห์นคือคนที่จะช่วยเหลือวันนี้"
SENTENCE_2 = "แมวมักจะซ่อนตัวใต้โซฟาเวลาที่มีสุนัขอยู่ในห้อง"
SENTENCE_3 = "เด็กชายวิ่งไปที่สนามเด็กเล่นหลังเลิกเรียนทุกวัน"
SENTENCE_4 = "ฝนตกหนักมากจนถนนหน้าบ้านกลายเป็นแม่น้ำเล็กๆ"
FORWARD_SEQUENCE = ["2", "1", "8", "5", "4"]
BACKWARD_SEQUENCE = ["2", "4", "7"]

THAI_WEEKDAYS = ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"]
THAI_MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
               "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]


def current_thai_context():
    now = datetime.datetime.now()
    weekday_th = THAI_WEEKDAYS[now.weekday()]
    month_th = THAI_MONTHS[now.month - 1]
    buddhist_year = now.year + 543
    # Thailand seasons (approximate): summer (มี.ค.-มิ.ย.), rainy (ก.ค.-ต.ค.), winter (พ.ย.-ก.พ.)
    if now.month in (3, 4, 5, 6):
        season_th = "ฤดูร้อน"
    elif now.month in (7, 8, 9, 10):
        season_th = "ฤดูฝน"
    else:
        season_th = "ฤดูหนาว"
    return {
        "day": now.day,
        "weekday": weekday_th,
        "month": month_th,
        "year": buddhist_year,
        "season": season_th,
    }


def transcribe_audio(audio_bytes: bytes) -> str | None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(audio_bytes)
        audio_path = f.name
    try:
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = r.record(source)
        return r.recognize_google(audio_data, language="th-TH")
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        st.error(f"เกิดข้อผิดพลาดของบริการแปลงเสียง: {e}")
        return None
    finally:
        os.unlink(audio_path)


def similarity_score(spoken: str, reference: str) -> float:
    ref_words = set(reference.replace(",", "").split())
    spoken_words = set(spoken.replace(",", "").split())
    if not ref_words:
        return 0.0
    # crude overlap check on substrings, since Thai has no spaces between words typically
    matches = 0
    spoken_clean = spoken.replace(" ", "")
    for w in reference.split():
        if w in spoken_clean:
            matches += 1
    return matches / max(len(reference.split()), 1)


def digits_in_order(text: str, sequence: list) -> bool:
    spoken_digits = [ch for ch in text if ch.isdigit()]
    return spoken_digits == sequence


def contains_any(text: str, keywords: list) -> bool:
    text_l = text.lower()
    return any(k in text_l for k in keywords)


def voice_input(label: str, key: str):
    """Show audio recorder, transcribe only when new bytes arrive. Returns transcript string."""
    audio = st.audio_input(label, key=key)
    if audio is not None:
        audio_bytes = audio.read()
        if audio_bytes != st.session_state.get(f"{key}_bytes"):
            st.session_state[f"{key}_bytes"] = audio_bytes
            with st.spinner("กำลังแปลงเสียงเป็นข้อความ…"):
                result = transcribe_audio(audio_bytes)
            st.session_state[f"{key}_text"] = result if result else ""
            if result is None:
                st.error("ไม่สามารถแปลงเสียงได้ — กรุณาลองอีกครั้ง")
    return st.session_state.get(f"{key}_text", "")


# ─────────────────────────────────────────────
# 1. WORD MEMORY
# ─────────────────────────────────────────────
st.subheader("1. แบบทดสอบความจำคำศัพท์")
st.write("กรุณาจดจำคำเหล่านี้:")
st.info("  ·  ".join(WORDS))
st.session_state["words"] = WORDS
st.write("---")

# ─────────────────────────────────────────────
# 1B. IMMEDIATE RECALL (new)
# ─────────────────────────────────────────────
st.subheader("1B. ทวนคำศัพท์ทันที (Immediate Recall)")
st.write("พูดทวนคำศัพท์ทั้ง 5 คำที่เพิ่งเห็นด้านบนทันที:")
immediate = voice_input("🎙 บันทึกเสียงทวนคำศัพท์", "immediate_recall")
if immediate:
    st.success(f"คุณพูดว่า: **{immediate}**")
    found_now = [w for w in WORDS if w in immediate]
    st.write(f"📊 จำได้ {len(found_now)} จาก {len(WORDS)} คำ")
    st.session_state["immediate_recall_count"] = len(found_now)
st.write("---")

# ─────────────────────────────────────────────
# 2. ATTENTION TEST — voice
# ─────────────────────────────────────────────
st.subheader("2. แบบทดสอบสมาธิและความจำใช้งาน")

st.markdown("**ความจำตัวเลขแบบเรียงไปข้างหน้า** — พูดตัวเลขต่อไปนี้ตามลำดับเดิม:")
st.info("2 – 1 – 8 – 5 – 4")
fwd = voice_input("🎙 บันทึกเสียงตัวเลขเรียงไปข้างหน้า", "fwd")
if fwd:
    st.success(f"คุณพูดว่า: **{fwd}**")
    fwd_ok = digits_in_order(fwd, FORWARD_SEQUENCE)
    st.write("✅ ถูกต้อง!" if fwd_ok else "❌ ยังไม่ถูกต้อง")
    st.session_state["fwd_ok"] = fwd_ok

st.markdown("**ความจำตัวเลขแบบย้อนกลับ** — พูดเลข **7 – 4 – 2** โดยเรียงย้อนกลับ:")
st.info("ให้พูดว่า: 2 – 4 – 7")
bwd = voice_input("🎙 บันทึกเสียงตัวเลขเรียงย้อนกลับ", "bwd")
if bwd:
    st.success(f"คุณพูดว่า: **{bwd}**")
    bwd_ok = digits_in_order(bwd, BACKWARD_SEQUENCE)
    st.write("✅ ถูกต้อง!" if bwd_ok else "❌ ยังไม่ถูกต้อง")
    st.session_state["bwd_ok"] = bwd_ok

st.write("---")

# ─────────────────────────────────────────────
# 3. LANGUAGE REPETITION — voice
# ─────────────────────────────────────────────
st.subheader("3. การทวนประโยค (Language Repetition)")

st.markdown(f"**ประโยคที่ 1:** {SENTENCE_1}")
lang1 = voice_input("🎙 บันทึกเสียงประโยคที่ 1", "lang1")
if lang1:
    sc = similarity_score(lang1, SENTENCE_1)
    st.success(f"คุณพูดว่า: **{lang1}**")
    st.progress(sc, text=f"ความตรงกัน: {sc:.0%}")
    st.session_state["lang1_score"] = sc

st.markdown(f"**ประโยคที่ 2:** {SENTENCE_2}")
lang2 = voice_input("🎙 บันทึกเสียงประโยคที่ 2", "lang2")
if lang2:
    sc = similarity_score(lang2, SENTENCE_2)
    st.success(f"คุณพูดว่า: **{lang2}**")
    st.progress(sc, text=f"ความตรงกัน: {sc:.0%}")
    st.session_state["lang2_score"] = sc

st.markdown(f"**ประโยคที่ 3:** {SENTENCE_3}")
lang3 = voice_input("🎙 บันทึกเสียงประโยคที่ 3", "lang3")
if lang3:
    sc = similarity_score(lang3, SENTENCE_3)
    st.success(f"คุณพูดว่า: **{lang3}**")
    st.progress(sc, text=f"ความตรงกัน: {sc:.0%}")
    st.session_state["lang3_score"] = sc

st.markdown(f"**ประโยคที่ 4:** {SENTENCE_4}")
lang4 = voice_input("🎙 บันทึกเสียงประโยคที่ 4", "lang4")
if lang4:
    sc = similarity_score(lang4, SENTENCE_4)
    st.success(f"คุณพูดว่า: **{lang4}**")
    st.progress(sc, text=f"ความตรงกัน: {sc:.0%}")
    st.session_state["lang4_score"] = sc

st.write("---")

# ─────────────────────────────────────────────
# 4. ABSTRACTION — voice
# ─────────────────────────────────────────────
st.subheader("4. การคิดเชิงนามธรรม (Abstraction)")

st.markdown("**รถไฟกับจักรยานเหมือนกันอย่างไร?**")
abs1 = voice_input("🎙️ บันทึกคำตอบของคุณ", "abs1_widget")
if abs1:
    st.success(f"คุณพูดว่า: **{abs1}**")
    vehicle_keywords = ["ยานพาหนะ", "พาหนะ", "เดินทาง", "ล้อ", "ขนส่ง", "ขับ", "นั่ง"]
    if contains_any(abs1, vehicle_keywords):
        st.info("🎯 ถูกต้อง! ทั้งสองเป็นยานพาหนะที่ใช้เดินทาง")
        st.session_state["abs1_correct"] = True
    else:
        st.warning("⚠️ คำตอบน่าสนใจ แต่ลองคิดดูว่าทั้งสองอย่างใช้เพื่ออะไร")
        st.session_state["abs1_correct"] = False

st.markdown("**นาฬิกากับไม้บรรทัดเหมือนกันอย่างไร?**")
abs2 = voice_input("🎙️ บันทึกคำตอบของคุณ", "abs2_widget")
if abs2:
    st.success(f"คุณพูดว่า: **{abs2}**")
    measurement_keywords = ["วัด", "เครื่องมือ", "อุปกรณ์", "ตัวเลข", "บอกเวลา", "มาตร"]
    if contains_any(abs2, measurement_keywords):
        st.info("🎯 ถูกต้อง! ทั้งสองเป็นเครื่องมือใช้วัด (เวลาและความยาว)")
        st.session_state["abs2_correct"] = True
    else:
        st.warning("⚠️ ยังไม่ตรงนัก ลองคิดว่าของสองอย่างนี้ใช้ทำอะไร")
        st.session_state["abs2_correct"] = False

st.markdown("**ส้มกับกล้วยเหมือนกันอย่างไร?**")
abs3 = voice_input("🎙️ บันทึกคำตอบของคุณ", "abs3_widget")
if abs3:
    st.success(f"คุณพูดว่า: **{abs3}**")
    fruit_keywords = ["ผลไม้", "กิน", "รับประทาน", "หวาน", "ผล"]
    if contains_any(abs3, fruit_keywords):
        st.info("🎯 ถูกต้อง! ทั้งสองเป็นผลไม้")
        st.session_state["abs3_correct"] = True
    else:
        st.warning("⚠️ ยังไม่ตรงนัก ลองคิดว่าทั้งสองอย่างจัดอยู่ในหมวดหมู่ใด")
        st.session_state["abs3_correct"] = False

st.markdown("**โต๊ะกับเก้าอี้เหมือนกันอย่างไร?**")
abs4 = voice_input("🎙️ บันทึกคำตอบของคุณ", "abs4_widget")
if abs4:
    st.success(f"คุณพูดว่า: **{abs4}**")
    furniture_keywords = ["เฟอร์นิเจอร์", "ของใช้", "ไม้", "บ้าน", "เครื่องเรือน"]
    if contains_any(abs4, furniture_keywords):
        st.info("🎯 ถูกต้อง! ทั้งสองเป็นเฟอร์นิเจอร์")
        st.session_state["abs4_correct"] = True
    else:
        st.warning("⚠️ ยังไม่ตรงนัก ลองคิดว่าทั้งสองอย่างจัดอยู่ในหมวดหมู่ใด")
        st.session_state["abs4_correct"] = False

st.write("---")

# ─────────────────────────────────────────────
# 5. ORIENTATION TO TIME (new)
# ─────────────────────────────────────────────
st.subheader("5. การรับรู้เรื่องเวลา (Orientation to Time)")
ctx = current_thai_context()

st.markdown("**วันนี้วันอะไร?**")
ori_day_name = voice_input("🎙 บันทึกคำตอบ", "ori_day_name")
if ori_day_name:
    st.success(f"คุณพูดว่า: **{ori_day_name}**")
    ok = ctx["weekday"].replace("วัน", "") in ori_day_name
    st.write("✅ ถูกต้อง!" if ok else f"❌ ที่จริงคือ {ctx['weekday']}")
    st.session_state["ori_day_name_ok"] = ok

st.markdown("**วันนี้วันที่เท่าไหร่?**")
ori_date = voice_input("🎙 บันทึกคำตอบ", "ori_date")
if ori_date:
    st.success(f"คุณพูดว่า: **{ori_date}**")
    ok = str(ctx["day"]) in ori_date
    st.write("✅ ถูกต้อง!" if ok else f"❌ ที่จริงคือวันที่ {ctx['day']}")
    st.session_state["ori_date_ok"] = ok

st.markdown("**เดือนนี้คือเดือนอะไร?**")
ori_month = voice_input("🎙 บันทึกคำตอบ", "ori_month")
if ori_month:
    st.success(f"คุณพูดว่า: **{ori_month}**")
    ok = ctx["month"] in ori_month
    st.write("✅ ถูกต้อง!" if ok else f"❌ ที่จริงคือ {ctx['month']}")
    st.session_state["ori_month_ok"] = ok

st.markdown("**ปีนี้คือปี พ.ศ. อะไร?**")
ori_year = voice_input("🎙 บันทึกคำตอบ", "ori_year")
if ori_year:
    st.success(f"คุณพูดว่า: **{ori_year}**")
    ok = str(ctx["year"]) in ori_year
    st.write("✅ ถูกต้อง!" if ok else f"❌ ที่จริงคือ พ.ศ. {ctx['year']}")
    st.session_state["ori_year_ok"] = ok

st.markdown("**ตอนนี้เป็นฤดูอะไร?**")
ori_season = voice_input("🎙 บันทึกคำตอบ", "ori_season")
if ori_season:
    st.success(f"คุณพูดว่า: **{ori_season}**")
    ok = ctx["season"].replace("ฤดู", "") in ori_season
    st.write("✅ ถูกต้อง!" if ok else f"❌ ที่จริงคือ {ctx['season']}")
    st.session_state["ori_season_ok"] = ok

st.write("---")

# ─────────────────────────────────────────────
# 6. ORIENTATION TO PLACE (new) — self-reported, recorded not graded against ground truth
# ─────────────────────────────────────────────
st.subheader("6. การรับรู้เรื่องสถานที่ (Orientation to Place)")
st.caption("คำตอบข้อนี้จะถูกบันทึกไว้ ผู้ประเมินสามารถตรวจสอบความถูกต้องด้วยตนเอง")

place_qs = [
    ("ตอนนี้คุณอยู่ประเทศอะไร?", "ori_country"),
    ("ตอนนี้คุณอยู่จังหวัดอะไร?", "ori_province"),
    ("ตอนนี้คุณอยู่ที่ไหน (เช่น บ้าน, โรงพยาบาล, คลินิก)?", "ori_place"),
    ("ตอนนี้คุณอยู่ชั้นไหนของอาคาร?", "ori_floor"),
    ("เมืองหรืออำเภอที่คุณอยู่ตอนนี้ชื่ออะไร?", "ori_city"),
]
for question, key in place_qs:
    st.markdown(f"**{question}**")
    ans = voice_input("🎙 บันทึกคำตอบ", key)
    if ans:
        st.success(f"คุณพูดว่า: **{ans}**")
        st.session_state[f"{key}_answered"] = True

st.write("---")

# ─────────────────────────────────────────────
# 7. VERBAL FLUENCY (new)
# ─────────────────────────────────────────────
st.subheader("7. ความคล่องแคล่วทางภาษา (Verbal Fluency)")

st.markdown("**บอกชื่อสัตว์ให้ได้มากที่สุดภายใน 1 นาที**")
fluency_animals = voice_input("🎙 บันทึกเสียง", "fluency_animals")
if fluency_animals:
    st.success(f"คุณพูดว่า: **{fluency_animals}**")
    words_count = len(set(fluency_animals.split()))
    st.write(f"📊 จำนวนคำที่พูดได้โดยประมาณ: {words_count}")
    st.session_state["fluency_animals_count"] = words_count

st.markdown("**บอกชื่อผลไม้ให้ได้มากที่สุดภายใน 1 นาที**")
fluency_fruits = voice_input("🎙 บันทึกเสียง", "fluency_fruits")
if fluency_fruits:
    st.success(f"คุณพูดว่า: **{fluency_fruits}**")
    words_count = len(set(fluency_fruits.split()))
    st.write(f"📊 จำนวนคำที่พูดได้โดยประมาณ: {words_count}")
    st.session_state["fluency_fruits_count"] = words_count

st.write("---")

# ─────────────────────────────────────────────
# 8. CALCULATION (new)
# ─────────────────────────────────────────────
st.subheader("8. การคำนวณ (Calculation)")
st.markdown("**เริ่มจาก 100 แล้วลบ 7 ไปเรื่อยๆ พูดผลลัพธ์ 5 ค่าติดต่อกัน (เช่น 93, 86, 79, 72, 65)**")
calc = voice_input("🎙 บันทึกเสียง", "calc_serial7")
if calc:
    st.success(f"คุณพูดว่า: **{calc}**")
    expected = ["93", "86", "79", "72", "65"]
    spoken_numbers = [tok for tok in calc.replace(",", " ").split() if tok.isdigit()]
    correct_count = sum(1 for e in expected if e in spoken_numbers)
    st.write(f"📊 ถูกต้อง {correct_count} จาก {len(expected)} ค่า")
    st.session_state["calc_correct_count"] = correct_count

st.write("---")

# ─────────────────────────────────────────────
# 9. NAMING (new)
# ─────────────────────────────────────────────
st.subheader("9. การเรียกชื่อสิ่งของ (Naming)")

naming_qs = [
    ("ของใช้ที่ใช้บอกเวลา ข้อมือสวมใส่ได้ เรียกว่าอะไร?", "naming_watch", ["นาฬิกา"]),
    ("สิ่งที่ใช้ในการเขียนหนังสือ เรียกว่าอะไร?", "naming_pen", ["ปากกา", "ดินสอ"]),
    ("สัตว์เลี้ยงที่เห่าและเฝ้าบ้าน เรียกว่าอะไร?", "naming_dog", ["สุนัข", "หมา"]),
]
for question, key, keywords in naming_qs:
    st.markdown(f"**{question}**")
    ans = voice_input("🎙 บันทึกคำตอบ", key)
    if ans:
        st.success(f"คุณพูดว่า: **{ans}**")
        ok = contains_any(ans, keywords)
        st.write("✅ ถูกต้อง!" if ok else "❌ ยังไม่ถูกต้อง")
        st.session_state[f"{key}_ok"] = ok

st.write("---")

# ─────────────────────────────────────────────
# 10. FUNCTIONAL DESCRIPTION (new)
# ─────────────────────────────────────────────
st.subheader("10. การอธิบายหน้าที่ของสิ่งของ (Functional Description)")

func_qs = [
    ("ค้อนใช้ทำอะไร?", "func_hammer", ["ตอก", "ตะปู", "ทุบ", "ต่อย"]),
    ("กรรไกรใช้ทำอะไร?", "func_scissors", ["ตัด", "หนีบ"]),
]
for question, key, keywords in func_qs:
    st.markdown(f"**{question}**")
    ans = voice_input("🎙 บันทึกคำตอบ", key)
    if ans:
        st.success(f"คุณพูดว่า: **{ans}**")
        ok = contains_any(ans, keywords)
        st.write("✅ ถูกต้อง!" if ok else "❌ ยังไม่ถูกต้อง")
        st.session_state[f"{key}_ok"] = ok

st.write("---")

# ─────────────────────────────────────────────
# 11. PROVERB INTERPRETATION (new)
# ─────────────────────────────────────────────
st.subheader("11. การอธิบายความหมายสุภาษิต (Proverb Interpretation)")

proverb_qs = [
    ("\"น้ำขึ้นให้รีบตัก\" หมายความว่าอย่างไร?", "proverb_water",
     ["โอกาส", "รีบ", "ฉวย", "ทัน"]),
    ("\"ช้าๆ ได้พร้าเล่มงาม\" หมายความว่าอย่างไร?", "proverb_slow",
     ["ใจเย็น", "ค่อยเป็นค่อยไป", "ระมัดระวัง", "รอบคอบ"]),
]
for question, key, keywords in proverb_qs:
    st.markdown(f"**{question}**")
    ans = voice_input("🎙 บันทึกคำตอบ", key)
    if ans:
        st.success(f"คุณพูดว่า: **{ans}**")
        ok = contains_any(ans, keywords)
        st.write("✅ ถูกต้อง!" if ok else "⚠️ ลองอธิบายอีกครั้งด้วยคำพูดของคุณเอง")
        st.session_state[f"{key}_ok"] = ok

st.write("---")

# ─────────────────────────────────────────────
# 12. DELAYED RECALL — voice, NO hint
# ─────────────────────────────────────────────
st.subheader("12. แบบทดสอบความจำครั้งสุดท้าย (Delayed Recall)")
st.write("พูดคำศัพท์ให้ได้มากที่สุดเท่าที่จำได้จากตอนต้น:")

recall = voice_input("🎙 บันทึกเสียงคำศัพท์ที่จำได้", "recall_widget")

if recall:
    st.success(f"คุณพูดว่า: **{recall}**")

    spoken_text = recall.lower()
    words_found = [word for word in WORDS if word in spoken_text]
    score_recall = len(words_found)
    total_words = len(WORDS)

    pct = score_recall / total_words
    st.progress(pct, text=f"ความแม่นยำในการจำคำศัพท์: {pct:.0%}")
    st.write(f"📊 **คะแนน:** จำได้ {score_recall} จาก {total_words} คำ")

    st.session_state["recall_score_count"] = score_recall

st.write("---")

# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────
if st.button("คำนวณคะแนน (Calculate Score)"):
    score = 0
    details = []

    # Immediate recall
    imm = st.session_state.get("immediate_recall_count", 0)
    score += imm
    details.append(f"🧠 ทวนคำศัพท์ทันที: {imm}/{len(WORDS)} คำ")

    # Attention
    if st.session_state.get("fwd_ok"):
        score += 1
        details.append("✅ ความจำตัวเลขไปข้างหน้า: ถูกต้อง")
    else:
        details.append("❌ ความจำตัวเลขไปข้างหน้า: ไม่ถูกต้อง")

    if st.session_state.get("bwd_ok"):
        score += 1
        details.append("✅ ความจำตัวเลขย้อนกลับ: ถูกต้อง")
    else:
        details.append("❌ ความจำตัวเลขย้อนกลับ: ไม่ถูกต้อง")

    # Language (4 sentences)
    for i in range(1, 5):
        s = st.session_state.get(f"lang{i}_score", 0.0)
        if s >= 0.6:
            score += 1
            details.append(f"✅ ประโยคที่ {i}: ตรงกัน {s:.0%}")
        else:
            details.append(f"❌ ประโยคที่ {i}: ตรงกัน {s:.0%} (ต้องการ ≥ 60%)")

    # Abstraction (4 pairs)
    for i in range(1, 5):
        if st.session_state.get(f"abs{i}_correct"):
            score += 1
            details.append(f"✅ การคิดเชิงนามธรรมข้อ {i}: ถูกต้อง")
        else:
            details.append(f"❌ การคิดเชิงนามธรรมข้อ {i}: ไม่ถูกต้อง")

    # Orientation to time
    ori_time_keys = ["ori_day_name_ok", "ori_date_ok", "ori_month_ok", "ori_year_ok", "ori_season_ok"]
    ori_time_labels = ["วัน", "วันที่", "เดือน", "ปี พ.ศ.", "ฤดู"]
    for key, label in zip(ori_time_keys, ori_time_labels):
        if st.session_state.get(key):
            score += 1
            details.append(f"✅ การรับรู้เวลา ({label}): ถูกต้อง")
        else:
            details.append(f"❌ การรับรู้เวลา ({label}): ไม่ถูกต้อง")

    # Orientation to place (recorded, 1 point each if answered)
    place_keys = ["ori_country_answered", "ori_province_answered", "ori_place_answered",
                  "ori_floor_answered", "ori_city_answered"]
    place_labels = ["ประเทศ", "จังหวัด", "สถานที่", "ชั้น", "เมือง"]
    for key, label in zip(place_keys, place_labels):
        if st.session_state.get(key):
            score += 1
            details.append(f"✅ การรับรู้สถานที่ ({label}): มีการตอบ (ต้องตรวจสอบความถูกต้องเอง)")
        else:
            details.append(f"❌ การรับรู้สถานที่ ({label}): ไม่มีคำตอบ")

    # Verbal fluency (2 categories, 1 point if >=8 unique words)
    for key, label in [("fluency_animals_count", "สัตว์"), ("fluency_fruits_count", "ผลไม้")]:
        count = st.session_state.get(key, 0)
        if count >= 8:
            score += 1
            details.append(f"✅ ความคล่องแคล่วทางภาษา ({label}): {count} คำ")
        else:
            details.append(f"❌ ความคล่องแคล่วทางภาษา ({label}): {count} คำ (ต้องการ ≥ 8)")

    # Calculation (up to 1 point per correct step, max 5)
    calc_correct = st.session_state.get("calc_correct_count", 0)
    score += calc_correct
    details.append(f"🧮 การคำนวณ (100 ลบ 7 ต่อเนื่อง): ถูกต้อง {calc_correct}/5")

    # Naming (3 items)
    for key, label in [("naming_watch_ok", "นาฬิกา"), ("naming_pen_ok", "ปากกา/ดินสอ"), ("naming_dog_ok", "สุนัข")]:
        if st.session_state.get(key):
            score += 1
            details.append(f"✅ การเรียกชื่อสิ่งของ ({label}): ถูกต้อง")
        else:
            details.append(f"❌ การเรียกชื่อสิ่งของ ({label}): ไม่ถูกต้อง")

    # Functional description (2 items)
    for key, label in [("func_hammer_ok", "ค้อน"), ("func_scissors_ok", "กรรไกร")]:
        if st.session_state.get(key):
            score += 1
            details.append(f"✅ การอธิบายหน้าที่ ({label}): ถูกต้อง")
        else:
            details.append(f"❌ การอธิบายหน้าที่ ({label}): ไม่ถูกต้อง")

    # Proverbs (2 items)
    for key, label in [("proverb_water_ok", "น้ำขึ้นให้รีบตัก"), ("proverb_slow_ok", "ช้าๆได้พร้าเล่มงาม")]:
        if st.session_state.get(key):
            score += 1
            details.append(f"✅ ความหมายสุภาษิต ({label}): ถูกต้อง")
        else:
            details.append(f"❌ ความหมายสุภาษิต ({label}): ไม่ถูกต้อง")

    # Delayed recall
    found = st.session_state.get("recall_score_count", 0)
    score += found
    details.append(f"🧠 ความจำระยะหลัง (Delayed Recall): {found}/{len(WORDS)} คำ")

    st.subheader("ผลการทดสอบ")
    for d in details:
        st.write(d)

    max_score = (
        len(WORDS)      # immediate recall
        + 2             # attention
        + 4             # language sentences
        + 4             # abstraction
        + 5             # orientation to time
        + 5             # orientation to place
        + 2             # verbal fluency
        + 5             # calculation
        + 3             # naming
        + 2             # functional description
        + 2             # proverbs
        + len(WORDS)    # delayed recall
    )
    st.write(f"**คะแนนรวม: {score} / {max_score}**")

    if score >= int(max_score * 0.7):
        st.success("🟢 ผลการทดสอบอยู่ในเกณฑ์ดี (ต้นแบบ/Prototype)")
    elif score >= int(max_score * 0.4):
        st.warning("🟡 มีความกังวลเล็กน้อย (ต้นแบบ/Prototype)")
    else:
        st.error("🔴 ควรได้รับการตรวจประเมินเพิ่มเติม (ต้นแบบ/Prototype)")

    st.caption("⚠️ นี่ไม่ใช่เครื่องมือวินิจฉัยทางการแพทย์ กรุณาปรึกษาแพทย์ผู้เชี่ยวชาญเพื่อการวินิจฉัยที่ถูกต้อง")
