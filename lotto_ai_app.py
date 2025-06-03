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
st.caption("พัฒนาโดย Phatarit AI Lab | เวอร์ชันทดลอง")

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

# ------------------------------- #
def detect_consecutive_doubles(data):
    recent = [x[0] for x in data[-3:]]
    return list(set([n for n in recent if n[0] == n[1] or n[1] == n[2]]))

def find_missing_digits(data, recent=10):
    used = "".join([a+b for a, b in data[-recent:]])
    return [d for d in "0123456789" if d not in used]

def adjacent_hot_digits(data):
    all_digits = "".join([a+b for a, b in data])
    counter = Counter(all_digits)
    top = counter.most_common(1)[0][0]
    return [(int(top)+i)%10 for i in [-1, 1]]

# ------------------------------- #
if st.session_state.lotto_data:
    df = pd.DataFrame(st.session_state.lotto_data, columns=["สามตัวบน", "สองตัวล่าง"])
    st.dataframe(df, use_container_width=True)

    all_digits = "".join([a + b for a, b in st.session_state.lotto_data])
    freq = Counter(all_digits).most_common()

    main_digit = freq[0][0]
    main_pairs = [f"{main_digit}{(int(main_digit)+i)%10}" for i in range(1, 5)]

    last_round = st.session_state.lotto_data[-1]
    second_last = st.session_state.lotto_data[-2] if len(st.session_state.lotto_data) >= 2 else None
    repeated = [n for n in last_round if last_round.count(n) > 1]

    st.subheader("📊 วิเคราะห์หลัก")
    st.markdown(f"**เลขเด่น:** `{main_digit}`")
    st.markdown(f"**เลขเบิ้ล:** {' '.join(repeated) if repeated else 'ไม่มี'}")
    if second_last:
        match = set(last_round) & set(second_last)
        st.markdown(f"**เลขซ้ำจากรอบก่อน:** {' '.join(match) if match else 'ไม่มี'}")

    start_digits = [a[0] for a, _ in st.session_state.lotto_data]
    end_digits = [a[-1] for a, _ in st.session_state.lotto_data]
    start_freq = Counter(start_digits).most_common(1)
    end_freq = Counter(end_digits).most_common(1)
    st.markdown(f"**ขึ้นต้นบ่อย:** {start_freq[0][0]} | **ลงท้ายบ่อย:** {end_freq[0][0]}")

    # 🔁 Pie Chart
    st.subheader("📈 กราฟความถี่ (Pie Chart)")
    labels = [item[0] for item in freq]
    sizes = [item[1] for item in freq]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

    # 🧠 วิเคราะห์สูตรขั้นสูง
    st.subheader("🧠 วิเคราะห์สูตรเพิ่มเติม")
    st.markdown(f"**เลขเบิ้ล 3 งวดติด:** {', '.join(detect_consecutive_doubles(st.session_state.lotto_data)) or 'ไม่มี'}")
    st.markdown(f"**เลขที่หายไปนาน:** {', '.join(find_missing_digits(st.session_state.lotto_data))}")
    st.markdown(f"**เลขข้างเคียงจากสถิติ:** {', '.join(map(str, adjacent_hot_digits(st.session_state.lotto_data)))}")

    if st.button("🧠 ทำนายรอบถัดไป"):
        st.markdown("### 🔮 ผลทำนาย:")
        st.success(f"เลขเด่น: `{main_digit}`")
        st.info(f"เลขสองตัวแนะนำ: `{', '.join(main_pairs)}`")

    # 📤 Export CSV
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 ดาวน์โหลดข้อมูลย้อนหลังเป็น CSV", data=csv, file_name="lotto_history.csv", mime="text/csv")
else:
    st.info("กรุณากรอกผลหวยย้อนหลังอย่างน้อย 1 งวดก่อนเริ่มวิเคราะห์")

st.markdown("---")
st.markdown("🔗 พัฒนาโดย **Phatarit AI Lab** | ใช้เทคโนโลยี Streamlit + Python")
