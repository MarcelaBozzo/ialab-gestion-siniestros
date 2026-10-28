from fastapi import FastAPI, HTTPException

from app.agent import agent, extract_claim_data
from app.config import EXTRACTION_MODEL
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ClaimData,
    ClaimExtractionRequest,
)


app = FastAPI(
    title="Automotive Claims Analyst Assistant",
    description=(
        "API para una plataforma de asistencia "
        "a analistas de siniestros automotrices."
    ),
    version="0.2.0",
    docs_url="/swagger-ui",
    openapi_url="/api-docs/openapi.json",
    redoc_url=None,
)


@app.get(
    "/health",
    tags=["Health"],
)
async def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.get(
    "/health/llm",
    tags=["Health"],
)
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


@app.get(
    "/health/extraction",
    tags=["Health"],
)
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
            detail="Extraction model unavailable or incompatible",
        ) from exc


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["Agent"],
)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = await agent.run(request.message)
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
        return await extract_claim_data(request.description)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Claim extraction failed",
        ) from exc
