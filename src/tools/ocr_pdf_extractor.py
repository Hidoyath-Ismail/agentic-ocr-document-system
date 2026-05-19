from __future__ import annotations

from pathlib import Path
from typing import Optional

from pdf2image import convert_from_path
import pytesseract


def extract_text_from_scanned_pdf(
    pdf_path: str | Path,
    *,
    first_page: int = 1,
    last_page: Optional[int] = None,
    dpi: int = 200,
) -> str:
    """
    Convert PDF pages to images using Poppler (pdftoppm) via pdf2image,
    then run Tesseract OCR on each page and return the combined text.

    Assumes:
      - Poppler is installed and pdftoppm is on PATH
      - Tesseract is installed and tesseract is on PATH
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path.resolve()}")

    images = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        first_page=first_page,
        last_page=last_page,
    )

    texts: list[str] = []
    for img in images:
        page_text = pytesseract.image_to_string(img)
        texts.append(page_text.strip())

    return "\n\n".join([t for t in texts if t])
