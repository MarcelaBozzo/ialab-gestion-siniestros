import re
from pathlib import Path

import pypdfium2 as pdfium
import pytesseract
from PIL import Image
from pypdf import PdfReader

from app.documents import get_claim_document, get_document_path
from app.schemas import ProcessedDocument


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]+(?=\n)", "", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.rstrip()


def extract_pdf_text(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(normalize_text(text))

    return pages


def extract_image_text(path: Path) -> str:
    with Image.open(path) as image:
        text = pytesseract.image_to_string(
            image,
            lang="spa",
        )

    return normalize_text(text)


def extract_scanned_pdf_text(path: Path) -> list[str]:
    pdf = pdfium.PdfDocument(str(path))
    pages: list[str] = []

    for page_index in range(len(pdf)):
        page = pdf[page_index]
        bitmap = page.render(scale=2.0)
        image = bitmap.to_pil()

        text = pytesseract.image_to_string(
            image,
            lang="spa",
        )

        pages.append(normalize_text(text))
        image.close()
        page.close()

    pdf.close()
    return pages


def pdf_requires_ocr(pages: list[str]) -> bool:
    meaningful_text = "".join(pages).strip()
    return len(meaningful_text) < 50


def process_pdf(path: Path) -> list[str]:
    pages = extract_pdf_text(path)

    if pdf_requires_ocr(pages):
        pages = extract_scanned_pdf_text(path)

    return [normalize_text(page) for page in pages]


async def process_document(
    claim_number: str,
    document_id: str,
) -> ProcessedDocument:
    document = get_claim_document(
        claim_number=claim_number,
        document_id=document_id,
    )

    if document is None:
        raise ValueError(
            "Document not found: "
            f"{document_id}"
        )

    path = get_document_path(
        claim_number=claim_number,
        document_id=document_id,
    )

    if path is None:
        raise FileNotFoundError(
            "Physical file not found "
            f"for document {document_id}"
        )

    content_type = (document.content_type or "").lower()

    if content_type == "application/pdf":
        pages = process_pdf(path)
    elif content_type in {"image/jpeg", "image/png"}:
        text = extract_image_text(path)
        pages = [text]
    else:
        raise ValueError(
            "Unsupported content type: "
            f"{content_type}"
        )

    return ProcessedDocument(
        document_id=document.document_id,
        claim_number=document.claim_number,
        document_type=document.document_type,
        pages=pages,
    )
