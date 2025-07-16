# ✅ checkmate-compliance-tracker  
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

## 🛠️ Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/rishikabanerjeeee/checkmate-compliance-tracker.git
cd checkmate-compliance-tracker
