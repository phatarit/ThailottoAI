import streamlit as st
import pandas as pd
from collections import Counter, defaultdict
from itertools import permutations

# ────────────────────────────── SETUP ──────────────────────────────
st.set_page_config(page_title="ThaiLottoAI v2.4", page_icon="🎯")
st.title("🎯 ThaiLottoAI – Multi‐Formula Analyzer with Hot-20 Boost")

# ────────────────────────── INPUT SECTION ──────────────────────────
st.markdown("ใส่ข้อมูลย้อนหลัง: สามตัวบน เว้นวรรค สองตัวล่าง เช่น `774 81` (หนึ่งบรรทัดต่อหนึ่งงวด)")
raw = st.text_area("📋 ข้อมูลย้อนหลัง", height=250)

extra = []
with st.expander("➕ เพิ่มข้อมูลทีละงวด"):
    for i in range(1, 6):
        txt = st.text_input(f"งวด #{i}", key=f"row_{i}")
        if txt:
            extra.append(txt)

lines = [l for l in (raw.splitlines() + extra) if l.strip()]
draws = []
for idx, line in enumerate(lines, 1):
    try:
        top, bottom = line.strip().split()
        if len(top) == 3 and len(bottom) == 2 and top.isdigit() and bottom.isdigit():
            draws.append((top, bottom))
        else:
            st.warning(f"ข้ามบรรทัด {idx}: รูปแบบไม่ถูกต้อง → {line}")
    except ValueError:
        st.warning(f"ข้ามบรรทัด {idx}: ไม่พบช่องว่างแบ่งบน/ล่าง → {line}")

if len(draws) < 40:
    st.info("⚠️ ต้องมีข้อมูลอย่างน้อย 40 งวดเพื่อประเมินสูตร")
    st.stop()

df = pd.DataFrame(draws, columns=["สามตัวบน", "สองตัวล่าง"])
st.success(f"โหลดข้อมูล {len(df)} งวด")
st.dataframe(df, use_container_width=True)

# ────────────────────────── HELPER FUNCTIONS ──────────────────────────
def hot_digits(history, window=10, n=5):
    segment = history[-window:] if len(history) >= window else history
    digits = "".join("".join(pair) for pair in segment)
    return [d for d, _ in Counter(digits).most_common(n)]

def hot20_top3(history):
    return hot_digits(history, window=20, n=3)

def run_digits(history):
    return list(history[-1][1])

def sum_mod(history):
    return str(sum(map(int, history[-1][0])) % 10)

# ───────────── EXP-HOT 27 (ตัวเด่น) ─────────────
def exp_hot(history, window=27, alpha=0.8):
    scores = Counter()
    recent = history[-window:]
    for n_back, (top, bottom) in enumerate(reversed(recent)):
        w = alpha ** n_back
        for d in top + bottom:
            scores[d] += w
    # Boost: เพิ่มน้ำหนัก 0.3 ให้เลขถี่สุด 3 ตัวใน 20 งวดหลัง
    for d in hot20_top3(history):
        scores[d] += 0.3
    return max(scores, key=scores.get)

# ───────────── MARKOV-20 (สองตัวล่าง 20 ชุด) ─────────────
def build_trans(history):
    t = defaultdict(Counter)
    for prev, curr in zip(history[:-1], history[1:]):
        t[prev[1]][curr[1]] += 1
    return t

def markov20(history, k=20):
    trans = build_trans(history)
    last = history[-1][1]
    cand = [c for c, _ in trans[last].most_common(k)]

    # Boost: เติมคู่ที่มี Hot-20 digits
    hot3 = hot20_top3(history)
    boost_pairs = [a + b for a in hot3 for b in "0123456789" if a != b]
    for p in boost_pairs:
        if p not in cand:
            cand.append(p)
        if len(cand) == k:
            break
    return cand[:k]

# ───────────── HYBRID-30 (สามตัวบน 30 ชุด) ─────────────
def hybrid30(history, pool_size=10, k=30):
    pool = []
    pool += run_digits(history)
    pool.append(sum_mod(history))
    pool += hot_digits(history, 5, 4)
    pool += hot_digits(history, len(history), 4)
    pool += hot20_top3(history)          # Boost pool
    pool = list(dict.fromkeys(pool))[:pool_size]

    scores = Counter()
    for idx, (top, bottom) in enumerate(history[-30:]):
        w = 1.0 - (idx / 30) * 0.9
        for d in top + bottom:
            scores[d] += w

    perms = ["".join(p) for p in permutations(pool, 3) if len(set(p)) == 3]
    perms.sort(key=lambda x: -(scores[x[0]] + scores[x[1]] + scores[x[2]]))
    return perms[:k]

# ───────────── WALK-FORWARD EVALUATOR ─────────────
def walk(history, predictor, hit_fn, start):
    hit = tot = 0
    for i in range(start, len(history)):
        past = history[:i]
        if hit_fn(predictor(past), history[i]):
            hit += 1
        tot += 1
    return hit / tot if tot else 0.0

hit_single = lambda p, act: p in act[0] or p in act[1]
hit_two = lambda preds, act: act[1] in preds or act[1][::-1] in preds
hit_three = lambda preds, act: act[0] in preds

acc_single = walk(draws, exp_hot, hit_single, 27)
acc_two = walk(draws, markov20, hit_two, 40)
acc_three = walk(draws, hybrid30, hit_three, 40)

# ───────────── PREDICT NEXT ─────────────
next_single = exp_hot(draws)
next_two = markov20(draws)
next_three = hybrid30(draws)

# ───────────── DISPLAY ─────────────
st.header("🔮 คาดการณ์งวดถัดไป")
left, right = st.columns(2)

with left:
    st.subheader("ตัวเด่น")
    st.markdown(f"**{next_single}**")
    st.caption(f"Hit-rate ≈ {acc_single*100:.1f}%")

with right:
    st.subheader("สองตัวล่าง (20)")
    st.write(" ".join(next_two))
    st.caption(f"Hit-rate ≈ {acc_two*100:.1f}% (ถือกลับได้)")

st.subheader("สามตัวบน (30)")
st.write(" ".join(next_three))
st.caption(f"Hit-rate ≈ {acc_three*100:.1f}%")

with st.expander("📊 วิธีคำนวณเปอร์เซ็นย้อนหลัง"):
    st.markdown(
        """
* **Walk-forward back-test** - ทำนายงวดถัดไปจากข้อมูลก่อนหน้า แล้ววัดผลแบบเลื่อนหน้าต่าง  
* **สองตัวล่าง** นับถูกทั้งเลขตรงและเลขคู่กลับ (AB / BA)  
* สูตร Boost ใหม่  
  * EXP-HOT 27 + top-3 hot digits (20 งวด)  
  * Markov-20 เติมคู่ที่มี hot-20 digits  
  * Hybrid-30 รวม hot-20 digits ใน pool
        """
    )

st.caption("© 2025 ThaiLottoAI v2.4")
