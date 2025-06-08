import streamlit as st
import pandas as pd
from collections import Counter, defaultdict
from itertools import permutations, combinations, islice

# ───────────────── SETUP ─────────────────
st.set_page_config(page_title='ThaiLottoAI v3.3', page_icon='🎯')
st.title('🎯 ThaiLottoAI – 20-Combo • Unordered • Focus Picks')

# ───────────────── INPUT ─────────────────
st.markdown('วางข้อมูลย้อนหลัง: **สามตัวบน เว้นวรรค สองตัวล่าง** เช่น `774 81` (1 บรรทัด/งวด)')
raw = st.text_area('📋 ข้อมูลย้อนหลัง', height=250)

extra = []
with st.expander('➕ เพิ่มข้อมูลทีละงวด'):
    for i in range(1, 6):
        r = st.text_input(f'งวด #{i}', key=f'row_{i}')
        if r:
            extra.append(r)

draws = []
for idx, line in enumerate([*raw.splitlines(), *extra], 1):
    try:
        t, b = line.split()
        if len(t) == 3 and len(b) == 2 and t.isdigit() and b.isdigit():
            draws.append((t, b))
        else:
            st.warning(f'ข้ามบรรทัด {idx}: รูปแบบผิด → {line}')
    except ValueError:
        if line.strip():
            st.warning(f'ข้ามบรรทัด {idx}: ไม่พบช่องว่าง → {line}')

if len(draws) < 40:
    st.info('⚠️ ต้องมีข้อมูล ≥ 40 งวด')
    st.stop()

st.dataframe(pd.DataFrame(draws, columns=['สามตัวบน', 'สองตัวล่าง']),
             use_container_width=True)

# ───────────────── HELPER ─────────────────
def hot_digits(hist, win, n=3):
    seg = hist[-win:] if len(hist) >= win else hist
    return [d for d, _ in Counter(''.join(''.join(x) for x in seg)).most_common(n)]

def pretty(lst, per_line=10):
    """คืนสตริงขึ้นบรรทัดใหม่ทุก per_line ตัว"""
    chunk = ['  '.join(lst[i:i+per_line]) for i in range(0, len(lst), per_line)]
    return '<br>'.join(chunk)

def unordered2(p): return ''.join(sorted(p))          # '97' → '79'
def unordered3(t): return ''.join(sorted(t))          # '693' → '369'
def run_digits(hist): return list(hist[-1][1])
def sum_mod(hist):  return str(sum(map(int, hist[-1][0])) % 10)

hot10 = hot_digits(draws, 10)
hot20 = hot_digits(draws, 20)
hot30 = hot_digits(draws, 30)
hot40 = hot_digits(draws, 40)

# ───────────── FORMULAS ─────────────
def exp_hot(hist, win=27):
    sc = Counter()
    for i, (t, b) in enumerate(reversed(hist[-win:])):
        w = 0.8 ** i
        for d in t + b:
            sc[d] += w
    for d in hot10 + hot20 + hot30 + hot40:
        sc[d] += 0.3
    return max(sc, key=sc.get)

def build_trans(hist):
    M = defaultdict(Counter)
    for (pt, pb), (ct, cb) in zip(hist[:-1], hist[1:]):
        M[unordered2(pb)][unordered2(cb)] += 1
    return M

def markov20_pairs(hist):
    trans = build_trans(hist)
    last = unordered2(hist[-1][1])
    base = [p for p, _ in trans[last].most_common(20)]

    boost = set(hot10 + hot20 + hot30 + hot40)
    for a, b in combinations(boost, 2):
        p = unordered2(a + b)
        if p not in base:
            base.append(p)
        if len(base) == 20:
            break
    return base[:20]

def hybrid20_combos(hist, pool_sz=12, k=20):
    pool = run_digits(hist) + [sum_mod(hist)] \
         + hot_digits(hist, 5, 3) + hot_digits(hist, len(hist), 3) \
         + hot10 + hot20 + hot30 + hot40
    pool = list(dict.fromkeys(pool))[:pool_sz]

    score = Counter()
    for i, (t, b) in enumerate(hist[-30:]):
        w = 1 - i / 30 * 0.9
        for d in t + b:
            score[d] += w

    combos = {"".join(sorted(c)) for c in combinations(pool, 3)}
    combos = sorted(combos,
                    key=lambda x: -(score[x[0]] + score[x[1]] + score[x[2]]))
    return combos[:k]

# ───────────── WALK-FORWARD (unordered) ─────────────
def walk(hist, pred_fn, hit_fn, start):
    hit = tot = 0
    for i in range(start, len(hist)):
        if hit_fn(pred_fn(hist[:i]), hist[i]):
            hit += 1
        tot += 1
    return hit / tot if tot else 0.0

hit_two = lambda preds, act: unordered2(act[1]) in preds or \
                             unordered2(act[0][1:]) in preds
hit_three = lambda preds, act: unordered3(act[0]) in preds

acc_two = walk(draws, markov20_pairs, hit_two, 40)
acc_three = walk(draws, hybrid20_combos, hit_three, 40)

# ───────────── PREDICT NEXT ─────────────
single   = exp_hot(draws)
two20    = markov20_pairs(draws)
three20  = hybrid20_combos(draws)

# รวม 2 ตัวท้ายบนเข้าชุดล่าง
for tail in {unordered2(t[1:]) for t, _ in [draws[-1]]}:
    if tail not in two20:
        two20.append(tail)
two20 = two20[:20]

focus_two   = two20[:5]
focus_three = three20[0]

# ───────────── DISPLAY ─────────────
st.markdown(
    f"<div style='font-size:44px;color:red;text-align:center'>ตัวเด่น: {single}</div>",
    unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    st.subheader('สองตัว (20 ชุด ไม่สนตำแหน่ง)')
    st.markdown(f"<div style='font-size:22px;color:red'>{pretty(two20,10)}</div>",
                unsafe_allow_html=True)
    st.caption(f"Hit≈{acc_two*100:.1f}%")

with c2:
    st.subheader('สามตัว (20 ชุด เต็ง-โต๊ด)')
    st.markdown(f"<div style='font-size:22px;color:red'>{pretty(three20,10)}</div>",
                unsafe_allow_html=True)
    st.caption(f"Hit≈{acc_three*100:.1f}%")

st.subheader('🚩 เลขเจาะ')
st.markdown(
    f"<div style='font-size:26px;color:red'>"
    f"สองตัว: {'  '.join(focus_two)}<br>สามตัว: {focus_three}</div>",
    unsafe_allow_html=True)

with st.expander('📊 วิธีคำนวณ Hit-rate'):
    st.markdown(
        '* **Walk-forward back-test** – ทำนายงวด n+1 จากข้อมูล 1…n แล้วเลื่อนหน้าต่าง\n'
        '* สองตัวล่าง: ตรง/กลับ + 2 ตัวท้ายบน\n'
        '* สามตัวบน: เต็ง-โต๊ด (ชุด 20 ตัว)\n'
        '* Boost: Top-3 digit ใน 10/20/30/40 งวด'
    )

st.caption('© 2025 ThaiLottoAI v3.3')
