from pydantic import ValidationError

from app.a2a.errors import A2AInvalidResponse
from app.a2a.policy_client import policy_a2a_client
from app.schemas import (
    ClaimData,
    CoverageAnalysis,
    CoverageAnalysisRequest,
    EvidenceReference,
)


def build_coverage_analysis_request(
    claim_number: str,
    claim_data: ClaimData,
    relevant_document_evidence: list[EvidenceReference] | None = None,
) -> CoverageAnalysisRequest:
    claim_number = claim_number.strip()
    if not claim_number:
        raise ValueError("claim_number cannot be empty")

    if (
        claim_data.claim_number is not None
        and claim_data.claim_number != claim_number
    ):
        raise ValueError("claim_number does not match ClaimData")

    return CoverageAnalysisRequest(
        claim_number=claim_number,
        policy_number=claim_data.policy_number,
        claims_occurrence=claim_data.claims_occurrence,
        veh_info=claim_data.veh_info,
        relevant_document_evidence=(relevant_document_evidence or []),
    )


async def analyze_claim_coverage(
    request: CoverageAnalysisRequest,
) -> CoverageAnalysis:
    result = await policy_a2a_client.analyze_coverage(request)

    try:
        analysis = CoverageAnalysis.model_validate(result)
    except ValidationError as exc:
        raise A2AInvalidResponse(
            "Policy Agent returned an invalid CoverageAnalysis"
        ) from exc

    if analysis.claim_number != request.claim_number:
        raise A2AInvalidResponse(
            "Policy Agent returned an analysis for a different claim"
        )

    if (
        request.policy_number is not None
        and analysis.policy_number != request.policy_number
    ):
        raise A2AInvalidResponse(
            "Policy Agent returned an analysis for a different policy"
        )

    return analysis
