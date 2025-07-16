import io
import pandas as pd
from datetime import datetime

def clean_field(val):
    if isinstance(val, str) and any(err in val for err in ["LLaMA Error", "Too Many Requests", "Payload Too Large"]):
        return "⚠️ Unable to generate reasoning (AI overload)"
    return val if val else "—"

def generate_final_csv_report(matched_controls, missing_controls, chat_history=None, audit_mode=True):
    output = io.BytesIO()

    def safe_series(df, *possible_keys, default="—"):
        for key in possible_keys:
            if key in df.columns:
                return df[key]
        return pd.Series([default] * len(df))

    def preprocess(df_raw, is_missing=False):
        if not df_raw:
            return pd.DataFrame(columns=[
                "Clause ID", "Control Clause", "Match Type", "Regulation", "Match Score (%)",
                "Overlap Terms", "Semantic Gap Analysis", "AI Reasoning",
                "Suggested Rewrite for Better Compliance", "Associated Risks", "Potential Fines"
            ])

        df = pd.DataFrame(df_raw).copy()

        df["Clause ID"] = safe_series(df, "Clause ID", "control_id")
        df["Control Clause"] = safe_series(df, "Control Clause", "control", "Missing Clause")
        df["Match Type"] = "Unmatched" if is_missing else safe_series(df, "Match Type", "status", default="—")
        df["Regulation"] = safe_series(df, "Regulation", "regulation")
        df["Match Score (%)"] = safe_series(df, "Score", "score", default=0.0)
        df["Overlap Terms"] = safe_series(df, "Overlap Terms", "overlap")
        df["Semantic Gap Analysis"] = safe_series(df, "Gap", "gap")

        df["AI Reasoning"] = safe_series(df, "Reasoning", "reason").apply(clean_field)
        df["Suggested Rewrite for Better Compliance"] = safe_series(df, "rewrite")
        df["Associated Risks"] = safe_series(df, "risk")
        df["Potential Fines"] = safe_series(df, "fine")

        return df[[ 
            "Clause ID",
            "Control Clause",
            "Match Type",
            "Regulation",
            "Match Score (%)",
            "Overlap Terms",
            "Semantic Gap Analysis",
            "AI Reasoning",
            "Suggested Rewrite for Better Compliance",
            "Associated Risks",
            "Potential Fines"
        ]]

    # --- Sheet 1: Full Summary ---
    df_matched = preprocess(matched_controls, is_missing=False)
    df_missing = preprocess(missing_controls, is_missing=True)
    df_compliance = pd.concat([df_matched, df_missing], ignore_index=True)

    # --- Sheet 2: Chat History ---
    chat_rows = []
    if chat_history:
        for msg in chat_history:
            chat_rows.append({
                "Role": msg.get("role", "system").title(),
                "Message": msg.get("content", "").replace("\n", " ").strip(),
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    df_chat = pd.DataFrame(chat_rows, columns=["Role", "Message", "Timestamp"])

    # --- Sheet 3: Rewrites ---
    df_rewrites = df_matched[
        df_matched["Suggested Rewrite for Better Compliance"] != "—"
    ][[
        "Clause ID", "Control Clause", "Suggested Rewrite for Better Compliance",
        "AI Reasoning", "Associated Risks", "Potential Fines"
    ]].copy()

    # --- Sheet 4: Cross Regulation ---
    cross_data = []
    for row in matched_controls:
        cross_data.append({
            "Clause ID": row.get("control_id", "—"),
            "Appears In Regulation": row.get("regulation", "—"),
            "Overlap Terms": row.get("overlap", "—"),
            "Gaps Noted": row.get("gap", "—")
        })
    df_cross = pd.DataFrame(cross_data, columns=[
        "Clause ID", "Appears In Regulation", "Overlap Terms", "Gaps Noted"
    ])

    # --- Sheet 5: Audit Mode Info ---
    session_info = pd.DataFrame([
        {"Field": "Audit Mode", "Value": "ON" if audit_mode else "OFF"},
        {"Field": "Generated On", "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"Field": "Matched Clauses", "Value": len(df_matched)},
        {"Field": "Missing Clauses", "Value": len(df_missing)}
    ])

    # --- Write to Excel ---
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_compliance.to_excel(writer, sheet_name="Compliance Report", index=False)
        df_chat.to_excel(writer, sheet_name="Chatbot History", index=False)
        df_rewrites.to_excel(writer, sheet_name="Rewritten Controls", index=False)
        df_cross.to_excel(writer, sheet_name="Cross-Document Analysis", index=False)
        session_info.to_excel(writer, sheet_name="Session Info", index=False)

    output.seek(0)
    return output
