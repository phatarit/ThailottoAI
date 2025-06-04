import streamlit as st
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import random

st.set_page_config(page_title="AI ทำนายหวย", layout="centered")

st.markdown("""
    <style>
    .stApp { font-family: 'Sarabun', sans-serif; font-size: 18px; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 700px; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 ระบบ AI วิเคราะห์และทำนายหวย")
st.caption("พัฒนาโดย Phatarit AI Lab")

# --- SESSION STATE ---
if "lotto_data" not in st.session_state:
    st.session_state.lotto_data = []
if "bulk_done" not in st.session_state:
    st.session_state.bulk_done = False

# จำกัดข้อมูลไม่เกิน 10 งวดล่าสุด
if len(st.session_state.lotto_data) > 10:
    st.session_state.lotto_data = st.session_state.lotto_data[-10:]

# --- INPUT BLOCK 1: หลายงวดรอบแรก ---
if not st.session_state.bulk_done:
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
            st.session_state.bulk_done = True

# --- INPUT BLOCK 2: วางข้อความย้อนหลังหลายชุด ---
st.subheader("📋 วางข้อมูลย้อนหลังจากข้อความ (สามตัวบน สองตัวล่าง)")
raw_text = st.text_area("วางข้อมูล เช่น:\n123 45\n678 90", height=150)
if st.button("📥 แปลงและเพิ่มข้อมูล"):
    lines = raw_text.strip().split("\n")
    count = 0
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            top, bottom = parts
            st.session_state.lotto_data.append((top.zfill(3), bottom.zfill(2)))
            count += 1
    if count:
        st.success(f"✅ เพิ่มข้อมูลจากข้อความแล้ว {count} งวด")
    else:
        st.warning("⚠️ กรุณาตรวจสอบรูปแบบข้อมูลที่วาง (เช่น 123 45)")

# --- INPUT BLOCK 3: เพิ่มทีละชุด ---
if st.session_state.bulk_done:
    st.subheader("➕ กรอกข้อมูลหวยเพิ่ม (ทีละงวด)")
    col1, col2 = st.columns(2)
    with col1:
        top3 = st.text_input("สามตัวบน", key="single_top", max_chars=3)
    with col2:
        bottom2 = st.text_input("สองตัวล่าง", key="single_bottom", max_chars=2)

    if st.button("➕ เพิ่มข้อมูล 1 งวด"):
        if top3.isdigit() and bottom2.isdigit():
            st.session_state.lotto_data.append((top3.zfill(3), bottom2.zfill(2)))
            st.success("✅ เพิ่มข้อมูลแล้ว")
        else:
            st.warning("⚠️ กรุณากรอกเลขให้ถูกต้อง")

# --- ฟังก์ชัน ---
def detect_common_digits(last, previous):
    return sorted(set("".join(last)) & set("".join(previous)))

def find_missing_digits(data, recent=5):
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

# --- จัดการลบ ---
st.subheader("🧹 จัดการข้อมูลย้อนหลัง")
if st.session_state.lotto_data:
    selected_idx = st.selectbox("เลือกแถวที่ต้องการลบ", list(range(1, len(st.session_state.lotto_data)+1)))
    if st.button("🗑️ ลบเฉพาะแถวที่เลือก"):
        st.session_state.lotto_data.pop(selected_idx - 1)
        st.success("ลบรายการที่เลือกแล้ว")

    if st.button("🔥 ลบข้อมูลทั้งหมด"):
        st.session_state.lotto_data.clear()
        st.success("ลบข้อมูลทั้งหมดเรียบร้อยแล้ว")

# --- วิเคราะห์ ---
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

    st.subheader("🥧 กราฟความถี่ (Pie Chart)")
    labels = [item[0] for item in freq]
    sizes = [item[1] for item in freq]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

    st.subheader("🧠 วิเคราะห์สูตรเพิ่มเติม")
    st.markdown(f"**เลขที่หายไปนาน:** {', '.join(find_missing_digits(st.session_state.lotto_data))}")
    st.markdown(f"**เลขข้างเคียงจากสถิติ:** {', '.join(map(str, adjacent_hot_digits(st.session_state.lotto_data)))}")

    if st.button("🔮 ทำนายรอบถัดไป"):
        st.markdown("### 🔮 ผลทำนายรอบถัดไป:")
        st.markdown(f"<h2 style='color:red;'>เลขเด่น: {main_digit}</h2>", unsafe_allow_html=True)
        pair_html = " ".join([f"<span style='font-size:28px; color:red;'>{pair}</span>" for pair in main_pairs])
        st.markdown(f"<div>เลขสองตัวแนะนำ: {pair_html}</div>", unsafe_allow_html=True)
        lucky_3 = str(random.randint(0, 9)) + main_digit + str(random.randint(0, 9))
        st.markdown(f"<h4 style='color:red;'>เลขเสียวสามตัว: {lucky_3}</h4>", unsafe_allow_html=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 ดาวน์โหลดข้อมูลย้อนหลัง", data=csv, file_name="lotto_history.csv", mime="text/csv")
else:
    st.info("กรุณากรอกผลหวยย้อนหลังอย่างน้อย 1 งวด")

st.markdown("---")
st.markdown("🔗 พัฒนาโดย **Phatarit AI Lab** | ใช้ Streamlit + Python")
