# PoC 4 - Guardrails y Human-in-the-Loop

## Objetivo
Validar una capa de control para un asistente de analistas de siniestros automotrices: permitir que analice, calcule, proponga y redacte, evitando que tome o simule decisiones sensibles que deben quedar bajo revisión humana.

## Requisitos
- macOS, Linux o entorno equivalente con terminal.
- Python 3.12 o superior.
- `uv` para gestionar el entorno Python.
- Ollama ejecutándose localmente.
- Modelo `qwen2.5:7b-instruct` disponible en Ollama.

## Instalación
Desde la carpeta `proyecto/`:

```bash
uv sync
```

Configurar las variables usadas en la sesión:

```bash
export LLM_MODEL="qwen2.5:7b-instruct"
export LLM_BASE_URL="http://localhost:11434/v1"
export LLM_API_KEY="local-dev"
```

`EXTRACTION_MODEL` permanece en la configuración porque el proyecto conserva capacidades heredadas, pero ese modelo y sus endpoints no fueron validados en esta sesión.

## Modelos necesarios
Para el flujo principal validado de esta PoC:

```text
qwen2.5:7b-instruct
```

La definición original nombraba `qwen2.5-instruct:7b`; durante las pruebas el modelo realmente instalado y utilizado en Ollama fue `qwen2.5:7b-instruct`.

## Cómo ejecutar
Con Ollama activo, desde `proyecto/`:

```bash
uv run fastapi dev app/main.py
```

La API queda disponible normalmente en:

```text
http://127.0.0.1:8000
```

## Endpoints o forma de probar
Flujo principal probado:

```text
POST /chat
```

Documentación incluida por FastAPI:

```text
http://127.0.0.1:8000/swagger-ui
http://127.0.0.1:8000/api-docs/openapi.json
```

Chequeo básico disponible:

```text
GET /health
```

El proyecto conserva endpoints heredados de extracción (`/claims/extract` y `/health/extraction`), pero no fueron probados durante esta sesión y no deben considerarse validados por este respaldo.
