# app_thailotto_clean.py
# -*- coding: utf-8 -*-
import streamlit as st
from collections import Counter, defaultdict
import re, random
import pandas as pd

# ===================== PAGE =====================
st.set_page_config(
    page_title="ThaiLotto",
    page_icon="icon.png",
    layout="centered"
)

# ===================== STYLE (พื้นน้ำเงิน ตัวอักษรขาว, เลขสีแดง) =====================
st.markdown("""
<style>
:root{
  --thai-blue:#00247D;
  --thai-red:#FF2A2A;
  --thai-white:#FFFFFF;
}
/* ซ่อน Top bar / Footer ของ Streamlit */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

.stApp { background: var(--thai-blue); color: var(--thai-white); }
.block-container{ max-width: 980px; }
.title { color: var(--thai-white); font-weight: 900; font-size: 2.0rem; }
.subtitle { color: var(--thai-white); opacity:.95; margin-top:2px; }

.card{
  background: rgba(255,255,255,0.06); border:2px solid rgba(255,255,255,0.25);
  border-radius:16px; padding:14px 16px; margin:12px 0 16px 0;
  box-shadow:0 8px 20px rgba(0,0,0,.12);
}
.heading{ color: var(--thai-white); font-weight:900; font-size:1.1rem; margin-bottom:6px; }

textarea, .stTextInput input, .stSelectbox [data-baseweb="select"] div{
  color: var(--thai-white) !important;
}
.stTextArea textarea{ background: rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.25); }

.num-xl,.num-lg,.num-md{ color: var(--thai-red); font-weight:900; line-height:1.25; word-break: break-word; }
.num-xl{ font-size:2.6rem; }
.num-lg{ font-size:2.2rem; }
.num-md{ font-size:2.0rem; }

.kbd{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono","Courier New",monospace;
  background: rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.35); border-radius:8px; padding:2px 8px;
  color: var(--thai-white);
}

.footer { text-align:center; margin: 18px 0 8px 0; color: var(--thai-white); font-weight:700; }
.stDownloadButton button{
  background: rgba(255,255,255,0.12); border:2px solid rgba(255,255,255,0.5);
  color: var(--thai-white); font-weight:800; border-radius:10px;
}
.copybtn{
  background: rgba(255,255,255,0.12); border:2px solid rgba(255,255,255,0.5);
  color: var(--thai-white); font-weight:800; border-radius:10px; padding:6px 10px; cursor:pointer;
}
</style>
""", unsafe_allow_html=True)

# ===================== HEADER =====================
st.markdown('<div class="title">ThaiLotto</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">วางผลย้อนหลังไม่น้อยกว่า10 งวด: '
            '<span class="kbd">สามตัวบน</span> (วรรคหรือแท็บ 1 ครั้ง) '
            '<span class="kbd">สองตัวล่าง</span> ต่อบรรทัด</div>', unsafe_allow_html=True)

# ===================== INPUTS =====================
ph = "เช่น\n774\t81\n227\t06\n403\t94\n938\t98\n446\t77"
raw = st.text_area("ผลย้อนหลัง", height=220, placeholder=ph)

mode = st.selectbox("โหมด", ["ครบตามเป้า", "คัดเลข"])  # คงไว้ 2 โหมด
k = st.number_input("ใช้ย้อนหลัง (งวด)", min_value=10, max_value=50, value=12, step=1)

# ===================== PARSE =====================
def parse_rows(text):
    rows=[]
    for line in text.strip().splitlines():
        if not line.strip(): continue
        parts=re.split(r"\s+", line.strip())
        if len(parts)>=2 and parts[0].isdigit() and parts[1].isdigit():
            top3=parts[0].zfill(3); two=parts[1].zfill(2)
            if len(top3)==3 and len(two)==2:
                rows.append({"top3":top3,"two":two})
    return rows

draws = parse_rows(raw)
st.write(f"อ่านได้ **{len(draws)}** งวด")
if len(draws) < k:
    st.stop()

# ===================== UTIL =====================
def mod10_digits(s): return sum(int(c) for c in s) % 10
def freq_digits_in(seq): return Counter("".join(seq))
def dedupe_pairs_reversed(pairs):
    seen=set(); out=[]
    for p in pairs:
        key=tuple(sorted(p))
        if key not in seen:
            seen.add(key); out.append(p)
    return out
def dedupe_triple_permutation(tris):
    seen=set(); out=[]
    for t in tris:
        key="".join(sorted(t))
        if key not in seen:
            seen.add(key); out.append(t)
    return out

