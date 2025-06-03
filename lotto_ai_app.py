import streamlit as st
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI ทำนายหวย", layout="centered")

st.markdown("""
    <style>
    .stApp {
        font-family: 'Sarabun', sans-serif;
        font-size: 18px;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 720px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 ระบบ AI วิเคราะห์และทำนายหวย")
st.caption("เวอร์ชันทดลอง | รองรับ Windows และมือถือ")

if "lotto_data" not in st.session_state:
    st.session_state.lotto_data = []

st.subheader("📝 กรอกผลหวยย้อนหลัง")
col1, col2 = st.columns(2)
with col1:
    top3 = st.text_input("สามตัวบน", max_chars=3)
with col2:
    bottom2 = st.text_input("สองตัวล่าง", max_chars=2)

col3, col4 = st.columns(2)
with col3:
    if st.button("➕ เพิ่มข้อมูล"):
        if top3.isdigit() and bottom2.isdigit():
            st.session_state.lotto_data.append((top3.zfill(3), bottom2.zfill(2)))
            st.success("เพิ่มข้อมูลแล้ว")
        else:
            st.error("กรุณากรอกตัวเลขเท่านั้น")

with col4:
    if st.button("🗑️ ล้างข้อมูล"):
        st.session_state.lotto_data = []
        st.success("ล้างข้อมูลแล้ว")

if st.session_state.lotto_data:
    df = pd.DataFrame(st.session_state.lotto_data, columns=["สามตัวบน", "สองตัวล่าง"])
    st.dataframe(df, use_container_width=True)

    digits = list("".join([a + b for a, b in st.session_state.lotto_data]))
    freq = Counter(digits).most_common()
    main_digit = freq[0][0] if freq else "-"
    pairs = [f"{main_digit}{(int(main_digit)+i)%10}" for i in range(1, 5)]

    st.subheader("📊 ผลการวิเคราะห์")
    st.markdown(f"**เลขที่ออกบ่อยที่สุด:** {main_digit}")
    st.markdown(f"**ชุดเลขสองตัวแนะนำ:** {', '.join(pairs)}")

    st.subheader("📈 กราฟความถี่ตัวเลข")
    freq_dict = dict(freq)
    fig, ax = plt.subplots()
    ax.bar(freq_dict.keys(), freq_dict.values(), color="skyblue")
    ax.set_title("ความถี่ของเลขที่ปรากฏ")
    ax.set_xlabel("เลข")
    ax.set_ylabel("จำนวนครั้ง")
    st.pyplot(fig)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📤 ดาวน์โหลดข้อมูลย้อนหลัง (.CSV)", data=csv, file_name="lotto_history.csv", mime="text/csv")
else:
    st.info("ยังไม่มีข้อมูลย้อนหลัง กรุณากรอกผลหวยก่อน")
