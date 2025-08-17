import os
from pathlib import Path

# === Paths base ===
BASE_DIR = Path(__file__).resolve().parents[1]
PDF_DIR = BASE_DIR / "PDF"
OUTPUT_DIR = BASE_DIR / "outputs"
JSON_DIR = OUTPUT_DIR / "json"
SENT_LOG = OUTPUT_DIR / "sent.json"
MD_PATH = OUTPUT_DIR / "consolidado.md"  # usado no storage

# === Playwright / Navegador ===
PLAYWRIGHT_PROFILE = BASE_DIR / ".playwright"
SLOW_MO_MS = int(os.environ.get("SLOW_MO_MS", "120"))
HEADLESS = os.environ.get("HEADLESS", "0") == "1"

# === Controles de execução ===
MAX_ARTIGOS_POR_EXECUCAO = int(os.environ.get("MAX_ARTIGOS_POR_EXECUCAO", "1"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "1"))
TEXT_MAX_CHARS = int(os.environ.get("TEXT_MAX_CHARS", "20000"))
WAIT_AFTER_SEND_SEC = float(os.environ.get("WAIT_AFTER_SEND_SEC", "6"))

# === Prompts externos / variantes ===
PROMPTS_DIR = BASE_DIR / "prompts"
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

# Variantes: 'cot', 'baseline', 'contrast'
PROMPT_VARIANT = os.getenv("PROMPT_VARIANT", "cot").strip().lower()

# Usa prompts/<variant>_*.txt; pode sobrepor com ENV
PROMPT_WITH_ATTACHMENT_FILE = Path(
    os.getenv("PROMPT_WITH_ATTACHMENT_FILE", str(PROMPTS_DIR / f"{PROMPT_VARIANT}_with_attachment.txt"))
)
PROMPT_WITHOUT_ATTACHMENT_FILE = Path(
    os.getenv("PROMPT_WITHOUT_ATTACHMENT_FILE", str(PROMPTS_DIR / f"{PROMPT_VARIANT}_without_attachment.txt"))
)
FIX_JSON_PROMPT_FILE = Path(
    os.getenv("FIX_JSON_PROMPT_FILE", str(PROMPTS_DIR / "fix_json.txt"))
)

# compat opcional
CONSOLIDATED_MD = MD_PATH

# === Controles de envio ===
SEND_CHECK_INTERVAL_SEC = float(os.environ.get("SEND_CHECK_INTERVAL_SEC", "4"))
SEND_MAX_WAIT_SEC = float(os.environ.get("SEND_MAX_WAIT_SEC", "240"))  # tempo máximo esperando liberar


# === Jitter (aleatoriedade leve) para parecer humano 
# Usados nas esperas curtas/médias/longas (segundos)
JITTER_SHORT = (0.15, 0.45)
JITTER_MED   = (0.60, 1.40)
JITTER_LONG  = (3.00, 6.00)