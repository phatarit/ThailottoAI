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
        max-width: 700px;
    }
    button {
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 ระบบ AI วิเคราะห์และทำนายหวย")
st.caption("เวอร์ชันทดลอง | รองรับ Windows และมือถือ")

# เก็บข้อมูลย้อนหลัง
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
            st.success("✅ เพิ่มข้อมูลแล้ว")
        else:
            st.error("❌ กรุณากรอกตัวเลขเท่านั้น")

with col4:
    if st.button("🗑️ ล้างข้อมูล"):
        st.session_state.lotto_data = []
        st.success("🧹 ล้างข้อมูลทั้งหมดแล้ว")

# แสดงผล
if st.session_state.lotto_data:
    df = pd.DataFrame(st.session_state.lotto_data, columns=["สามตัวบน", "สองตัวล่าง"])
    st.dataframe(df, use_container_width=True)

    # 🔍 วิเคราะห์ความถี่
    all_digits = "".join([a + b for a, b in st.session_state.lotto_data])
    freq = Counter(all_digits).most_common()

    main_digit = freq[0][0]
    main_pairs = [f"{main_digit}{(int(main_digit)+i)%10}" for i in range(1, 5)]

    # 🔁 เลขเบิ้ลและซ้ำ
    last_round = st.session_state.lotto_data[-1]
    second_last = st.session_state.lotto_data[-2] if len(st.session_state.lotto_data) >= 2 else None
    repeated = [n for n in last_round if last_round.count(n) > 1]

    st.subheader("📊 วิเคราะห์ข้อมูล")
    st.markdown(f"**เลขที่ออกบ่อยที่สุด:** `{main_digit}`")
    st.markdown(f"**เลขเบิ้ลล่าสุด:** {' '.join(repeated) if repeated else 'ไม่มี'}")
    if second_last:
        match = set(last_round) & set(second_last)
        st.markdown(f"**เลขซ้ำจากรอบก่อน:** {' '.join(match) if match else 'ไม่มี'}")

    # 🔠 วิเคราะห์ขึ้นต้น/ลงท้าย
    start_digits = [a[0] for a, _ in st.session_state.lotto_data]
    end_digits = [a[-1] for a, _ in st.session_state.lotto_data]
    start_freq = Counter(start_digits).most_common(1)
    end_freq = Counter(end_digits).most_common(1)

    st.markdown(f"**ขึ้นต้นบ่อย:** {start_freq[0][0]}  |  **ลงท้ายบ่อย:** {end_freq[0][0]}")

    # 📈 กราฟ
    st.subheader("📈 กราฟความถี่ตัวเลข")
    fig, ax = plt.subplots()
    ax.bar(dict(freq).keys(), dict(freq).values(), color="skyblue")
    ax.set_xlabel("เลข")
    ax.set_ylabel("จำนวนครั้ง")
    st.pyplot(fig)

    # 🔮 ทำนายรอบถัดไป
    if st.button("🧠 ทำนายรอบถัดไป"):
        st.markdown("### 🔮 ผลทำนายรอบถัดไป:")
        st.success(f"เลขเด่นที่สุด: `{main_digit}`")
        st.info(f"ชุดเลขสองตัวที่แนะนำ: `{', '.join(main_pairs)}`")

    # 📤 ดาวน์โหลดข้อมูล
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 ดาวน์โหลดเป็น .CSV", data=csv, file_name="lotto_history.csv", mime="text/csv")
else:
    st.info("ยังไม่มีข้อมูลย้อนหลัง กรุณากรอกผลหวยก่อน")

st.markdown("---")
st.markdown("🧠 พัฒนาโดย **Phatarit AI Lab**")
