# PoC 8 - Secure RAG y trazabilidad de evidencia

## Objetivo
Validar que Claim RAG y Corporate RAG traten el contenido recuperado como no confiable, filtren instrucciones sospechosas y entreguen respuestas respaldadas por evidencia trazable.

## Requisitos
- Python 3.11
- Ollama activo
- Qdrant disponible en `http://localhost:6333`
- Tesseract disponible para OCR cuando corresponda

## Instalación
Desde `proyecto/`:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install "fastapi[standard]" "pydantic-ai-slim[openai]" httpx pypdf pillow pytesseract pypdfium2 qdrant-client pytest pytest-asyncio
```

Nota: durante la validación `pip install -e .` falló por descubrimiento automático de paquetes de setuptools, por lo que la instalación validada fue la instalación explícita de dependencias anterior.

## Modelos necesarios
- `qwen2.5-instruct:7b`
- `qwen2.5-extraction:1.5b`
- `embeddinggemma`

## Cómo ejecutar
1. Iniciar Ollama y Qdrant.
2. Desde `proyecto/`, activar `.venv`.
3. Ejecutar:

```bash
uvicorn app.main:app --reload
```

Swagger UI: `http://localhost:8000/swagger-ui`
OpenAPI: `http://localhost:8000/api-docs/openapi.json`

## Endpoints o forma de probar
Endpoints principales de Secure RAG:
- `POST /claims/{claim_number}/context/secure-search`
- `POST /knowledge/secure-search`
- `POST /claims/{claim_number}/context/answer`

Endpoints auxiliares usados durante las pruebas:
- `POST /claims/{claim_number}/documents`
- `POST /claims/{claim_number}/process`
- `POST /claims/{claim_number}/context/search`
- `POST /knowledge/index`

Los fixtures de prueba quedan en `tests/fixtures/` y en `data/corporate/conditions/`.
