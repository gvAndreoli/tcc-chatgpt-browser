# src/chatgpt_runner.py
import json, re, time, os
from typing import Optional
from pydantic import ValidationError
from src.config import OUTPUT_DIR
from src.schema import ArticleSummary
from src.prompt_manager import PromptManager
from src.selectors import STOP_GENERATING_BTN, LAST_MESSAGE_SELECTOR, SEND_BUTTONS
from src.browser_utils import (
    ensure_ready, looks_like_human_check, attach_file,
    dismiss_overlays, find_visible_editor, pause_until_ready_manual,
    wait_until_send_enabled,
    human_idle_short, human_idle_med, human_idle_long, humanize_cursor,
)

PM = PromptManager()

def _save_debug(file_title: str, tag: str, text: str):
    try:
        d = OUTPUT_DIR / "debug"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{file_title}_{tag}.txt").write_text(text or "", encoding="utf-8")
    except Exception:
        pass


# ===== editor =====
def _focus_editor(page):
    dismiss_overlays(page)
    editor = find_visible_editor(page)
    if not editor:
        pause_until_ready_manual(page, reason="editor do chat não está visível")
        editor = find_visible_editor(page)
        if not editor:
            raise RuntimeError("Editor do chat não encontrado/visível.")
    try: editor.scroll_into_view_if_needed(timeout=2000)
    except Exception: pass
    try: editor.evaluate("(el) => el.focus()")
    except Exception: pass
    try: editor.click(timeout=1500)
    except Exception: pass
    return editor

def _clear_editor(page):
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")

def _insert_big_text(page, text: str, chunk_size: int = 1800, pause: float = 0.03):
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        ed = find_visible_editor(page)
        if ed:
            try: ed.evaluate("(el) => el.focus()")
            except Exception: pass
        page.keyboard.insert_text(chunk)
        time.sleep(pause)

def _fill_editor(page, text: str):
    """Preenche o editor digitando (sem Ctrl+V), com toques humanos leves."""
    _focus_editor(page); _clear_editor(page)
    human_idle_short()
    humanize_cursor(page)
    _insert_big_text(page, text, chunk_size=1200, pause=0.04)
    human_idle_med()

# ===== envio =====
def _assistant_count(page) -> int:
    try: return page.locator(LAST_MESSAGE_SELECTOR).count()
    except Exception: return 0

def _send_keys_then_click(page):
    """Envia a mensagem SEM usar tecla Enter – clica no primeiro botão válido de SEND_BUTTONS."""
    last_err = None
    for sel in SEND_BUTTONS:
        try:
            btns = page.locator(sel)
            if btns.count() == 0:
                continue
            btn = btns.first
            # garantir que está visível na viewport e interativo
            try: btn.scroll_into_view_if_needed(timeout=1500)
            except Exception: pass
            if not btn.is_visible():
                continue
            # checa se não está disabled (ARIA ou atributo)
            aria = (btn.get_attribute("aria-disabled") or "").lower()
            disabled = btn.get_attribute("disabled")
            if disabled is not None or aria in ("true", "1"):
                continue
            # aproxima o cursor e dá uma “micro pensada”
            try: btn.hover(timeout=1000)
            except Exception: pass
            human_idle_short()
            btn.click(timeout=3000)
            return  # sucesso
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Botão de envio não encontrado ou não habilitado pelos seletores SEND_BUTTONS. Último erro: {last_err}")

def _ensure_outbound_or_pause(page, prev_assistant_count: int, wait_s: float = 8.0):
    start = time.time()
    while time.time() - start < wait_s:
        if page.locator(STOP_GENERATING_BTN).count() > 0: return
        if _assistant_count(page) > prev_assistant_count: return
        time.sleep(0.4)
    print("\n────────────────────────────────────────────────────────")
    print("⏸  Parece que a mensagem NÃO foi enviada automaticamente.")
    print("    Por favor, CLIQUE em 'Enviar' no chat (ou pressione Enter lá).")
    print("    Assim que começar a gerar, aperte ENTER aqui.")
    print("────────────────────────────────────────────────────────\n")
    input("Pressione ENTER para continuar após enviar manualmente... ")

