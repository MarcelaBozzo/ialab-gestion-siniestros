from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile

from app.documents import (
    delete_claim_document,
    get_claim_document,
    list_claim_documents,
    save_claim_document,
)
from app.schemas import ClaimDocument, DocumentType


app = FastAPI(
    title="Claims Analyst Assistant - PoC 5",
    description=(
        "PoC 5: ingesta, validación básica, metadata y almacenamiento local "
        "de documentos de siniestros automotrices. Los archivos se consideran "
        "UNTRUSTED CONTENT y no son interpretados por un LLM en esta etapa."
    ),
    version="0.5.0",
    docs_url="/swagger-ui",
    openapi_url="/api-docs/openapi.json",
)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "poc": "5"}


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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Document upload failed") from exc


@app.get(
    "/claims/{claim_number}/documents",
    response_model=list[ClaimDocument],
    tags=["Documents"],
)
async def get_claim_documents(claim_number: str) -> list[ClaimDocument]:
    try:
        return list_claim_documents(claim_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get(
    "/claims/{claim_number}/documents/{document_id}",
    response_model=ClaimDocument,
    tags=["Documents"],
)
async def get_claim_document_endpoint(
    claim_number: str,
    document_id: str,
) -> ClaimDocument:
    try:
        document = get_claim_document(
            claim_number=claim_number,
            document_id=document_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found for claim {claim_number}",
        )

    return document


@app.delete(
    "/claims/{claim_number}/documents/{document_id}",
    status_code=204,
    tags=["Documents"],
)
async def delete_claim_document_endpoint(
    claim_number: str,
    document_id: str,
) -> Response:
    try:
        deleted = delete_claim_document(
            claim_number=claim_number,
            document_id=document_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found for claim {claim_number}",
        )

    return Response(status_code=204)