def compute_features(draws, k):
    window=draws[-k:]
    latest3 = window[-1]["top3"]
    latest2 = window[-1]["two"]
    A = mod10_digits(latest3)
    B = int(latest2[-1])
    cnt2 = freq_digits_in([d["two"] for d in window])
    cnt3 = freq_digits_in([d["top3"] for d in window])
    F2 = int(max(cnt2.items(), key=lambda x:x[1])[0])
    F3 = int(max(cnt3.items(), key=lambda x:x[1])[0])
    return window, latest3, latest2, A, B, cnt2, cnt3, F2, F3

# ===================== BUILDERS =====================
def build_singles(draws, k, need=3, pick=1, filtered=False):
    window, latest3, latest2, A, B, cnt2, cnt3, F2, F3 = compute_features(draws, k)
    T5 = (sum(int(x[-1]) for x in [d["two"] for d in window]) + sum(int(c) for c in latest3)) % 10
    scores=defaultdict(float)
    for d in [A, B, F2, F3, T5]: scores[d]+=1.0
    scores[A]+=0.5; scores[B]+=0.3; scores[F2]+=0.4; scores[F3]+=0.4; scores[T5]+=0.2
    for dstr,c in cnt2.items(): scores[int(dstr)] += 0.04*c
    for dstr,c in cnt3.items(): scores[int(dstr)] += 0.03*c
    ranked=[str(k) for k,_ in sorted(scores.items(), key=lambda x:(-x[1], x[0]))]
    if filtered:
        pool = ranked[:max(3, need)]
        return [pool[0]]  # คัด 1 ตัวแบบกำหนดแน่นอน (ไม่สุ่ม)
    return ranked[:need]

def build_pairs(draws, k, need=37, pick=5, filtered=False):
    window, latest3, latest2, A, B, cnt2, cnt3, F2, F3 = compute_features(draws, k)
    w10=lambda x:(x+10)%10
    neighbors=[w10(B+i) for i in [-2,-1,0,1,2]]
    pool=set([A,F2,F3]+neighbors+[int(latest2[0]), int(latest2[1])])

    hist2=[d["two"] for d in window]
    pair_scores=defaultdict(float); cand=set()
    for d in pool:
        for e in pool:
            cand.add(f"{d}{e}")

    last2 = latest2
    for p in cand:
        a,b=int(p[0]),int(p[1])
        pair_scores[p]+= 0.9*hist2.count(p)
        pair_scores[p]+= 0.06*cnt2.get(str(a),0) + 0.06*cnt2.get(str(b),0)
        h=(p[0]!=last2[0])+(p[1]!=last2[1])
        pair_scores[p]+= {0:0.35, 1:0.2, 2:0.0}[h]

    ranked=[p for p,_ in sorted(pair_scores.items(), key=lambda x:(-x[1], x[0]))]
    ranked = dedupe_pairs_reversed(ranked)
    if filtered:
        return ranked[:pick]  # คัด 5 ตัวบนสุด
    return ranked[:need]

def build_triples(draws, k, need=66, pick=5, filtered=False, two_best=None):
    window, latest3, latest2, A, B, cnt2, cnt3, F2, F3 = compute_features(draws, k)
    if two_best is None:
        base = build_pairs(draws, k, need=1)[0]
    else:
        base = two_best
    missing=[str(d) for d in range(10) if str(d) not in cnt3]
    rare = missing[0] if missing else min([str(d) for d in range(10)], key=lambda d: (cnt3.get(d,0), int(d)))
    specials=['3','4','6','7','8']
    prefix_pool = [rare] + [x for x in specials if x!=rare] + [str(A), str(F3)] + list(set(latest3))

    def score(t):
        freq = sum(cnt3.get(ch,0) for ch in t)
        ca, cb = Counter(t), Counter(latest3)
        sim = sum(min(ca[d], cb[d]) for d in set(ca)|set(cb))
        bonus = 0.3 if t[0] in [str(A), str(F3), rare] else 0.0
        return 0.55*freq + 0.35*sim + bonus

    cand=[f"{p}{base}" for p in prefix_pool]
    ranked = sorted(dedupe_triple_permutation(cand), key=lambda x:(-score(x), x))
    if filtered:
        return ranked[:pick]  # คัด 5 ชุดบนสุด
    return ranked[:need]

# ===================== BUILD (ตามโหมด) =====================
if mode == "ครบตามเป้า":
    singles = build_singles(draws, k, need=3, filtered=False)
    pairs   = build_pairs(draws, k, need=37, filtered=False)
    triples = build_triples(draws, k, need=66, filtered=False)
else:
    singles = build_singles(draws, k, need=3, pick=1, filtered=True)
    pairs   = build_pairs(draws, k, need=37, pick=5, filtered=True)
    base2 = pairs[0] if pairs else None
    triples = build_triples(draws, k, need=66, pick=5, filtered=True, two_best=base2)

# ===================== OUTPUT =====================
st.markdown(f'''
<div class="card">
  <div class="heading">เด่น — 3 บน + 2 ล่าง {("(คัด 1 ตัว)" if mode=="คัดเลข" else "(3 ตัว)")}</div>
  <div class="num-xl">{"  ".join(singles)}</div>
</div>
''', unsafe_allow_html=True)

