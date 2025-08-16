from PyPDF2 import PdfReader
from pathlib import Path
from src.config import TEXT_MAX_CHARS

def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    text_parts = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        text_parts.append(page_text)
    full_text = "\n".join(text_parts)
    return full_text[:TEXT_MAX_CHARS]
