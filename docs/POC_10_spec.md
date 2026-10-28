# PoC 10 — Integración con el sistema de clientes mediante API REST

## Objetivo

Incorporar al asistente la capacidad de consultar el **sistema corporativo de clientes** mediante una API REST para verificar si el declarante corresponde a un cliente de la compañía y, cuando sea necesario, recuperar información personal relevante para el análisis del siniestro.

Hasta la PoC 9, la plataforma dispone de:

    documentos del siniestro
        ↓
    Structured Extraction
        ↓
    ClaimData
        ↓
    Secure RAG
        ↓
    Conversation Session Memory

El asistente puede comprender el expediente, recuperar evidencia documental segura y mantener continuidad entre diferentes turnos de una conversación.

Sin embargo, los documentos aportados por el denunciante no son necesariamente suficientes para determinar:

    si el declarante es cliente

    qué identificador tiene en el sistema corporativo

    cuáles son sus datos registrados

    si los datos informados coinciden con los registros corporativos

En esta PoC incorporaremos:

    Customer API

como sistema externo de referencia.

El flujo será:

    Claims Analyst Agent
             │
             ▼
       Customer Service
             │
             ▼
         REST API
             │
             ▼
      Customer System

El objetivo principal es demostrar que el asistente puede **enriquecer el expediente utilizando información corporativa estructurada**, manteniendo una frontera clara entre:

    datos extraídos de documentos

    datos recuperados del sistema de clientes

    memoria conversacional

    evidencia documental

El sistema de clientes continúa siendo la fuente de verdad para:

    customer information

La conversación no debe convertirse en fuente autoritativa de esos datos.

---

# 1. Alcance y problema de negocio

Esta PoC incorpora:

- integración REST con Customer API;
- cliente HTTP desacoplado;
- configuración de endpoint;
- búsqueda de cliente;
- verificación de existencia;
- recuperación controlada de perfil;
- modelos de dominio para cliente;
- separación entre verificación y recuperación de PII;
- timeouts;
- manejo de errores;
- incorporación de datos de cliente al análisis;
- integración con Conversation Session Memory;
- continuidad conversacional utilizando `session_id`;
- data minimization;
- tests unitarios;
- tests de integración;
- endpoints de diagnóstico;
- Swagger UI;
- OpenAPI.

Se mantienen:

- FastAPI;
- Pydantic AI;
- Ollama;
- `qwen2.5-instruct:7b`;
- Structured Extraction;
- `ClaimData`;
- EmbeddingGemma;
- Qdrant;
- Claim RAG;
- Corporate RAG;
- Secure RAG;
- Guardrails;
- Tools determinísticas;
- Conversation Session Memory.

No se incorporan todavía:

- MCP;
- A2A;
- Microsoft Entra ID;
- OBO;
- Azure API Management;
- Azure AI Search;
- Azure OpenAI;
- Microsoft Foundry.

La integración se realizará inicialmente mediante:

    REST directo

El reemplazo posterior por:

    MCP

permitirá comprobar que el agente puede mantener el mismo comportamiento cambiando únicamente la frontera de integración.

---

### Problema de negocio

En un siniestro automotriz, el expediente puede contener información del declarante.

Por ejemplo:

    nombre

    RUT

    teléfono

    email

Pero estos datos provienen de:

    documentos

    formulario de denuncia

    OCR

y por tanto no necesariamente representan la información corporativa vigente.

El asistente debe poder realizar:

    información del denunciante
             │
             ▼
       Customer API
             │
       ┌─────┴─────┐
       │           │
       ▼           ▼
    encontrado   no encontrado
       │
       ▼
   customer data

---

### Capacidades requeridas

La plataforma podrá:

- verificar si una persona existe como cliente;
- identificar el `customer_id`;
- recuperar información personal cuando sea necesaria;
- comparar información declarada con información corporativa;
- utilizar esa información como contexto para el analista.

Por ejemplo:

    Declarante:
        RUT 12.345.678-5

              ↓

        Customer API

              ↓

    Customer found:
        customer_id = CUST-000123

---

### Límites de la PoC

La PoC no debe:

- modificar información del cliente;
- crear clientes;
- eliminar clientes;
- actualizar datos personales;
- utilizar información de otra persona;
- recuperar más PII de la necesaria;
- almacenar el perfil completo dentro de Conversation Memory.

La integración será:

    READ ONLY

---

# 2. Fuentes de información y arquitectura

A partir de esta PoC tendremos:

    Conversation Memory
        → qué veníamos hablando

    ClaimData
        → hechos extraídos del expediente

    Secure RAG
        → evidencia documental

    Customer API
        → datos corporativos del cliente

No deben confundirse.

---

### Memoria conversacional

La PoC 9 incorporó:

    session_id

y:

    ConversationSession

Esto permite conversaciones como:

    Usuario:
    "¿El declarante es cliente?"

    Asistente:
    "Sí, está registrado como cliente."

    Usuario:
    "¿Cuál es su correo?"

El segundo turno puede interpretarse porque:

    ConversationSession
        → recuerda que estamos hablando
          del mismo declarante

Pero el correo no debe recuperarse desde:

    respuesta anterior almacenada

La plataforma debe volver a utilizar:

    Customer API

cuando el dato corporativo sea necesario.

---

### Autoridad de los datos

La regla será:

    Conversation Memory
        → contexto

    Customer API
        → customer truth

Por ejemplo:

    Assistant anteriormente dijo:
        "El correo es A"

pero posteriormente:

    Customer API dice:
        "El correo es B"

El valor utilizado debe ser:

    B

porque:

    Customer API
        =
    source of truth

---

### Arquitectura de integración

