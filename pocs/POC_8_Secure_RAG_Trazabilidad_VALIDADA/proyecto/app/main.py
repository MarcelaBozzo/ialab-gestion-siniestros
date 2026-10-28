from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.openapi.utils import get_openapi

from app.agent import (
    GROUNDED_INSUFFICIENT_EVIDENCE,
    agent,
    extract_claim_data,
    run_grounded_answer,
)
from app.claim_processing import process_claim_documents
from app.config import EXTRACTION_MODEL, QDRANT_CLAIM_COLLECTION
from app.documents import (
    delete_claim_document,
    get_claim_document,
    list_claim_documents,
    save_claim_document,
)
from app.guardrails import validate_input, validate_output
from app.policies import get_policy
from app.corporate_knowledge import (
    index_corporate_documents,
    search_corporate_knowledge,
)
from app.retrieval import search_claim_documents
from app.secure_rag import (
    build_grounded_context,
    evidence_from_claim_chunk,
    secure_search_claim_documents,
    secure_search_corporate_knowledge,
)
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
    Policy,
    CorporateKnowledgeChunk,
    CorporateKnowledgeSearchRequest,
    GroundedAnswer,
    ContentClassification,
    ContentGuardrailDecision,
    SecureCorporateSearchRequest,
    SecureSearchRequest,
)
from app.vector_store import delete_document_chunks, qdrant_client


app = FastAPI(
    title="Automotive Claims Analyst Assistant",
    description=(
        "API para una plataforma de asistencia "
        "a analistas de siniestros automotrices."
    ),
    version="0.8.0",
    docs_url="/swagger-ui",
    openapi_url="/api-docs/openapi.json",
    redoc_url=None,
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    schemas = schema.setdefault("components", {}).setdefault("schemas", {})

    schemas["ContentClassification"] = {
        "type": "string",
        "enum": [item.value for item in ContentClassification],
        "title": "ContentClassification",
    }

    decision_schema = ContentGuardrailDecision.model_json_schema(
        ref_template="#/components/schemas/{model}"
    )
    decision_schema.pop("$defs", None)
    schemas["ContentGuardrailDecision"] = decision_schema

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


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


@app.get(
    "/policies/{policy_number}",
    response_model=Policy,
    tags=["Policies"],
)
async def get_policy_endpoint(policy_number: str) -> Policy:
    return await get_policy(policy_number)


@app.post(
    "/knowledge/index",
    tags=["Corporate Knowledge"],
)
async def index_corporate_knowledge_endpoint() -> dict[str, int | str]:
    try:
        return await index_corporate_documents()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Corporate conditions directory is missing",
        ) from exc


@app.post(
    "/knowledge/search",
    response_model=list[CorporateKnowledgeChunk],
    tags=["Corporate Knowledge"],
)
async def search_corporate_knowledge_endpoint(
    request: CorporateKnowledgeSearchRequest,
) -> list[CorporateKnowledgeChunk]:
    return await search_corporate_knowledge(
        query=request.query,
        product_code=request.product_code,
        coverage_cd=request.coverage_cd,
        limit=request.limit,
    )

INSUFFICIENT_EVIDENCE = GROUNDED_INSUFFICIENT_EVIDENCE


@app.post(
    "/claims/{claim_number}/context/secure-search",
    response_model=list[DocumentChunk],
    tags=["Secure RAG"],
)
async def secure_claim_search_endpoint(
    claim_number: str,
    request: SecureSearchRequest,
) -> list[DocumentChunk]:
    try:
        return await secure_search_claim_documents(
            claim_number=claim_number,
            query=request.query,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Secure claim retrieval is unavailable",
        ) from exc


@app.post(
    "/knowledge/secure-search",
    response_model=list[CorporateKnowledgeChunk],
    tags=["Secure RAG"],
)
async def secure_corporate_search_endpoint(
    request: SecureCorporateSearchRequest,
) -> list[CorporateKnowledgeChunk]:
    try:
        return await secure_search_corporate_knowledge(
            query=request.query,
            product_code=request.product_code,
            coverage_cd=request.coverage_cd,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid corporate search filters",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Secure corporate retrieval is unavailable",
        ) from exc


@app.post(
    "/claims/{claim_number}/context/answer",
    response_model=GroundedAnswer,
    tags=["Secure RAG"],
)
async def grounded_claim_answer_endpoint(
    claim_number: str,
    request: SecureSearchRequest,
) -> GroundedAnswer:
    try:
        chunks = await secure_search_claim_documents(
            claim_number=claim_number,
            query=request.query,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Secure claim retrieval is unavailable",
        ) from exc

    if not chunks:
        return GroundedAnswer(
            answer=INSUFFICIENT_EVIDENCE,
            evidence=[],
        )

    context = build_grounded_context(
        query=request.query,
        chunks=chunks,
    )

    try:
        answer = await run_grounded_answer(context)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Grounded answer generation is unavailable",
        ) from exc

    if answer.strip() == INSUFFICIENT_EVIDENCE:
        return GroundedAnswer(
            answer=INSUFFICIENT_EVIDENCE,
            evidence=[],
        )

    evidence = [
        evidence_from_claim_chunk(chunk)
        for chunk in chunks
    ]
    return GroundedAnswer(
        answer=answer,
        evidence=evidence,
    )

