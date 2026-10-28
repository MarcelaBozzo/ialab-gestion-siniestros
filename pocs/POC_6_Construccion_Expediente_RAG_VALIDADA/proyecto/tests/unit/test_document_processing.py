from app.document_processing import normalize_text, pdf_requires_ocr


def test_normalize_text():
    result = normalize_text(
        "  El   vehículo \n\n\n"
        " sufrió\t daños.  "
    )

    assert result == (
        " El vehículo\n"
        " sufrió daños."
    )


def test_pdf_requires_ocr_when_empty():
    assert pdf_requires_ocr([""]) is True


def test_pdf_requires_ocr_when_text_is_short():
    assert pdf_requires_ocr(["texto"]) is True


def test_pdf_does_not_require_ocr_when_text_exists():
    text = (
        "Este documento contiene una "
        "cantidad suficiente de texto "
        "para evitar la ejecución del "
        "proceso OCR."
    )

    assert pdf_requires_ocr([text]) is False