La arquitectura será:

                         ANALISTA
                            │
                            ▼
                     Conversation
                            │
                       session_id
                            │
                            ▼
                      Claims API
                            │
                  ┌─────────┴─────────┐
                  │                   │
                  ▼                   ▼
        Conversation Memory        ClaimData
                  │                   │
                  └─────────┬─────────┘
                            ▼
                   Claims Analyst Agent
                            │
            ┌───────────────┼────────────────┐
            │               │                │
            ▼               ▼                ▼
       Secure RAG         Tools       Customer Service
                                             │
                                             ▼
                                        Customer API
                                             │
                                             ▼
                                      Customer System

---

# 3. Customer API y minimización de datos

Para esta PoC asumiremos que existe una API REST corporativa.

Por ejemplo:

    GET
    /customers/by-national-id/{national_id}

y:

    GET
    /customers/{customer_id}

La consulta de perfil acepta `fields` como query parameter, por ejemplo `GET /customers/CUST-000123?fields=email`. La respuesta contiene siempre `customer_id`, `national_id` y `full_name`, además únicamente del campo de contacto solicitado. El servidor rechaza campos no permitidos.

La primera operación permite:

    verificar existencia

La segunda permite:

    obtener perfil

---

### Minimización de datos

No debemos recuperar siempre el perfil completo.

Separaremos:

    verify_customer()

de:

    get_customer_profile()

Por ejemplo:

    "¿Es cliente?"

debe ejecutar:

    verify_customer()

No:

    get_customer_profile()

Esto reduce exposición innecesaria de:

    email

    teléfono

    dirección

    otros datos personales

---

### Nomenclatura de negocio

Cuando exista un término ACORD equivalente utilizaremos la nomenclatura correspondiente.

Para la integración utilizaremos:

    Party

como concepto de persona u organización relacionada con el siniestro.

Mantendremos:

    Customer

para el concepto propio del sistema corporativo de clientes cuando no corresponda sustituirlo.

---

# 4. Modelos y contexto de análisis

Agregar en:

    app/schemas.py

```python
from pydantic import (
    BaseModel,
    EmailStr,
)


class CustomerVerification(BaseModel):
    customer_found: bool
    customer_id: str | None = None


class CustomerProfile(BaseModel):
    customer_id: str
    national_id: str
    full_name: str

    email: EmailStr | None = None
    phone_number: str | None = None
    address: str | None = None
```

Para aplicar minimización, `customer_id`, `national_id` y `full_name` identifican el perfil; de los campos opcionales de contacto sólo se solicita y devuelve el requerido (`email`, `phone_number` o `address`). Los otros campos opcionales quedan en `None`.

---

### Dependencia EmailStr

Si todavía no está disponible:

    uv add email-validator

Pydantic utilizará esta dependencia para:

    EmailStr

Si el proyecto aún no tiene estas dependencias, agregar también `httpx` al entorno de aplicación y `pytest`, `pytest-asyncio` y `uvicorn` al entorno de desarrollo:

```text
uv add httpx email-validator
uv add --dev pytest pytest-asyncio fastapi-cli
```

---

### Separación de ClaimData

No modificar:

```python
class ClaimData(...)
```

para incluir directamente:

```python
customer_profile: CustomerProfile
```

`ClaimData` representa información del siniestro.

Los datos corporativos del cliente provienen de una fuente diferente.

---

### Contexto de análisis

Cuando sea necesario combinar información puede crearse una estructura de aplicación.

Agregar:

```python
class ClaimAnalysisContext(BaseModel):
    claim_number: str
    claim_data: ClaimData

    customer: CustomerProfile | None = None
```

Esta estructura:

    no sustituye ClaimData

Sólo agrupa información para una ejecución concreta.

---

# 5. Configuración y cliente HTTP

Modificar:

    app/config.py

Agregar:

```python
import os
from urllib.parse import urlsplit


CUSTOMER_API_BASE_URL = os.getenv(
    "CUSTOMER_API_BASE_URL",
    "http://localhost:8081",
).rstrip("/")

CUSTOMER_API_TIMEOUT_SECONDS = float(
    os.getenv(
        "CUSTOMER_API_TIMEOUT_SECONDS",
        "10",
    )
)

customer_api_url = urlsplit(CUSTOMER_API_BASE_URL)
if (
    customer_api_url.scheme not in {"http", "https"}
    or not customer_api_url.netloc
    or customer_api_url.username
    or customer_api_url.password
    or customer_api_url.query
    or customer_api_url.fragment
):
    raise ValueError("Invalid CUSTOMER_API_BASE_URL")

if CUSTOMER_API_TIMEOUT_SECONDS <= 0:
    raise ValueError("CUSTOMER_API_TIMEOUT_SECONDS must be positive")
```

La URL debe ser la raíz del servicio, sin credenciales ni parámetros sensibles. Si el proyecto ya centraliza configuración en `pydantic-settings`, agregar allí estas variables en lugar de crear una segunda fuente de configuración. Rechazar al iniciar una URL vacía o que no tenga esquema y host.

---

### Variables de entorno

Configurar:

    CUSTOMER_API_BASE_URL=http://localhost:8081

    CUSTOMER_API_TIMEOUT_SECONDS=10

---

### Cliente HTTP

Crear:

    app/customer_client.py

Imports:

```python
from urllib.parse import quote

import httpx
from pydantic import ValidationError
from app.config import (
    CUSTOMER_API_BASE_URL,
    CUSTOMER_API_TIMEOUT_SECONDS,
)
from app.schemas import (
    CustomerProfile,
    CustomerVerification,
)
```

---

### Excepciones específicas

Agregar:

```python
class CustomerApiError(
    RuntimeError
):
    pass


class CustomerApiUnavailable(
    CustomerApiError
):
    pass


class CustomerNotFound(
    CustomerApiError
):
    pass
```

Esto evita que el resto de la aplicación dependa directamente de:

    httpx exceptions

Centralizar la creación del cliente permite inyectar `httpx.MockTransport` en tests sin levantar un servidor:

```python
def _create_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=CUSTOMER_API_TIMEOUT_SECONDS,
    )
```

