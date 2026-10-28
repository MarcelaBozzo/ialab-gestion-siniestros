# PoC 2 — Modelo estructurado del siniestro automotriz

## Objetivo

Transformar una descripción de un siniestro automotriz escrita en lenguaje natural en un modelo `ClaimData` estructurado, tipado y validado, manteniendo además el chat heredado de la PoC 1.

## Requisitos

- Python 3.12 o superior.
- `uv` instalado.
- Ollama instalado y ejecutándose localmente.
- Modelos de Ollama:
  - `phi4-mini`
  - `qwen2.5:7b-instruct`

> La definición original proponía `qwen2.5-extraction:1.5b`. Durante las pruebas ese modelo no superó el caso de información ausente. La configuración final validada utiliza `qwen2.5:7b-instruct`.

## Instalación

Desde la carpeta `proyecto`:

```bash
uv sync
```

Instalar los modelos si todavía no están disponibles:

```bash
ollama pull phi4-mini
ollama pull qwen2.5:7b-instruct
```

## Modelos necesarios

- Chat: `phi4-mini`
- Extracción: `qwen2.5:7b-instruct`

Valores por defecto del proyecto:

```text
LLM_MODEL=phi4-mini
EXTRACTION_MODEL=qwen2.5:7b-instruct
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=local-dev
```

## Cómo ejecutar

```bash
cd proyecto
uv run fastapi dev app/main.py
```

La API queda disponible normalmente en `http://127.0.0.1:8000`.

## Endpoints o forma de probar

- `GET /health`
- `GET /health/llm`
- `GET /health/extraction`
- `POST /chat`
- `POST /claims/extract`
- Swagger UI: `http://127.0.0.1:8000/swagger-ui`
- OpenAPI: `http://127.0.0.1:8000/api-docs/openapi.json`

Ejemplo de extracción:

```bash
curl -s -X POST 127.0.0.1:8000/claims/extract \
  -H "Content-Type: application/json" \
  -d '{"description":"El siniestro ocurrió el 5 de septiembre de 2026 a las 18:30 en Avenida Providencia, Santiago. El Toyota Corolla patente ABCD12 chocó contra otro vehículo. La póliza es POL-123456."}'
```

El detalle de las pruebas ejecutadas, correcciones, desviaciones y limitaciones está en `informe pruebas/informe_pruebas.md`.
