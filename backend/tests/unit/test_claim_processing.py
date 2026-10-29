from datetime import date

from app.claim_processing import consolidate_claim_data
from app.schemas import (
    ClaimData,
    ClaimsOccurrence,
    DocumentType,
    ProcessedDocument,
)


def extracted_document(
    document_id: str,
    document_type: DocumentType,
    loss_dt: date,
):
    document = ProcessedDocument(
        document_id=document_id,
        claim_number="CLM-1",
        document_type=document_type,
        pages=["test"],
    )
    claim_data = ClaimData(
        policy_number="POL-123456",
        claims_occurrence=ClaimsOccurrence(loss_dt=loss_dt)
    )
    return document, claim_data


def test_repair_estimate_date_does_not_override_loss_date():
    result = consolidate_claim_data(
        [
            extracted_document(
                "claim-report",
                DocumentType.CLAIM_REPORT,
                date(2026, 9, 5),
            ),
            extracted_document(
                "repair-estimate",
                DocumentType.REPAIR_ESTIMATE,
                date(2026, 9, 20),
            ),
        ]
    )

    assert result.claims_occurrence.loss_dt == date(2026, 9, 5)


def test_conflicting_authoritative_loss_dates_remain_unresolved():
    result = consolidate_claim_data(
        [
            extracted_document(
                "claim-report",
                DocumentType.CLAIM_REPORT,
                date(2026, 9, 5),
            ),
            extracted_document(
                "police-report",
                DocumentType.POLICE_REPORT,
                date(2026, 9, 6),
            ),
        ]
    )

    assert result.claims_occurrence.loss_dt is None