Centralizar la traducción de estados HTTP evita tratar un error del sistema como una búsqueda negativa:

```python
def _raise_for_customer_response(
    response: httpx.Response,
) -> None:
    if response.status_code >= 500:
        raise CustomerApiUnavailable(
            f"Customer API returned HTTP {response.status_code}"
        )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise CustomerApiError(
            f"Customer API returned HTTP {response.status_code}"
        ) from exc
```

---

### Normalización de national_id

Crear:

```python
def normalize_national_id(
    national_id: str,
) -> str:

    normalized = (
        national_id
        .replace(".", "")
        .replace("-", "")
        .strip()
        .upper()
    )

    if not normalized:
        raise ValueError(
            "national_id cannot be empty"
        )

    return normalized
```

Para esta PoC la función sólo normaliza formato.

No implementa todavía validación completa del dígito verificador.

---

### Verificación de cliente

Agregar:

```python
async def verify_customer(
    national_id: str,
) -> CustomerVerification:

    normalized = normalize_national_id(
        national_id
    )

    url = (
        f"{CUSTOMER_API_BASE_URL}"
        "/customers/by-national-id/"
        f"{quote(normalized, safe='')}"
    )

    try:
        async with _create_http_client() as client:

            response = await client.get(
                url
            )

    except httpx.RequestError as exc:
        raise CustomerApiUnavailable(
            "Customer API unavailable"
        ) from exc

    if response.status_code == 404:
        return CustomerVerification(
            customer_found=False,
            customer_id=None,
        )

    _raise_for_customer_response(response)

    try:
        data = response.json()
    except ValueError as exc:
        raise CustomerApiError(
            "Customer API returned invalid JSON"
        ) from exc

    if not isinstance(data, dict):
        raise CustomerApiError(
            "Customer API response must be a JSON object"
        )

    customer_id = data.get(
        "customer_id"
    )

    if not isinstance(customer_id, str) or not customer_id.strip():
        raise CustomerApiError(
            "Customer API response "
            "does not contain customer_id"
        )

    return CustomerVerification(
        customer_found=True,
        customer_id=customer_id,
    )
```

---

### Recuperación de perfil

Agregar:

```python
async def get_customer_profile(
    customer_id: str,
    requested_field: str,
) -> CustomerProfile:

    if not customer_id or not customer_id.strip():
        raise ValueError(
            "customer_id cannot be empty"
        )

    if requested_field not in {"email", "phone_number", "address"}:
        raise ValueError("Unsupported customer profile field")

    url = (
        f"{CUSTOMER_API_BASE_URL}"
        f"/customers/{quote(customer_id, safe='')}"
    )

    try:
        async with _create_http_client() as client:

            response = await client.get(
                url,
                params={"fields": requested_field},
            )

    except httpx.RequestError as exc:
        raise CustomerApiUnavailable(
            "Customer API unavailable"
        ) from exc

    if response.status_code == 404:
        raise CustomerNotFound(
            "Customer not found"
        )

    _raise_for_customer_response(response)

    try:
        data = response.json()
        return CustomerProfile.model_validate(data)
    except ValidationError as exc:
        raise CustomerApiError(
            "Customer API returned an invalid customer profile"
        ) from exc
    except ValueError as exc:
        raise CustomerApiError(
            "Customer API returned invalid JSON"
        ) from exc
```

---

# 6. Customer Service y frontera de integración

El agente no debería utilizar directamente:

    httpx

ni conocer URLs.

Crear:

    app/customer_service.py

```python
from app.customer_client import (
    CustomerApiError,
    CustomerNotFound,
    get_customer_profile,
    normalize_national_id,
    verify_customer,
)
from app.schemas import (
    CustomerProfile,
    CustomerVerification,
)
```

---

### Servicio de verificación

Agregar:

```python
async def verify_claimant_customer(
    national_id: str,
) -> CustomerVerification:

    return await verify_customer(
        national_id
    )
```

Esta frontera será útil posteriormente para sustituir:

    REST directo

por:

    MCP

---

### Servicio de perfil

Agregar:

```python
async def get_claimant_customer_profile(
    national_id: str,
    requested_field: str,
) -> CustomerProfile:

    verification = await verify_customer(national_id)
    if not verification.customer_found or not verification.customer_id:
        raise CustomerNotFound("Claimant is not a customer")

    profile = await get_customer_profile(
        verification.customer_id,
        requested_field,
    )
    if normalize_national_id(profile.national_id) != normalize_national_id(national_id):
        raise CustomerApiError(
            "Customer profile does not match the claimant"
        )

    return profile
```

Importar `CustomerApiError` y `normalize_national_id` desde `customer_client.py`. El servicio vuelve a resolver el `customer_id` desde el identificador del declarante y verifica la coincidencia del perfil; así la tool no acepta un ID de cliente arbitrario ni depende de un ID antiguo recordado en la conversación.

---

### Frontera para migrar a MCP

Aunque inicialmente parezca una capa pequeña:

    Agent
      ↓
    Customer Service
      ↓
    Customer Client
      ↓
    REST

permite posteriormente reemplazar:

    Customer Client REST

por:

    Customer MCP Client

sin modificar el agente.

---

# 7. Tools y políticas del Claims Analyst Agent

El Claims Analyst Agent necesita poder decidir cuándo verificar al declarante.

En:

    app/tools.py

o el módulo utilizado actualmente para Tools, agregar:

```python
from typing import Literal

from app.customer_service import (
    get_claimant_customer_profile,
    verify_claimant_customer,
)
from app.schemas import (
    CustomerProfile,
    CustomerVerification,
)
```

Implementar:

```python
async def verify_customer_tool(
    national_id: str,
) -> CustomerVerification:
    """Verifica si el declarante es cliente usando su identificador nacional.

    Sólo devuelve existencia e identificador de cliente; no devuelve PII.
    En este documento, PII significa Personally Identifiable Information:
    información de identificación personal, como correo, teléfono o dirección.
    """

    return await verify_claimant_customer(
        national_id
    )
```

