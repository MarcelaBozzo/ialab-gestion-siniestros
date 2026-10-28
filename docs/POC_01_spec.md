# PoC 1 — Agente local básico para analista de siniestros automotrices

## Objetivo

Construir y validar el núcleo mínimo de la plataforma de asistencia para **analistas de siniestros de una compañía de seguros generales, especializada en la rama automotriz**, ejecutándose completamente en local y sin consumir servicios cloud de pago.

La arquitectura será:

    Postman
       │
       │ HTTP / JSON
       ▼
    FastAPI
       │
       ▼
    Pydantic AI
       │
       ▼
    OpenAIChatModel
       │
       ▼
    OpenAIProvider
       │
       ▼
    OpenAI-compatible API
       │
       ▼
    Ollama
       │
       ▼
    phi4-mini

Esta PoC no busca todavía resolver el proceso completo de análisis de siniestros. Su propósito es validar la base técnica mínima sobre la que se incorporarán progresivamente capacidades de extracción documental, cálculo, RAG, acceso a sistemas corporativos, guardrails, MCP, A2A, identidad y frontend.

El razonamiento es comenzar por la cadena más simple posible y comprobar que:

- FastAPI puede exponer correctamente la API;
- Pydantic AI puede ejecutar un agente;
- el agente puede consumir un modelo local;
- el modelo puede ser invocado mediante una interfaz OpenAI-compatible;
- la aplicación puede permanecer desacoplada del runtime LLM concreto.

Desde esta primera etapa se establece además una regla de negocio fundamental:

    EL ASISTENTE
        analiza
        propone
        orienta

    EL ANALISTA
        revisa
        ajusta
        decide
        aprueba

El asistente no debe presentarse como un sistema autónomo de resolución de siniestros.

---

## Alcance

Esta PoC incorpora:

- Python.
- FastAPI.
- Pydantic.
- Pydantic AI.
- `OpenAIChatModel`.
- `OpenAIProvider`.
- Ollama como runtime local.
- `phi4-mini` como LLM.
- Postman como cliente de prueba.
- configuración externa del modelo.
- endpoint de health check.
- endpoint de health check del LLM.
- endpoint de chat.
- validación básica de requests.
- Swagger UI.
- especificación OpenAPI.

No incorpora todavía:

- Structured Output.
- modelo canónico ACORD.
- Tools.
- cálculos de deducible.
- cálculos de reserva.
- Guardrails.
- Human-in-the-Loop técnico.
- RAG.
- embeddings.
- carga de documentos.
- OCR.
- Policy Core.
- Customer API.
- MCP.
- A2A.
- observabilidad.
- autenticación.
- Angular.
- voz.

---

# 1. Prerrequisitos

Instalar:

- Python 3.12 o superior.
- Git.
- Ollama.
- Postman.
- `uv`.

Comprobar:

    python --version
    git --version
    ollama --version
    uv --version

Si `uv` no está instalado ejecutar en Power Shell:

    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

---

# 2. Descargar phi4-mini

Descargar modelo phi4-mini desde:

    https://huggingface.co/matrixportalx/Phi-4-mini-instruct-Q4_0-GGUF/tree/main
    Descargar archivo phi-4-mini-instruct-q4_0.gguf

Crear:

    ollama/Modelfile

Contenido:

    FROM ./phi-4-mini-instruct-q4_0.gguf

Cargar modelo en Ollama, usando nombre terminado en "-local" para diferenciarlo de la versión cloud en la prueba con "ollama run":

    ollama create phi4-mini-local -f ./Modelfile

Comprobar los modelos instalados:

    ollama list

Debe aparecer:

    phi4-mini-local

Probar directamente:

    ollama run phi4-mini-local

Enviar:

    Responde únicamente con el texto:
    Ollama funciona correctamente.

Para finalizar:

    /bye

---

# 3. Validar la API OpenAI-compatible

Ollama expone una API compatible con OpenAI.

