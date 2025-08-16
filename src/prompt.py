from textwrap import dedent

SCHEMA_KEYS = [
    "title",
    "main_objectives",
    "research_questions",
    "study_type",
    "methodology",
    "main_findings",
    "conclusions",
    "limitations",
]

SYSTEM_PROMPT = "You are a meticulous research assistant."

def make_user_prompt(file_title: str, raw_text: str) -> str:
    return dedent(f"""
    Please summarize the provided research article by addressing the following. Return ONLY a minified JSON object with these exact keys:
    {', '.join(SCHEMA_KEYS)}.
    Rules:
    - 'title': concise title inferred from the text (or the given file name if missing).
    - 'main_objectives': 1–3 sentences.
    - 'research_questions': bullet-like list in a single string (use '; ' between items).
    - 'study_type': (e.g., experimental, case study, review, qualitative, quantitative, mixed-methods).
    - 'methodology': 2–4 sentences on data collection and analysis.
    - 'main_findings': 2–5 sentences.
    - 'conclusions': 1–3 sentences.
    - 'limitations': 1–3 sentences (if none stated, say 'Not explicitly stated').
    Respond in English. Do not include markdown code fences. Do not include commentary.
    If unsure, make a best-effort faithful summary; do not fabricate facts.

    File name (for context): {file_title}
    --- ARTICLE RAW TEXT START ---
    {raw_text}
    --- ARTICLE RAW TEXT END ---
    """).strip()

FIX_JSON_PROMPT = dedent("""
The previous answer did not comply with the required strict JSON schema.
Please return the same content as a single minified JSON object with exactly these keys:
title, main_objectives, research_questions, study_type, methodology, main_findings, conclusions, limitations.
No markdown, no backticks, no commentary — JSON only.
""").strip()
