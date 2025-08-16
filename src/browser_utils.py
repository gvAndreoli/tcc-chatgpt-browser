from __future__ import annotations
import os, time
from typing import Optional
from playwright.sync_api import sync_playwright

from src.config import PLAYWRIGHT_PROFILE, SLOW_MO_MS, HEADLESS, SEND_CHECK_INTERVAL_SEC, SEND_MAX_WAIT_SEC
from src.selectors import (
    OVERLAY_BUTTONS,
    COMPOSER_VISIBLE,
    ATTACH_BUTTONS,
    FILE_INPUTS,
    FILE_PREVIEWS,
    UPLOAD_IN_PROGRESS,
    UPLOAD_DONE_HINTS,
    SEND_BUTTONS,
)

COMMON_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-default-browser-check",
    "--disable-dev-shm-usage",
    "--disable-gpu",
]

def launch_browser():
    pw = sync_playwright().start()
    browser = pw.chromium.launch_persistent_context(
        user_data_dir=str(PLAYWRIGHT_PROFILE),
        headless=HEADLESS,
        slow_mo=SLOW_MO_MS,
        args=COMMON_ARGS,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="pt-BR",
    )
    page = browser.new_page()
    return pw, browser, page

def open_chat_home(page):
    page.bring_to_front()
    page.goto("https://chat.openai.com/", wait_until="domcontentloaded")
    dismiss_overlays(page)

# ---------- editor / overlays ---------- #
def find_visible_editor(page):
    for sel in COMPOSER_VISIBLE:
        loc = page.locator(sel)
        try:
            if loc.count() > 0:
                cand = loc.first
                if cand.is_visible():
                    return cand
        except Exception:
            continue
    return None

def _input_visible(page) -> bool:
    return find_visible_editor(page) is not None

def looks_like_human_check(page) -> bool:
    try:
        for sel in [
            "iframe[src*='hcaptcha.com']",
            "iframe[src*='challenges.cloudflare.com']",
            "iframe[title*='challenge']",
        ]:
            if page.locator(sel).count() > 0:
                return True
        for t in [
            "Verify you are human",
            "Verifique se você é humano",
            "I am human",
            "Sou humano",
            "Please stand by, while we are checking your browser",
            "Checking if the site connection is secure",
        ]:
            if page.get_by_text(t, exact=False).count() > 0:
                return True
    except Exception:
        pass
    return False

def dismiss_overlays(page):
    try:
        for sel in OVERLAY_BUTTONS:
            btn = page.locator(sel)
            if btn.count() > 0 and btn.first.is_visible():
                try:
                    btn.first.click(timeout=1000)
                except Exception:
                    pass
    except Exception:
        pass

def pause_until_ready_manual(page, reason: str = "login/captcha pendente"):
    print("\n────────────────────────────────────────────────────────")
    print("⏸  Automação pausada:", reason)
    print("    1) Conclua login/captcha e feche popups no navegador.")
    print("    2) Quando o campo de mensagem do chat aparecer, pressione ENTER aqui.")
    print("────────────────────────────────────────────────────────\n")

    while True:
        input("Pressione ENTER depois de resolver (vou verificar o input)... ")
        dismiss_overlays(page)
        if _input_visible(page):
            print("✅ Campo de mensagem detectado. Retomando automação.\n")
            return
        if looks_like_human_check(page):
            print("⚠️  Ainda detecto verificação humana. Resolva e tente novamente.")
        else:
            print("⚠️  Ainda não vejo o campo de mensagem. Aguarde e tente novamente.")

def ensure_ready(page):
    dismiss_overlays(page)
    if looks_like_human_check(page) or not _input_visible(page):
        pause_until_ready_manual(page)

# ---------- upload / anexo ---------- #
def _has_preview(page, filename: str) -> bool:
    try:
        if page.get_by_text(filename, exact=False).count() > 0:
            return True
    except Exception:
        pass
    for sel in FILE_PREVIEWS:
        try:
            if page.locator(sel).count() > 0:
                return True
        except Exception:
            pass
    return False

def _is_uploading(page) -> bool:
    for sel in UPLOAD_IN_PROGRESS:
        try:
            if page.locator(sel).count() > 0:
                return True
        except Exception:
            pass
    return False

def _upload_done_hints(page) -> bool:
    for sel in UPLOAD_DONE_HINTS:
        try:
            if page.locator(sel).count() > 0:
                return True
        except Exception:
            pass
    return False