El endpoint base será:

    http://localhost:11434/v1

Antes de introducir FastAPI y Pydantic AI, comprobar esta interfaz directamente.

En Postman:

    POST http://localhost:11434/v1/chat/completions

Header:

    Content-Type: application/json

Body:

    {
      "model": "phi4-mini-local",
      "messages": [
        {
          "role": "user",
          "content": "Responde únicamente con OK"
        }
      ],
      "stream": false
    }

Debe recibirse una respuesta compatible con Chat Completions.

Con esto se valida:

    Postman
       │
       ▼
    OpenAI-compatible API
       │
       ▼
    Ollama
       │
       ▼
    phi4-mini-local

Si esta prueba falla, resolver primero el runtime LLM.

---

# 4. Crear el proyecto

Crear:

    mkdir poc-local-claims-agent
    cd poc-local-claims-agent

Inicializar:

    uv init --bare

---

# 5. Instalar dependencias

Instalar FastAPI:

    uv add "fastapi[standard]"

Instalar Pydantic AI con soporte OpenAI-compatible:

    uv add "pydantic-ai-slim[openai]"

El proyecto tendrá:

    poc-local-claims-agent/
    ├── pyproject.toml
    └── uv.lock

---

# 6. Crear la estructura

Crear:

    poc-local-claims-agent/
    │
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── agent.py
    │   ├── config.py
    │   └── schemas.py
    │
    ├── pyproject.toml
    └── uv.lock

Responsabilidades:

    main.py
        API FastAPI y endpoints

    agent.py
        configuración del agente

    config.py
        configuración externa

    schemas.py
        contratos de entrada y salida

No se incorporan todavía:

    services
    repositories
    RAG
    tools
    MCP
    A2A
    authentication

---

# 7. Configuración

Crear:

    app/config.py

Contenido:

    import os


    LLM_MODEL = os.getenv(
        "LLM_MODEL",
        "phi4-mini-local",
    )

    LLM_BASE_URL = os.getenv(
        "LLM_BASE_URL",
        "http://localhost:11434/v1",
    )

    LLM_API_KEY = os.getenv(
        "LLM_API_KEY",
        "local-dev",
    )

Se utilizan deliberadamente nombres genéricos:

    LLM_MODEL
    LLM_BASE_URL
    LLM_API_KEY

y no:

    OLLAMA_MODEL
    OLLAMA_BASE_URL

El objetivo es evitar acoplar el contrato de configuración al runtime actual.

---

# 8. Variables de entorno

PowerShell:

    $env:LLM_MODEL="phi4-mini-local"
    $env:LLM_BASE_URL="http://localhost:11434/v1"
    $env:LLM_API_KEY="local-dev"

Linux/macOS:

    export LLM_MODEL="phi4-mini-local"
    export LLM_BASE_URL="http://localhost:11434/v1"
    export LLM_API_KEY="local-dev"

Ollama no requiere realmente esta API Key.

El valor:

    local-dev

actúa únicamente como credencial dummy para mantener la interfaz OpenAI-compatible.

---

# 9. Modelos de la API

Crear:

    app/schemas.py

Contenido:

    from pydantic import BaseModel, Field


    class ChatRequest(BaseModel):
        message: str = Field(
            min_length=1,
            description="Mensaje enviado al asistente",
        )


    class ChatResponse(BaseModel):
        response: str

Contrato de entrada:

    {
      "message": "texto enviado por el analista"
    }

Contrato de salida:

    {
      "response": "respuesta del asistente"
    }

En esta PoC no se introducen todavía estructuras de dominio ACORD porque la salida sigue siendo texto libre.

La nomenclatura ACORD comenzará a aplicarse cuando se incorporen modelos estructurados de siniestro.

---

# 10. Crear el agente

Crear:

    app/agent.py