---

### Tool de perfil

Agregar:

```python
async def get_customer_profile_tool(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
) -> CustomerProfile:
    """Obtiene el perfil actual del declarante ya identificado.

    Requiere el identificador nacional disponible en ClaimData. La capa de
    servicio verifica la identidad antes de devolver el perfil.
    """

    return (
        await get_claimant_customer_profile(
            national_id,
            requested_field,
        )
    )
```

---

### Registro de tools

Agregar las tools al:

    Claims Analyst Agent

utilizando el mecanismo ya implementado con Pydantic AI.

`claims_agent` es la instancia conversacional de `pydantic_ai.Agent` definida en `app/agent.py`: el agente que atiende las consultas del analista, interpreta la petición y orquesta Tool Calling con `chat_model`. En la PoC 3 esta misma instancia se muestra con el nombre `agent`, configurada con `OpenAIChatModel(LLM_MODEL, provider=provider)` y `LLM_MODEL="qwen2.5-instruct:7b"`. En esta PoC se usa el nombre `claims_agent` para dejar explícito su rol de Claims Analyst Agent; no es un segundo agente.

No debe confundirse con `extract_claim_data()`, que realiza Structured Extraction y no es una instancia de `Agent` ni recibe estas tools. En `app/agent.py`, agregar `verify_customer_tool` y `get_customer_profile_tool` a la lista `tools` del `Agent` conversacional existente, junto con las tools ya registradas. Si el código todavía nombra esa instancia `agent`, conservar ese nombre o renombrarla de forma consistente en sus usos; no crear una instancia paralela ni reemplazar el modelo, el `system_prompt` o las demás dependencias.

Mantener las Tools existentes:

    calculate_deductible

    calculate_reserve

    get_missing_claim_information

---

### Descripción de verify_customer_tool

La descripción debe indicar claramente:

> Utiliza esta herramienta cuando necesites verificar si el declarante existe como cliente de la compañía. Requiere el identificador nacional de la persona. Esta herramienta sólo verifica existencia y devuelve el identificador de cliente; no devuelve PII adicional.

Esta descripción ayuda al LLM a diferenciarla de:

    get_customer_profile_tool()

---

### Descripción de get_customer_profile_tool

Debe indicar:

> Utiliza esta herramienta únicamente cuando una solicitud requiera un dato personal específico de un cliente ya identificado. Proporciona el identificador nacional del declarante y el campo requerido (`email`, `phone_number` o `address`). La herramienta verifica la identidad y solicita sólo ese campo. No la utilices si sólo necesitas comprobar si la persona es cliente.

Esto refuerza:

    data minimization

---

### System prompt

Actualizar el `system_prompt` del Claims Analyst Agent.

Agregar reglas equivalentes a:

```python
    "Cuando necesites saber si el declarante es cliente de la compañía, "
    "utiliza verify_customer_tool. "
    "No deduzcas que una persona es cliente basándote únicamente en "
    "documentos del expediente. "
    "Utiliza get_customer_profile_tool sólo cuando sea necesario obtener "
    "datos personales concretos del cliente. "
    "No solicites el perfil completo si sólo necesitas verificar que la "
    "persona es cliente. "
    "Los datos obtenidos desde Customer API son información corporativa y "
    "tienen prioridad sobre afirmaciones previas almacenadas en "
    "Conversation Memory. "
    "No inventes datos de cliente. "
    "Solicita únicamente el campo de perfil necesario para responder."
```

---

# 8. Memoria conversacional y ClaimData

El agente puede utilizar memoria para interpretar referencias.

Ejemplo:

    Usuario:
    "¿El declarante es cliente?"

El agente:

    obtiene national_id
        ↓
    verify_customer_tool()

Después:

    Usuario:
    "¿Cuál es su correo?"

Conversation Memory permite entender:

    "su"
        ↓
        mismo cliente
Pero la respuesta debe ejecutar:

    get_customer_profile_tool()

No debe depender de que el correo haya quedado anteriormente en:

    ConversationSession

---

### No enviar el historial a Customer API

La llamada correcta es:

```text
Claims Analyst Agent
        │
        ▼
verify_customer_tool(
    national_id="123456785"
)
```

No:

```text
verify_customer_tool(
    conversation_history=[...]
)
```

Customer API no necesita conocer la conversación.

---

### Uso de session_id

No enviar:

    session_id

a Customer API como parámetro funcional.
a Customer API como parámetro funcional.

La operación corporativa necesita:

    national_id

o:

    customer_id

`session_id` puede utilizarse posteriormente sólo como metadata técnica de observabilidad.

---

### Obtener national_id desde ClaimData

El modelo `ClaimsPartyInfo` de las PoC anteriores contiene información de las partes.

Cuando exista un identificador nacional extraído:

    ClaimData
        ↓
    ClaimsPartyInfo
        ↓
    national_id

el agente puede utilizarlo para:

    verify_customer_tool()

El nombre exacto del campo debe corresponder al modelo ya implementado en `schemas.py`.

---

### Evitar solicitar datos ya disponibles

Si el expediente contiene un national ID confiable:

    no preguntar nuevamente

al analista:

    "¿Cuál es el RUT?"

Primero utilizar:

    ClaimData

---

### Identificador faltante

Si:

    national_id

no existe en:

    ClaimData

el agente debe indicar que necesita ese dato para verificar al cliente.

Puede utilizar:

    get_missing_claim_information

cuando corresponda.

---

### Flujo de verificación

El flujo queda:

    User:
    "¿El declarante es cliente?"
                │
                ▼
       ConversationSession
                │
                ▼
          Claims Agent
                │
                ▼
      buscar national_id
          en ClaimData
                │
          ┌─────┴─────┐
          │           │
        existe      no existe
          │           │
          ▼           ▼
 verify_customer   solicitar dato
          │
          ▼
     Customer API
          │
          ▼
  CustomerVerification

