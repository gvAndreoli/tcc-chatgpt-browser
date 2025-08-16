# Seletores robustos para diferentes versões da UI do ChatGPT

# 1) Editores possíveis (ordem de prioridade)
COMPOSER_VISIBLE = [
    "div[contenteditable='true'][data-testid*='composer']",
    "div[contenteditable='true'][data-gramm='false']",
    "div[contenteditable='true']",
    "textarea[name='prompt-textarea']",
    "textarea",
]

# 2) Botão de parar geração
STOP_GENERATING_BTN = (
    "button[aria-label*='Stop'], button:has-text('Stop generating'), "
    "button:has-text('Parar geração'), button:has-text('Parar')"
)

# 3) Última mensagem do assistente
LAST_MESSAGE_SELECTOR = (
    "[data-message-author-role='assistant'] .markdown, "
    "div[data-message-author-role='assistant'] .markdown, "
    "article:has([data-message-author-role='assistant']) .markdown, "
    "div.markdown"
)

# 4) Overlays/Banners comuns
OVERLAY_BUTTONS = [
    "button:has-text('Aceitar')",
    "button:has-text('Accept')",
    "button:has-text('I agree')",
    "button:has-text('Concordo')",
    "button:has-text('OK')",
    "button:has-text('Entendi')",
    "button:has-text('Got it')",
    "button:has-text('Fechar')",
    "button:has-text('Close')",
    "button:has-text('Continuar')",
    "button:has-text('Continue')",
    "button:has-text('Agree')",
]

# 5) Upload de arquivos
ATTACH_BUTTONS = [
    "button[aria-label*='Attach']",
    "button[aria-label*='Upload']",
    "button[aria-label*='Adicionar']",
    "button:has-text('Attach')",
    "button:has-text('Anexar')",
    "button:has-text('Upload')",
    "[data-testid*='attach']",
    "[data-testid*='upload']",
    "button:has(svg[aria-label*='Attach'])",
]
FILE_INPUTS = [
    "input[type='file']",
    "input[type='file'][multiple]",
    "input[data-testid*='file']",
    "input[accept*='pdf']",
]
FILE_PREVIEWS = [
    "[data-testid*='attachment']",
    "[data-testid*='file']",
    "[data-testid*='chip']",
]

# 6) Upload em andamento / concluído
UPLOAD_IN_PROGRESS = [
    "[aria-label*='Uploading']",
    "[data-state='uploading']",
    "div:has-text('Uploading')",
    "div:has-text('Carregando')",
    "div:has-text('Enviando')",
    "progress",
]
UPLOAD_DONE_HINTS = [
    "div:has-text('Uploaded')",
    "div:has-text('Concluído')",
    "div:has-text('Pronto')",
]

# 7) Enviar mensagem
SEND_BUTTONS = [
    "button[aria-label*='Send']",
    "button:has-text('Send')",
    "button:has-text('Enviar')",
    "[data-testid*='send']",
]
