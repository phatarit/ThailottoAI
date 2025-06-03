import streamlit as st
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI ทำนายหวย", layout="centered")

# ------------------- CSS ------------------
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
    </style>
""", unsafe_allow_html=True)

st.title("🎯 ระบบ AI วิเคราะห์และทำนายหวย")
st.caption("พัฒนาโดย Phatarit AI Lab")

# ------------------- เก็บข้อมูล ------------------
if "lotto_data" not in st.session_state:
    st.session_state.lotto_data = []

# ------------------- กรอกย้อนหลังหลายชุด ------------------
st.subheader("🧾 เพิ่มข้อมูลย้อนหลัง (สูงสุด 10 งวด)")
num_rows = 10
bulk_data = []

with st.form("bulk_input_form"):
    for i in range(num_rows):
        cols = st.columns(2)
        with cols[0]:
            top = st.text_input(f"งวดที่ {i+1} - สามตัวบน", key=f"top_{i}", max_chars=3)
        with cols[1]:
            bottom = st.text_input(f"งวดที่ {i+1} - สองตัวล่าง", key=f"bottom_{i}", max_chars=2)
        bulk_data.append((top, bottom))

    submitted = st.form_submit_button("➕ เพิ่มข้อมูลย้อนหลังทั้งหมด")
    if submitted:
        count = 0
        for top, bottom in bulk_data:
            if top.isdigit() and bottom.isdigit():
                st.session_state.lotto_data.append((top.zfill(3), bottom.zfill(2)))
                count += 1
        st.success(f"✅ เพิ่มข้อมูลทั้งหมด {count} รายการ")

# ------------------- วิเคราะห์ ------------------
def detect_common_digits(last, previous):
    return sorted(set("".join(last)) & set("".join(previous)))

def find_missing_digits(data, recent=10):
    used = "".join([a + b for a, b in data[-recent:]])
    return [d for d in "0123456789" if d not in used]

def adjacent_hot_digits(data):
    all_digits = "".join([a + b for a, b in data])
    counter = Counter(all_digits)
    top = counter.most_common(1)[0][0]
    return [(int(top) + i) % 10 for i in [-1, 1]]

def tail_digit_freq(data):
    tails = [a[-1] for a, b in data]
    return Counter(tails).most_common()

def bottom_tail_freq(data):
    tails = [b[-1] for a, b in data]
    return Counter(tails).most_common()

# ------------------- แสดงผล ------------------
if st.session_state.lotto_data:
    df = pd.DataFrame(st.session_state.lotto_data, columns=["สามตัวบน", "สองตัวล่าง"])
    st.dataframe(df, use_container_width=True)

    all_digits = "".join([a + b for a, b in st.session_state.lotto_data])
    freq = Counter(all_digits).most_common()

    main_digit = freq[0][0]
    main_pairs = [f"{main_digit}{(int(main_digit)+i)%10}" for i in range(1, 5)]

    last_round = st.session_state.lotto_data[-1]
    second_last = st.session_state.lotto_data[-2] if len(st.session_state.lotto_data) >= 2 else None

    st.subheader("📊 วิเคราะห์หลัก")
    st.markdown(f"**เลขเด่น:** `{main_digit}`")

    if second_last:
        shared = detect_common_digits(last_round, second_last)
        st.markdown(f"**เลขซ้ำจากรอบก่อน:** {' '.join(shared) if shared else 'ไม่มี'}")

    top_tail = tail_digit_freq(st.session_state.lotto_data)
    bottom_tail = bottom_tail_freq(st.session_state.lotto_data)
    st.markdown(f"**เลขลงท้ายบ่อย (สามตัวบน):** `{top_tail[0][0]}` ({top_tail[0][1]} ครั้ง)")
    st.markdown(f"**เลขลงท้ายบ่อย (สองตัวล่าง):** `{bottom_tail[0][0]}` ({bottom_tail[0][1]} ครั้ง)")

    # 🔁 Pie Chart
    st.subheader("🥧 กราฟความถี่ (Pie Chart)")
    labels = [item[0] for item in freq]
    sizes = [item[1] for item in freq]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

    # 🧠 วิเคราะห์สูตร
    st.subheader("🧠 วิเคราะห์สูตรเพิ่มเติม")
    st.markdown(f"**เลขที่หายไปนาน:** {', '.join(find_missing_digits(st.session_state.lotto_data))}")
    st.markdown(f"**เลขข้างเคียงจากสถิติ:** {', '.join(map(str, adjacent_hot_digits(st.session_state.lotto_data)))}")

 if st.button("🔮 ทำนายรอบถัดไป"):
    st.markdown("### 🔮 ผลทำนายรอบถัดไป:")

    # เลขเด่น - ใหญ่ สีแดง
    st.markdown(f"<h2 style='color:red;'>เลขเด่น: {main_digit}</h2>", unsafe_allow_html=True)

    # เลขสองตัวแนะนำ - สีแดง
    main_pairs_html = " ".join([f"<span style='font-size:28px; color:red;'>{pair}</span>" for pair in main_pairs])
    st.markdown(f"<div>เลขสองตัวแนะนำ: {main_pairs_html}</div>", unsafe_allow_html=True)

    # เลขเสียวสามตัว - main_digit อยู่หลักสิบ
    import random
    d1 = str(random.randint(0, 9))
    d2 = main_digit
    d3 = str(random.randint(0, 9))
    lucky_3 = d1 + d2 + d3
    st.markdown(f"<h4 style='color:red;'>เลขเสียวสามตัว: {lucky_3}</h4>", unsafe_allow_html=True)


    # 📥 Download
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 ดาวน์โหลดข้อมูลย้อนหลัง", data=csv, file_name="lotto_history.csv", mime="text/csv")

else:
    st.info("กรุณากรอกผลหวยย้อนหลังอย่างน้อย 1 งวด")

st.markdown("---")
st.markdown("🔗 พัฒนาโดย **Phatarit AI Lab** | ใช้ Streamlit + Python")