---

### Flujo de perfil

    User:
    "¿Cuál es su correo?"
                │
                ▼
       ConversationSession
                │
                ▼
          Claims Agent
                │
                ▼
        national_id + campo solicitado
                │
                ▼
    verificar declarante
        ↓
    get_customer_profile(fields=requested_field)
                │
                ▼
         Customer API
                │
                ▼
       CustomerProfile
                │
                ▼
         devolver email

---

### No persistir el perfil en memoria

Después de una consulta como:

    "¿Cuál es el correo?"

la conversación almacenará naturalmente:

    user message
    assistant response

Pero no debemos agregar además una copia estructurada completa de:

    CustomerProfile

a:

    ConversationSession

La memoria no es:

    customer cache

---

# 9. Errores, diagnóstico y disponibilidad

Esta PoC no implementará cache de Customer API.

Cada dato corporativo que deba verificarse puede consultarse nuevamente.

Posteriormente puede incorporarse caching controlado si existe necesidad.

---

### Clasificación de errores

Si Customer API no responde:

    CustomerApiUnavailable

El asistente debe responder conceptualmente:

    "No fue posible consultar el sistema
     de clientes en este momento."

No:

    "El declarante no es cliente."

Es importante diferenciar:

    not found

de:

    system unavailable

---

### Cliente inexistente

Cuando:

    GET /customers/by-national-id/...
        → 404

la respuesta funcional será:

```json
{
  "customer_found": false,
  "customer_id": null
}
```

Esto representa:

    búsqueda ejecutada correctamente
        +
    cliente no encontrado

---

### Sistema no disponible

Si existe:

    timeout

    connection refused

    HTTP 503

la respuesta no debe convertirse en:

    customer_found=false

El estado es:

    UNKNOWN

porque la consulta no pudo realizarse.

---

### Timeout

Configurar:

    CUSTOMER_API_TIMEOUT_SECONDS=10

El agente no debe quedar esperando indefinidamente.

---

### Health check de Customer API

En `schemas.py` agregar:

Agregar:

```python
class CustomerHealthResponse(
    BaseModel
):
    status: str
    base_url: str
```

---

### Implementar health check

En:

    customer_client.py

El módulo ya importa `httpx`, `CUSTOMER_API_BASE_URL` y `CUSTOMER_API_TIMEOUT_SECONDS`, y utiliza `_create_http_client()` para compartir la configuración de timeout.

agregar:

```python
async def check_customer_api_health() -> bool:

    url = (
        f"{CUSTOMER_API_BASE_URL}"
        "/health"
    )

    try:
        async with _create_http_client() as client:

            response = await client.get(
                url
            )

    except httpx.RequestError:
        return False

    return response.is_success
```

---

### Endpoint /health/customer

En:

    main.py

Agregar los imports correspondientes al módulo:

```python
from app.config import CUSTOMER_API_BASE_URL
from app.customer_client import check_customer_api_health
from app.schemas import CustomerHealthResponse
```

agregar:

```python
@app.get(
    "/health/customer",
    response_model=CustomerHealthResponse,
    tags=["Health"],
)
async def customer_health_endpoint(
) -> CustomerHealthResponse:

    healthy = (
        await check_customer_api_health()
    )

    return CustomerHealthResponse(
        status=(
            "ok"
            if healthy
            else "unavailable"
        ),
        base_url=(
            CUSTOMER_API_BASE_URL
        ),
    )
```

---

# 10. API simulada y datos de laboratorio

Para poder probar la integración sin depender todavía del sistema corporativo real puede utilizarse una API simulada local.

Crear la carpeta para la API simulada:

    customer_mock/

La API debe implementar al menos:

    GET /health

    GET /customers/by-national-id/{national_id}

    GET /customers/{customer_id}
