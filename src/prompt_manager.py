# src/prompt_manager.py
from __future__ import annotations
from pathlib import Path
from typing import Optional

from src.config import (
    PROMPTS_DIR,
    PROMPT_VARIANT,
    PROMPT_WITH_ATTACHMENT_FILE,
    PROMPT_WITHOUT_ATTACHMENT_FILE,
    FIX_JSON_PROMPT_FILE,
)

class PromptManager:
    """Lê prompts de arquivos .txt e renderiza com placeholders."""
    def __init__(
        self,
        with_attachment_file: Optional[Path] = None,
        without_attachment_file: Optional[Path] = None,
        fix_json_file: Optional[Path] = None,
    ):
        self.with_attachment_file = Path(with_attachment_file or PROMPT_WITH_ATTACHMENT_FILE)
        self.without_attachment_file = Path(without_attachment_file or PROMPT_WITHOUT_ATTACHMENT_FILE)
        self.fix_json_file = Path(fix_json_file or FIX_JSON_PROMPT_FILE)

        PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

        # Semeia defaults da variante ativa
        variant = PROMPT_VARIANT
        if not self.with_attachment_file.exists():
            self.with_attachment_file.write_text(DEFAULTS[variant]["with"], encoding="utf-8")
        if not self.without_attachment_file.exists():
            self.without_attachment_file.write_text(DEFAULTS[variant]["without"], encoding="utf-8")
        if not self.fix_json_file.exists():
            self.fix_json_file.write_text(DEFAULT_FIX_JSON, encoding="utf-8")

        # Semeia arquivos das outras variantes se faltarem
        for name, tpl in DEFAULTS.items():
            wp = PROMPTS_DIR / f"{name}_with_attachment.txt"
            wop = PROMPTS_DIR / f"{name}_without_attachment.txt"
            if not wp.exists(): wp.write_text(tpl["with"], encoding="utf-8")
            if not wop.exists(): wop.write_text(tpl["without"], encoding="utf-8")

    def _read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def render_with_attachment(self, file_title: str) -> str:
        tmpl = self._read(self.with_attachment_file)
        return tmpl.replace("{file_title}", file_title)

    def render_without_attachment(self, file_title: str, article_text: str) -> str:
        tmpl = self._read(self.without_attachment_file)
        return tmpl.replace("{file_title}", file_title).replace("{article_text}", article_text)  

    def get_fix_prompt(self) -> str:
        return self._read(self.fix_json_file)

# =================== DEFAULTS ===================

# Chaves do JSON (todas as variantes têm o campo opcional "rationale")
JSON_SCHEMA_EXPLICIT = """Return ONLY this JSON (no markdown, no extra keys):
{
  "title": "...",
  "main_objectives": "... (1–3 sentences)",
  "research_questions": "... (single string; items separated by '; ')",
  "study_type": "...",
  "methodology": "... (2–4 sentences)",
  "main_findings": "... (2–5 sentences)",
  "conclusions": "... (1–3 sentences)",
  "limitations": "... (1–3 sentences or 'Not explicitly stated')",
  "rationale": "... (2–6 sentences explaining how you arrived at the answers; cite sections/excerpts if helpful)"
}
"""

# 1) ZERO-SHOT — instruções diretas, sem exemplos, sem CoT externo
ZEROSHOT_WITH = f"""You are a meticulous research assistant. Read the ATTACHED PDF (file: {{file_title}}).
Extract the following fields faithfully and concisely. {JSON_SCHEMA_EXPLICIT}"""

ZEROSHOT_WITHOUT = f"""You are a meticulous research assistant. The article text is below (file: {{file_title}}).
Extract the following fields faithfully and concisely. {JSON_SCHEMA_EXPLICIT}

ARTICLE RAW TEXT
--- START ---
{{article_text}}
--- END ---"""

