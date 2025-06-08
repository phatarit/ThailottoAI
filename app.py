# ThaiLottoAI – Predict Thai Government Lottery (3‑digit on top / 2‑digit bottom)
import streamlit as st
import pandas as pd
from collections import Counter
from itertools import permutations
from datetime import datetime, timedelta
import os, traceback

st.set_page_config(page_title="ThaiLottoAI", page_icon="🎯")
st.title("🎯 ThaiLottoAI – Advanced Thai Lottery Analyzer")

st.markdown(
    """ใช้สูตรสถิติ 6 ชั้น (Run, Sum‑mod, Hot, Pair‑Reverse, HL/OE Switch, No‑Double)
    เพื่อคัดกรองเลข **สามตัวบน** และ **สองตัวล่าง** โดยอาศัยข้อมูลย้อนหลัง
    • รองรับการวางข้อมูลทีละหลายงวด หรือเพิ่มภายหลัง
    • รูปแบบ: `774 81` (สามตัวบน เว้นวรรค สองตัวล่าง) หนึ่งบรรทัดต่อหนึ่งงวด""")

# ---------- INPUT AREA ----------
data_input = st.text_area("📋 วางข้อมูลย้อนหลังหลายบรรทัด (*สามตัวบน เว้นวรรค สองตัวล่าง*)", height=250)

extra_inputs = []
with st.expander("➕ เพิ่มข้อมูลทีละงวด"):
    for i in range(1, 6):
        v = st.text_input(f"งวด #{i}", key=f"row_{i}")
        if v: extra_inputs.append(v)

# Merge & clean lines
raw_lines = [l for l in (data_input.splitlines() + extra_inputs) if l.strip()]
draws = []
for idx, line in enumerate(raw_lines, 1):
    try:
        top, bottom = line.strip().split()
        if len(top) == 3 and len(bottom) == 2 and top.isdigit() and bottom.isdigit():
            draws.append((top, bottom))
        else:
            st.warning(f"ข้ามบรรทัด {idx}: รูปแบบไม่ถูกต้อง → {line}")
    except ValueError:
        st.warning(f"ข้ามบรรทัด {idx}: ไม่พบช่องว่างแบ่งบน/ล่าง → {line}")

if len(draws) < 5:
    st.info("⚠️ ต้องมีข้อมูลอย่างน้อย 5 งวดเพื่อเริ่มวิเคราะห์")
    st.stop()

df = pd.DataFrame(draws, columns=["สามตัวบน", "สองตัวล่าง"])
st.success(f"โหลดข้อมูลสำเร็จ {len(df)} งวด")
st.dataframe(df, use_container_width=True)

# ---------- CORE FORMULAS ----------
def predict(df: pd.DataFrame, two_limit: int = 12, three_limit: int = 10):
    all_digits = "".join("".join(pair) for pair in df.values)
    hot = [d for d, _ in Counter(all_digits).most_common(5)]

    last_top, last_bottom = df.iloc[-1]
    run_digits = list(last_bottom)

    sum_mod = str(sum(map(int, last_top)) % 10)
    pair_rev = last_bottom[::-1]

    # candidate pool (unique, ordered)
    pool = []
    for d in run_digits + [sum_mod] + hot:
        if d not in pool:
            pool.append(d)
    # pad to at least 6 digits
    while len(pool) < 6:
        pool.append(str((int(pool[-1]) + 1) % 10))

    # two‑digit prediction
    want_odd = int(last_bottom[-1]) % 2 == 0  # if last even → want odd
    two_list = []
    for a in pool:
        for b in pool:
            if a == b:         # No‑Double (พักเบิ้ล)
                continue
            if want_odd and int(b) % 2 == 0:
                continue
            two_list.append(a + b)
    two_list = two_list[:two_limit]

    # three‑digit prediction
    three_list = []
    for perm in permutations(pool, 3):
        if len(set(perm)) == 3:
            three_list.append("".join(perm))
            if len(three_list) == three_limit:
                break

    meta = {
        "pool": pool,
        "sum_mod": sum_mod,
        "pair_reverse": pair_rev,
        "want_odd_bottom": want_odd
    }
    return two_list, three_list, meta

# ---------- PREDICTION ----------
two_digits, three_digits, meta = predict(df)

st.header("🔮 สรุปผลคัดกรอง (สูตรขั้นสูง)")
st.subheader("สองตัว (บน/ล่าง)")
st.code(" ".join(two_digits))

st.subheader("สามตัวบน")
st.code(" ".join(three_digits))

with st.expander("ℹ️ ข้อมูลเสริมสูตร (debug)"):
    st.write("*Candidate Digits*:", meta["pool"])
    st.write("SUM‑MOD 10 ของงวดล่าสุด:", meta["sum_mod"])
    st.write("คู่กลับ (สองตัวล่างล่าสุด):", meta["pair_reverse"])
    st.write("ต้องการให้หลักหน่วยล่างเป็นคี่? →", meta["want_odd_bottom"])

st.caption("© 2025 ThaiLottoAI – minimal demo")