Implementación mínima sugerida en `customer_mock/main.py`:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()
customers = {
    "123456785": {
        "customer_id": "CUST-000123",
        "national_id": "123456785",
        "full_name": "Alejandro Torres Muñoz",
        "email": "alejandro.torres@example.com",
        "phone_number": "+56955550123",
        "address": "Av. Ejemplo 1234, Santiago",
    }
}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/customers/by-national-id/{national_id}")
async def find_customer(national_id: str) -> dict[str, str]:
    customer = customers.get(national_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer_id": customer["customer_id"]}


@app.get("/customers/{customer_id}")
async def customer_profile(
    customer_id: str,
    fields: str,
) -> dict[str, str]:
    customer = next(
        (item for item in customers.values()
         if item["customer_id"] == customer_id),
        None,
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    allowed_fields = {"email", "phone_number", "address"}
    requested_fields = set(fields.split(","))
    if not requested_fields or not requested_fields <= allowed_fields:
        raise HTTPException(status_code=400, detail="Invalid fields")

    identity_fields = {"customer_id", "national_id", "full_name"}
    return {
        key: value
        for key, value in customer.items()
        if key in identity_fields or key in requested_fields
    }
```

Ejecutar en una terminal separada con FastAPI y Uvicorn instalados:

```text
uv run fastapi dev customer_mock/main.py --port 8081
```

La API simulada sólo debe usar los datos ficticios de laboratorio y no exponerse fuera del entorno local.

---

### Datos de laboratorio

Para el expediente:

    CLM-000123

podemos utilizar un cliente ficticio:

```json
{
  "customer_id": "CUST-000123",
  "national_id": "123456785",
  "full_name": "Alejandro Torres Muñoz",
  "email": "alejandro.torres@example.com",
  "phone_number": "+56955550123",
  "address": "Av. Ejemplo 1234, Santiago"
}
```

Todos estos datos deben considerarse:

    ficticios

---

# 11. Tests del cliente HTTP

Crear:

    tests/unit/test_customer_client.py

```python
from app.customer_client import (
    normalize_national_id,
)


def test_normalize_national_id():

    result = normalize_national_id(
        "12.345.678-5"
    )

    assert result == (
        "123456785"
    )
```

---

### Validación de national_id

Agregar:

```python
import pytest


def test_normalize_empty_national_id():

    with pytest.raises(
        ValueError
    ):
        normalize_national_id(
            "   "
        )
```

---

### Transporte HTTP simulado

Los tests unitarios del cliente no deben depender necesariamente de una Customer API real.

Puede utilizarse:

    httpx.MockTransport

o mockear el cliente HTTP.

El objetivo es comprobar:

    200

    404

    500

    timeout

de forma determinística.
Agregar una fixture reutilizable en `tests/unit/test_customer_client.py`. Al sustituir la fábrica privada, los tests controlan el transporte sin modificar la API pública del cliente:

```python
import httpx
import pytest

from app import customer_client


@pytest.fixture
def mock_customer_api(monkeypatch):
    def install(handler):
        def create_client():
            return httpx.AsyncClient(
                transport=httpx.MockTransport(handler),
                timeout=1,
            )

        monkeypatch.setattr(
            customer_client,
            "_create_http_client",
            create_client,
        )

    return install
```

---

### Verificación de cliente

El siguiente ejemplo supone que la fixture `mock_customer_api` de la sección anterior está disponible en el mismo módulo. Agregar los imports indicados al inicio del archivo de test:

```python
import httpx
import pytest

from app.customer_client import (
    CustomerApiUnavailable,
    CustomerProfile,
    get_customer_profile,
    normalize_national_id,
    verify_customer,
)


@pytest.mark.asyncio
async def test_verify_customer_found(mock_customer_api):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith(
            "/customers/by-national-id/123456785"
        )
        return httpx.Response(
            200,
            json={"customer_id": "CUST-000123"},
        )

    mock_customer_api(handler)
    result = await verify_customer("12.345.678-5")

    assert result.customer_found is True
    assert result.customer_id == "CUST-000123"
```

---

### Cliente inexistente
```python
@pytest.mark.asyncio
async def test_verify_customer_not_found(mock_customer_api):
    mock_customer_api(lambda request: httpx.Response(404))

    result = await verify_customer("999999999")

    assert result.customer_found is False
    assert result.customer_id is None
```

Debe comprobar:

```python
assert (
    result.customer_found
    is False
)

assert (
    result.customer_id
    is None
)
```

para un:

    HTTP 404

---

### Sistema no disponible y timeout
```python
@pytest.mark.asyncio
async def test_customer_api_500_is_unavailable(mock_customer_api):
    mock_customer_api(lambda request: httpx.Response(500))

    with pytest.raises(CustomerApiUnavailable):
        await verify_customer("123456785")
```
```python
@pytest.mark.asyncio
async def test_customer_api_unavailable(mock_customer_api):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    mock_customer_api(handler)

    with pytest.raises(CustomerApiUnavailable):
        await verify_customer("123456785")


@pytest.mark.asyncio
async def test_customer_api_timeout_is_unavailable(mock_customer_api):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    mock_customer_api(handler)

    with pytest.raises(CustomerApiUnavailable):
        await verify_customer("123456785")
```

Debe verificar que un error de conexión produzca:

    CustomerApiUnavailable

y no:

    CustomerVerification(
        customer_found=False
    )

---

### Validación y minimización del perfil
```python
@pytest.mark.asyncio
async def test_profile_requests_only_the_requested_field(mock_customer_api):
    profile_data = {
        "customer_id": "CUST-000123",
        "national_id": "123456785",
        "full_name": "Alejandro Torres Muñoz",
        "email": "alejandro.torres@example.com",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["fields"] == "email"
        return httpx.Response(200, json=profile_data)

    mock_customer_api(handler)
    profile = await get_customer_profile("CUST-000123", "email")

    assert profile.email == "alejandro.torres@example.com"
    assert profile.phone_number is None
    assert profile.address is None
```
```python
@pytest.mark.asyncio
async def test_get_customer_profile(mock_customer_api):
    profile_data = {
        "customer_id": "CUST-000123",
        "national_id": "123456785",
        "full_name": "Alejandro Torres Muñoz",
        "email": "alejandro.torres@example.com",
    }
    mock_customer_api(
        lambda request: httpx.Response(200, json=profile_data)
    )

    profile = await get_customer_profile("CUST-000123", "email")

    assert isinstance(profile, CustomerProfile)
    assert profile.customer_id == "CUST-000123"
    assert profile.national_id == "123456785"
    assert profile.full_name == "Alejandro Torres Muñoz"
    assert str(profile.email) == "alejandro.torres@example.com"
```

Verificar:

    CustomerProfile

a partir de la respuesta REST.

Comprobar:

    customer_id

    national_id

    full_name

    email

---

# 12. Tests de agente y conversación

Agregar también una prueba unitaria del servicio que demuestre que un perfil con un `national_id` distinto al del declarante se rechaza antes de llegar al agente. En el archivo `tests/unit/test_customer_service.py`, agregar:

```python
from unittest.mock import AsyncMock

import pytest

from app import customer_service
from app.customer_client import CustomerApiError
from app.schemas import CustomerProfile, CustomerVerification


@pytest.mark.asyncio
async def test_customer_profile_must_match_claimant(monkeypatch):
    monkeypatch.setattr(
        customer_service,
        "verify_customer",
        AsyncMock(
            return_value=CustomerVerification(
                customer_found=True,
                customer_id="CUST-000123",
            )
        ),
    )
    get_profile = AsyncMock(
        return_value=CustomerProfile(
            customer_id="CUST-000123",
            national_id="999999999",
            full_name="Otro cliente",
        )
    )
    monkeypatch.setattr(
        customer_service,
        "get_customer_profile",
        get_profile,
    )

    with pytest.raises(CustomerApiError):
        await customer_service.get_claimant_customer_profile(
            "123456785",
            "email",
        )

    get_profile.assert_awaited_once_with("CUST-000123", "email")
```

A nivel de agente, crear un test para una consulta:

    "¿El declarante es cliente?"

y comprobar que se utiliza:

    verify_customer_tool

sin necesidad de:

    get_customer_profile_tool

Este test es especialmente importante porque valida una decisión de privacidad, no sólo funcionalidad.

---

### Continuidad conversacional

Probar:

    SESSION-001

Turno 1:

    "¿El declarante es cliente?"

Turno 2:

    "¿Cuál es su correo?"

El segundo turno debe mantener la referencia al mismo cliente.

Pero la respuesta debe sustentarse en:

    Customer API

---

### Datos corporativos desactualizados en memoria

Probar:

    Turno 1:
        "Su correo es A"

Posteriormente simular que Customer API devuelve:

    B

Una nueva consulta:

    "¿Cuál es su correo?"

debe responder:

    B

Esto demuestra:

    memory
        !=
    source of truth

---

# 13. Integración y protección de datos

La secuencia end-to-end será:

    documentos
        ↓
    Structured Extraction
        ↓
    ClaimData
        │
        └── claimant national_id
                    │
                    ▼
             Customer API
                    │
                    ▼
           CustomerVerification
                    │
                    ▼
             CustomerProfile
                si necesario

---

### Integración con ConversationSession

El flujo completo será:

    POST /assistant/query
             │
             ├── session_id
             └── message
                    │
                    ▼
            load session
                    │
                    ▼
         conversation context
                    │
                    +
                ClaimData
                    │
                    ▼
             Claims Agent
                    │
                    ▼
           Customer Tool
                    │
                    ▼
            Customer API
                    │
                    ▼
               response
                    │
                    ▼
            save conversation

---

### Metadata de correlación

Aunque todavía no se incorpore la observabilidad distribuida completa, preparar las firmas para que posteriormente puedan recibir:

    correlation_id

y:

    session_id

como metadata técnica.

No enviarlos como parte del prompt ni como parámetros funcionales de Customer API.

---

### Minimizar PII en logs

Evitar logs como:

```text
Customer profile:
{
    email: ...
    address: ...
    ...
}
```

Los logs deberían indicar como máximo:

    operation

    success/failure

    customer_id cuando sea apropiado

sin volcar todo:

    CustomerProfile

---

### Logs conversacionales

La misma regla aplica a:

    ConversationSession

No registrar indiscriminadamente:

    todos los mensajes

en:

    application logs

La persistencia conversacional ya existe en:

    data/sessions

---

# 14. Documentación y pruebas manuales

Abrir:

    http://localhost:8000/swagger-ui

Debe continuar mostrando:

    POST /sessions

    GET /sessions/{session_id}

    DELETE /sessions/{session_id}

    POST /assistant/query

Además:

    GET /health/customer

---

### OpenAPI
FastAPI sólo incorpora automáticamente a OpenAPI los modelos usados por operaciones HTTP. `CustomerVerification` y `CustomerProfile` son contratos internos de las tools; no se deben exponer mediante endpoints artificiales ni devolver desde el endpoint de diagnóstico. Para cumplir el criterio de esta PoC de incluirlos como schemas reutilizables, registrarlos explícitamente en `main.py`:

```python
from fastapi.openapi.utils import get_openapi

from app.schemas import CustomerProfile, CustomerVerification


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    components = schema.setdefault("components", {}).setdefault(
        "schemas", {}
    )
    for model in (CustomerVerification, CustomerProfile):
        model_schema = model.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        definitions = model_schema.pop("$defs", {})
        components.update(definitions)
        components[model.__name__] = model_schema

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
```

Mantener `CustomerHealthResponse` como `response_model` de `/health/customer`; el health check sólo comunica disponibilidad y URL, nunca PII.

Abrir:

    http://localhost:8000/api-docs/openapi.json

Debe incluir:

    CustomerVerification

    CustomerProfile

    CustomerHealthResponse

y conservar los contratos de:

    ConversationSession

    ConversationRequest

    ConversationResponse

---

### Comprobar health

Ejecutar:

    GET
    /health/customer

Esperado:

```json
{
  "status": "ok",
  "base_url": "http://localhost:8081"
}
```

---

### Crear sesión

Ejecutar:

    POST /sessions

```json
{
  "claim_number": "CLM-000123"
}
```

Guardar:

    session_id

---

### Verificar cliente

Enviar:

    POST /assistant/query

```json
{
  "session_id": "<session-id>",
  "message": "¿El declarante es cliente de la compañía?"
}
```

Esperado:

    Claims Agent
        ↓
    verify_customer_tool()
        ↓
    Customer API

---

### Recuperar un dato personal

Segundo turno:

```json
{
  "session_id": "<session-id>",
  "message": "¿Cuál es su correo electrónico?"
}
```

Esperado:

    Conversation Memory
        → resuelve referencia "su"

    Customer API
        → obtiene email actual

---

### Cliente inexistente

Utilizar un RUT ficticio que no exista.

El agente debe informar:

    cliente no encontrado

No debe inventar:

    customer_id

---

### API no disponible

Detener la API simulada.

Preguntar nuevamente:

    "¿El declarante es cliente?"

Esperado:

    sistema de clientes no disponible

No:

    "No es cliente"

---

### Sesión diferente

Crear:

    SESSION-B

La nueva sesión no debe conocer automáticamente qué cliente se consultó en:

    SESSION-A

Debe reconstruir contexto utilizando:

    claim_number

    ClaimData

    Customer API

---

### Aislamiento de sesiones

Aunque ambas sesiones estén asociadas a:

    CLM-000123

no deben compartir automáticamente:

    ConversationMessage[]

Lo compartido es:

    Claim context

No:

    conversation history

---

# 15. Preparación para MCP

La arquitectura implementada deliberadamente utiliza:

    Claims Agent
        ↓
    Customer Service
        ↓
    Customer Client
        ↓
    REST

Posteriormente podremos cambiar:

    Customer Client
        ↓
    REST

por:

    Customer MCP Client

manteniendo:

    verify_claimant_customer()

    get_claimant_customer_profile()

---

### Contrato estable

La capa superior debe continuar recibiendo:

    CustomerVerification

y:

    CustomerProfile

independientemente de si la implementación utiliza:

    REST

o:

    MCP

---

### Alcance actual: REST

Aunque la arquitectura ya prepare esa evolución, esta PoC debe validar primero:

    integración externa básica

    errores

    PII

    data minimization

    conversación

con el menor número posible de nuevas variables.

---

### Impacto en Conversation Session Memory

La PoC 9 permanece prácticamente sin cambios.

Lo que se establece ahora es una regla adicional:

    ConversationSession
        no guarda automáticamente
        CustomerProfile

El agente utiliza memoria para:

    referencias conversacionales

y Customer API para:

    datos actuales

---

# 16. Ejecución de pruebas y aceptación

Ejecutar:

    uv run pytest tests/unit -v

Los tests nuevos deben cubrir:

    normalize_national_id()

    customer response mapping

    customer not found

    customer API errors

    CustomerProfile validation

---

### Tests de integración

Con Customer API simulada ejecutándose:

    uv run pytest tests/integration -v

Agregar tests para:

    Customer API

    Claims Agent Tool Calling

    Conversation Session + Customer API

---

### Test end-to-end

La prueba completa debe cubrir:

    documentos
        ↓
    Structured Extraction
        ↓
    ClaimData
        ↓
    ConversationSession
        ↓
    User question
        ↓
    Claims Agent
        ↓
    Customer API
        ↓
    CustomerVerification
        ↓
    follow-up question
        ↓
    Conversation Memory
        ↓
    CustomerProfile
        ↓
    response

---

# 17. Resumen y criterios de éxito

La plataforma incorpora:

    Customer API integration

    CustomerVerification

    CustomerProfile

    customer tools

    customer error taxonomy

    data minimization rules

La Conversation Session permite referencias entre turnos.

---

### Qué no cambia

No cambian:

    ClaimData

    DocumentChunk

    Claim RAG

    Corporate RAG

    Secure RAG

    ConversationSession

    EmbeddingGemma

    Qdrant

    deterministic calculations

---

### Separación de responsabilidades

La arquitectura queda:

    Conversation Memory
        → qué veníamos hablando

    ClaimData
        → qué sabemos del siniestro

    Secure RAG
        → qué dicen los documentos

    Customer API
        → quién es el cliente
          y cuáles son sus datos actuales

    Tools
        → cálculos determinísticos

---

### Regla de mínimo contexto

Cada componente debe recibir sólo lo necesario:

    Customer API
        → identifiers

    RAG
        → query + claim scope

    Tools
        → calculation parameters

    Conversation Agent
        → conversation context

No utilizar:

    ConversationSession completa

como payload universal entre componentes.

---

### Criterios de éxito

La PoC se considera validada si:

    Customer API
        → puede consultarse

    verify_customer
        → identifica cliente

    cliente inexistente
        → se distingue correctamente

    API unavailable
        → se distingue de not found

    get_customer_profile
        → recupera datos

    data minimization
        → se aplica

    Claims Agent
        → utiliza customer tools

    ClaimData
        → aporta national_id

    ConversationSession
        → mantiene referencias

    follow-up questions
        → pueden utilizar el mismo cliente

    Customer API
        → sigue siendo source of truth

    CustomerProfile
        → no se almacena como estado de ClaimData

    CustomerProfile
        → no se almacena automáticamente en memoria

    Swagger
        → documenta health

    OpenAPI
        → contiene schemas

    tests unitarios
        → pasan

    tests integración
        → pasan

---

### Resultado esperado

Al finalizar:

                           ANALISTA
                              │
                              ▼
                      Conversation
                              │
                         session_id
                              │
                              ▼
                     Conversation Store
                              │
                              ▼
                      Conversation Context
                              │
                   ┌──────────┴──────────┐
                   │                     │
                   ▼                     ▼
               ClaimData             Secure RAG
                   │                     │
                   └──────────┬──────────┘
                              ▼
                     Claims Analyst Agent
                              │
                   ┌──────────┼───────────┐
                   │          │           │
                   ▼          ▼           ▼
             Customer Tool   Tools       RAG
                   │
                   ▼
             Customer Service
                   │
                   ▼
             Customer Client
                   │
                   ▼
               REST API
                   │
                   ▼
            Customer System
                   │
                   ▼
        CustomerVerification /
          CustomerProfile
                   │
                   ▼
            Claims Analyst Agent
                   │
                   ▼
                Response
                   │
                   ▼
            Conversation Store

El principio central de esta PoC es:

    MEMORY
        → REMEMBERS THE CONVERSATION

    CUSTOMER API
        → PROVIDES CUSTOMER TRUTH

Esto significa que una secuencia:

    "¿El declarante es cliente?"
        ↓
    verify_customer()

    "¿Cuál es su correo?"
        ↓
    Conversation Memory
        → identifica referencia

    Customer API
        → entrega dato actualizado

La nueva PoC 10 deja además preparada una frontera que posteriormente permitirá migrar:

    REST
        ↓
    MCP

sin modificar:

    ConversationSession

    Claims Analyst Agent contract

    CustomerVerification

    CustomerProfile

De esta manera, la incorporación de memoria conversacional en la PoC 9 no acopla las integraciones posteriores a la conversación, sino que refuerza una separación fundamental:

    CONVERSATION
        ≠
    BUSINESS STATE
        ≠
    SYSTEM OF RECORD