# ===== parser/espera =====
# === troque a função atual por esta SUPER-robusta ===
def _extract_json_from_text(text: str):
    """
    Tenta extrair um OBJETO JSON (dict). Se não conseguir, retorna None.
    Nunca retorna string/list/etc.
    """
    import json, re

    REQUIRED_KEYS = [
        "title",
        "main_objectives",
        "research_questions",
        "study_type",
        "methodology",
        "main_findings",
        "conclusions",
        "limitations",
        "rationale",
    ]

    def _normalize(s: str) -> str:
        s = s.replace("\ufeff", "")
        s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        return s

    def _try_load(cand: str):
        try:
            obj = json.loads(cand)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    raw = _normalize(text)

    # 1) ```json ... ```
    m = re.findall(r"```json\s*([\s\S]*?)\s*```", raw, flags=re.I)
    if m:
        for block in reversed(m):
            obj = _try_load(block.strip())
            if obj is not None: return obj

    # 2) maior { ... } balanceado
    start, depth, best = None, 0, None
    for i, ch in enumerate(raw):
        if ch == "{":
            if depth == 0: start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    best = raw[start:i+1]
                    start = None
    if best:
        obj = _try_load(best.strip())
        if obj is not None: return obj

    # 3) pares "key": value linha a linha -> embrulha
    kv_lines = re.findall(r'^\s*"[^"]+"\s*:\s*.+$', raw, flags=re.M)
    if kv_lines:
        wrapped = "{\n" + "\n".join(kv_lines) + "\n}"
        obj = _try_load(wrapped)
        if obj is not None: return obj

    # 4) fallback: extrai campo a campo (aceita sem chaves)
    def grab(key: str) -> str | None:
        pat = rf'"{re.escape(key)}"\s*:\s*(".*?"|\[.*?\]|\{{.*?\}}|.*?)(?:,\s*|$)'
        m1 = re.search(pat, raw, flags=re.S)
        if m1:
            val = m1.group(1).strip()
            if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
                val = val[1:-1]
            return val.strip()
        pat2 = rf'\b{re.escape(key)}\b\s*:\s*(".*?"|\[.*?\]|\{{.*?\}}|.*?)(?:,\s*|$)'
        m2 = re.search(pat2, raw, flags=re.S)
        if m2:
            val = m2.group(1).strip()
            if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
                val = val[1:-1]
            return val.strip()
        return None

    recovered = {}
    for k in REQUIRED_KEYS:
        v = grab(k)
        if v is not None:
            recovered[k] = v.strip().rstrip(",")

    return recovered if recovered else None



def wait_for_response_complete(page, timeout=300):
    start = time.time(); last_stable = ""; stable_rounds = 0
    while True:
        if looks_like_human_check(page): ensure_ready(page)
        stop_count = page.locator(STOP_GENERATING_BTN).count()
        last_el = page.locator(LAST_MESSAGE_SELECTOR).last
        try: txt = last_el.inner_text(timeout=2000)
        except Exception: txt = ""
        if stop_count == 0 and txt.strip():
            if txt.strip() == last_stable.strip():
                stable_rounds += 1
                if stable_rounds >= 3: return
            else:
                stable_rounds = 0; last_stable = txt
        if time.time() - start > timeout: return
        time.sleep(1.0)

# ===== fluxo principal =====
from typing import Optional
from src.config import OUTPUT_DIR

def _save_debug(file_title: str, tag: str, text: str):
    """Salva conteúdo bruto da resposta para depuração."""
    try:
        dbg_dir = OUTPUT_DIR / "debug"
        dbg_dir.mkdir(parents=True, exist_ok=True)
        (dbg_dir / f"{file_title}_{tag}.txt").write_text(text or "", encoding="utf-8")
    except Exception:
        pass


