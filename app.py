import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations

# ─────────────────── ATTEMPT IMPORT ML DEPENDENCY ───────────────────
try:
    from sklearn.neural_network import MLPClassifier
except ModuleNotFoundError:
    st.error(
        "**Error:** Library `scikit-learn` ยังไม่ถูกติดตั้งใน environment นี้\n"
        "กรุณาเพิ่ม `scikit-learn` ในไฟล์ requirements.txt ของคุณ แล้ว redeploy ใหม่"
    )
    st.stop()

# ─────────────────── CONFIG ───────────────────
st.set_page_config(page_title="ThaiLottoAI", page_icon="🎯", layout="centered")
st.title("🎯 ThaiLottoAI - Enhanced Next-Draw Predictor")

# ────────────────── SESSION STATE ──────────────────
if "history" not in st.session_state:
    st.session_state.history = []  # store tuples of (triple, pair)

# ────────────────── INPUT ──────────────────
st.markdown("วางผลย้อนหลัง **สามตัวบน เว้นวรรค สองตัวล่าง** ต่อเนื่องกันคนละบรรทัด เช่น `774 81`")
raw = st.text_area("📋 ข้อมูลย้อนหลัง", height=300,
                   placeholder="774 81\n227 06\n403 94\n...\n")

# ────────────────── PARSE & VALIDATE ──────────────────
draws = []
for idx, line in enumerate(raw.splitlines(), 1):
    parts = line.strip().split()
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        t, b = parts
        if len(t)==3 and len(b)==2:
            draws.append((t, b))
        else:
            st.warning(f"ข้ามบรรทัด {idx}: รูปแบบไม่ถูกต้อง → {line}")
    elif line.strip():
        st.warning(f"ข้ามบรรทัด {idx}: ไม่พบข้อมูลที่ใช้ได้ → {line}")

if len(draws) < 60:
    st.info("กรุณาป้อนข้อมูลย้อนหลังอย่างน้อย 60 งวด เพื่อความแม่นยำสูงสุด")
    st.stop()

# update session history
st.session_state.history = draws

# ────────────────── PREPROCESS ──────────────────
triples = [int(t) for t, _ in draws]
pairs = [int(b) for _, b in draws]

# ────────────────── WEIGHTED FREQUENCY PREDICTION ───────────────────
def weighted_freq(sequence, window, decay=0.85):
    seq = sequence[-window:]
    weights = [decay**i for i in range(len(seq)-1, -1, -1)]
    cnt = defaultdict(float)
    for val, w in zip(seq, weights):
        cnt[val] += w
    return sorted(cnt.items(), key=lambda x: -x[1])

def predict_weighted_next(seq, window, topk, exclude_count=2):
    freq = weighted_freq(seq, window)
    hist_count = Counter(seq)
    preds = []
    for val, _ in freq:
        if hist_count[val] < exclude_count:
            preds.append(val)
        if len(preds) == topk:
            break
    return preds

# ────────────────── ML-BASED PREDICTION ───────────────────
def ml_predict_seq(sequence, window, topk):
    X, y = [], []
    for i in range(len(sequence)-window):
        X.append(sequence[i:i+window])
        y.append(sequence[i+window])
    X, y = np.array(X), np.array(y)
    if len(X) < window*2:
        return []
    model = MLPClassifier(hidden_layer_sizes=(64,32), max_iter=2000, random_state=42)
    model.fit(X, y)
    probs = model.predict_proba([sequence[-window:]])[0]
    classes = model.classes_
    top_idx = np.argsort(probs)[-topk:][::-1]
    return [classes[i] for i in top_idx]

# ────────────────── ENSEMBLE METHODS ───────────────────
win_w, win_ml = 100, 60
k_pairs, k_triples = 4, 2
w_triples = predict_weighted_next(triples, win_w, k_triples)
w_pairs = predict_weighted_next(pairs, win_w, k_pairs)
ml_triples = ml_predict_seq(triples, win_ml, k_triples)
ml_pairs = ml_predict_seq(pairs, win_ml, k_pairs)

def merge_preds(w, m, k):
    inter = [v for v in w if v in m]
    merged = inter + [v for v in w if v not in inter] + [v for v in m if v not in inter]
    return merged[:k]

next_triples = merge_preds(w_triples, ml_triples, k_triples)
next_pairs = merge_preds(w_pairs, ml_pairs, k_pairs)

# ────────────────── DISPLAY RESULTS ───────────────────
st.header("📊 ผลทำนายงวดถัดไป 📊")
st.subheader("🔴 สามตัวบน (2 ชุด)")
st.write([f"{v:03d}" for v in next_triples])
st.subheader("🟢 สองตัวล่าง (4 ชุด)")
st.write([f"{v:02d}" for v in next_pairs])

st.caption("สูตร: Weighted Frequency + ML Ensemble | พัฒนาโดย ThaiLottoAI")
