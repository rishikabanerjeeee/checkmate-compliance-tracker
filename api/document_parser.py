# api/document_parser.py

import os
import re
import time
import logging
from datetime import datetime
import pandas as pd
import nltk

from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords

import fitz  # PyMuPDF
from docx import Document

# --- Logging Setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- NLTK Setup ---
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

stop_words = set(stopwords.words("english"))
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".csv", ".xlsx", ".xls"]
KNOWN_REGULATIONS = ["GDPR", "ISO27001", "RBI", "SEBI", "PDPB", "DPDP", "MSA"]

# --- Extractor Dispatcher ---
def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"❌ Unsupported file format: {ext}")

    try:
        if ext == ".pdf":
            return extract_pdf_clauses(file_path)
        elif ext == ".docx":
            return extract_docx_clauses(file_path)
        elif ext == ".txt":
            return extract_txt_clauses(file_path)
        elif ext == ".csv":
            return extract_csv_clauses(file_path)
        elif ext in [".xlsx", ".xls"]:
            return extract_excel_clauses(file_path)
    except Exception as e:
        raise Exception(f"⚠️ Error reading {file_path}: {str(e)}")

# --- Format-Specific Extraction Functions ---
def extract_pdf_clauses(file_path):
    clauses = []
    with fitz.open(file_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            for i, sent in enumerate(sent_tokenize(text)):
                sent = sanitize_clause(sent)
                if is_valid_clause(sent):
                    clauses.append(make_clause_dict(file_path, sent, page_num, f"Page {page_num}", f"P{page_num}-C{i+1}"))
    return clauses

def extract_docx_clauses(file_path):
    clauses = []
    doc = Document(file_path)
    current_section = ""
    para_count = 0
    for para in doc.paragraphs:
        text = para.text.strip()
        if para.style.name.startswith("Heading"):
            current_section = text
            continue
        if len(text) < 20:
            continue
        para_count += 1
        sent = sanitize_clause(text)
        if is_valid_clause(sent):
            clauses.append(make_clause_dict(file_path, sent, None, current_section or "Untitled", f"S{para_count}"))
    return clauses

def extract_txt_clauses(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return split_sentences_into_clauses(text, file_path)

def extract_csv_clauses(file_path):
    df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
    clauses = []
    for i, row in df.iterrows():
        joined = " ".join(map(str, row.dropna())).strip()
        joined = sanitize_clause(joined)
        if is_valid_clause(joined):
            clauses.append(make_clause_dict(file_path, joined, None, "Row", f"R{i+1}"))
    return clauses

def extract_excel_clauses(file_path):
    df = pd.read_excel(file_path)
    clauses = []
    for i, row in df.iterrows():
        joined = " ".join(map(str, row.dropna())).strip()
        joined = sanitize_clause(joined)
        if is_valid_clause(joined):
            clauses.append(make_clause_dict(file_path, joined, None, "Sheet", f"XL{i+1}"))
    return clauses

def split_sentences_into_clauses(text, file_path):
    clauses = []
    for i, sent in enumerate(sent_tokenize(text)):
        sent = sanitize_clause(sent)
        if is_valid_clause(sent):
            clauses.append(make_clause_dict(file_path, sent, None, "Text File", f"T{i+1}"))
    return clauses

# --- Shared Helpers ---
def make_clause_dict(file_path, text, page_num, section, suffix):
    base = os.path.splitext(os.path.basename(file_path))[0]
    return {
        "clause_id": f"{base}-{suffix}",
        "text": text,
        "doc_name": os.path.basename(file_path),
        "page_num": page_num,
        "section": section,
        "source_type": infer_source_type(file_path)
    }

def sanitize_clause(clause):
    s = re.sub(r"[^A-Za-z0-9\s,.()\-–/]", "", clause.strip())
    s = re.sub(r"\s+", " ", s)
    return s

def is_valid_clause(text):
    if any(skip in text.lower() for skip in ["table of contents", "annexure", "appendix"]):
        return False
    return len(text) >= 20 and any(c.isalpha() for c in text)

def infer_source_type(file_path):
    fname = os.path.basename(file_path).upper()
    if "CONTROL" in fname or "POLICY" in fname:
        return "Control"
    elif any(reg in fname for reg in KNOWN_REGULATIONS):
        return "Regulation"
    else:
        return "Unknown"

# --- Save Upload ---
def save_uploaded_file(uploaded_file, save_dir="data/uploads"):
    os.makedirs(save_dir, exist_ok=True)
    safe_filename = re.sub(r"[^A-Za-z0-9_\-\.]", "_", uploaded_file.name)
    file_path = os.path.join(save_dir, safe_filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def save_text_and_metadata(text, original_filename, save_dir="data/texts"):
    os.makedirs(save_dir, exist_ok=True)
    base = os.path.splitext(original_filename)[0]
    safe_base = re.sub(r"[^A-Za-z0-9_\-]", "_", base)
    text_path = os.path.join(save_dir, f"{safe_base}.txt")
    meta_path = os.path.join(save_dir, f"{safe_base}_meta.txt")

    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)

    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"📂 File: {original_filename}\n")
        f.write(f"📦 Size (KB): {len(text.encode('utf-8')) // 1024}\n")
        f.write(f"⏱️ Processed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return text_path, meta_path

# --- Full Pipeline ---
def process_uploaded_file(uploaded_file, save_dir="data/uploads"):
    start = time.time()
    file_path = save_uploaded_file(uploaded_file, save_dir)
    logger.info(f"[✓] Saved: {file_path}")

    clauses = extract_text(file_path)
    flat_text = "\n".join([c["text"] for c in clauses])
    save_text_and_metadata(flat_text, uploaded_file.name, save_dir="data/texts")

    logger.info(f"[✓] Extracted {len(clauses)} clauses from {uploaded_file.name} in {time.time() - start:.2f}s")
    return clauses