st.markdown(f'''
<div class="card">
  <div class="heading">สองตัว (บน–ล่าง) {("(คัด 5 คู่ | ตัดสลับซ้ำ)" if mode=="คัดเลข" else "(37 คู่ | ตัดสลับซ้ำ)")}</div>
  <div class="num-lg">{"  ".join(pairs)}</div>
</div>
''', unsafe_allow_html=True)

st.markdown(f'''
<div class="card">
  <div class="heading">เจาะลาก — 3 ตัวบน {("(คัด 5 ชุด | ตัดสลับซ้ำ)" if mode=="คัดเลข" else "(66 ชุด | ตัดสลับซ้ำ)")}</div>
  <div class="num-md">{"  ".join(triples)}</div>
</div>
''', unsafe_allow_html=True)

# ===================== DOWNLOAD & CLIPBOARD =====================
def export_text():
    lines = []
    lines.append(f"เด่น: {' '.join(singles)}")
    lines.append(f"สองตัว: {' '.join(pairs)}")
    lines.append(f"เจาะลาก: {' '.join(triples)}")
    return "\n".join(lines)

def export_csv_df():
    rows=[]
    for d in singles: rows.append({"type":"single","value":d})
    for p in pairs:   rows.append({"type":"pair","value":p})
    for t in triples: rows.append({"type":"triple","value":t})
    return pd.DataFrame(rows)

st.markdown('<div class="card"><div class="heading">ดาวน์โหลด / คัดลอก</div>', unsafe_allow_html=True)
dcol1, dcol2, dcol3 = st.columns([1,1,2])
with dcol1:
    st.download_button("ดาวน์โหลด TXT", data=export_text().encode("utf-8"),
                       file_name="ThaiLotto.txt", mime="text/plain")
with dcol2:
    csv_df = export_csv_df()
    st.download_button("ดาวน์โหลด CSV", data=csv_df.to_csv(index=False).encode("utf-8"),
                       file_name="ThaiLotto.csv", mime="text/csv")
with dcol3:
    clip_payload = export_text().replace('"','\\"').replace("\n","\\n")
    st.markdown(f'<button class="copybtn" onclick="navigator.clipboard.writeText(`{clip_payload}`)">คัดลอกคลิปบอร์ด</button>',
                unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ===================== BACKTEST (คงไว้ตามที่ขอ) =====================
def eval_single_ok(pred_singles, top3, two2):
    digits = list(top3) + list(two2)
    return any(d in digits for d in pred_singles)
def eval_pair_ok(pred_pairs, top3, two2):
    f2 = top3[-2:]; b2 = two2
    ok=lambda p,t: (p==t or p[::-1]==t)
    return any(ok(p,f2) or ok(p,b2) for p in pred_pairs)
def eval_triple_ok(pred_tris, top3):
    s = "".join(sorted(top3))
    return any("".join(sorted(t))==s for t in pred_tris)

if st.toggle("แสดงแบ็กเทสต์กับประวัติย้อนหลัง", value=False):
    hits_s=hits_p=hits_t=0; total=0
    for idx in range(int(k), len(draws)):
        hist = draws[:idx]
        singles_bt = build_singles(hist, k=int(min(k, len(hist))), need=3, filtered=False)
        pairs_bt   = build_pairs(hist,   k=int(min(k, len(hist))), need=37, filtered=False)
        triples_bt = build_triples(hist, k=int(min(k, len(hist))), need=66, filtered=False)
        nxt = draws[idx]
        hits_s += int(eval_single_ok(singles_bt, nxt["top3"], nxt["two"]))
        hits_p += int(eval_pair_ok(pairs_bt, nxt["top3"], nxt["two"]))
        hits_t += int(eval_triple_ok(triples_bt, nxt["top3"]))
        total += 1
    res = pd.DataFrame({
        "หมวด":["เด่น (3 บน + 2 ล่าง | 3 ตัว)", "สองตัว (บน–ล่าง | 37 คู่)", "เจาะลาก (3 ตัวบน | 66 ชุด)"],
        "ถูก(ครั้ง)":[hits_s, hits_p, hits_t],
        "ทั้งหมด":[total,total,total],
    })
    res["เปอร์เซ็นต์(%)"] = (res["ถูก(ครั้ง)"]/res["ทั้งหมด"]*100).round(2)
    st.markdown('<div class="card"><div class="heading">ผลแบ็กเทสต์</div>', unsafe_allow_html=True)
    st.dataframe(res, hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ===================== FOOTER (ตามคำสั่ง) =====================
st.markdown('<div class="footer">ลิขสิทธิ์@Phatarit#2025</div>', unsafe_allow_html=True)
