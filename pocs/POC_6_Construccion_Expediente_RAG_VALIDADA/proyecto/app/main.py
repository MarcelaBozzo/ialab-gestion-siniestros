from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)

from app.agent import agent, extract_claim_data
from app.claim_processing import process_claim_documents
from app.config import EXTRACTION_MODEL, QDRANT_CLAIM_COLLECTION
from app.documents import (
    delete_claim_document,
    get_claim_document,
    list_claim_documents,
    save_claim_document,
)
from app.guardrails import validate_input, validate_output
from app.retrieval import search_claim_documents
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ClaimContextSearchRequest,
    ClaimData,
    ClaimDocument,
    ClaimExtractionRequest,
    DocumentChunk,
    DocumentType,
    ProcessedClaimCase,
    RequestClassification,
)
from app.vector_store import delete_document_chunks, qdrant_client


app = FastAPI(
    title="Automotive Claims Analyst Assistant",
    description=(
        "API para una plataforma de asistencia "
        "a analistas de siniestros automotrices."
    ),
    version="0.6.0",
    docs_url="/swagger-ui",
    openapi_url="/api-docs/openapi.json",
    redoc_url=None,
)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/llm", tags=["Health"])
async def health_llm() -> dict[str, str]:
    try:
        result = await agent.run(
            "Responde únicamente con la palabra OK."
        )
        return {
            "status": "ok",
            "model_response": result.output,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="LLM unavailable",
        ) from exc


@app.get("/health/extraction", tags=["Health"])
async def health_extraction() -> dict[str, str]:
    try:
        claim = await extract_claim_data(
            "El accidente ocurrió el "
            "5 de septiembre de 2026 en Santiago."
        )

        if claim.claims_occurrence.loss_dt is None:
            raise ValueError("LossDt was not extracted")

        return {
            "status": "ok",
            "model": EXTRACTION_MODEL,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Extraction model unavailable "
                "or incompatible"
            ),
        ) from exc


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["Agent"],
)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        input_decision = await validate_input(
            request.message
        )

        if (
            input_decision.classification
            != RequestClassification.IN_SCOPE
        ):
            return ChatResponse(
                response=(
                    "No puedo procesar esa solicitud. "
                    "Este asistente está limitado al análisis "
                    "de siniestros automotrices."
                )
            )

        result = await agent.run(request.message)
        output_decision = await validate_output(result.output)

        if (
            output_decision.classification
            != RequestClassification.IN_SCOPE
        ):
            return ChatResponse(
                response=(
                    "No puedo proporcionar la respuesta generada."
                )
            )

        return ChatResponse(response=result.output)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Agent execution failed",
        ) from exc


@app.post(
    "/claims/extract",
    response_model=ClaimData,
    tags=["Claims"],
)
async def extract_claim(
    request: ClaimExtractionRequest,
) -> ClaimData:
    try:
        return await extract_claim_data(
            request.description
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Claim extraction failed",
        ) from exc


@app.post(
    "/claims/{claim_number}/documents",
    response_model=ClaimDocument,
    tags=["Documents"],
)
async def upload_claim_document(
    claim_number: str,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
) -> ClaimDocument:
    try:
        return await save_claim_document(
            claim_number=claim_number,
            document_type=document_type,
            file=file,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Document upload failed",
        ) from exc


@app.get(
    "/claims/{claim_number}/documents",
    response_model=list[ClaimDocument],
    tags=["Documents"],
)
async def get_claim_documents(
    claim_number: str,
) -> list[ClaimDocument]:
    try:
        return list_claim_documents(claim_number)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.get(
    "/claims/{claim_number}/documents/{document_id}",
    response_model=ClaimDocument,
    tags=["Documents"],
)
async def get_claim_document_endpoint(
    claim_number: str,
    document_id: str,
) -> ClaimDocument:
    document = get_claim_document(
        claim_number=claim_number,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Document not found for "
                f"claim {claim_number}"
            ),
        )

    return document


@app.delete(
    "/claims/{claim_number}/documents/{document_id}",
    status_code=204,
    tags=["Claims"],
)
async def delete_claim_document_endpoint(
    claim_number: str,
    document_id: str,
) -> Response:
    deleted = delete_claim_document(
        claim_number=claim_number,
        document_id=document_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=(
                "Document not found for "
                f"claim {claim_number}"
            ),
        )

    if await qdrant_client.collection_exists(
        QDRANT_CLAIM_COLLECTION
    ):
        await delete_document_chunks(document_id)

    return Response(status_code=204)


@app.post(
    "/claims/{claim_number}/process",
    response_model=ProcessedClaimCase,
    tags=["Claims"],
)
async def process_claim_endpoint(
    claim_number: str,
) -> ProcessedClaimCase:
    try:
        return await process_claim_documents(claim_number)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@app.post(
    "/claims/{claim_number}/context/search",
    response_model=list[DocumentChunk],
    tags=["Claims"],
)
async def search_claim_context_endpoint(
    claim_number: str,
    request: ClaimContextSearchRequest,
) -> list[DocumentChunk]:
    try:
        return await search_claim_documents(
            claim_number=claim_number,
            query=request.query,
            limit=request.limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Claim document search failed",
        ) from exc
