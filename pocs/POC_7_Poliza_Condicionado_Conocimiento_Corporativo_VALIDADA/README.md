# PoC 7 — Póliza, condicionado y conocimiento corporativo

## Objetivo

Validar que la plataforma pueda complementar los hechos de un siniestro con información verificable de una póliza y con conocimiento corporativo recuperado desde el condicionado, manteniendo separadas las fuentes y su trazabilidad. Esta PoC no determina automáticamente si un siniestro está cubierto.

## Requisitos

- Python 3.11 o superior.
- `uv`.
- Ollama activo en `http://localhost:11434`.
- Qdrant activo en `http://localhost:6333`.
- Docker Desktop, si se desea levantar Qdrant de la misma forma utilizada durante la sesión validada.

El proyecto mantiene las dependencias Python en `proyecto/pyproject.toml`.

## Instalación

Desde la carpeta `proyecto/`:

```bash
uv sync
```

Si Qdrant se ejecuta con Docker, la forma utilizada durante las pruebas fue:

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

## Modelos necesarios

Modelos locales disponibles y utilizados en la configuración final:

- `qwen2.5-instruct:7b` — modelo principal del asistente.
- `qwen2.5-extraction:1.5b` — extracción estructurada heredada de la PoC anterior.
- `embeddinggemma` — embeddings para Qdrant.

## Cómo ejecutar

Desde `proyecto/`, abrir dos terminales adicionales además de Qdrant/Ollama.

Policy Core Mock:

```bash
uv run fastapi dev app/policy_core.py --port 8001
```

Claims API:

```bash
uv run fastapi dev app/main.py --port 8000
```

## Endpoints o forma de probar

Consulta de póliza existente:

```bash
curl -i http://localhost:8000/policies/POL-123456
```

Consulta de póliza inexistente:

```bash
curl -i http://localhost:8000/policies/POL-999999
```

Indexación del corpus corporativo incluido:

```bash
curl -X POST http://localhost:8000/knowledge/index
```

Búsqueda corporativa filtrada por producto y cobertura:

```bash
curl -X POST http://localhost:8000/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query":"¿Qué indica el condicionado sobre daños por colisión?","product_code":"AUTO_STANDARD","coverage_cd":"COLLISION","limit":5}'
```

Documentación:

- Swagger UI: `http://localhost:8000/swagger-ui`
- OpenAPI: `http://localhost:8000/api-docs/openapi.json`
