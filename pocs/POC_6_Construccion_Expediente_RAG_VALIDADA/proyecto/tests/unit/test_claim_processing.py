from app.claim_processing import detect_conflicts, document_text
from app.schemas import ClaimData, DocumentType, ProcessedDocument


def test_document_text():
    document = ProcessedDocument(
        document_id="DOC-001",
        claim_number="CLM-000123",
        document_type=DocumentType.CLAIM_REPORT,
        pages=[
            "Página uno",
            "",
            "Página tres",
        ],
    )

    result = document_text(document)

    assert result == (
        "Página uno\n\n"
        "Página tres"
    )


def test_detect_policy_number_conflict():
    document_a = ProcessedDocument(
        document_id="DOC-A",
        claim_number="CLM-000123",
        document_type=DocumentType.CLAIM_REPORT,
        pages=["Documento A"],
    )

    document_b = ProcessedDocument(
        document_id="DOC-B",
        claim_number="CLM-000123",
        document_type=DocumentType.POLICE_REPORT,
        pages=["Documento B"],
    )

    extracted = [
        (
            document_a,
            ClaimData(policy_number="POL-123456"),
        ),
        (
            document_b,
            ClaimData(policy_number="POL-999999"),
        ),
    ]

    conflicts = detect_conflicts(extracted)

    assert len(conflicts) == 1
    assert conflicts[0].field_name == "PolicyNumber"
    assert set(conflicts[0].values) == {
        "POL-123456",
        "POL-999999",
    }