from typing import Optional
from pydantic import ValidationError


def _get_assistant_text_by_index(page, idx: int, timeout_ms: int = 120000) -> str:
    """Lê o balão de ASSISTANT de índice idx (0-based) aguardando o conteúdo.
    Evita usar .last, que pode apontar para o turno anterior."""
    import time
    deadline = time.time() + (timeout_ms / 1000.0)
    while time.time() < deadline:
        try:
            count = page.locator(LAST_MESSAGE_SELECTOR).count()
            if count > idx:
                text = page.locator(LAST_MESSAGE_SELECTOR).nth(idx).inner_text(timeout=8000)
                if text and text.strip():
                    return text
        except Exception:
            pass
        time.sleep(0.5)
    try:
        return page.locator(LAST_MESSAGE_SELECTOR).nth(idx).inner_text(timeout=2000)
    except Exception:
        return ""


def send_prompt_and_get_json(page, file_title: str, text: str, file_path: Optional[str] = None,
                             *, parse_fix_attempts: int = 2) -> "ArticleSummary":
    ensure_ready(page)

    if file_path:
        attach_file(page, file_path)
        prompt = PM.render_with_attachment(file_title=file_title)
    else:
        prompt = PM.render_without_attachment(file_title=file_title, article_text=text)

    if os.getenv("DEBUG_PROMPT", "0") == "1":
        try:
            dbgdir = OUTPUT_DIR / "debug"
            dbgdir.mkdir(parents=True, exist_ok=True)
            (dbgdir / f"{file_title}_PROMPT.txt").write_text(prompt, encoding="utf-8")
        except Exception:
            pass

    # 1) digita o prompt inteiro no editor
    _fill_editor(page, prompt)

    # 2) espera o botão habilitar + “pensadinha”
    wait_until_send_enabled(page)
    human_idle_med()  # 👈 apenas pausa; não envia nada

    # 3) mede quantos turnos do assistant existem e envia (APENAS clique)
    prev_assistant = _assistant_count(page)
    _send_keys_then_click(page)                 # 👈 envia pelo botão
    _ensure_outbound_or_pause(page, prev_assistant)

    # 4) espera terminar e lê exatamente o novo balão
    wait_for_response_complete(page)
    content = _get_assistant_text_by_index(page, prev_assistant)
    if os.getenv("DEBUG_RAW", "0") == "1":
        _save_debug(file_title, "raw", content)

    data = _extract_json_from_text(content)
    last_schema_error = None
    if data:
        try:
            return ArticleSummary(**data)
        except ValidationError as ve:
            last_schema_error = ve
            _save_debug(file_title, "raw_bad_schema", content)
    else:
        _save_debug(file_title, "raw_no_parse", content)

    # 5) tentativa de correção (fix JSON)
    for attempt in range(parse_fix_attempts):
        fix_prompt = PM.get_fix_prompt()
        _fill_editor(page, fix_prompt)
        wait_until_send_enabled(page)

        prev2 = _assistant_count(page)
        _send_keys_then_click(page)
        _ensure_outbound_or_pause(page, prev2)
        wait_for_response_complete(page)

        content2 = _get_assistant_text_by_index(page, prev2)
        if os.getenv("DEBUG_RAW", "0") == "1":
            _save_debug(file_title, f"raw_fix_{attempt+1}", content2)

        data2 = _extract_json_from_text(content2)
        if not data2:
            _save_debug(file_title, f"raw_validation_fix_no_parse_{attempt+1}", content2)
            continue
        try:
            return ArticleSummary(**data2)
        except ValidationError as ve2:
            last_schema_error = ve2
            _save_debug(file_title, f"raw_validation_fix_bad_schema_{attempt+1}", content2)

    if last_schema_error:
        raise ValueError(f"Validation error after fix: {last_schema_error}")
    raise ValueError("Could not parse JSON from model response.")
