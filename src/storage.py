from __future__ import annotations
import json
from pathlib import Path
from typing import Set

from src.config import BASE_DIR, MD_PATH
from src.schema import ArticleSummary

OUT_DIR = BASE_DIR / "outputs"
OUT_JSON_DIR = OUT_DIR / "json"
SENT_LOG = OUT_DIR / "sent.json"

def load_sent_files() -> Set[str]:
    if not SENT_LOG.exists():
        return set()
    try:
        raw = SENT_LOG.read_text(encoding="utf-8").strip()
        if not raw:
            return set()
        data = json.loads(raw)
        if isinstance(data, list):
            return set(data)
        return set()
    except Exception:
        return set()

def save_sent_files(sent: Set[str]) -> None:
    SENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    SENT_LOG.write_text(json.dumps(sorted(sent), ensure_ascii=False, indent=2), encoding="utf-8")

def save_article_json(stem: str, summary: ArticleSummary) -> Path:
    OUT_JSON_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_JSON_DIR / f"{stem}.json"
    try:
        data = summary.model_dump()
    except AttributeError:
        data = summary.dict()
    text = json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")
    return path

def append_to_md(summary: ArticleSummary) -> None:
    MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        d = summary.model_dump()
    except AttributeError:
        d = summary.dict()

    block = []
    block.append(f"## {d.get('title','(no title)')}\n")
    block.append(f"**Objectives:** {d.get('main_objectives','')}\n\n")
    block.append(f"**Research Questions:** {d.get('research_questions','')}\n\n")
    block.append(f"**Study Type:** {d.get('study_type','')}\n\n")
    block.append(f"**Methodology:** {d.get('methodology','')}\n\n")
    block.append(f"**Main Findings:** {d.get('main_findings','')}\n\n")
    block.append(f"**Conclusions:** {d.get('conclusions','')}\n\n")
    block.append(f"**Limitations:** {d.get('limitations','')}\n\n")
    rationale = d.get("rationale")
    if rationale:
        block.append(f"**Rationale (CoT):** {rationale}\n\n")
    block.append("---\n\n")

    with MD_PATH.open("a", encoding="utf-8") as f:
        f.writelines(block)
