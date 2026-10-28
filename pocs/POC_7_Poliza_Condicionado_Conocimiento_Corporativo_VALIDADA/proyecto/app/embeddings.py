import httpx

from app.config import EMBEDDING_MODEL, OLLAMA_BASE_URL


async def _create_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={
                "model": EMBEDDING_MODEL,
                "input": text,
            },
        )
        response.raise_for_status()
        data = response.json()

    embeddings = data.get("embeddings")

    if not isinstance(embeddings, list) or not embeddings:
        raise ValueError(
            "Ollama did not return an embedding"
        )

    embedding = embeddings[0]

    if not isinstance(embedding, list) or not embedding:
        raise ValueError("Invalid embedding response")

    return [float(value) for value in embedding]


async def create_document_embedding(text: str) -> list[float]:
    formatted_text = "title: none | text: " f"{text}"
    return await _create_embedding(formatted_text)


async def create_query_embedding(query: str) -> list[float]:
    formatted_query = (
        "task: search result | "
        f"query: {query}"
    )
    return await _create_embedding(formatted_query)
