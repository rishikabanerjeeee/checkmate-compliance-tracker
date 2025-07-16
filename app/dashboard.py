import os
import sys
import logging
from pathlib import Path
import streamlit as st

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.resolve()))

# App modules
from api.document_parser import process_uploaded_file
from api.match_engine import process_and_match_multiple_docs
from api.report_builder import generate_final_csv_report
from api.llama_chat_agent import ask_llama, get_flashcard_prompts_from_context

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit Page Setup
st.set_page_config(page_title="Compliance Intelligence Engine", layout="wide")

# 🧠 Session Init
def init_session():
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("processed_data", None)
    st.session_state.setdefault("context_injected", False)

init_session()

# 🎨 Dark Mode Styling
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0e1117;
    color: #ffffff;
}
[data-testid="stSidebar"] {
    background-color: #1e1e1e;
}
.stTextInput > div > input {
    color: white; background-color: #262730;
}
.stButton > button {
    color: white; background-color: #2a2d3a;
}
thead tr th, tbody tr td {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# 📂 Upload Section
st.sidebar.header("📂 Upload Documents")
control_docs = st.sidebar.file_uploader("Upload Company Controls", type=["pdf", "docx", "txt", "csv", "xlsx"], accept_multiple_files=True)
regulation_docs = st.sidebar.file_uploader("Upload Regulations", type=["pdf", "docx", "txt", "csv", "xlsx"], accept_multiple_files=True)

# 🛡️ Audit Mode Toggle
st.sidebar.markdown("---")
audit_mode_enabled = st.sidebar.toggle("🛡️ Enable Audit Mode", value=True, help="Strict mode: Only use uploaded content, no assumptions.")

if not control_docs or not regulation_docs:
    st.sidebar.warning("Please upload both control and regulatory documents.")
    st.stop()

# 🔍 Run Matching
@st.cache_data(show_spinner=False)
def run_matching():
    try:
        control_clauses, regulation_clauses = [], []

        for f in control_docs:
            control_clauses += process_uploaded_file(f)

        for f in regulation_docs:
            clauses = process_uploaded_file(f)
            regulation_clauses += [{"text": c["text"], "regulation": f.name} for c in clauses]

        results = process_and_match_multiple_docs(control_clauses, regulation_clauses)
        matched, missing = [], []

        for r in results:
            score = r.get("score", 0.0)
            if r["status"] == "Unmatched":
                missing.append({
                    "Missing Clause": r.get("control", "—"),
                    "Score": score,
                    "gap": r.get("gap", "—"),
                    "reason": r.get("reason", "—"),
                    "Regulation": r.get("regulation", "—"),
                    "rewrite": r.get("rewrite", "—"),
                    "risk": r.get("risk", "—"),
                    "fine": r.get("fine", "—")
                })
            else:
                matched.append({
                    "Clause ID": r.get("control_id", "—"),
                    "Control Clause": r.get("control", "—"),
                    "Match Type": r.get("status", "—"),
                    "Score": score,
                    "Regulation": r.get("regulation", "—"),
                    "Overlap Terms": r.get("overlap", "—"),
                    "Gap": r.get("gap", "—"),
                    "Reasoning": r.get("reason", "—"),
                    "rewrite": r.get("rewrite", "—"),
                    "risk": r.get("risk", "—"),
                    "fine": r.get("fine", "—")
                })

        return {"matched": matched, "missing": missing}
    except Exception as e:
        logger.exception(e)
        st.error("❌ AI Matching failed.")
        return {"matched": [], "missing": []}

if st.sidebar.button("🔍 Run Compliance Matching"):
    with st.spinner("Running AI-based clause analysis..."):
        st.session_state.processed_data = run_matching()

if st.sidebar.button("📥 Download CSV Report"):
    try:
        report = generate_final_csv_report(
            st.session_state.get("processed_data", {}).get("matched", []),
            st.session_state.get("processed_data", {}).get("missing", []),
            chat_history=st.session_state.get("chat_history", [])
        )
        st.sidebar.download_button(
            label="📊 Export Compliance Report",
            data=report,
            file_name="Compliance_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        logger.error(e)
        st.sidebar.error("❌ Report generation failed.")

# 🧠 Summary UI
if st.session_state.get("processed_data"):
    st.markdown("## 📊 Compliance Summary")
    top_matches = st.session_state["processed_data"].get("matched", [])[:3]
    top_misses = st.session_state["processed_data"].get("missing", [])[:2]

    for m in top_matches:
        st.success(f"✅ `{m['Clause ID']}` matched in **{m['Regulation']}** (Score: {round(m['Score'], 2)})")
    for m in top_misses:
        st.warning(f"⚠️ Missing: “{m['Missing Clause'][:60]}...” — Gap: **{m['gap']}**")

    # Flashcards
    st.markdown("### 🧠 Suggested Prompts")
    for prompt in get_flashcard_prompts_from_context():
        if st.button(prompt, key=f"prompt_{prompt}"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            try:
                with st.spinner("Thinking..."):
                    stream = ask_llama(st.session_state.chat_history, stream=True, audit_mode=audit_mode_enabled)
                    full_response = ""
                    for chunk in stream:
                        full_response += chunk
                        st.write_stream(iter([chunk]))
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error("❌ Chat failed.")
                logger.error(e)

# 💬 Chatbox
st.markdown("## 💬 Chat with Compliance Assistant")
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask about gaps, risks, rewrites or matches:")
    submitted = st.form_submit_button("📨 Send")

if submitted and user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    try:
        with st.spinner("Analyzing..."):
            stream = ask_llama(st.session_state.chat_history, stream=True, audit_mode=audit_mode_enabled)
            response = ""
            for chunk in stream:
                response += chunk
                st.write_stream(iter([chunk]))
        st.session_state.chat_history.append({"role": "assistant", "content": response})
    except Exception as e:
        st.error("❌ Chat failed.")
        logger.error(e)

# 💾 Chat History
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ♻️ Reset
if st.sidebar.button("🧹 Reset All"):
    for key in ["chat_history", "processed_data", "context_injected"]:
        st.session_state[key] = [] if "history" in key else None
    st.rerun()
