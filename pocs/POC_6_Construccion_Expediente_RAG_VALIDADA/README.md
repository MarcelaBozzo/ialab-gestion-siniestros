# PoC 6 — Construcción automática del expediente y RAG documental

## Objetivo
Transformar los documentos asociados a un siniestro automotriz en un expediente estructurado y consultable. La PoC procesa PDF digitales, PDF escaneados e imágenes; extrae texto, construye `ClaimData`, conserva evidencia, detecta conflictos e indexa contenido en Qdrant para búsqueda semántica aislada por `ClaimNumber`.

## Requisitos
- macOS/Linux con Python `>=3.11`.
- `uv` para instalar dependencias y ejecutar el proyecto.
- Ollama local.
- Qdrant local.
- Tesseract OCR con idioma español `spa`.

En la sesión de validación se trabajó en macOS Apple Silicon. Pytest mostró Python 3.14.7 y se utilizó `uv 0.12.18`.

## Instalación
Desde la carpeta `proyecto/`:

```bash
uv sync
```

Verificar el idioma español de Tesseract:

```bash
tesseract --list-langs
```

Debe aparecer `spa`.

Verificar que los modelos estén disponibles en Ollama:

```bash
ollama list
```

## Modelos necesarios
Los nombres utilizados por la aplicación durante la validación fueron:

- `qwen2.5-instruct:7b` — chat / Tool Calling.
- `qwen2.5-extraction:1.5b` — Structured Extraction.
- `embeddinggemma` — embeddings de documentos y consultas.

Los modelos no se incluyen dentro del ZIP.

## Cómo ejecutar
Con Ollama y Qdrant activos, desde `proyecto/`:

```bash
uv run uvicorn app.main:app --reload
```

La API queda disponible en:

```text
http://127.0.0.1:8000
```

Qdrant debe estar disponible en:

```text
http://127.0.0.1:6333
```

Para ejecutar los tests unitarios:

```bash
uv run pytest tests/unit -v
```

La regresión completa logró ejecutarse durante la sesión con:

```bash
uv run pytest -v --import-mode=importlib
```

Resultado observado: `16 passed, 1 skipped`. El `skipped` correspondió al test de procesamiento documental al no pasar `TEST_DOCUMENT_ID` en esa ejecución conjunta; esa capacidad sí fue validada por separado con PDF digital, PNG y PDF escaneado.

## Endpoints o forma de probar
Endpoints principales:

- `POST /claims/{claim_number}/documents` — cargar documento.
- `GET /claims/{claim_number}/documents` — listar documentos.
- `DELETE /claims/{claim_number}/documents/{document_id}` — eliminar documento y sus datos asociados.
- `POST /claims/{claim_number}/process` — construir/procesar el expediente.
- `POST /claims/{claim_number}/context/search` — buscar evidencia documental.
- `POST /claims/extract` — extracción estructurada.
- `POST /chat` — chat de la aplicación.

Los archivos sintéticos usados para validar PDF digital, OCR de imagen y OCR de PDF escaneado están en `proyecto/samples/`.

El detalle completo de las pruebas, errores, correcciones y limitaciones reales de esta sesión está en `informe pruebas/informe_pruebas.md`.
