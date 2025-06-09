import streamlit as st
import pandas as pd
from collections import Counter, defaultdict
from itertools import combinations

# ─────────────────── CONFIG ───────────────────
st.set_page_config(page_title="ThaiLottoAI", page_icon="🎯", layout="centered")
st.title("🎯 ThaiLottoAI")

# ────────────────── SESSION STATE ──────────────────
if "history_raw" not in st.session_state:
    st.session_state.history_raw = ""
if "premium" not in st.session_state:
    st.session_state.premium = False

# ────────────────── INPUT ──────────────────
st.markdown("วางผลย้อนหลัง **สามตัวบน เว้นวรรค สองตัวล่าง** ต่อเนื่องกันคนละบรรทัด เช่น `774 81`")
raw = st.text_area("📋 ข้อมูลย้อนหลัง", value=st.session_state.history_raw, height=250)

col_save, col_clear = st.columns(2)
with col_save:
    if st.button("💾 บันทึกข้อมูล"):
        st.session_state.history_raw = raw
        st.success("บันทึกข้อมูลเรียบร้อย ✔")
with col_clear:
    if st.button("🗑 ล้างข้อมูลที่บันทึก"):
        st.session_state.history_raw = ""
        st.success("ล้างข้อมูลแล้ว")

# ────────────────── PARSE DRAWS ──────────────────
extra_rows = []

draws = []
for idx, line in enumerate(raw.splitlines(), 1):
    try:
        t, b = line.split()
        if len(t) == 3 and len(b) == 2 and t.isdigit() and b.isdigit():
            draws.append((t, b))
        else:
            st.warning(f"ข้ามบรรทัด {idx}: รูปแบบผิด → {line}")
    except ValueError:
        if line.strip():
            st.warning(f"ข้ามบรรทัด {idx}: ไม่พบช่องว่าง → {line}")

if len(draws) < 40:
    st.info("⚠️ ต้องมีข้อมูล ≥ 40 งวด")
    st.stop()

st.dataframe(pd.DataFrame(draws, columns=["สามตัวบน", "สองตัวล่าง"]), use_container_width=True)

# ────────────────── HELPER FUNCTIONS ──────────────────

def hot_digits(hist, win, n=3):
    seg = hist[-win:] if len(hist) >= win else hist
    return [d for d, _ in Counter("".join("".join(x) for x in seg)).most_common(n)]

def pretty(lst, per_line=10):
    chunk = ["  ".join(lst[i : i + per_line]) for i in range(0, len(lst), per_line)]
    return "<br>".join(chunk)

def unordered2(p):
    return "".join(sorted(p))

def unordered3(t):
    return "".join(sorted(t))

def run_digits(hist):
    return list(hist[-1][1])

def sum_mod(hist):
    return str(sum(map(int, hist[-1][0])) % 10)

hot10 = hot_digits(draws, 10)
hot20 = hot_digits(draws, 20)
hot30 = hot_digits(draws, 30)
hot40 = hot_digits(draws, 40)

# ────────────────── CORE ALGORITHMS ──────────────────

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
    pool = (
        run_digits(hist)
        + [sum_mod(hist)]
        + hot_digits(hist, 5, 3)
        + hot_digits(hist, len(hist), 3)
        + hot10
        + hot20
        + hot30
        + hot40
    )
    pool = list(dict.fromkeys(pool))[:pool_sz]

    score = Counter()
    for i, (t, b) in enumerate(hist[-30:]):
        w = 1 - i / 30 * 0.9
        for d in t + b:
            score[d] += w

    combos = {"".join(sorted(c)) for c in combinations(pool, 3)}
    combos = sorted(combos, key=lambda x: -(score[x[0]] + score[x[1]] + score[x[2]]))
    return combos[:k]

# ────────────────── BACK‑TEST HIT RATE ──────────────────