def wait_for_upload_complete(page, filename: str, soft_timeout: float = 30.0, hard_timeout: float = 90.0):
    start = time.time()
    # 1) preview
    while time.time() - start < soft_timeout:
        dismiss_overlays(page)
        if _has_preview(page, filename):
            break
        time.sleep(0.4)
    else:
        print("\n────────────────────────────────────────────────────────")
        print("⏸  Não detectei o preview do arquivo ainda.")
        print("    Anexe manualmente e confirme quando aparecer o chip/preview.")
        print("────────────────────────────────────────────────────────\n")
        while True:
            input("Pressione ENTER quando o preview do arquivo aparecer... ")
            dismiss_overlays(page)
            if _has_preview(page, filename):
                break

    # 2) fim do upload
    start2 = time.time()
    while True:
        dismiss_overlays(page)
        if not _is_uploading(page) or _upload_done_hints(page):
            return
        if time.time() - start2 > soft_timeout:
            print("\n────────────────────────────────────────────────────────")
            print("⏸  O arquivo ainda parece estar subindo.")
            print("    Confira no navegador. Quando terminar, pressione ENTER aqui.")
            print("────────────────────────────────────────────────────────\n")
            input("Pressione ENTER quando o upload tiver terminado... ")
            dismiss_overlays(page)
            if not _is_uploading(page) or _upload_done_hints(page):
                return
            start2 = time.time()
        if time.time() - start > hard_timeout:
            raise RuntimeError("Upload do arquivo não finalizou a tempo.")
        time.sleep(0.5)

def attach_file(page, file_path: str, wait_seconds: float = 15.0):
    filename = os.path.basename(file_path)

    def _try_set_on_any_input() -> bool:
        for sel in FILE_INPUTS:
            inp = page.locator(sel)
            if inp.count() > 0:
                try:
                    inp.first.set_input_files(file_path, timeout=1500)
                    return True
                except Exception:
                    continue
        return False

    dismiss_overlays(page)

    # 1) direto no input
    if _try_set_on_any_input():
        wait_for_upload_complete(page, filename)
        return

    # 2) clicar em botões e tentar novamente
    for btn_sel in ATTACH_BUTTONS:
        btn = page.locator(btn_sel)
        if btn.count() > 0 and btn.first.is_visible():
            try:
                btn.first.click(timeout=1500)
                time.sleep(0.3)
                if _try_set_on_any_input():
                    wait_for_upload_complete(page, filename)
                    return
            except Exception:
                continue

    # 3) interceptar chooser
    try:
        with page.expect_file_chooser(timeout=2500) as fc_info:
            clicked = False
            for btn_sel in ATTACH_BUTTONS:
                btn = page.locator(btn_sel)
                if btn.count() > 0 and btn.first.is_visible():
                    try:
                        btn.first.click(timeout=1500)
                        clicked = True
                        break
                    except Exception:
                        continue
            if not clicked:
                raise RuntimeError("Nenhum botão de anexar abriu o seletor de arquivos.")
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)
        wait_for_upload_complete(page, filename)
        return
    except Exception:
        pass

    # 4) manual
    print("\n────────────────────────────────────────────────────────")
    print("⏸  Anexe o arquivo MANUALMENTE agora.")
    print(f"    → Clique em 'Attach/Anexar' e selecione: {filename}")
    print("    → Depois que aparecer o chip/preview e terminar 'Uploading', pressione ENTER aqui.")
    print("────────────────────────────────────────────────────────\n")
    input("Pressione ENTER quando o arquivo estiver ANEXADO e o upload CONCLUÍDO... ")
    dismiss_overlays(page)
    wait_for_upload_complete(page, filename)


def _send_button_enabled(page) -> bool:
    """Retorna True se existir um botão de Enviar visível e habilitado."""
    for sel in SEND_BUTTONS:
        btn = page.locator(sel)
        if btn.count() > 0:
            b = btn.first
            try:
                if b.is_visible():
                    # tenta pelos atributos clássicos
                    aria = b.get_attribute("aria-disabled") or ""
                    disabled = b.get_attribute("disabled")
                    if disabled is None and aria.lower() not in ("true", "1"):
                        return True
            except Exception:
                continue
    return False

def wait_until_send_enabled(page, timeout: float = None, interval: float = None):
    """Espera até o botão de enviar estar habilitado e nenhum upload em andamento."""
    timeout = timeout or SEND_MAX_WAIT_SEC
    interval = interval or SEND_CHECK_INTERVAL_SEC

    start = time.time()
    while True:
        dismiss_overlays(page)
        # se houver upload rolando, nem tenta enviar ainda
        if not _is_uploading(page) and _send_button_enabled(page):
            return True

        if time.time() - start > timeout:
            # dá uma última chance: deixa o usuário confirmar manualmente
            print("\n────────────────────────────────────────────────────────")
            print("⏸  O botão 'Enviar' não liberou a tempo.")
            print("    Confirme no navegador se o upload terminou e o botão está ativo.")
            print("    Depois clique em 'Enviar' manualmente e pressione ENTER aqui.")
            print("────────────────────────────────────────────────────────\n")
            input("Pressione ENTER após enviar manualmente (ou quando liberar)... ")
            return True

        time.sleep(interval)