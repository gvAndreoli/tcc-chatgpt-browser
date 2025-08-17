# src/pipeline.py
from __future__ import annotations
import os
import time
from pathlib import Path

from src.config import (
    BASE_DIR,
    PDF_DIR,
    WAIT_AFTER_SEND_SEC,
)
from src.log import info, warn, error
from src.browser_utils import (
    launch_browser,
    open_chat_home,
    pause_until_ready_manual,
    ensure_ready,
    human_idle_long,
)
from src.pdf_utils import extract_text_from_pdf
from src.storage import (
    load_sent_files,
    save_sent_files,
    save_article_json,
    append_to_md,
)
from src.chatgpt_runner import send_prompt_and_get_json


# ---------- util ----------
def _ensure_dirs() -> None:
    """Garante a estrutura mínima de pastas do projeto."""
    (BASE_DIR / "PDF").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "outputs" / "json").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "outputs" / "debug").mkdir(parents=True, exist_ok=True)


def _wait_for_login_ready(page) -> None:
    """Abre o ChatGPT e BLOQUEIA até você concluir login/captcha e o input aparecer."""
    open_chat_home(page)
    pause_until_ready_manual(page, reason="login/captcha pendente")


# ---------- pipeline ----------
def main(max_count: int | None = None) -> None:
    """
    Executa o processamento:
      - escolhe até 'max_count' PDFs ainda não enviados
      - para cada PDF: anexa, envia prompt, espera resposta, salva JSON/MD e marca como enviado.
    """
    _ensure_dirs()

    # resolve max_count: CLI (--count) > ENV > default(1)
    if max_count is None:
        max_count = int(os.environ.get("MAX_ARTIGOS_POR_EXECUCAO", "1"))

    # coleta PDFs
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        warn("Nenhum PDF encontrado em ./PDF — adicione arquivos e rode novamente.")
        return

    # filtra os que faltam (com base no sent.json)
    sent = load_sent_files()
    todo = [p for p in pdfs if str(p) not in sent][:max_count]
    if not todo:
        info("Nenhum PDF novo para processar (todos já estão em outputs/sent.json).")
        return

    info(f"Processando {len(todo)} arquivo(s) nesta execução...")

    # 1 navegador/ sessão para toda a rodada
    pw, browser, page = launch_browser()
    try:
        _wait_for_login_ready(page)

        for idx, pdf_path in enumerate(todo, start=1):
            info(f"[{idx}/{len(todo)}] {pdf_path.name}")

            # extrai texto (fallback se algum PDF vier sem texto)
            text = extract_text_from_pdf(pdf_path)
            if not text.strip():
                warn(f"Sem texto extraído — pulando: {pdf_path.name}")
                continue

            try:
                # garante que não há captcha/overlay antes de enviar
                ensure_ready(page)

                # envia (com anexo) e valida schema internamente
                summary = send_prompt_and_get_json(
                    page=page,
                    file_title=pdf_path.stem,
                    text=text,
                    file_path=str(pdf_path),
                )
            except Exception as e:
                error(f"Falha ao obter/validar JSON para {pdf_path.name}: {e}")
                continue

            # persistência: JSON individual + consolidado.md
            save_article_json(pdf_path.stem, summary)
            append_to_md(summary)
            info(f"✅ Salvo JSON e consolidado para {pdf_path.name}")

            # marca como enviado e salva frequentemente (tolerante a falhas)
            sent.add(str(pdf_path))
            save_sent_files(sent)

            # respiro entre mensagens (evita bloqueios/limites)
            time.sleep(max(1.0, WAIT_AFTER_SEND_SEC))

        info("Concluído.")
    finally:
        # encerra tudo com segurança
        try:
            browser.close()
        except Exception:
            pass
        try:
            pw.stop()
        except Exception:
            pass


if __name__ == "__main__":
    # quando chamar direto: respeita ENV MAX_ARTIGOS_POR_EXECUCAO
    main()
