from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="Mensaje enviado al asistente",
    )


class ChatResponse(BaseModel):
    response: str


class ClaimsOccurrence(BaseModel):
    loss_dt: date | None = None
    loss_time: time | None = None
    loss_cause_cd: str | None = None
    loss_cause_desc: str | None = None
    loss_desc: str | None = None
    loss_location_desc: str | None = None


class VehInfo(BaseModel):
    veh_identification_number: str | None = None
    vehicle_plate: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    model_year: int | None = None


class ClaimsDriverInfo(BaseModel):
    full_name: str | None = None
    driver_license_number: str | None = None


class ClaimsPartyInfo(BaseModel):
    party_role: str | None = None
    full_name: str | None = None
    vehicle_plate: str | None = None


class ClaimData(BaseModel):
    claim_number: str | None = None
    claim_type_cd: str | None = None
    claim_status_cd: str | None = None
    policy_number: str | None = None

    claims_occurrence: ClaimsOccurrence = Field(
        default_factory=ClaimsOccurrence,
    )

    veh_info: VehInfo | None = None
    claims_driver_info: ClaimsDriverInfo | None = None
    claims_party_info: list[ClaimsPartyInfo] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_extracted_information(self):
        occurrence = self.claims_occurrence

        has_occurrence = any(
            [
                occurrence.loss_dt,
                occurrence.loss_time,
                occurrence.loss_cause_cd,
                occurrence.loss_cause_desc,
                occurrence.loss_desc,
                occurrence.loss_location_desc,
            ]
        )

        has_data = any(
            [
                self.claim_number,
                self.claim_type_cd,
                self.claim_status_cd,
                self.policy_number,
                self.veh_info,
                self.claims_driver_info,
                self.claims_party_info,
                has_occurrence,
            ]
        )

        if not has_data:
            raise ValueError(
                "No claim information could be extracted"
            )

        return self


class ClaimExtractionRequest(BaseModel):
    description: str = Field(
        min_length=1,
        description=(
            "Descripción del siniestro "
            "en lenguaje natural."
        ),
    )


class DeductibleCalculation(BaseModel):
    loss_amount: Decimal
    deductible_percentage: Decimal
    minimum_deductible: Decimal
    calculated_deductible: Decimal


class ReserveCalculation(BaseModel):
    estimated_loss_amount: Decimal
    deductible_amount: Decimal
    calculated_reserve: Decimal


class RequestClassification(str, Enum):
    IN_SCOPE = "IN_SCOPE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    SUSPICIOUS = "SUSPICIOUS"


class GuardrailDecision(BaseModel):
    classification: RequestClassification
    reason: str


class AssistantAction(str, Enum):
    ANALYZE = "ANALYZE"
    CALCULATE = "CALCULATE"
    PROPOSE = "PROPOSE"
    DRAFT = "DRAFT"


class RestrictedAction(str, Enum):
    APPROVE_COVERAGE = "APPROVE_COVERAGE"
    REJECT_COVERAGE = "REJECT_COVERAGE"
    SEND_COMMUNICATION = "SEND_COMMUNICATION"
    CLOSE_CLAIM = "CLOSE_CLAIM"
    AUTHORIZE_PAYMENT = "AUTHORIZE_PAYMENT"


class DocumentType(str, Enum):
    CLAIM_REPORT = "CLAIM_REPORT"
    DRIVER_LICENSE = "DRIVER_LICENSE"
    POLICE_REPORT = "POLICE_REPORT"
    DAMAGE_PHOTO = "DAMAGE_PHOTO"
    REPAIR_ESTIMATE = "REPAIR_ESTIMATE"
    OTHER = "OTHER"


class ClaimDocument(BaseModel):
    document_id: str
    claim_number: str
    document_type: DocumentType
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime

    @property
    def stored_filename(self) -> str:
        suffix_map = {
            "application/pdf": ".pdf",
            "image/jpeg": ".jpg",
            "image/png": ".png",
        }
        suffix = suffix_map.get(
            self.content_type,
            "",
        )
        return f"{self.document_id}{suffix}"


class ProcessedDocument(BaseModel):
    document_id: str
    claim_number: str
    document_type: DocumentType
    pages: list[str]


class EvidenceSource(BaseModel):
    document_id: str
    document_type: DocumentType
    page: int | None = None


class ExtractedEvidence(BaseModel):
    field_name: str
    value: str
    source: EvidenceSource


class ClaimDataConflict(BaseModel):
    field_name: str
    values: list[str]
    document_ids: list[str]


class DocumentChunk(BaseModel):
    claim_number: str
    document_id: str
    document_type: DocumentType
    page: int
    chunk_index: int
    content: str


class ProcessedClaimCase(BaseModel):
    claim_number: str
    claim_data: ClaimData
    evidence: list[ExtractedEvidence] = Field(
        default_factory=list
    )
    conflicts: list[ClaimDataConflict] = Field(
        default_factory=list
    )


class ClaimContextSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
