# api/llama_chat_agent.py

# api/llama_chat_agent.py

import re
import os
import streamlit as st
from typing import List, Dict, Generator, Union
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("🚨 GROQ_API_KEY not found. Check your .env file.")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key
)

# --- Utility: Token Counting ---
def approximate_token_count(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text, re.UNICODE))

def dynamic_max_tokens(messages: List[Dict], model_max_tokens: int = 8192) -> int:
    used = sum(approximate_token_count(m.get("content", "")) for m in messages)
    return max(model_max_tokens - used - 150, 150)

# --- Match Summary Context Injection ---
def get_memory_context() -> Union[Dict, None]:
    if not st.session_state.get("processed_data"):
        return None

    matched = st.session_state["processed_data"].get("matched", [])[:5]
    missing = st.session_state["processed_data"].get("missing", [])[:3]
    context_lines = []

    if matched:
        context_lines.append("✅ Top Matched Clauses:")
        for item in matched:
            cid = item.get("control_id", "Clause")
            reg = item.get("regulation", "Regulation")
            score = item.get("score", "—")
            clause_text = item.get("control", "")[:80]
            context_lines.append(f"- `{cid}` in **{reg}** (Score: {score}): \"{clause_text}...\"")

    if missing:
        context_lines.append("❌ Missing Clauses:")
        for item in missing:
            clause_text = item.get("control", "")[:70]
            gap = item.get("gap", "—")
            context_lines.append(f"- \"{clause_text}...\"  (Gap: {gap})")

    return {
        "role": "system",
        "content": (
            "You are a legal compliance AI assistant. In Audit Mode, only use uploaded clause data.\n"
            "Always cite specific clause IDs and their regulation sources.\n\n"
            "📄 Clause Summary:\n" + "\n".join(context_lines)
        )
    }

def inject_context_once(chat_history: List[Dict]) -> List[Dict]:
    if not st.session_state.get("context_injected", False):
        context = get_memory_context()
        if context:
            st.session_state.context_injected = True
            return [context] + [m for m in chat_history if m["role"] != "system"]
    return chat_history

# --- Chat Function ---
def ask_llama(
    messages: Union[str, List[Dict]],
    model: str = "llama3-8b-8192",  # use 8b model for token safety
    temperature: float = 0.2,
    stream: bool = False,
    audit_mode: bool = True
) -> Union[str, Generator[str, None, None]]:
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]

    messages = inject_context_once(messages)

    if audit_mode:
        system_msg = {
            "role": "system",
            "content": (
                "You are in AUDIT MODE.\n"
                "Only use uploaded clause content (matched or missing).\n"
                "If unsure, respond: \"I cannot verify this based on uploaded documents.\"\n"
                "Cite clause IDs and regulation names always. Do not assume or hallucinate."
            )
        }
        messages.insert(0, system_msg)

    max_tokens = dynamic_max_tokens(messages)

    params = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream
    }

    try:
        if stream:
            response = client.chat.completions.create(**params)
            return (chunk.choices[0].delta.content or "" for chunk in response)
        else:
            response = client.chat.completions.create(**params)
            reply = response.choices[0].message.content.strip()
            if response.choices[0].finish_reason != "stop":
                reply += "\n\n⚠️ Truncated due to token limit."
            return reply
    except Exception as e:
        return (
            "⚠️ The system was unable to analyze this fully due to token limit or API failure.\n"
            f"Error: {str(e)}\n"
            "Please try a shorter query or re-run matching."
        )

# --- Flashcard Generator ---
def get_flashcard_prompts_from_context() -> List[str]:
    prompts = []
    data = st.session_state.get("processed_data")
    if not data:
        return prompts

    matched = data.get("matched", [])
    missing = data.get("missing", [])

    if matched:
        top = matched[0]
        cid = top.get("control_id", "Control")
        reg = top.get("regulation", "Regulation")
        prompts.append(f"🔍 How does **{cid}** align with {reg}?")
        prompts.append(f"💡 Can **{cid}** be improved to meet full compliance?")

    if missing:
        top = missing[0]
        gap = top.get("gap", "—")
        text = top.get("control", "")[:50]
        prompts.append(f"⚠️ Why is this clause marked missing? “{text}...”")
        prompts.append(f"📘 Suggest a new control to cover: {gap}")

    prompts.append("🧠 What's the overall risk profile based on current matches?")

    return prompts
