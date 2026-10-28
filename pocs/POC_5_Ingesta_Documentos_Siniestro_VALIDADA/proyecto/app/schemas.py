from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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
