from fastapi import FastAPI, HTTPException
from app.agent import agent
from app.schemas import ChatRequest, ChatResponse

app = FastAPI(
    title="Automotive Claims Analyst Assistant",
    description="API para asistencia local a analistas de siniestros automotrices.",
    version="0.1.0",
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
        result = await agent.run("Responde unicamente con la palabra OK.")
        return {"status": "ok", "model_response": str(result.output)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="LLM unavailable") from exc

@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = await agent.run(request.message)
        return ChatResponse(response=str(result.output))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Agent execution failed") from exc