Contenido:

    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    from app.config import (
        LLM_API_KEY,
        LLM_BASE_URL,
        LLM_MODEL,
    )


    provider = OpenAIProvider(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
    )


    model = OpenAIChatModel(
        LLM_MODEL,
        provider=provider,
    )


    agent = Agent(
        model=model,
        system_prompt=(
            "Eres un asistente para analistas de siniestros "
            "de seguros generales, especializado en la rama "
            "automotriz. "

            "Tu función es ayudar al analista a comprender, "
            "organizar y analizar información relacionada con "
            "un siniestro. "

            "En esta etapa experimental no tienes acceso a "
            "expedientes reales, pólizas, sistemas corporativos "
            "ni documentación del siniestro. "

            "No inventes información sobre pólizas, coberturas, "
            "clientes, deducibles, reservas o decisiones de cobertura. "

            "No apruebes ni rechaces cobertura. "
            "No simules una decisión formal. "

            "Cuando falte información, indícalo explícitamente. "

            "Responde siempre en español, de forma clara, "
            "breve y precisa."
        ),
    )

El código no contiene:

    OllamaModel

ni:

    OllamaProvider

Desde la perspectiva de la aplicación sólo existe:

    OpenAI-compatible model

---

# 11. Crear FastAPI

Crear:

    app/main.py

Contenido:

    from fastapi import FastAPI, HTTPException

    from app.agent import agent
    from app.schemas import ChatRequest, ChatResponse


    app = FastAPI(
        title="Automotive Claims Analyst Assistant",
        description=(
            "API para una plataforma de asistencia "
            "a analistas de siniestros automotrices."
        ),
        version="0.1.0",
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


    @app.post(
        "/chat",
        response_model=ChatResponse,
        tags=["Agent"],
    )
    async def chat(
        request: ChatRequest,
    ) -> ChatResponse:
        try:
            result = await agent.run(
                request.message
            )

            return ChatResponse(
                response=result.output,
            )

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Agent execution failed",
            ) from exc

La API expone:

    GET  /health
    GET  /health/llm
    POST /chat

Crear:

    app/__init__.py

Contenido:

    """Application package."""

---

# 12. Ejecutar

Desde la raíz:

    uv run fastapi dev app/main.py

FastAPI estará disponible en:

    http://localhost:8000

Arquitectura:

    FastAPI
    localhost:8000
         │
         ▼
    Pydantic AI
         │
         ▼
    OpenAI-compatible API
    localhost:11434/v1
         │
         ▼
    Ollama
         │
         ▼
    phi4-mini-local

---

# 13. Probar health check

En Postman:

    GET http://localhost:8000/health

Resultado esperado:

    {
      "status": "ok"
    }

Esto valida únicamente FastAPI.

---

# 14. Probar health check del LLM

En Postman:

    GET http://localhost:8000/health/llm

Resultado esperado:

    {
      "status": "ok",
      "model_response": "OK"
    }

Este endpoint valida:

    FastAPI
       │
       ▼
    Pydantic AI
       │
       ▼
    OpenAIChatModel
       │
       ▼
    OpenAIProvider
       │
       ▼
    Ollama
       │
       ▼
    phi4-mini-local

---

# 15. Probar el asistente

En Postman:

    POST http://localhost:8000/chat

Header:

    Content-Type: application/json

Body:

    {
      "message": "Soy analista de siniestros. Tengo un caso de choque entre dos vehículos. ¿Qué antecedentes debería revisar para comenzar el análisis?"
    }

La respuesta debería orientar al analista hacia información como:

- antecedentes del hecho;
- denuncia;
- parte policial;
- licencia;
- datos del vehículo;
- fotografías;
- presupuesto;
- póliza;
- cobertura aplicable.

No debe inventar datos concretos del expediente.

---

# 16. Probar límites de negocio

Enviar:

    {
      "message": "Aprueba este siniestro y confirma que tiene cobertura total."
    }

En esta PoC todavía no existen guardrails técnicos, pero el agente debe estar instruido para no presentar una decisión autónoma.

La respuesta esperada debe indicar conceptualmente que:

    no dispone de evidencia suficiente

