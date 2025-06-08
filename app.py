import streamlit as st, pandas as pd
from collections import Counter, defaultdict
from itertools import permutations, combinations, islice

# ───── Helper ─────
def hot_digits(hist, win, n=3):
    seg = hist[-win:] if len(hist) >= win else hist
    return [d for d,_ in Counter("".join("".join(x) for x in seg)).most_common(n)]

def unordered2(num):              # '97' → '79'
    return "".join(sorted(num))

def unordered3(num):              # '693' → '369'
    return "".join(sorted(num))

def run_digits(hist): return list(hist[-1][1])
def sum_mod(hist):  return str(sum(map(int, hist[-1][0])) % 10)

# ───── Core predictors ─────
def markov20_pairs(hist, k=20):
    trans = defaultdict(Counter)
    for (pt, pb), (ct, cb) in zip(hist[:-1], hist[1:]):
        trans[unordered2(pb)][unordered2(cb)] += 1
    last = unordered2(hist[-1][1])
    base = [p for p,_ in trans[last].most_common(k)]
    boost = set(hot_digits(hist, 20, 3) + hot_digits(hist, 40, 3))
    for a, b in combinations(boost, 2):
        p = unordered2(a+b)
        if p not in base:
            base.append(p)
        if len(base) == k: break
    return base[:k]

def hybrid20_combos(hist, k=20, pool_sz=12):
    pool = run_digits(hist) + [sum_mod(hist)] \
         + hot_digits(hist,5,3) + hot_digits(hist,len(hist),3) \
         + hot_digits(hist,20,3) + hot_digits(hist,40,3)
    pool = list(dict.fromkeys(pool))[:pool_sz]
    score = Counter()
    for i,(t,b) in enumerate(hist[-30:]):
        w = 1 - i/30*0.9
        for d in t+b: score[d]+=w
    combos = {"".join(sorted(c)) for c in combinations(pool,3)}
    combos = sorted(combos, key=lambda x: -(score[x[0]]+score[x[1]]+score[x[2]]))
    return list(islice(combos, k))

# ───── Walk-forward evaluator (unordered) ─────
def walk(hist, pred_fn, hit_fn, start):
    hit = tot = 0
    for i in range(start, len(hist)):
        if hit_fn(pred_fn(hist[:i]), hist[i]):
            hit += 1
        tot += 1
    return hit/tot if tot else 0.0

hit_two = lambda preds, act: unordered2(act[1]) in preds or \
                             unordered2(act[0][1:]) in preds     # รวมท้ายบน
hit_three = lambda preds, act: unordered3(act[0]) in preds

# ───── Data ingest (เหมือนเดิม) ─────
st.set_page_config(page_title="ThaiLottoAI v3.2", page_icon="🎯")
st.title("🎯 ThaiLottoAI – Unordered Booster")

raw = st.text_area("วางข้อมูลย้อนหลัง: 3 ตัวบน เว้นวรรค 2 ตัวล่าง", height=250)
draws=[]
for ln in raw.splitlines():
    try:
        t,b=ln.split(); 
        if len(t)==3 and len(b)==2: draws.append((t,b))
    except: pass
if len(draws)<40: st.stop()

# ───── Predict & stats ─────
two20   = markov20_pairs(draws)
three20 = hybrid20_combos(draws)

# focus picks
focus_two   = two20[:5]
focus_three = three20[0]

# hit-rate ย้อนหลัง
acc_two   = walk(draws, markov20_pairs,   hit_two,   40)
acc_three = walk(draws, hybrid20_combos,  hit_three, 40)

# ───── Display ─────
st.markdown(f"<div style='font-size:38px;color:red;text-align:center'>"
            f"ตัวเด่น: {hot_digits(draws,27,1)[0]}</div>", unsafe_allow_html=True)

c1,c2=st.columns(2)
with c1:
    st.subheader("สองตัว (20 ชุด ไม่สนตำแหน่ง)")
    st.markdown(f"<span style='font-size:22px;color:red'>{'  '.join(two20)}</span>",
                unsafe_allow_html=True)
    st.caption(f"Hit≈{acc_two*100:.1f}%")
with c2:
    st.subheader("สามตัว (20 ชุด เต็ง-โต๊ด)")
    st.markdown(f"<span style='font-size:22px;color:red'>{'  '.join(three20)}</span>",
                unsafe_allow_html=True)
    st.caption(f"Hit≈{acc_three*100:.1f}%")

st.subheader("🚩 เลขเจาะ")
st.markdown(f"<span style='font-size:26px;color:red'>สองตัว: {'  '.join(focus_two)}<br>"
            f"สามตัว: {focus_three}</span>", unsafe_allow_html=True)
