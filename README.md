# ✅ checkmate-compliance-tracker  
A PROJECT MADE BY RISHIKA BANERJEE FROM KJ SOMAIYA SCHOOL OF ENGINEERING UNDER INTERNSHIP AT DELOITTE ( MAY 2025- JULY 2025)
Compliance Intelligence Engine — AI-Powered Regulation Alignment Platform

An AI-powered compliance tool that matches internal controls with regulatory clauses (e.g., GDPR, RBI, ISO 27001), detects semantic gaps, suggests rewrites, and highlights associated risks/fines using LLaMA3 via Groq API.  
Includes Audit Mode, an interactive chatbot, multi-format uploads, and auto-generated Excel reports.

---

## 🧠 Overview

The Compliance Intelligence Engine is built for legal, risk, and audit teams to:

- Rapidly assess alignment between internal controls and external regulations  
- Understand compliance risks and get AI-generated rewrites  
- Generate structured audit-ready reports  

---

## 🚀 Key Features

- 📂 Multi-format Uploads: PDF, DOCX, TXT, CSV, XLSX  
- 🔍 Semantic Clause Matching: MiniLM embeddings classify matches as Strong / Partial / Weak  
- 🧠 LLaMA3-Powered AI Reasoning (via Groq):
  - Clause overlap analysis  
  - Semantic gap detection  
  - Rewrite suggestions  
  - Non-compliance risks + fine estimates  
- 🛡️ Audit Mode: Restrict chatbot to only reference uploaded documents — no hallucinations  
- 🤖 Interactive Chatbot: GPT-style assistant to explain matches, gaps, and summaries  
- 💬 Flashcard Prompts: Suggested queries based on uploaded document context  
- 📊 Excel Report Generation:
  - Full clause comparison
  - AI insights (gaps, risks, rewrites)
  - Chat history
  - Cross-document mapping

---

🛠️ Setup Instructions

## 1. Clone the Repo
git clone https://github.com/rishikabanerjeeee/checkmate-compliance-tracker.git
cd checkmate-compliance-tracker

### 🛠️ Setup Instructions

## 2. Install Python Dependencies
pip install -r requirements.txt

## 3. Set Environment Variables
# Option 1: Create a `.env` file manually
# Option 2: Export variable directly
export GROQ_API_KEY=your_groq_api_key_here

## 4. Run the App
streamlit run app/dashboard.py

# 📁 Project Structure

.
├── app/
│   └── dashboard.py             # Streamlit UI
├── api/
│   ├── document_parser.py       # File parsing (PDF, Word, Excel, etc.)
│   ├── match_engine.py          # Clause matching + LLaMA3 semantic gap analysis
│   ├── report_builder.py        # Excel report generation
│   └── llama_chat_agent.py      # Audit-aware chatbot engine
├── data/                        # Uploaded and processed files
├── requirements.txt             # Python package dependencies
# 🔐 Audit Mode

# Use the toggle in the Streamlit sidebar. In Audit Mode:
# - Chatbot ONLY uses uploaded clause content (no hallucinations or outside assumptions).
# - If insufficient data exists, the bot replies with:

"I cannot verify this based on uploaded documents."
# 📤 Excel Report Includes

- Full compliance summary (Matched + Missing clauses)
- Rewrites, Gaps, Risks, Fines
- Chatbot history
- Cross-document control-to-regulation mapping
# ✅ Use Cases

- Vendor risk audits
- Internal control validation
- DPDP / GDPR / RBI audit trail preparation
- Due diligence automation
# 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first.
