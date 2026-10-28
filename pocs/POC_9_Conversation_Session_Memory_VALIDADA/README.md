# PoC 9 — Conversation Session Memory

## Objetivo
Validar memoria conversacional persistente dentro de una sesión para que el Claims Analyst Agent mantenga continuidad entre requests, sin confundir lo conversado con hechos autoritativos del siniestro.

## Requisitos
- macOS/Linux con Terminal.
- Python 3.11 o superior. La validación se realizó con Python 3.14.7.
- `uv` instalado.
- Ollama activo en `http://localhost:11434`.
- Para los componentes RAG heredados de PoC 8, Qdrant según la configuración existente del proyecto.

## Instalación
Desde la carpeta `proyecto/`:

```bash
uv sync
```

Durante la validación se utilizó Pydantic AI 2.54.0. La compatibilidad con esa versión está incorporada en `app/guardrails.py` mediante `PromptedOutput`.

## Modelos necesarios
Modelos usados en la versión validada:

```text
qwen2.5-instruct:7b
qwen2.5-extraction:1.5b
embeddinggemma:latest
```

Puedes verificarlos con:

```bash
ollama list
```

## Cómo ejecutar
Desde `proyecto/`:

```bash
uv run uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`.

Tests de memoria:

```bash
uv run pytest tests/unit -v
uv run pytest tests/integration/test_conversation_service.py -v
```

Los tests de integración requieren Ollama activo.

## Endpoints o forma de probar
Swagger UI:

```text
http://127.0.0.1:8000/swagger-ui
```

OpenAPI:

```text
http://127.0.0.1:8000/api-docs/openapi.json
```

Endpoints principales de esta PoC:

```text
POST   /sessions
GET    /sessions/{session_id}
DELETE /sessions/{session_id}
POST   /assistant/query
```

Flujo mínimo: crear una sesión con `POST /sessions`, reutilizar su `session_id` en varios `POST /assistant/query` y comprobar que una pregunta posterior pueda resolverse usando el contexto previo. La memoria recuerda lo conversado, pero no reemplaza ClaimData, evidencia documental ni tools como fuente de verdad.
