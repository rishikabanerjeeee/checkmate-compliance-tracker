# api/match_engine.py

import os
import re
import numpy as np
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer, util
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import httpx
import json

# --- Config ---
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

THRESH_STRONG = 0.75
THRESH_PARTIAL = 0.5
THRESH_WEAK = 0.25
TOP_K = 1  # How many top matches per control clause

STOPWORDS = set(stopwords.words("english"))
USE_LLaMA = True
MAX_LLaMA_ANALYSIS = st.session_state.get("max_llama_clauses", 3)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLAMA_MODEL = "llama3-70b-8192"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


@st.cache_data(show_spinner=False)
def batch_encode(texts):
    return model.encode(texts, convert_to_tensor=True, show_progress_bar=False)


def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip())


def extract_words(text, remove_stopwords=True):
    words = set(re.findall(r'\w+', text.lower()))
    return words - STOPWORDS if remove_stopwords else words


def classify_status(score):
    if score >= THRESH_STRONG:
        return "Strong Match"
    elif score >= THRESH_PARTIAL:
        return "Partial Match"
    elif score >= THRESH_WEAK:
        return "Weak Match"
    else:
        return "Unmatched"


def parse_llama_response(response_text):
    result = {
        "rewrite": "—",
        "overlap": "—",
        "gap": "—",
        "reason": "—",
        "risk": "—",
        "fine": "—"
    }
    try:
        # Simple line-based breakdown
        lines = response_text.split("\n")
        for line in lines:
            l = line.lower()
            if "overlap" in l:
                result["overlap"] = line.split(":")[-1].strip()
            elif "gap" in l or "missing" in l:
                result["gap"] = line.split(":")[-1].strip()
            elif "rewrite" in l:
                result["rewrite"] = line.split(":", 1)[-1].strip()
            elif "risk" in l:
                result["risk"] = line.split(":", 1)[-1].strip()
            elif "fine" in l:
                result["fine"] = line.split(":", 1)[-1].strip()
            elif "classify" in l or "match" in l:
                result["reason"] = line.strip()
    except Exception:
        result["reason"] = response_text.strip()
    return result


def generate_llama_analysis(control, regulation, score, reg_name):
    prompt = f"""
Control Clause:
\"\"\"{control}\"\"\"

Regulation Clause from {reg_name}:
\"\"\"{regulation}\"\"\"

Match score: {round(score, 3)}

You are a compliance analyst. Analyze the above in detail:

1. Classify the match: Strong, Partial, Weak, Unmatched
2. 🔗 Overlap
3. 📉 Gaps
4. 🧠 Rewrite (if needed)
5. ⚠️ Non-Compliance Risk
6. 💸 Estimated Fine (Low, Medium, High + reason)
Provide your answer in plain text format.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLAMA_MODEL,
        "temperature": 0.4,
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = httpx.post(GROQ_URL, json=payload, headers=headers, timeout=45.0)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[LLaMA Error: {str(e)}]"


def match_single_clause(i, control_clause, reg_clauses, reg_embeddings):
    control_text = control_clause.get("text", "").strip()
    if not control_text:
        return [{
            "control_id": control_clause.get("clause_id", f"Control-{i+1}"),
            "control": "[EMPTY]",
            "status": "Unmatched",
            "score": 0.0,
            "matched_clause": "—",
            "regulation": "—",
            "doc_name": "—",
            "page_num": "—",
            "section": "—",
            "overlap": "—",
            "gap": "Clause was empty",
            "reason": "—",
            "rewrite": "—",
            "risk": "—",
            "fine": "—"
        }]

    cleaned_control = clean_text(control_text)
    control_embedding = model.encode(cleaned_control, convert_to_tensor=True)
    similarities = util.cos_sim(control_embedding, reg_embeddings)[0].cpu().numpy()

    top_indices = similarities.argsort()[-TOP_K:][::-1]
    results = []

    for j, best_idx in enumerate(top_indices):
        reg_clause = reg_clauses[best_idx]
        best_score = float(similarities[best_idx])

        should_use_llama = USE_LLaMA and i < MAX_LLaMA_ANALYSIS
        llama_response = generate_llama_analysis(cleaned_control, reg_clause["text"], best_score, reg_clause["regulation"]) if should_use_llama else "AI analysis not applied."
        parsed = parse_llama_response(llama_response)

        result = {
            "control_id": control_clause.get("clause_id", f"Control-{i+1}"),
            "control": cleaned_control,
            "status": classify_status(best_score),
            "score": round(best_score, 3),
            "matched_clause": reg_clause["text"],
            "regulation": reg_clause["regulation"],
            "doc_name": reg_clause.get("doc_name", "Unknown"),
            "page_num": reg_clause.get("page_num", "—"),
            "section": reg_clause.get("section", "—"),
            "overlap": parsed.get("overlap", "—"),
            "gap": parsed.get("gap", "—"),
            "reason": parsed.get("reason", "AI analysis not applied."),
            "rewrite": parsed.get("rewrite", "—"),
            "risk": parsed.get("risk", "—"),
            "fine": parsed.get("fine", "—")
        }

        results.append(result)
    return results


def process_and_match_multiple_docs(control_clauses, regulation_clauses, remove_stopwords=True):
    reg_clean = []
    for r in regulation_clauses:
        reg_clean.append({
            "text": clean_text(r.get("text", "")),
            "regulation": r.get("regulation", "Unknown Regulation"),
            "doc_name": r.get("doc_name", "—"),
            "page_num": r.get("page_num", "—"),
            "section": r.get("section", "—")
        })

    reg_embeddings = batch_encode([r["text"] for r in reg_clean])

    results = []
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(match_single_clause, i, clause, reg_clean, reg_embeddings)
            for i, clause in enumerate(control_clauses)
        ]
        for future in futures:
            results.extend(future.result())

    return results
