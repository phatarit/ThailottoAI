import streamlit as st
import pandas as pd
from collections import Counter, defaultdict
from itertools import permutations, combinations

# ─────────── SETUP ───────────
st.set_page_config(page_title="ThaiLottoAI v3.0", page_icon="🎯")
st.title("🎯 ThaiLottoAI – Multi-Window Hot-Digit Booster")

# ─────────── INPUT ───────────
st.markdown("วางข้อมูลย้อนหลัง: **สามตัวบน เว้นวรรค สองตัวล่าง** เช่น `774 81` (1 บรรทัด/งวด)")
raw = st.text_area("📋 ข้อมูลย้อนหลัง", height=250)

extra = []
with st.expander("➕ เพิ่มข้อมูลทีละงวด"):
    for i in range(1, 6):
        v = st.text_input(f"งวด #{i}", key=f"row_{i}")
        if v:
            extra.append(v)

lines = [l for l in (raw.splitlines() + extra) if l.strip()]
draws = []
for idx, line in enumerate(lines, 1):
    try:
        top, bottom = line.strip().split()
        if len(top) == 3 and len(bottom) == 2 and top.isdigit() and bottom.isdigit():
            draws.append((top, bottom))
        else:
            st.warning(f"ข้ามบรรทัด {idx}: รูปแบบผิด → {line}")
    except ValueError:
        st.warning(f"ข้ามบรรทัด {idx}: ไม่พบช่องวรรค → {line}")

if len(draws) < 40:
    st.info("⚠️ ต้องมีข้อมูล ≥ 40 งวดเพื่อใช้สูตรทั้งหมด")
    st.stop()

df = pd.DataFrame(draws, columns=["สามตัวบน", "สองตัวล่าง"])
st.success(f"โหลด {len(df)} งวด")
st.dataframe(df, use_container_width=True)

# ─────────── HELPER ───────────
def hot_digits(history, window, n=3):
    seg = history[-window:] if len(history) >= window else history
    digits = "".join("".join(x) for x in seg)
    return [d for d, _ in Counter(digits).most_common(n)]

def run_digits(history): return list(history[-1][1])
def sum_mod(history): return str(sum(map(int, history[-1][0])) % 10)

# Hot-digit sets
hot10 = hot_digits(draws, 10)
hot20 = hot_digits(draws, 20)
hot30 = hot_digits(draws, 30)
hot40 = hot_digits(draws, 40)

# ─────────── FORMULAS ───────────
def exp_hot(history, window=27, alpha=0.8):
    scores = Counter()
    recent = history[-window:]
    for n_back, (top, bottom) in enumerate(reversed(recent)):
        w = alpha ** n_back
        for d in top + bottom:
            scores[d] += w
    # Boost 4 ระยะ
    for d in hot10 + hot20 + hot30 + hot40:
        scores[d] += 0.3
    return max(scores, key=scores.get)

def build_trans(history):
    t = defaultdict(Counter)
    for prev, curr in zip(history[:-1], history[1:]):
        t[prev[1]][curr[1]] += 1
    return t

def markov(history, k=10):
    trans = build_trans(history)
    last = history[-1][1]
    cand = [c for c, _ in trans[last].most_common(k)]
    # เติมคู่ที่มี hot digits
    boost = set(hot10 + hot20 + hot30 + hot40)
    for a, b in combinations(boost, 2):
        for p in (a + b, b + a):
            if p not in cand:
                cand.append(p)
            if len(cand) == k:
                return cand
    return cand[:k]

def hybrid(history, pool_size=10, k=10):
    pool = []
    pool += run_digits(history)
    pool.append(sum_mod(history))
    pool += hot_digits(history, 5, 3)
    pool += hot_digits(history, len(history), 3)
    pool += hot10 + hot20 + hot30 + hot40
    pool = list(dict.fromkeys(pool))[:pool_size]

    score = Counter()
    for idx, (t, b) in enumerate(history[-30:]):
        w = 1 - idx / 30 * 0.9
        for d in t + b:
            score[d] += w

    perms = ["".join(p) for p in permutations(pool, 3) if len(set(p)) == 3]
    perms.sort(key=lambda x: -(score[x[0]] + score[x[1]] + score[x[2]]))
    return perms[:k]

# ─────────── WALK-FORWARD ───────────
def walk(history, predictor, hit_fn, start):
    h = tot = 0
    for i in range(start, len(history)):
        if hit_fn(predictor(history[:i]), history[i]):
            h += 1
        tot += 1
    return h / tot if tot else 0

hit_single = lambda p, act: p in act[0] or p in act[1]
hit_two = lambda preds, act: act[1] in preds or act[1][::-1] in preds
hit_three = lambda preds, act: act[0] in preds

acc_single = walk(draws, exp_hot, hit_single, 27)
acc_two = walk(draws, markov, hit_two, 40)
acc_three = walk(draws, hybrid, hit_three, 40)

# ─────────── PREDICT NEXT ───────────
next_single = exp_hot(draws)
next_two = markov(draws)
next_three = hybrid(draws)

# ─────────── DISPLAY ───────────
st.header("🔮 คาดการณ์งวดถัดไป")

st.markdown(
    f"<div style='font-size:48px; color:red; text-align:center;'>ตัวเด่น: {next_single}</div>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("สองตัวล่าง (10)")
    st.markdown(
        f"<div style='font-size:24px; color:red;'>{'  '.join(next_two)}</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Hit-rate ≈ {acc_two*100:.1f}%")

with col2:
    st.subheader("สามตัวบน (10)")
    st.markdown(
        f"<div style='font-size:24px; color:red;'>{'  '.join(next_three)}</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Hit-rate ≈ {acc_three*100:.1f}%")

with st.expander("📊 วิธีคำนวณเปอร์เซ็นย้อนหลัง"):
    st.markdown(
        """
* **Walk-forward back-test** - ทำนายงวดถัดไปจากข้อมูลก่อนหน้า แล้ววัดทีละงวด  
* **สองตัวล่าง** นับถูกทั้งเลขตรงและคู่กลับ (AB / BA)  
* Boost ด้วย Top-3 digit ใน 4 หน้าต่าง (10 / 20 / 30 / 40 งวด)
"""
    )

st.caption("© 2025 ThaiLottoAI v3.0")