# 2) FEW-SHOT — inclui 2 exemplos MINIMALISTAS (mantenha curtos!)
FEWSHOT_EXEMPLARS = """EXEMPLARS (for guidance; DO NOT copy wording):

Example A (input: methods-driven empirical study)
Expected JSON (abridged):
{
  "title": "Effects of X on Y in Z",
  "main_objectives": "Investigate the relationship between X and Y in Z.",
  "research_questions": "Does X affect Y?; How strong is the effect?",
  "study_type": "experimental",
  "methodology": "Participants ...; Data collected via ...; Analysis used regression ...",
  "main_findings": "X significantly increased Y ...",
  "conclusions": "Findings support ...",
  "limitations": "Small sample; Single site",
  "rationale": "Derived from Abstract purpose, Methods design, Results tables, and Discussion."
}

Example B (input: narrative review)
Expected JSON (abridged):
{
  "title": "A Review of ABC Approaches",
  "main_objectives": "Synthesize literature on ABC ...",
  "research_questions": "What approaches exist?; What gaps remain?",
  "study_type": "review",
  "methodology": "Sources from ...; Inclusion criteria ...; Thematic synthesis ...",
  "main_findings": "Three themes ...",
  "conclusions": "ABC remains limited by ...",
  "limitations": "Potential selection bias; Limited databases",
  "rationale": "Taken from stated aims, methods section, and concluding remarks."
}
"""

FEWSHOT_WITH = f"""You are a meticulous research assistant. Read the ATTACHED PDF (file: {{file_title}}).
Mimic the style of the exemplars below, but keep content faithful to THIS paper. {JSON_SCHEMA_EXPLICIT}

{FEWSHOT_EXEMPLARS}
"""

FEWSHOT_WITHOUT = f"""You are a meticulous research assistant. The article text is below (file: {{file_title}}).
Mimic the style of the exemplars below, but keep content faithful to THIS paper. {JSON_SCHEMA_EXPLICIT}

{FEWSHOT_EXEMPLARS}

ARTICLE RAW TEXT
--- START ---
{{article_text}}
--- END ---"""

# 3) CHAIN-OF-THOUGHT (COT) — seu CoT como instrução INTERNA (não revelar passo-a-passo)
COT_STEPS = """Follow the Chain-of-Thought (CoT) INTERNALLY; DO NOT reveal reasoning:
- Q1 Objectives/RQs: read intro/abstract; find aims/gaps; derive objectives; list RQs.
- Q2 Study type: inspect Methods for design; decide among experimental/case study/review/meta/qualitative/quantitative/etc.
- Q3 Methodology: participants/sample; instruments; collection procedures; analysis techniques/software.
- Q4 Findings: extract main results (tables/figures); focus on primary outcomes.
- Q5 Conclusions: how authors interpret results vs objectives/RQs; key message.
- Q6 Limitations: explicit section or statements about sample/design/collection/analysis constraints; impacts.
"""

COT_WITH = f"""You are a meticulous research assistant. Read the ATTACHED PDF (file: {{file_title}}).
{COT_STEPS}
Your final output must be a compact JSON ONLY. {JSON_SCHEMA_EXPLICIT}"""

COT_WITHOUT = f"""You are a meticulous research assistant. The article text is below (file: {{file_title}}).
{COT_STEPS}
Your final output must be a compact JSON ONLY. {JSON_SCHEMA_EXPLICIT}

ARTICLE RAW TEXT
--- START ---
{{article_text}}
--- END ---"""

DEFAULT_FIX_JSON = """Your previous message did not contain a valid JSON matching the schema.
Please re-send ONLY a valid minified JSON object with exactly these keys (no extra keys, no markdown): 
title, main_objectives, research_questions, study_type, methodology, main_findings, conclusions, limitations, rationale.
"""

DEFAULTS = {
    "zeroshot": {"with": ZEROSHOT_WITH, "without": ZEROSHOT_WITHOUT},
    "fewshot": {"with": FEWSHOT_WITH, "without": FEWSHOT_WITHOUT},
    "cot": {"with": COT_WITH, "without": COT_WITHOUT},
}
