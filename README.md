# checkmate-compliance-tracker
An AI-powered compliance tool that matches company controls with regulatory clauses (GDPR, RBI, etc.), detects gaps, suggests rewrites, and provides risk/fine insights using LLaMA3. Features audit mode, chatbot, multi-format uploads, and generates Excel compliance reports. 

Compliance Intelligence Engine — AI-Powered Regulation Alignment Platform
Overview:
The Compliance Intelligence Engine is a robust AI-powered web application that automates the analysis and alignment of internal company controls with external regulatory requirements (e.g., GDPR, RBI, ISO 27001). It enables legal, risk, and audit teams to rapidly identify gaps, understand compliance risks, and receive AI-suggested rewrites for improved adherence.

Key Features:
Multi-format document ingestion: Upload .pdf, .docx, .txt, .csv, and .xlsx for both control and regulation files.
Semantic Clause Matching: Uses MiniLM sentence embeddings to intelligently match internal clauses to corresponding regulatory clauses with strong/partial/weak status.
LLaMA3-powered AI Reasoning: For top matches, LLaMA3-70B (via Groq API) provides:
Overlap analysis
Semantic gap summary
Rewrite suggestions
Risk estimates and potential fines
Audit Mode (Strict Grounding): Toggle to enforce that chatbot only references uploaded documents, ensuring no hallucinations or speculative answers.

Interactive Chatbot: Engage with a GPT-style assistant that:
Explains gaps and risks
Summarizes matches
Answers user queries using uploaded content
Flashcard Prompts: Suggested questions based on the uploaded document context for quick exploration.

Excel Report Generation:
Full compliance summary
Rewritten clauses
Chatbot Q&A history
Cross-document mapping of control-to-regulation coverage

Tech Stack:
Frontend: Streamlit (custom dark theme, dynamic prompt buttons)

AI/NLP:

SentenceTransformer (MiniLM for embeddings)

Meta LLaMA3 (via Groq API)

Backend: Python (modular architecture)

Exports: XLSX reports via pandas + xlsxwriter

Infra: Stateless session, supports large clause volumes with threading

Use Cases:
Regulatory gap assessments



🧠 Compliance Intelligence Engine
An AI-powered compliance analysis tool that matches internal control clauses against regulations like GDPR, RBI, ISO27001, etc. It detects semantic gaps, suggests rewrites, and identifies risks/fines using LLaMA3 models via Groq API. Includes an audit-only chatbot and detailed Excel reports.

🚀 Features
🔍 Clause Matching with AI (MiniLM + LLaMA3)

📂 Upload controls & regulations (PDF, DOCX, TXT, CSV, XLSX)

⚠️ Semantic gap detection + risk & fine insights

🤖 Chatbot with Audit Mode toggle

📊 Auto-generated Excel report with all findings

🧠 Flashcard prompts based on detected compliance context

🛠️ Setup Instructions
1. Clone the Repo
bash
Copy
Edit
git clone https://github.com/your-username/compliance-intelligence-engine.git
cd compliance-intelligence-engine
2. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
3. Set Environment Variables
Create a .env file or export these:

bash
Copy
Edit
export GROQ_API_KEY=your_groq_api_key_here
4. Run the App
bash
Copy
Edit
streamlit run app/dashboard.py
📁 Project Structure
bash
Copy
Edit
.
├── app/
│   └── dashboard.py             # Streamlit UI
├── api/
│   ├── document_parser.py       # File parsing (PDF, Word, etc.)
│   ├── match_engine.py          # Clause matching + LLaMA analysis
│   ├── report_builder.py        # Excel report generation
│   └── llama_chat_agent.py      # Audit-aware chatbot logic
├── data/                        # Uploaded/processed files
├── requirements.txt             # Python dependencies
🔐 Audit Mode
Toggle Audit Mode in the sidebar to make the chatbot strictly grounded in uploaded content. If no relevant content is found, the assistant responds with:

"I cannot verify this based on uploaded documents."

📤 Report Output
Excel report includes:

Full clause matches/mismatches

AI rewrites, gaps, risks, fines

Chatbot interaction log

Cross-document traceability

🤝 Contributing
Pull requests are welcome. For major changes, please open an issue first.

Vendor risk audits

Internal control validation

Due diligence automation

DPDP/GDPR/RBI audit trail prep
