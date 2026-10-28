from app.agent import extract_claim_data
from app.chunking import create_document_chunks
from app.document_processing import process_document
from app.documents import list_claim_documents
from app.schemas import (
    ClaimData,
    ClaimDataConflict,
    ClaimsOccurrence,
    EvidenceSource,
    ExtractedEvidence,
    ProcessedClaimCase,
    ProcessedDocument,
    VehInfo,
)
from app.vector_store import replace_document_chunks


def document_text(document: ProcessedDocument) -> str:
    return "\n\n".join(
        page
        for page in document.pages
        if page.strip()
    )


async def extract_document_claim_data(
    document: ProcessedDocument,
) -> ClaimData:
    description = document_text(document)

    if not description.strip():
        raise ValueError(
            "Document has no extractable text"
        )

    return await extract_claim_data(description)


def flatten_claim_data(
    claim_data: ClaimData,
) -> dict[str, str]:
    result: dict[str, str] = {}

    if claim_data.policy_number:
        result["PolicyNumber"] = claim_data.policy_number

    occurrence = claim_data.claims_occurrence

    if occurrence:
        if occurrence.loss_dt:
            result["ClaimsOccurrence.LossDt"] = str(
                occurrence.loss_dt
            )
        if occurrence.loss_time:
            result["ClaimsOccurrence.LossTime"] = str(
                occurrence.loss_time
            )
        if occurrence.loss_desc:
            result["ClaimsOccurrence.LossDesc"] = (
                occurrence.loss_desc
            )
        if occurrence.loss_location_desc:
            result[
                "ClaimsOccurrence.LossLocationDesc"
            ] = occurrence.loss_location_desc

    vehicle = claim_data.veh_info

    if vehicle:
        if vehicle.vehicle_plate:
            result["VehInfo.vehicle_plate"] = (
                vehicle.vehicle_plate
            )
        if vehicle.manufacturer:
            result["VehInfo.manufacturer"] = vehicle.manufacturer
        if vehicle.model:
            result["VehInfo.model"] = vehicle.model
        if vehicle.model_year:
            result["VehInfo.model_year"] = str(
                vehicle.model_year
            )

    return result


def create_evidence(
    document: ProcessedDocument,
    claim_data: ClaimData,
) -> list[ExtractedEvidence]:
    flattened = flatten_claim_data(claim_data)
    evidence: list[ExtractedEvidence] = []

    for field_name, value in flattened.items():
        evidence.append(
            ExtractedEvidence(
                field_name=field_name,
                value=value,
                source=EvidenceSource(
                    document_id=document.document_id,
                    document_type=document.document_type,
                    page=None,
                ),
            )
        )

    return evidence


def unique_values(
    values: list[tuple[str, str]],
) -> list[str]:
    return list(
        dict.fromkeys(
            value
            for _, value in values
        )
    )


def detect_conflicts(
    extracted: list[tuple[ProcessedDocument, ClaimData]],
) -> list[ClaimDataConflict]:
    fields: dict[str, list[tuple[str, str]]] = {}

    for document, claim_data in extracted:
        flattened = flatten_claim_data(claim_data)

        for field_name, value in flattened.items():
            fields.setdefault(field_name, []).append(
                (document.document_id, value)
            )

    conflicts: list[ClaimDataConflict] = []

    for field_name, entries in fields.items():
        values = unique_values(entries)

        if len(values) <= 1:
            continue

        conflicts.append(
            ClaimDataConflict(
                field_name=field_name,
                values=values,
                document_ids=list(
                    dict.fromkeys(
                        document_id
                        for document_id, _ in entries
                    )
                ),
            )
        )

    return conflicts


def get_consistent_value(
    extracted: list[tuple[ProcessedDocument, ClaimData]],
    field_name: str,
) -> str | None:
    values: list[str] = []

    for _, claim_data in extracted:
        flattened = flatten_claim_data(claim_data)
        value = flattened.get(field_name)

        if value is not None:
            values.append(value)

    unique = list(dict.fromkeys(values))

    if len(unique) == 1:
        return unique[0]

    return None


def consolidate_claim_data(
    extracted: list[tuple[ProcessedDocument, ClaimData]],
) -> ClaimData:
    policy_number = get_consistent_value(
        extracted,
        "PolicyNumber",
    )
    loss_dt = get_consistent_value(
        extracted,
        "ClaimsOccurrence.LossDt",
    )
    loss_time = get_consistent_value(
        extracted,
        "ClaimsOccurrence.LossTime",
    )
    loss_desc = get_consistent_value(
        extracted,
        "ClaimsOccurrence.LossDesc",
    )
    loss_location = get_consistent_value(
        extracted,
        "ClaimsOccurrence.LossLocationDesc",
    )
    vehicle_plate = get_consistent_value(
        extracted,
        "VehInfo.vehicle_plate",
    )
    manufacturer = get_consistent_value(
        extracted,
        "VehInfo.manufacturer",
    )
    model = get_consistent_value(
        extracted,
        "VehInfo.model",
    )
    model_year = get_consistent_value(
        extracted,
        "VehInfo.model_year",
    )

    occurrence = ClaimsOccurrence()

    if any([loss_dt, loss_time, loss_desc, loss_location]):
        occurrence = ClaimsOccurrence(
            loss_dt=loss_dt,
            loss_time=loss_time,
            loss_desc=loss_desc,
            loss_location_desc=loss_location,
        )

    vehicle = None

    if any(
        [
            vehicle_plate,
            manufacturer,
            model,
            model_year,
        ]
    ):
        vehicle = VehInfo(
            vehicle_plate=vehicle_plate,
            manufacturer=manufacturer,
            model=model,
            model_year=(
                int(model_year)
                if model_year
                else None
            ),
        )

    return ClaimData(
        policy_number=policy_number,
        claims_occurrence=occurrence,
        veh_info=vehicle,
    )


async def process_claim_documents(
    claim_number: str,
) -> ProcessedClaimCase:
    documents = list_claim_documents(claim_number)

    if not documents:
        raise ValueError(
            "No documents found for "
            f"claim {claim_number}"
        )

    extracted: list[tuple[ProcessedDocument, ClaimData]] = []
    evidence: list[ExtractedEvidence] = []

    for document_metadata in documents:
        processed_document = await process_document(
            claim_number=claim_number,
            document_id=document_metadata.document_id,
        )

        claim_data = await extract_document_claim_data(
            processed_document
        )

        extracted.append(
            (processed_document, claim_data)
        )

        evidence.extend(
            create_evidence(
                processed_document,
                claim_data,
            )
        )

        chunks = create_document_chunks(
            processed_document
        )

        await replace_document_chunks(chunks)

    conflicts = detect_conflicts(extracted)
    consolidated = consolidate_claim_data(extracted)

    return ProcessedClaimCase(
        claim_number=claim_number,
        claim_data=consolidated,
        evidence=evidence,
        conflicts=conflicts,
    )