def walk(hist, pred_fn, hit_fn, start):
    hit = tot = 0
    for i in range(start, len(hist)):
        if hit_fn(pred_fn(hist[:i]), hist[i]):
            hit += 1
        tot += 1
    return hit / tot if tot else 0.0

hit_two = (
    lambda preds, act: unordered2(act[1]) in preds or unordered2(act[0][1:]) in preds
)

def hit_three(preds, act):
    return unordered3(act[0]) in preds

acc_two = walk(draws, markov20_pairs, hit_two, 40)
acc_three = walk(draws, hybrid20_combos, hit_three, 40)

# ────────────────── PREDICT NEXT ──────────────────

single = exp_hot(draws)
two20 = markov20_pairs(draws)
three20 = hybrid20_combos(draws)

# รวม 2 ตัวท้ายบนเข้าชุดล่าง
for tail in {unordered2(t[1:]) for t, _ in [draws[-1]]}:
    if tail not in two20:
        two20.append(tail)

two20 = two20[:20]

focus_two = two20[:5]
focus_three = three20[:3]

# ────────────────── PREMIUM PAYMENT ──────────────────

st.header("🏆 อัปเกรดเป็น Premium 59 บาท")
st.image("https://promptpay.io/0869135982/59.png", width=220)
slip = st.file_uploader("แนบสลิปชำระเงิน", type=["jpg", "jpeg", "png", "pdf"])

if slip is not None:
    st.success("ได้รับสลิปแล้ว กรุณาให้แอดมินตรวจสอบ ⏳")

    with st.expander("🔐 สำหรับแอดมินเท่านั้น"):
        with st.form("admin_unlock"):
            admin_pass = st.text_input("รหัสแอดมิน", type="password")
            unlock = st.form_submit_button("ปลดล็อค Premium")
            if unlock:
                if admin_pass == "Mnopphata#2":
                    st.session_state.premium = True
                    st.success("✅ Premium ปลดล็อคแล้ว!")
                else:
                    st.error("รหัสผิด ❌")

# ────────────────── DISPLAY RESULTS ──────────────────

if st.session_state.premium:
    # PREMIUM VIEW
    st.markdown(
        f"<div style='font-size:44px;color:red;text-align:center'>ตัวเด่น: {single}</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("สองตัว (20 ชุด ไม่สนตำแหน่ง)")
        st.markdown(
            f"<div style='font-size:22px;color:red'>{pretty(two20,10)}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Hit≈{acc_two*100:.1f}%")

    with c2:
        st.subheader("สามตัว (20 ชุด เต็ง‑โต๊ด)")
        st.markdown(
            f"<div style='font-size:22px;color:red'>{pretty(three20,10)}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Hit≈{acc_three*100:.1f}%")

    st.subheader("🚩 เลขเจาะ (Premium)")
    st.markdown(
        f"<div style='font-size:26px;color:red'>สองตัว: {'  '.join(focus_two)}<br>"
        f"สามตัว: {'  '.join(focus_three)}</div>",
        unsafe_allow_html=True,
    )
else:
    # FREE VIEW
    top2 = hot_digits(draws, 10, 2)
    main, runner = top2[0], (top2[1] if len(top2) > 1 else "-")

    st.markdown(
        f"<div style='font-size:40px;color:red;text-align:center'>ตัวเด่น: {main}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:32px;color:orange;text-align:center'>ตัวรอง: {runner}</div>",
        unsafe_allow_html=True,
    )

    st.subheader("🚩 เลขเจาะ (Free Preview)")
    st.markdown(
        f"<div style='font-size:24px;color:red'>สองตัว (5 ชุด): {'  '.join(focus_two)}<br>"
        f"สามตัว (3 ชุด): {'  '.join(focus_three)}</div>",
        unsafe_allow_html=True,
    )

    st.info("ปลดล็อค Premium เพื่อดูชุดตัวเลขเต็ม 20 ชุด และสถิติย้อนหลังทั้งหมด!")

# ────────────────── FOOTER ──────────────────
st.caption("© 2025 ThaiLottoAI")
