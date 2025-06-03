import streamlit as st
import pandas as pd
from collections import Counter

st.set_page_config(page_title="AI ทำนายหวย", layout="centered")

st.markdown("""
    <style>
    body {
        background-color: white !important;
        color: black !important;
    }
    .stApp {
        font-family: 'Sarabun', sans-serif;
        font-size: 18px;
    }
    .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Vessavana_Giant_at_Wat_Arun.jpg/800px-Vessavana_Giant_at_Wat_Arun.jpg", caption="ยักษ์เวสสุวรรณเสริมสิริมงคล", use_column_width=True)

st.title("🎯 ระบบ AI วิเคราะห์และทำนายหวย")
st.caption("ออกแบบสำหรับการใช้งานบน Windows และมือถือ | เวอร์ชันทดลอง")

if "lotto_data" not in st.session_state:
    st.session_state.lotto_data = []

st.subheader("📝 กรอกผลหวยย้อนหลัง")
col1, col2 = st.columns(2)
with col1:
    top3 = st.text_input("สามตัวบน", max_chars=3)
with col2:
    bottom2 = st.text_input("สองตัวล่าง", max_chars=2)

if st.button("➕ เพิ่มข้อมูล"):
    if top3.isdigit() and bottom2.isdigit():
        st.session_state.lotto_data.append((top3.zfill(3), bottom2.zfill(2)))
        st.success("เพิ่มข้อมูลแล้ว")
    else:
        st.error("กรุณากรอกตัวเลขเท่านั้น")

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
else:
    st.info("ยังไม่มีข้อมูลย้อนหลัง กรุณากรอกผลหวยก่อน")

st.image("https://www.matichonweekly.com/wp-content/uploads/2022/08/yant1.jpg", caption="ยันต์มหาลาภ เสริมโชคลาภ", use_column_width=True)
