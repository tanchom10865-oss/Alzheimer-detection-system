วimport streamlit as st

st.title("🧠 Cognitive Screening Test (No Voice Version)")

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
# 2. ATTENTION TEST
# -----------------------------
st.subheader("2. Attention Test")

forward = st.text_input("Enter FORWARD numbers (e.g. 2 1 8 5 4)")
backward = st.text_input("Enter BACKWARD numbers (e.g. 2 4 7)")

st.write("---")


# -----------------------------
# 3. LANGUAGE TEST
# -----------------------------
st.subheader("3. Language Repetition")

lang1 = st.text_input("Repeat sentence 1 I only know that John is the one to help today")
lang2 = st.text_input("Repeat sentence 2 The cat always hid under the couch when dogs were in the room")

st.write("---")


# -----------------------------
# 4. ABSTRACTION
# -----------------------------
st.subheader("4. Abstraction")

t1 = st.text_input("Train vs Bicycle similarity?")
t2 = st.text_input("Watch vs Ruler similarity?")


# -----------------------------
# 5. DELAYED RECALL
# -----------------------------
st.subheader("5. Final Memory Test")

recall = st.text_input("Type the words you remember")

st.write("Words were: face, velvet, church, daisy, red")

st.write("---")


# -----------------------------
# SCORING
# -----------------------------
if st.button("Calculate Score"):

    score = 0

    # abstraction
    if len(t1) > 2:
        score += 1
    if len(t2) > 2:
        score += 1

    # recall scoring
    correct_words = st.session_state.get("words", [])

    if recall:
        found = sum(word in recall.lower() for word in correct_words)
        score += found


    st.subheader("Results")

    if score >= 5:
        st.success("🟢 Good performance (prototype)")
    elif score >= 3:
        st.warning("🟡 Mild concern (prototype)")
    else:
        st.error("🔴 Needs review (prototype)")

    st.write("⚠️ Not a medical diagnosis tool")
