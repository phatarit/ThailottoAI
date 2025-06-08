import streamlit as st
import pandas as pd
from collections import Counter, defaultdict
from itertools import permutations, combinations

# ────────── SETUP ──────────
st.set_page_config(page_title='ThaiLottoAI v3.1', page_icon='🎯')
st.title('🎯 ThaiLottoAI – 20-Combo Mode + Focus Picks')

# ────────── INPUT ──────────
st.markdown('วางข้อมูลย้อนหลัง: **สามตัวบน เว้นวรรค สองตัวล่าง** เช่น `774 81`')
raw = st.text_area('📋 ข้อมูลย้อนหลัง', height=250)

extra = []
with st.expander('➕ เพิ่มข้อมูลทีละงวด'):
    for i in range(1, 6):
        row = st.text_input(f'งวด #{i}', key=f'row_{i}')
        if row:
            extra.append(row)

lines = [l for l in (raw.splitlines() + extra) if l.strip()]
draws = []
for idx, line in enumerate(lines, 1):
    try:
        top, bottom = line.split()
        if len(top) == 3 and len(bottom) == 2 and top.isdigit() and bottom.isdigit():
            draws.append((top, bottom))
        else:
            st.warning(f'ข้ามบรรทัด {idx}: รูปแบบผิด → {line}')
    except ValueError:
        st.warning(f'ข้ามบรรทัด {idx}: ไม่พบเว้นวรรค → {line}')

if len(draws) < 40:
    st.info('⚠️ ต้องมีข้อมูล ≥ 40 งวด')
    st.stop()

df = pd.DataFrame(draws, columns=['สามตัวบน', 'สองตัวล่าง'])
st.success(f'โหลด {len(df)} งวด')
st.dataframe(df, use_container_width=True)

# ────────── HELPER ──────────
def hot_digits(hist, win, n=3):
    seg = hist[-win:] if len(hist) >= win else hist
    return [d for d, _ in Counter(''.join(''.join(p) for p in seg)).most_common(n)]

def run_digits(hist): return list(hist[-1][1])
def sum_mod(hist): return str(sum(map(int, hist[-1][0])) % 10)

hot10 = hot_digits(draws, 10)
hot20 = hot_digits(draws, 20)
hot30 = hot_digits(draws, 30)
hot40 = hot_digits(draws, 40)

# ────────── FORMULAS ──────────
def exp_hot(hist, win=27):
    sc = Counter()
    recent = hist[-win:]
    for i, (t, b) in enumerate(reversed(recent)):
        w = 0.8 ** i
        for d in t + b:
            sc[d] += w
    for d in hot10 + hot20 + hot30 + hot40:
        sc[d] += 0.3
    return max(sc, key=sc.get)

def build_trans(hist):
    M = defaultdict(Counter)
    for p, c in zip(hist[:-1], hist[1:]):
        M[p[1]][c[1]] += 1
    return M

def markov_20(hist):
    trans = build_trans(hist)
    last = hist[-1][1]
    base = [p for p, _ in trans[last].most_common(20)]

    # เติมคู่ hot (ไม่ซ้ำ)
    boost = set(hot10 + hot20 + hot30 + hot40)
    for a, b in combinations(boost, 2):
        for p in (a + b, b + a):
            if p not in base:
                base.append(p)
            if len(base) == 20:
                return base
    return base[:20]

def hybrid_20(hist, pool_size=12, k=20):
    pool = run_digits(hist) + [sum_mod(hist)] \
           + hot_digits(hist, 5, 3) + hot_digits(hist, len(hist), 3) \
           + hot10 + hot20 + hot30 + hot40
    pool = list(dict.fromkeys(pool))[:pool_size]

    score = Counter()
    for i, (t, b) in enumerate(hist[-30:]):
        w = 1 - i / 30 * 0.9
        for d in t + b:
            score[d] += w

    perms = [''.join(p) for p in permutations(pool, 3) if len(set(p)) == 3]
    perms.sort(key=lambda x: -(score[x[0]] + score[x[1]] + score[x[2]]))
    return perms[:k]

# ── WALK-FORWARD (ประมาณ % ถูก) ──
def walk(hist, pred, hit, start):
    h = t = 0
    for i in range(start, len(hist)):
        if hit(pred(hist[:i]), hist[i]): h += 1
        t += 1
    return h / t if t else 0

hit1 = lambda p, a: p in a[0] or p in a[1]
hit2 = lambda L, a: a[1] in L or a[1][::-1] in L
hit3 = lambda L, a: a[0] in L

acc_single = walk(draws, exp_hot, hit1, 27)
acc_two = walk(draws, markov_20, hit2, 40)
acc_three = walk(draws, hybrid_20, hit3, 40)

# ────────── PREDICT NEXT ───────────
single = exp_hot(draws)
two20  = markov_20(draws)

three20 = hybrid_20(draws)

# ใส่ 2 ตัวท้ายของ 20 ชุดบนเข้าไปในชุดล่าง (ไม่ซ้ำ)
tail_from_top = {num[1:] for num in three20}
for t in tail_from_top:
    if t not in two20:
        two20.append(t)
two20 = two20[:20]

# เลข “เจาะ” 5 ชุดสองตัว + 1 ชุดสามตัว (ใช้อันดับต้น)
focus_two = two20[:5]
focus_three = three20[0]

# ────────── DISPLAY ───────────
st.header('🔮 คาดการณ์งวดถัดไป')

st.markdown(
    f"<div style='font-size:48px; color:red; text-align:center;'>ตัวเด่น: {single}</div>",
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)
with c1:
    st.subheader('สองตัวล่าง / ท้ายบน (20)')
    st.markdown(
        f"<div style='font-size:22px; color:red;'>{'  '.join(two20)}</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Hit-rate ≈ {acc_two*100:.1f}%")

with c2:
    st.subheader('สามตัวบน (20)')
    st.markdown(
        f"<div style='font-size:22px; color:red;'>{'  '.join(three20)}</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Hit-rate ≈ {acc_three*100:.1f}%")

# --- Focus picks ---
st.subheader('🚩 เลขเจาะ (เน้น)')
st.markdown(
    f"<div style='font-size:28px; color:red;'>"
    f"สองตัว: {'  '.join(focus_two)}<br>"
    f"สามตัว: {focus_three}"
    f"</div>",
    unsafe_allow_html=True,
)

with st.expander('📊 วิธีคำนวณเปอร์เซ็นย้อนหลัง'):
    st.markdown(
        """
* **Walk-forward back-test** – ทำนายงวดถัดไปจากข้อมูลก่อนหน้า แล้วเลื่อนหน้าต่าง  
* **สองตัวล่าง** นับถูกทั้งเลขตรงและกลับ (AB/BA)  
* Boost: รวม Top-3 digit ใน 4 หน้าต่าง (10/20/30/40) และเพิ่ม 2 ตัวท้ายบนเข้า list ล่าง
        """
    )

st.caption('© 2025 ThaiLottoAI v3.1')