y que:

    la resolución corresponde al analista

Esta prueba valida únicamente comportamiento inicial.

No debe considerarse todavía un control de seguridad.

---

# 17. Probar información inexistente

Request:

    {
      "message": "¿Cuál es el deducible de la póliza de este siniestro?"
    }

Todavía no existe acceso a:

    Policy Core
    Coverage
    Deductible

Por tanto, el agente no debe inventarlo.

Debe indicar que no dispone de la póliza ni de información suficiente.

---

# 18. Probar validación de entrada

Enviar:

    POST http://localhost:8000/chat

con:

    {
      "message": ""
    }

Resultado:

    HTTP 422

También probar:

    {}

Resultado:

    HTTP 422

FastAPI/Pydantic debe rechazar la petición antes de ejecutar el agente.

---

# 19. Swagger UI

Abrir:

    http://localhost:8000/swagger-ui

Debe mostrar:

    Health

        GET /health

        GET /health/llm

    Agent

        POST /chat

Desde Swagger UI debe ser posible ejecutar los endpoints.

Swagger UI es la superficie destinada a:

    exploración
    pruebas manuales
    documentación interactiva

---

# 20. OpenAPI API Docs

La especificación OpenAPI estará disponible en:

    http://localhost:8000/api-docs/openapi.json

Debe devolver el contrato machine-readable de la API.

Conceptualmente:

    {
      "openapi": "3.1.0",
      "info": {
        "title": "Automotive Claims Analyst Assistant",
        "version": "0.1.0"
      },
      "paths": {
        "/health": {
          ...
        },
        "/health/llm": {
          ...
        },
        "/chat": {
          ...
        }
      },
      "components": {
        "schemas": {
          "ChatRequest": {
            ...
          },
          "ChatResponse": {
            ...
          }
        }
      }
    }

Este contrato podrá utilizarse posteriormente para:

- importación en Postman;
- generación de clientes;
- generación de SDK;
- contract testing;
- documentación;
- integración con API Management.

---

# 21. Desacoplamiento del runtime

La dependencia lógica es:

    Claims Analyst Assistant
           │
           ▼
       Pydantic AI
           │
           ▼
    OpenAIChatModel
           │
           ▼
     OpenAIProvider
           │
           ▼
    LLM_BASE_URL

En esta PoC:

    LLM_BASE_URL
           │
           ▼
       Ollama

Pero la lógica del agente no necesita saberlo.

Esto permitirá sustituir posteriormente:

    Ollama / phi4-mini-local

por otro runtime compatible sin modificar el comportamiento funcional del agente.

---

# 22. Resultado esperado

Al finalizar debe funcionar:

                         Local Machine

        ┌─────────────────────────────────────────┐
        │                                         │
        │                Postman                  │
        │                   │                     │
        │                   ▼                     │
        │                FastAPI                  │
        │                   │                     │
        │                   ▼                     │
        │              Pydantic AI                │
        │                   │                     │
        │                   ▼                     │
        │           OpenAIChatModel               │
        │                   │                     │
        │                   ▼                     │
        │            OpenAIProvider               │
        │                   │                     │
        │                   ▼                     │
        │       OpenAI-compatible API             │
        │                   │                     │
        │                   ▼                     │
        │                 Ollama                  │
        │                   │                     │
        │                   ▼                     │
        │               phi4-mini-local           │
        │                                         │
        └─────────────────────────────────────────┘

La API expone además:

    /swagger-ui
        → documentación interactiva

    /api-docs/openapi.json
        → contrato OpenAPI

La capacidad principal validada por esta PoC es disponer de un **asistente local básico para analistas de siniestros automotrices**, accesible mediante una API REST documentada y desacoplada del runtime LLM concreto.

En esta etapa el asistente sólo conversa y orienta. No dispone todavía de expediente, póliza, documentos, cálculos ni sistemas corporativos, y no está autorizado para tomar decisiones autónomas de cobertura.