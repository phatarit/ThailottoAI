# ThaiLottoAI v2 – Multiple formulas with hit‑rate estimate
import streamlit as st
import pandas as pd
from collections import Counter, defaultdict
from itertools import permutations
import math, traceback

st.set_page_config(page_title="ThaiLottoAI v2", page_icon="🎯")
st.title("🎯 ThaiLottoAI – Multi‑Formula Analyzer with Hit‑Rate")

# ---------- Input ----------
st.markdown("ใส่ข้อมูลย้อนหลัง: สามตัวบน เว้นวรรค สองตัวล่าง เช่น `774 81` หนึ่งบรรทัดต่อหนึ่งงวด")
data = st.text_area("📋 ข้อมูลย้อนหลัง", height=250)

extra = []
with st.expander("➕ เพิ่มข้อมูลทีละงวด"):
    for i in range(1, 6):
        v = st.text_input(f"งวด #{i}", key=f"row_{i}")
        if v:
            extra.append(v)

raw_lines = [l for l in (data.splitlines() + extra) if l.strip()]
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

if len(draws) < 40:
    st.info("⚠️ ต้องมีข้อมูลอย่างน้อย 40 งวด (เพื่อเทรน Markov)"); st.stop()

df = pd.DataFrame(draws, columns=["สามตัวบน", "สองตัวล่าง"])
st.success(f"โหลดข้อมูล {len(df)} งวด")
st.dataframe(df, use_container_width=True)

# ---------- Helper ----------
def exp_hot_single(history, window=27, alpha=0.8):
    """Exponential weighted frequency – return digit with max score"""
    scores = Counter()
    recent = history[-window:] if len(history) >= window else history
    for n_back, (top, bottom) in enumerate(reversed(recent)):
        w = alpha ** n_back
        for d in top + bottom:
            scores[d] += w
    return max(scores, key=scores.get)

def build_transitions(history):
    trans = defaultdict(Counter)
    for prev, curr in zip(history[:-1], history[1:]):
        trans[prev[1]][curr[1]] += 1
    return trans

def markov20_predict(history, topk=20):
    trans = build_transitions(history)
    last = history[-1][1]
    cand = [c for c, _ in trans[last].most_common(topk)]
    # fill if not enough
    if len(cand) < topk:
        overall = Counter()
        for d in trans.values():
            overall.update(d)
        for c, _ in overall.most_common():
            if c not in cand:
                cand.append(c)
            if len(cand) == topk:
                break
    return cand[:topk]

def hot_digits(history, window=10, n=5):
    rec = history[-window:] if len(history) >= window else history
    digits = "".join("".join(pair) for pair in rec)
    return [d for d, _ in Counter(digits).most_common(n)]

def run_digits(history):
    return list(history[-1][1])

def sum_mod(history):
    return str(sum(map(int, history[-1][0])) % 10)

def hybrid30_predict(history, pool_size=10, topk=30):
    pool = []
    pool.extend(run_digits(history))
    pool.append(sum_mod(history))
    pool.extend(hot_digits(history, window=5, n=4))
    pool.extend(hot_digits(history, window=len(history), n=4))
    pool = list(dict.fromkeys(pool))[:pool_size]

    # score by weighted freq 30 งวด
    scores = Counter()
    recent = history[-30:]
    for idx, (top, bottom) in enumerate(recent):
        w = 1.0 - (idx / 30) * 0.9
        for d in top + bottom:
            scores[d] += w

    perms = ["".join(p) for p in permutations(pool, 3) if len(set(p)) == 3]
    perms.sort(key=lambda x: -(scores[x[0]] + scores[x[1]] + scores[x[2]]))
    return perms[:topk]

# ---------- Back‑test evaluator ----------
def walk_forward(history, predictor, hit_fn, min_start):
    hits = 0; total = 0
    for i in range(min_start, len(history)):
        past = history[:i]
        pred = predictor(past)
        actual = history[i]
        if hit_fn(pred, actual):
            hits += 1
        total += 1
    return hits / total if total else 0.0, total

# Hit functions
hit_single = lambda pred, act: pred in act[0] or pred in act[1]
hit_two = lambda preds, act: act[1] in preds or act[1][::-1] in preds
hit_three = lambda preds, act: act[0] in preds

# ---------- Compute stats ----------
single_acc, _ = walk_forward(draws, exp_hot_single, hit_single, 27)
two_acc, _ = walk_forward(draws, lambda h: markov20_predict(h, 20), hit_two, 40)
three_acc, _ = walk_forward(draws, lambda h: hybrid30_predict(h, 10, 30), hit_three, 40)

# ---------- Predict next draw ----------
next_single = exp_hot_single(draws)
next_two20 = markov20_predict(draws, 20)
next_three30 = hybrid30_predict(draws, 10, 30)

st.header("🔮 คาดการณ์งวดถัดไป (Multi‑Formula)")
col1, col2 = st.columns(2)
with col1:
    st.subheader("ตัวเด่น – EXP‑HOT 27")
    st.markdown(f"**{next_single}**")
    st.caption(f"อัตราถูกย้อนหลัง ~ {single_acc*100:.1f}%")

with col2:
    st.subheader("สองตัวล่าง – MARKOV‑20")
    st.code(" ".join(next_two20))
    st.caption(f"อัตราถูกย้อนหลัง ~ {two_acc*100:.1f}% (ถือตรง/กลับ)")
st.subheader("สามตัวบน – HYBRID‑30")
st.code(" ".join(next_three30))
st.caption(f"อัตราถูกย้อนหลัง ~ {three_acc*100:.1f}% (ใน 30 ชุด)")

st.markdown("---")
with st.expander("📊 วิธีคำนวณเปอร์เซ็นย้อนหลัง"):
    st.write("• Walk‑forward back‑test: ทำนายงวดถัดไปจากข้อมูลทั้งหมดก่อนหน้าทุกครั้งแล้วค่อยวัดผล")             .write("• ชุดล่างถือทั้งตรงและกลับ (AB/BA) เพื่อเทียบ")             .write("• EXP‑HOT ใช้ถ่วงน้ำหนัก 0.8^n, Markov ใช้ top 20 คู่, Hybrid ใช้ pool 10 → 30 permutations")

st.caption("© 2025 ThaiLottoAI v2 – with Prob‑Estimates")
