"""Model inference + embeddings, Wikipedia, recommendations and care plans."""
import io, os
import numpy as np
import streamlit as st
import wikipedia
from PIL import Image
from data import WIKI, norm, pretty, profile

MODEL_PATH = "dog_breed_classifier_model_via_inceptionv3.h5"
IMAGES_DIR = "Images/"

SIM_HIGH, SIM_MID = 0.90, 0.80   # cosine-similarity bands; calibrate on your own registry


@st.cache_resource(show_spinner="Loading AI model...")
def get_model():
    """Returns a model that outputs (embedding, breed probabilities) in one forward pass.
    Works for Sequential models that were loaded from .h5 and never called (no .input defined)."""
    from tensorflow.keras import Input, Model
    from tensorflow.keras.layers import GlobalAveragePooling2D
    from tensorflow.keras.models import load_model
    m = load_model(MODEL_PATH, compile=False)
    inp = Input(shape=(299, 299, 3))
    try:
        x = inp
        for layer in m.layers[:-1]:       # everything except the final softmax layer
            x = layer(x)
        feat = GlobalAveragePooling2D()(x) if len(x.shape) == 4 else x
        return Model(inp, [feat, m.layers[-1](x)])
    except Exception:
        out = m(inp)                       # fallback: use the breed probabilities as the fingerprint
        return Model(inp, [out, out])


@st.cache_data
def get_breeds():
    return sorted(f.split("-", 1)[1] for f in os.listdir(IMAGES_DIR))  # same order as LabelEncoder

@st.cache_data(show_spinner=False, max_entries=64)
def analyze(img_bytes: bytes):
    """Returns (top-5 [(breed, prob)], L2-normalised embedding)."""
    from tensorflow.keras.applications.inception_v3 import preprocess_input
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((299, 299))
    arr = preprocess_input(np.expand_dims(np.asarray(img, dtype="float32"), 0))
    feat, probs = get_model().predict(arr, verbose=0)
    feat, probs = feat[0].astype("float32"), probs[0]
    feat /= (np.linalg.norm(feat) + 1e-9)
    idx = np.argsort(probs)[::-1][:5]
    names = get_breeds()
    return [(names[i], float(probs[i])) for i in idx], feat


@st.cache_data(show_spinner=False, ttl=86400)
def wiki_summary(raw, sentences=4):
    title = WIKI.get(norm(raw), pretty(raw))
    for q in (title, f"{title} (dog breed)", f"{title} (dog)"):
        try:
            return wikipedia.summary(q, sentences=sentences, auto_suggest=False)
        except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
            continue
        except Exception:
            return "Couldn't reach Wikipedia right now. Check your connection and try again."
    return "No Wikipedia summary found for this breed."

def care_plan(p):
    ex = {1:"20-30 min",2:"30-45 min",3:"45-60 min",4:"60-90 min",5:"90-120 min"}[p["energy"]]
    gr = {1:"Quick weekly brush",2:"Brush 1-2x a week",3:"Brush 2-3x a week",4:"Brush most days",5:"Daily brushing + pro grooming"}[p["grooming"]]
    food = {"Toy":"1/4 - 1 cup","Small":"1 - 1.5 cups","Medium":"1.5 - 2.5 cups","Large":"2.5 - 4 cups","Giant":"4 - 6 cups"}[p["size"]]
    tips = []
    if p["size"] in ("Large","Giant"): tips.append("Large breeds benefit from joint support and slow-growth puppy food. Ask your vet.")
    if p["size"] == "Toy": tips.append("Toy breeds need small, frequent meals and early dental care.")
    if p["energy"] >= 4: tips.append("Pair walks with mental work like puzzle feeders and training games.")
    if p["train"] <= 2: tips.append("Keep training short and reward-based; this breed can be independent.")
    tips.append("Food amounts are a rough guide. Follow your food's label and your vet's advice.")
    return ex, gr, food, tips

def compat_score(p, a):
    ideal = float(np.interp(a["hours"], [0.5, 1, 1.5, 2, 3], [1, 2, 3, 4, 5]))
    s_energy = 1 - abs(p["energy"] - ideal) / 4
    s_home = p["apt"] / 5 if a["home"] == "Apartment" else (0.85 + 0.15 * p["energy"] / 5 if a["yard"] else 0.8)
    s_kids = p["kids"] / 5 if a["kids"] else 1.0
    s_maint = 1 - (p["grooming"] - 1) / 4 * (a["lowmaint"] / 5)
    s_exp = {"Beginner": p["train"] / 5, "Some experience": 0.5 + p["train"] / 10, "Experienced": 1.0}[a["exp"]]
    w = [3, 2, 2 if a["kids"] else 0.5, 1 + a["lowmaint"] / 5, 1.5]
    vals = [s_energy, s_home, s_kids, s_maint, s_exp]
    score = 100 * sum(v * x for v, x in zip(vals, w)) / sum(w)
    names = ["Activity match", "Home fit", "Family fit", "Low upkeep", "Easy to train"]
    return score, dict(zip(names, vals))