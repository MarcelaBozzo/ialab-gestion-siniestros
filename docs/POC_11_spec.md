# PoC 11 — Integración de sistemas mediante Model Context Protocol (MCP)

## Objetivo

Evolucionar la integración con sistemas externos introducida en la PoC 10 desde una integración REST específica de aplicación hacia una arquitectura basada en **Model Context Protocol (MCP)**.

En la PoC 10 incorporamos:

    Claims Analyst Agent
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

Esta integración permitió validar:

- consulta del sistema de clientes;
- verificación del declarante;
- recuperación controlada de información personal;
- manejo de errores;
- data minimization;
- integración con `ConversationSession`.

Sin embargo, el Claims Analyst Agent continúa dependiendo de una integración específica construida para:

    Customer API

En esta PoC introduciremos:

    MCP

como protocolo estándar para exponer capacidades de sistemas externos a los agentes.

La arquitectura evolucionará hacia:

    Claims Analyst Agent
            │
            ▼
        MCP Client
            │
            ▼
    Customer MCP Server
            │
            ▼
       Customer API
            │
            ▼
      Customer System

El objetivo no es simplemente reemplazar:

    HTTP
        por
    MCP

El objetivo es establecer una frontera estándar:

    Agent
        → MCP
        → System

que permita que los agentes descubran y utilicen capacidades externas mediante contratos explícitos y controlados.

La PoC debe demostrar además que la incorporación de MCP **no modifica la arquitectura de memoria conversacional introducida en la PoC 9**.

El principio será:

    ConversationSession
        → pertenece al Claims Analyst Agent

    MCP
        → recibe parámetros explícitos

    Customer System
        → continúa siendo source of truth

Por tanto:

    Conversation Memory
        ≠
    MCP State

y:

    MCP
        ≠
    Conversation Memory

---

# 1. Alcance

Esta PoC incorpora:

- Model Context Protocol;
- Customer MCP Server;
- MCP Client;
- MCP Tools;
- `verify_customer`;
- `get_customer_profile`;
- reutilización de Customer API;
- contratos estructurados;
- Tool Discovery;
- Tool Calling mediante MCP;
- separación Agent → MCP → System;
- data minimization;
- manejo de errores MCP;
- tests unitarios;
- tests de integración;
- integración con Conversation Session Memory;
- aislamiento entre conversación y MCP;
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
- Conversation Session Memory;
- Customer API;
- `CustomerVerification`;
- `CustomerProfile`;
- `CustomerFieldValue` como contrato mínimo de salida hacia el agente.

No se incorporan todavía:

- A2A;
- Policy Agent independiente;
- Microsoft Entra ID;
- OBO;
- Azure API Management;
- Azure AI Search;
- Azure OpenAI;
- Microsoft Foundry.

---

# 2. Motivación y arquitectura

En la PoC 10 el agente utiliza una integración específica:

    Claims Agent
        ↓
    Customer Service
        ↓
    REST Client
        ↓
    Customer API

Esto funciona correctamente.

Pero si posteriormente agregamos:

    Policy Core

    Payment System

    Repair Network

    Fraud System

    Document System

podríamos terminar construyendo una integración diferente para cada sistema.

Por ejemplo:

    customer_client.py

    policy_client.py

    payment_client.py

    repair_client.py

MCP introduce una frontera común:

    Agent
       │
       ▼
      MCP
       │
       ├── Customer System
       ├── Policy System
       ├── Payment System
       └── ...

En esta PoC validaremos el patrón utilizando primero:

    Customer System

---

## Límites de MCP

MCP no sustituye:

    Customer API

    ClaimData

    ConversationSession

    Secure RAG

    Qdrant

    Tools determinísticas

Tampoco convierte automáticamente una API REST en una capacidad segura para agentes.

Seguimos siendo responsables de:

    tool design

    autorización

    validación

    data minimization

    errores

    observabilidad

---

## Arquitectura anterior

Después de la PoC 10:

                     Claims Analyst Agent
                              │
                              ▼
                      Customer Service
                              │
                              ▼
                       Customer Client
                              │
                              ▼
                           REST
                              │
                              ▼
                       Customer API

---

## Arquitectura objetivo

En esta PoC:

                     Claims Analyst Agent
                              │
                              ▼
                         MCP Client
                              │
                              ▼
                     Customer MCP Server
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
             verify_customer    get_customer_profile
                    │                   │
                    └─────────┬─────────┘
                              ▼
                       Customer Client
                              │
                              ▼
                       Customer API
                              │
                              ▼
                      Customer System

Customer API continúa existiendo.

MCP actúa como:

    agent integration boundary

---

# 3. Memoria conversacional y mínimo contexto

La PoC 9 incorporó:

    ConversationSession

La PoC 10 demostró que una conversación puede utilizar información de Customer API sin convertir la memoria en fuente de verdad.

Esta regla se mantiene con MCP.

El flujo será:

    ConversationSession
            │
            ▼
    Claims Analyst Agent
            │
            │ interpreta
            │ la conversación
            ▼
         MCP Tool
            │
            │ argumentos
            │ explícitos
            ▼
       Customer API

---

## ConversationSession no viaja a MCP

No debemos realizar:

```json
{
  "session_id": "SESSION-001",
  "conversation_history": [
    "...",
    "..."
  ],
  "national_id": "123456785"
}
```

como argumento funcional de:

    verify_customer

La llamada correcta será equivalente a:

```json
{
  "national_id": "123456785"
}
```

El agente es responsable de transformar:

    conversación

en:

    argumentos estructurados

---

## Primer turno

Conversación:

    Usuario:
    "¿El declarante es cliente?"

El Claims Analyst Agent utiliza:

    ClaimData
        ↓
    ClaimsPartyInfo
        ↓
    national_id

y ejecuta:

    verify_customer(
        national_id="123456785"
    )

MCP no necesita conocer:

    qué preguntó el usuario

    qué respondió anteriormente el agente

    cuál es el summary de la sesión

---

## Segundo turno

Después:

    Usuario:
    "¿Cuál es su correo?"

Conversation Memory permite resolver:

    "su"
        ↓
    mismo cliente

El agente ejecuta:

    get_customer_profile(
        national_id="123456785",
        requested_field="email",
    )

El MCP Server recibe únicamente el identificador nacional. Resuelve el `customer_id` internamente después de verificar al declarante.

---

## Regla de mínimo contexto

La arquitectura establece:

    Conversation Agent
        → conversation context

    MCP Tool
        → explicit arguments

    Customer API
        → business request

Esto implementa:

    least context

además de:

    least privilege

---

# 4. Customer MCP Server y Tools

Crear un módulo independiente para el servidor MCP.

Estructura:

    app/
    ├── main.py
    ├── health.py
    ├── ...
    │
    └── mcp/
        ├── __init__.py
        └── customer_server.py

El servidor MCP expondrá exclusivamente capacidades relacionadas con:

    Customer System

---

## Dependencia MCP

Agregar la dependencia y conservar `uv.lock` en el repositorio para fijar la versión resuelta del SDK en todos los entornos:

```bash
uv add "mcp>=2,<3"
```

Esta PoC se construye explícitamente con **MCP Python SDK versión 2**. `pyproject.toml` declara `mcp>=2,<3` y `uv.lock` fija la versión concreta resuelta dentro de esa línea principal. Conservar ambos archivos y ejecutar la aplicación y los tests con `uv run`.

En un entorno limpio, instalar las versiones fijadas con:

```bash
uv sync --locked
```

Antes de iniciar el servidor, comprobar que la versión instalada corresponde a la API usada:

```bash
uv run python -c "from importlib.metadata import version; from mcp.server.mcpserver import MCPServer; print(version('mcp')); assert version('mcp').split('.')[0] == '2'"
```

La importación de `MCPServer` debe completarse y la versión impresa debe tener major `2`.

---

## Módulo del servidor

Crear:

    app/mcp/customer_server.py

Imports:

```python
from mcp.server.mcpserver import MCPServer

from app.customer_client import (
    CustomerApiError,
    CustomerApiUnavailable,
    CustomerNotFound,
    get_customer_profile as get_customer_profile_from_api,
    verify_customer as verify_customer_from_api,
)
```

---

## Instancia del servidor

Agregar:

```python
mcp = MCPServer(
    "customer-mcp"
)
```

Este servidor representa:

    Customer System capabilities

No representa:

    Claims Analyst Agent

---

## Tool verify_customer

Contrato de entrada:

```python
async def verify_customer(national_id: str) -> dict:
    ...
```

La descripción de la Tool debe indicar que verifica existencia y devuelve únicamente `customer_found` y `customer_id`; no devuelve el perfil. Para evitar conflicto entre el nombre de la Tool y el cliente REST, importar la función REST con alias. La implementación con manejo de errores aparece una sola vez en el servidor completo de la sección siguiente.

---

## Tool get_customer_profile

Contrato de entrada:

```python
async def get_customer_profile(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
) -> dict:
    ...
```

La Tool recibe el identificador nacional del declarante y el campo de contacto requerido. Verifica que exista como cliente, resuelve internamente su `customer_id` y solicita únicamente ese campo. No acepta un ID interno proveniente de la conversación ni devuelve el perfil completo.

---

## Implementación completa del servidor

El archivo queda:

```python
from typing import Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app.customer_client import (
    CustomerApiError,
    CustomerApiUnavailable,
    CustomerNotFound,
    get_customer_profile as get_customer_profile_from_api,
    normalize_national_id,
    verify_customer as verify_customer_from_api,
)


mcp = MCPServer(
    "customer-mcp"
)


@mcp.tool()
async def verify_customer(
    national_id: str,
) -> dict:
    """
    Comprueba si una persona existe como
    cliente de la compañía de seguros.

    Devuelve únicamente si existe y su
    customer_id.

    No la utilices para obtener datos
    personales del perfil.
    """

    try:
        result = await verify_customer_from_api(national_id)
    except CustomerApiUnavailable as exc:
        raise ToolError("CUSTOMER_API_UNAVAILABLE") from exc
    except CustomerApiError as exc:
        raise ToolError("CUSTOMER_API_ERROR") from exc

    return result.model_dump(
        mode="json"
    )


@mcp.tool()
async def get_customer_profile(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
) -> dict:
    """
    Verifica al declarante por su identificador
    nacional y devuelve sólo el campo solicitado.

    Usa el customer_id devuelto por la verificación
    únicamente dentro del servidor.
    """

    try:
        verification = await verify_customer_from_api(national_id)
        if not verification.customer_found or not verification.customer_id:
            raise ToolError("CUSTOMER_NOT_FOUND")

        result = await get_customer_profile_from_api(
            verification.customer_id,
            requested_field,
        )
        if normalize_national_id(result.national_id) != normalize_national_id(
            national_id
        ):
            raise ToolError("CUSTOMER_API_ERROR")
    except CustomerApiUnavailable as exc:
        raise ToolError("CUSTOMER_API_UNAVAILABLE") from exc
    except CustomerNotFound as exc:
        raise ToolError("CUSTOMER_NOT_FOUND") from exc
    except CustomerApiError as exc:
        raise ToolError("CUSTOMER_API_ERROR") from exc

    return result.model_dump(
        mode="json"
    )


if __name__ == "__main__":
    mcp.run()
```

El bloque:

```python
if __name__ == "__main__":
```

es el entry point del servidor MCP, no un script temporal de testing.

Los tests continúan separados en:

    tests/

---

## Ejecución del servidor

La ejecución del servidor en esta etapa es sólo para verifica que se inicia correctamente. En el uso normal, no se lanza en forma independiente, sino que se integra dentro del flujo de la aplicación principal como un proceso hijo.

Ejecutar:

    uv run python -m app.mcp.customer_server

El servidor debe iniciar utilizando el transporte configurado por MCP.

Para desarrollo local puede utilizarse inicialmente:

    stdio

`stdio` es un transporte que utiliza la entrada y salida estándar para la comunicación entre el MCP Client y el MCP Server.

Posteriormente podremos utilizar un transporte HTTP apropiado cuando el MCP Server se despliegue como servicio independiente.

---

## Por qué empezar con stdio

Para esta PoC:

    Claims API
        +
    MCP Server

se ejecutan localmente.

`stdio` permite validar:

    MCP protocol

    tool discovery

    tool invocation

sin introducir todavía:

    networking

    authentication

    certificates

    API gateway

Estas preocupaciones aparecerán posteriormente.

---

## stdio no es la entrada del chat

El transporte:

    stdio

es un mecanismo de comunicación:

    MCP Client
        ↔
    MCP Server

No representa:

    chat input

ni:

    terminal interactiva del usuario

---

# 5. MCP Client y contrato de dominio

Antes de crear el cliente, definir sus excepciones para que el módulo pueda importarlas desde el primer momento.

Crear:

    app/mcp/errors.py

```python
class McpError(RuntimeError):
    pass


class McpUnavailable(McpError):
    pass


class McpToolNotFound(McpError):
    pass


class McpToolExecutionError(McpError):
    pass


class McpInvalidResponse(McpError):
    pass


class McpCustomerApiUnavailable(McpError):
    pass


class McpCustomerApiError(McpError):
    pass


class McpCustomerNotFound(McpError):
    pass
```

Una vez definido el módulo de errores, crear el cliente que importa estas clases:

    app/mcp/customer_client.py

Este módulo es el adaptador entre el protocolo y la aplicación. Para el transporte `stdio`, el cliente inicia el proceso MCP como hijo; no se levanta el servidor en una terminal aparte. En esta primera PoC se abre una conexión por operación para mantener simple el ciclo de vida. En producción se puede mantener una sesión por proceso y cerrarla durante el shutdown de FastAPI.

```python
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.mcp.errors import (
    McpCustomerApiUnavailable,
    McpCustomerApiError,
    McpCustomerNotFound,
    McpInvalidResponse,
    McpToolExecutionError,
    McpToolNotFound,
    McpUnavailable,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
python_path = os.environ.get("PYTHONPATH", "")
SERVER_ENV = {
    **os.environ,
    "PYTHONPATH": os.pathsep.join(
        path for path in (str(PROJECT_ROOT), python_path) if path
    ),
}

SERVER_PARAMETERS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "app.mcp.customer_server"],
    env=SERVER_ENV,
)


async def call_customer_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    try:
        async with stdio_client(SERVER_PARAMETERS) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:
                await session.initialize()
                listed_tools = await session.list_tools()
                tool_names = {
                    tool.name for tool in listed_tools.tools
                }

                if tool_name not in tool_names:
                    raise McpToolNotFound(tool_name)

                result = await session.call_tool(
                    tool_name,
                    arguments,
                )

                if result.is_error:
                    error_text = " ".join(
                        block.text
                        for block in result.content
                        if hasattr(block, "text")
                    )
                    if "CUSTOMER_API_UNAVAILABLE" in error_text:
                        raise McpCustomerApiUnavailable()
                    if "CUSTOMER_API_ERROR" in error_text:
                        raise McpCustomerApiError()
                    if "CUSTOMER_NOT_FOUND" in error_text:
                        raise McpCustomerNotFound()
                    raise McpToolExecutionError(
                        tool_name,
                        "Customer MCP tool failed",
                    )

                payload = result.structured_content
                if not isinstance(payload, dict):
                    raise McpInvalidResponse(
                        f"Tool {tool_name!r} did not return an object"
                    )

                return payload
    except (
        McpCustomerApiUnavailable,
        McpCustomerApiError,
        McpCustomerNotFound,
        McpInvalidResponse,
        McpToolExecutionError,
        McpToolNotFound,
    ):
        raise
    except Exception as exc:
        raise McpUnavailable(
            "Could not connect to customer-mcp"
        ) from exc


async def list_customer_mcp_tools() -> list[str]:
    try:
        async with stdio_client(SERVER_PARAMETERS) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]
    except Exception as exc:
        raise McpUnavailable(
            "Could not connect to customer-mcp"
        ) from exc
```

El proceso se ejecuta con el mismo intérprete que Claims API. `PYTHONPATH` incluye la raíz del proyecto para resolver `app.mcp.customer_server`. La salida estándar queda reservada para el protocolo MCP; los logs del servidor deben escribirse a `stderr`.

El ejemplo hereda el entorno para reutilizar la configuración de Customer API. En despliegues reales, reemplazar `os.environ` por una lista permitida de variables estrictamente necesarias; no propagar secretos ni configuración ajenos al MCP Server.

El cliente realiza Tool Discovery antes de invocar. Así puede distinguir una Tool ausente de un fallo de conexión y evitar invocaciones a capacidades no publicadas. El payload de respuesta se valida después contra el modelo de dominio; el cliente no devuelve contenido MCP directamente al agente.

---

## Contratos estables

Aunque MCP devuelva contenido protocolar, la aplicación continuará trabajando con:

    CustomerVerification

y con el resultado mínimo de perfil:

    CustomerFieldValue

`CustomerProfile` sigue siendo el modelo interno de la respuesta de Customer API; no se devuelve al agente mediante MCP.

Definir el contrato mínimo compartido por Customer Service y el wrapper local del agente en `app/schemas.py`:

```python
from typing import Literal

from pydantic import BaseModel


class CustomerFieldValue(BaseModel):
    requested_field: Literal["email", "phone_number", "address"]
    value: str | None
```

El protocolo no debe filtrarse al dominio.

---

## Servicio Customer

En el archivo `app/customer_service.py`, la interfaz utilizada por el Claims Agent debe mantenerse, aunque cambiando el retorno de `get_claimant_customer_profile` a `CustomerFieldValue`:

```python
async def verify_claimant_customer(
    national_id: str,
) -> CustomerVerification:
    ...
```

y:

```python
async def get_claimant_customer_profile(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
) -> CustomerFieldValue:
    ...
```

Lo que cambia es su implementación.

---

## Implementación anterior

En PoC 10:

```python
async def verify_claimant_customer(
    national_id: str,
) -> CustomerVerification:

    return await verify_customer(
        national_id
    )
```

---

## Implementación mediante MCP

En esta PoC, en el archivo `app/customer_service.py` se reemplaza la implementación anterior por llamadas al MCP Server:

```python
from pydantic import ValidationError
from app.mcp.customer_client import call_customer_mcp_tool
from app.mcp.errors import McpInvalidResponse

async def verify_claimant_customer(
    national_id: str,
) -> CustomerVerification:

    result = await call_customer_mcp_tool(
        tool_name="verify_customer",
        arguments={
            "national_id": national_id,
        },
    )

    try:
        return CustomerVerification.model_validate(result)
    except ValidationError as exc:
        raise McpInvalidResponse(
            "verify_customer devolvió una respuesta no válida"
        ) from exc
```

---

## Perfil mediante MCP

Igualmente reemplazar:

```python
from typing import Literal


async def get_claimant_customer_profile(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
) -> CustomerFieldValue:

    result = await call_customer_mcp_tool(
        tool_name=(
            "get_customer_profile"
        ),
        arguments={
            "national_id": national_id,
            "requested_field": requested_field,
        },
    )

    if not isinstance(result, dict) or set(result) != {requested_field}:
        raise McpInvalidResponse(
            "get_customer_profile devolvió una respuesta no válida"
        )

    try:
        return CustomerFieldValue.model_validate(
            {
                "requested_field": requested_field,
                "value": result[requested_field],
            }
        )
    except ValidationError as exc:
        raise McpInvalidResponse(
            "get_customer_profile devolvió una respuesta no válida"
        ) from exc
```

Estos son los adaptadores del camino MCP. La selección del provider REST/MCP y las importaciones completas se muestran en la sección 11; importar `ValidationError` desde Pydantic y reutilizar los modelos de dominio existentes.

---

## Aislamiento del Claims Analyst Agent respecto al protocolo

El Claims Analyst Agent continúa utilizando:

    verify_claimant_customer()

y:

    get_claimant_customer_profile()

No necesita saber si internamente existe REST o MCP. La capa Customer Service conserva `CustomerVerification` para la verificación y devuelve `CustomerFieldValue` para el dato de perfil solicitado. `CustomerProfile` permanece dentro de la integración con Customer API.

---

# 6. Tool Discovery, mínimo privilegio y selección del agente

El MCP Client ejecuta Tool Discovery y espera encontrar exactamente:

    verify_customer

    get_customer_profile

El test de integración debe comprobar que ambas herramientas aparecen en `list_tools`. El agente sólo debe seleccionar la capacidad mínima que responda a la intención del usuario.

## No exponer más Tools de las necesarias

Customer MCP Server no debe publicar:

    update_customer

    delete_customer

    create_customer

porque el asistente no necesita esas capacidades.

El servidor será:

    READ ONLY

---

## Least privilege

La frontera MCP debe representar las capacidades que el agente realmente necesita.

No debemos transformar automáticamente todos los endpoints de:

    Customer API

en:

    MCP Tools

---

## Data minimization

Mantenemos:

    verify_customer
        → existencia + customer_id

    get_customer_profile
        → información personal

Esto es deliberado.

No crear una única Tool:

    get_everything_about_customer()

---

## Descripciones de Tools

Las descripciones de Tools forman parte del contrato con el LLM.

Deben indicar:

    cuándo utilizar la Tool

    qué parámetros requiere

    qué devuelve

    cuándo no utilizarla

Para `get_customer_profile`, especificar que `requested_field` sólo acepta `email`, `phone_number` o `address`, y que la respuesta MCP contiene únicamente ese campo. No devuelve `customer_id`, `national_id`, `full_name` ni los otros campos de contacto.

Esto reduce Tool Calling incorrecto.

### Adapters locales del Claims Analyst Agent

Los wrappers locales `verify_customer_tool` y `get_customer_profile_tool` conservan sus nombres y argumentos en `app/tools.py`. La lista `tools` del Claims Analyst Agent también se conserva en `app/agent.py`; no se renombran ni se registran las Tools MCP directamente en Pydantic AI.

El tipo de retorno de `get_customer_profile_tool` sí cambia: deja de devolver `CustomerProfile` y devuelve `CustomerFieldValue`. El wrapper sigue delegando en Customer Service, pero el agente recibe únicamente el campo solicitado:

```python
async def get_customer_profile_tool(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
) -> CustomerFieldValue:
    return await get_claimant_customer_profile(
        national_id,
        requested_field,
    )
```

`CustomerProfile` permanece como modelo interno de Customer API; no forma parte de la salida de la Tool local ni de la respuesta MCP.

El cambio de implementación queda detrás de esos wrappers: `app/customer_service.py` mantiene las mismas firmas de negocio, pero selecciona el provider MCP y llama al MCP Client. Los nombres remotos `verify_customer` y `get_customer_profile` sólo se usan en las llamadas entre Customer Service y Customer MCP Server.

---

## System Prompt

Actualizar el `system_prompt` existente del Claims Analyst Agent; no crear un segundo prompt.

### Actualizar las reglas incorporadas en PoC 10

Antes de agregar las reglas MCP, actualizar dentro del `system_prompt` los nombres y la frontera de integración introducidos en PoC 10:

- Conservar `verify_customer_tool` y `get_customer_profile_tool` como nombres de las Tools locales que Pydantic AI registra en el Agent.
- Actualizar las instrucciones para indicar que `get_customer_profile_tool` recibe `national_id` y `requested_field` (`email`, `phone_number` o `address`).
- Sustituir la descripción de una llamada REST directa del agente por la frontera local existente: Agent → wrapper Pydantic AI → Customer Service → MCP Client → Customer MCP Server. Customer System sigue siendo la fuente de verdad.
- Conservar las reglas de PoC 10: no inferir que alguien es cliente sólo a partir de documentos, no inventar datos, no pedir el perfil completo, priorizar los datos corporativos frente a afirmaciones contradictorias de la conversación y solicitar únicamente el campo personal necesario.

No conservar en paralelo las instrucciones anteriores con los nombres de las Tools REST; se reemplazan por sus equivalentes MCP dentro del mismo prompt.

De esta manera, el texto que se agregó en la PoC 10 queda actualizado de la siguiente manera:

```text
"Cuando necesites verificar si el declarante es cliente, "
"utiliza verify_customer_tool con el national_id disponible en ClaimData. "
"No deduzcas que una persona es cliente basándote únicamente en "
"documentos del expediente. "
"Utiliza get_customer_profile_tool sólo cuando necesites un dato personal "
"concreto del declarante. Envía su national_id y el requested_field "
"necesario, que debe ser email, phone_number o address. "
"La herramienta verifica la identidad del declarante y consulta mediante "
"MCP en Customer System únicamente el campo indicado; no pidas el perfil "
"completo ni uses un customer_id obtenido de la conversación. "
"Los datos devueltos por Customer System mediante las herramientas MCP "
"son la fuente de verdad y tienen prioridad sobre afirmaciones previas "
"almacenadas en Conversation Memory. "
"No inventes datos de cliente. "
"Solicita únicamente el campo de perfil necesario para responder."
```

### Agregar las reglas de contexto MCP

En el mismo `system_prompt`, integrar además estas reglas para la propiedad de la conversación y el mínimo contexto enviado a las Tools:

```text
"Utiliza las herramientas de Customer MCP "
"cuando necesites consultar información "
"del sistema corporativo de clientes. "

"Utiliza verify_customer_tool cuando sólo "
"necesites comprobar si el declarante "
"es cliente. "

"Utiliza get_customer_profile_tool únicamente "
"cuando necesites un dato personal "
"específico. Envía el national_id del "
"declarante y sólo el requested_field "
"necesario: email, phone_number o address. "

"No inventes información del cliente. "

"No utilices Conversation Memory como "
"fuente de verdad para datos del cliente. "

"Conversation Memory puede utilizarse para "
"resolver referencias conversacionales, "
"pero no es fuente de verdad para datos "
"corporativos. Obtén esos datos desde las "
"herramientas MCP autorizadas. "
```

---

# 7. Flujo conversacional con MCP

El flujo conversacional queda:

    session_id
        ↓
    ConversationSession
        ↓
    summary + recent messages
        ↓
    Claims Analyst Agent
        ↓
    determina intención
        ↓
    MCP Tool Call

MCP no carga:

    ConversationSession

---

## Ejemplo completo del primer turno

Turno 1:

    User:
    "¿El declarante es cliente?"

El agente obtiene:

    national_id
        =
    123456785

desde:

    ClaimData

y llama:

```json
{
  "tool": "verify_customer",
  "arguments": {
    "national_id": "123456785"
  }
}
```

Respuesta:

```json
{
  "customer_found": true,
  "customer_id": "CUST-000123"
}
```

---

## Segundo turno y resolución de referencias

Usuario:

    "¿Cuál es su correo?"

La memoria permite interpretar:

    "su"
        ↓
    mismo declarante

El agente obtiene el `national_id` desde `ClaimData`; la memoria resuelve la referencia conversacional, pero no proporciona ni valida un ID interno.

La información se obtiene mediante:

```json
{
  "tool": "get_customer_profile",
  "arguments": {
        "national_id": "123456785",
        "requested_field": "email"
  }
}
```

---

## session_id no es argumento funcional

Incorrecto:

```json
{
  "session_id": "...",
    "national_id": "123456785",
    "requested_field": "email"
}
```

Correcto:

```json
{
    "national_id": "123456785",
    "requested_field": "email"
}
```

Posteriormente `session_id` puede propagarse como:

    telemetry metadata

pero no como argumento funcional.

---

## MCP no almacena conversación

Customer MCP Server debe ser:

    stateless

respecto de:

    ConversationSession

Cada invocación contiene todos los argumentos necesarios.

---

## MCP tampoco almacena CustomerProfile

No utilizar el MCP Server como:

    customer cache

Customer API continúa siendo:

    source of truth

---

# 8. Errores y validación de respuestas

Necesitamos diferenciar:

    MCP connection failure

    MCP tool unavailable

    MCP invalid response

    Customer API unavailable

    Customer not found

---

## Excepciones MCP

El MCP Server traduce los fallos del cliente REST a los códigos estables `CUSTOMER_API_UNAVAILABLE`, `CUSTOMER_API_ERROR` y `CUSTOMER_NOT_FOUND`. El MCP Client interpreta esos códigos y los convierte en las excepciones definidas previamente, sin propagar respuestas HTTP, mensajes con PII ni trazas internas. `verify_customer` representa una persona inexistente con `customer_found=false`; `CUSTOMER_NOT_FOUND` se reserva para un perfil cuyo `customer_id` no existe.

---

## No convertir todos los errores en not found

Si MCP falla:

    customer_found
        !=
    false

El estado es:

    unknown

porque la operación no pudo completarse.

---

## Validación de respuesta

Toda respuesta de:

    verify_customer

debe validarse mediante:

```python
CustomerVerification.model_validate(
    result
)
```

Toda respuesta de:

    get_customer_profile

debe contener exactamente el campo solicitado, por ejemplo:

```python
{"email": "ana@example.com"}
```

Customer Service valida que no existan campos adicionales y adapta el valor al modelo `CustomerFieldValue`. `CustomerProfile` no se usa para validar la respuesta MCP porque sus campos de identidad no forman parte de este contrato minimizado.

No confiar en JSON arbitrario.

La conversión debe capturar `pydantic.ValidationError` y elevar `McpInvalidResponse`, conservando la excepción original como causa. No rellenar campos faltantes ni descartar campos inválidos silenciosamente.

---

## MCP es una frontera no confiable

Aunque sea un componente propio:

    MCP response

debe considerarse:

    external input

Por tanto:

    validate
        ↓
    domain model

antes de usarlo.

---

# 9. Health de Customer MCP

Agregar un health check para comprobar que:

    Customer MCP Server

está disponible y publica las Tools esperadas.

Conceptualmente:

    GET
    /health/customer-mcp

---

## Modelo de respuesta

Definir en `app/schemas.py`, junto a los demás modelos de la API:

```python
from typing import Literal

from pydantic import BaseModel


class CustomerMcpHealthResponse(
    BaseModel
):
    status: Literal["ok"]
    server: Literal["customer-mcp"]
    tools: list[str]
```

---

## Resultado esperado

Por ejemplo:

```json
{
  "status": "ok",
  "server": "customer-mcp",
  "tools": [
    "verify_customer",
    "get_customer_profile"
  ]
}
```

---

## Comprobación real de disponibilidad

El health check no debe limitarse a:

    proceso existe

Debe comprobar:

    conexión MCP
        ↓
    list tools
        ↓
    expected tools

El endpoint de Claims API llama `list_customer_mcp_tools()`. Con `stdio`, esa función inicia el proceso, hace handshake, ejecuta `list_tools` y cierra la conexión. El endpoint devuelve `503 Service Unavailable` si el proceso no inicia o el conjunto publicado no coincide exactamente con las dos Tools permitidas. Este check valida el proceso MCP y su contrato, pero no comprueba Customer API; `/health/customer` conserva esa responsabilidad.

Crear:

    app/health.py

Agregar:

```python
from fastapi import APIRouter, HTTPException

from app.schemas import CustomerMcpHealthResponse
from app.mcp.customer_client import (
    list_customer_mcp_tools,
)
from app.mcp.errors import McpUnavailable


router = APIRouter()
EXPECTED_CUSTOMER_TOOLS = {
    "verify_customer",
    "get_customer_profile",
}


@router.get(
    "/health/customer-mcp",
    response_model=CustomerMcpHealthResponse,
    responses={
        503: {"description": "Customer MCP unavailable or unhealthy"},
    },
)
async def customer_mcp_health() -> CustomerMcpHealthResponse:
    try:
        tool_names = await list_customer_mcp_tools()
    except McpUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="Customer MCP is unavailable",
        ) from exc

    if set(tool_names) != EXPECTED_CUSTOMER_TOOLS:
        raise HTTPException(
            status_code=503,
            detail="Customer MCP tool contract is unhealthy",
        )

    return CustomerMcpHealthResponse(
        status="ok",
        server="customer-mcp",
        tools=sorted(tool_names),
    )
```

Se debe registrar este `router` en la aplicación FastAPI. En una aplicación multi-worker, cada chequeo `stdio` inicia un proceso hijo; limitar la frecuencia del health polling y considerar un proceso/sesión MCP persistente si el coste resulta significativo.

### Registrar el router en Claims API

En `app/main.py`, reutilizar la instancia `app = FastAPI(...)` que ya existe. Importar el router de `app/health.py` y registrarlo una sola vez después de crear la aplicación; no crear otra instancia de `FastAPI`.

```python
from app.health import router as health_router


app = FastAPI(...)
app.include_router(health_router)
```

Como `app` ya está definido, añadir únicamente el import y `app.include_router(health_router)` junto al registro de las demás rutas. Como el router declara la ruta completa `/health/customer-mcp`, no se necesita un `prefix`.

---

# 10. Estrategia de pruebas

Crear:

    tests/unit/test_customer_mcp_server.py

Los tests deben comprobar la lógica de las Tools utilizando mocks del:

    Customer Client

No necesitan Customer API real.

Además de los casos nominales, cubrir con tests unitarios el mapeo de las excepciones del Customer Client a los códigos MCP, y comprobar que `verify_customer` devuelve `customer_found=false` para un identificador desconocido en vez de elevar `CUSTOMER_NOT_FOUND`.

---

## Test unitario de verify_customer

Implementar en `tests/unit/test_customer_mcp_server.py`:

```python
from unittest.mock import AsyncMock

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from app.customer_client import CustomerApiError, CustomerApiUnavailable
from app.mcp import customer_server
from app.schemas import CustomerVerification


@pytest.mark.asyncio
async def test_verify_customer_returns_verification(monkeypatch):
    verify_mock = AsyncMock(
        return_value=CustomerVerification(
            customer_found=True,
            customer_id="CUST-000123",
        )
    )
    monkeypatch.setattr(
        customer_server,
        "verify_customer_from_api",
        verify_mock,
    )

    result = await customer_server.verify_customer("123456785")

    verify_mock.assert_awaited_once_with("123456785")
    assert result == {
        "customer_found": True,
        "customer_id": "CUST-000123",
    }


@pytest.mark.asyncio
async def test_verify_customer_returns_not_found_without_error(monkeypatch):
    verify_mock = AsyncMock(
        return_value=CustomerVerification(
            customer_found=False,
            customer_id=None,
        )
    )
    monkeypatch.setattr(
        customer_server,
        "verify_customer_from_api",
        verify_mock,
    )

    result = await customer_server.verify_customer("999999999")

    assert result["customer_found"] is False
    assert result["customer_id"] is None


@pytest.mark.parametrize(
    ("api_error", "expected_code"),
    [
        (CustomerApiUnavailable("offline"), "CUSTOMER_API_UNAVAILABLE"),
        (CustomerApiError("failed"), "CUSTOMER_API_ERROR"),
    ],
)
@pytest.mark.asyncio
async def test_verify_customer_maps_customer_api_errors(
    monkeypatch,
    api_error,
    expected_code,
):
    monkeypatch.setattr(
        customer_server,
        "verify_customer_from_api",
        AsyncMock(side_effect=api_error),
    )

    with pytest.raises(ToolError, match=expected_code):
        await customer_server.verify_customer("123456785")
```

---

## Test unitario de get_customer_profile

Implementar el test con mocks para no depender de Customer API real. Parametrizarlo para cada campo permitido y comprobar que el servicio verifica `national_id`, usa el `customer_id` resultante sólo en la llamada REST y que la Tool MCP devuelve únicamente el dato de contacto solicitado:

```python
from unittest.mock import AsyncMock

import pytest

from app.mcp import customer_server
from app.schemas import CustomerProfile, CustomerVerification


@pytest.mark.parametrize(
    ("requested_field", "requested_value"),
    [
        ("email", "ana@example.com"),
        ("phone_number", "+34123456789"),
        ("address", "Calle Mayor 1"),
    ],
)
@pytest.mark.asyncio
async def test_get_customer_profile_requests_only_requested_field(
    monkeypatch,
    requested_field,
    requested_value,
):
    national_id = "123456785"
    customer_id = "CUST-000123"
    verification_mock = AsyncMock(
        return_value=CustomerVerification(
            customer_found=True,
            customer_id=customer_id,
        )
    )
    contact_data = {
        "email": None,
        "phone_number": None,
        "address": None,
    }
    contact_data[requested_field] = requested_value
    profile_mock = AsyncMock(
        return_value=CustomerProfile(
            customer_id=customer_id,
            national_id=national_id,
            full_name="Ana García",
            **contact_data,
        )
    )
    monkeypatch.setattr(
        customer_server,
        "verify_customer_from_api",
        verification_mock,
    )
    monkeypatch.setattr(
        customer_server,
        "get_customer_profile_from_api",
        profile_mock,
    )

    result = await customer_server.get_customer_profile(
        national_id,
        requested_field,
    )

    verification_mock.assert_awaited_once_with(national_id)
    profile_mock.assert_awaited_once_with(
        customer_id,
        requested_field,
    )
    assert result == {requested_field: requested_value}
```

La validación de un `requested_field` fuera de `email`, `phone_number` y `address` corresponde al test de integración que invoca la Tool mediante MCP, para comprobar el esquema publicado y la validación del protocolo.
Agregar también estos casos unitarios en `tests/unit/test_customer_mcp_server.py`:

```python
@pytest.mark.asyncio
async def test_get_customer_profile_does_not_lookup_unknown_customer(
    monkeypatch,
):
    verify_mock = AsyncMock(
        return_value=CustomerVerification(
            customer_found=False,
            customer_id=None,
        )
    )
    profile_mock = AsyncMock()
    monkeypatch.setattr(customer_server, "verify_customer_from_api", verify_mock)
    monkeypatch.setattr(
        customer_server,
        "get_customer_profile_from_api",
        profile_mock,
    )

    with pytest.raises(ToolError, match="CUSTOMER_NOT_FOUND"):
        await customer_server.get_customer_profile("999999999", "email")

    profile_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_customer_profile_rejects_mismatched_identity(
    monkeypatch,
):
    monkeypatch.setattr(
        customer_server,
        "verify_customer_from_api",
        AsyncMock(
            return_value=CustomerVerification(
                customer_found=True,
                customer_id="CUST-000123",
            )
        ),
    )
    monkeypatch.setattr(
        customer_server,
        "get_customer_profile_from_api",
        AsyncMock(
            return_value=CustomerProfile(
                customer_id="CUST-000123",
                national_id="999999999",
                full_name="Otro cliente",
                email="otro@example.com",
            )
        ),
    )

    with pytest.raises(ToolError, match="CUSTOMER_API_ERROR"):
        await customer_server.get_customer_profile("123456785", "email")
```

En `tests/unit/test_customer_service.py`, comprobar el mapeo de errores del adaptador y la validación de la respuesta MCP y la validación de la respuesta MCP del servicio directo:

```python
from unittest.mock import AsyncMock

import pytest

from app import customer_service
from app.mcp.errors import McpInvalidResponse


@pytest.mark.asyncio
async def test_customer_service_rejects_invalid_mcp_profile(monkeypatch):
    monkeypatch.setattr(
        customer_service,
        "call_customer_mcp_tool",
        AsyncMock(return_value={"unexpected": "payload"}),
    )

    with pytest.raises(McpInvalidResponse):
        await customer_service.get_claimant_customer_profile(
            "123456785",
            "email",
        )
```

Para comprobar que un fallo al iniciar el proceso servidor se clasifica como indisponibilidad MCP, agregar al mismo archivo:

```python
from app.mcp import customer_client as customer_mcp_client
from app.mcp.errors import McpUnavailable


@pytest.mark.asyncio
async def test_mcp_client_maps_stdio_start_failure_to_unavailable(monkeypatch):
    class FailingStdio:
        async def __aenter__(self):
            raise OSError("server executable not found")

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(
        customer_mcp_client,
        "stdio_client",
        lambda _: FailingStdio(),
    )

    with pytest.raises(McpUnavailable):
        await customer_mcp_client.list_customer_mcp_tools()
```

---

## Test de Tool Discovery

Crear:

    tests/integration/test_customer_mcp.py

Agregar los siguientes tests. `Client(customer_server.mcp)` comprueba el contrato cliente-servidor en memoria; el test con `SERVER_PARAMETERS` confirma además que el proceso stdio se inicia y publica las mismas Tools.

```python
from unittest.mock import AsyncMock

import pytest
from mcp import Client

from app.mcp import customer_server
from app.customer_client import CustomerApiUnavailable
from app.mcp.customer_client import SERVER_PARAMETERS
from app.schemas import CustomerProfile, CustomerVerification


@pytest.mark.asyncio
async def test_customer_mcp_discovers_expected_tools():
    async with Client(customer_server.mcp) as client:
        listing = await client.list_tools()

    tools_by_name = {tool.name: tool for tool in listing.tools}
    assert set(tools_by_name) == {
        "verify_customer",
        "get_customer_profile",
    }
    assert set(tools_by_name["verify_customer"].input_schema["properties"]) == {
        "national_id",
    }
    profile_schema = tools_by_name["get_customer_profile"].input_schema
    assert set(profile_schema["properties"]) == {
        "national_id",
        "requested_field",
    }
    assert profile_schema["properties"]["requested_field"]["enum"] == [
        "email",
        "phone_number",
        "address",
    ]

@pytest.mark.asyncio
async def test_customer_mcp_stdio_process_starts_and_discovers_tools():
    async with Client(SERVER_PARAMETERS) as client:
        result = await client.list_tools()

    assert {tool.name for tool in result.tools} == {
        "verify_customer",
        "get_customer_profile",
    }
```

El primer test valida el contrato en memoria; este segundo lanza el proceso servidor mediante `stdio`.

### Invocación de verify_customer mediante MCP

No llamar directamente a la función REST:

```python
@pytest.mark.asyncio
async def test_verify_customer_is_invoked_through_mcp(monkeypatch):
    verify_mock = AsyncMock(
        return_value=CustomerVerification(
            customer_found=True,
            customer_id="CUST-000123",
        )
    )
    monkeypatch.setattr(
        customer_server,
        "verify_customer_from_api",
        verify_mock,
    )

    async with Client(customer_server.mcp) as client:
        result = await client.call_tool(
            "verify_customer",
            {"national_id": "123456785"},
        )

    assert result.is_error is False
    assert result.structured_content == {
        "customer_found": True,
        "customer_id": "CUST-000123",
    }
    verify_mock.assert_awaited_once_with("123456785")
```

---

## Test de perfil mediante MCP

Invocar `get_customer_profile` mediante MCP y comprobar la respuesta minimizada y la delegación interna al cliente REST:

```python
@pytest.mark.asyncio
async def test_get_customer_profile_is_invoked_through_mcp(monkeypatch):
    national_id = "123456785"
    customer_id = "CUST-000123"
    verify_mock = AsyncMock(
        return_value=CustomerVerification(
            customer_found=True,
            customer_id=customer_id,
        )
    )
    profile_mock = AsyncMock(
        return_value=CustomerProfile(
            customer_id=customer_id,
            national_id=national_id,
            full_name="Ana García",
            email="ana@example.com",
        )
    )
    monkeypatch.setattr(
        customer_server,
        "verify_customer_from_api",
        verify_mock,
    )
    monkeypatch.setattr(
        customer_server,
        "get_customer_profile_from_api",
        profile_mock,
    )

    async with Client(customer_server.mcp) as client:
        result = await client.call_tool(
            "get_customer_profile",
            {
                "national_id": national_id,
                "requested_field": "email",
            },
        )

    assert result.is_error is False
    assert result.structured_content == {
        "email": "ana@example.com",
    }
    assert "customer_id" not in result.structured_content
    assert "national_id" not in result.structured_content
    assert "full_name" not in result.structured_content
    verify_mock.assert_awaited_once_with(national_id)
    profile_mock.assert_awaited_once_with(customer_id, "email")
```

La validación del esquema se prueba invocando un valor fuera del enum anunciado por discovery:

```python
@pytest.mark.asyncio
async def test_get_customer_profile_rejects_disallowed_requested_field():
    async with Client(customer_server.mcp) as client:
        result = await client.call_tool(
            "get_customer_profile",
            {
                "national_id": "123456785",
                "requested_field": "birth_date",
            },
        )

    assert result.is_error is True
```

---

## Test de data minimization

La pregunta:

    "¿El declarante es cliente?"

debe producir:

    verify_customer

No:

    get_customer_profile

Este test continúa siendo necesario después de introducir MCP. En el nivel del contrato MCP, verificar que cada Tool sólo publica los argumentos que necesita:

```python
@pytest.mark.asyncio
async def test_customer_mcp_tools_publish_minimal_argument_schemas():
    async with Client(customer_server.mcp) as client:
        listing = await client.list_tools()

    schemas = {
        tool.name: tool.input_schema
        for tool in listing.tools
    }
    assert set(schemas["verify_customer"]["properties"]) == {
        "national_id",
    }
    assert set(schemas["get_customer_profile"]["properties"]) == {
        "national_id",
        "requested_field",
    }
    assert "customer_id" not in str(schemas)
    assert "session_id" not in str(schemas)
```

La elección semántica del agente (pregunta de existencia frente a pregunta de perfil) se comprueba en los tests del Claims Analyst Agent con un modelo determinista de prueba; no se intenta inferirla desde un test del servidor MCP.
El test siguiente fuerza cada adapter local de `app/tools.py` y comprueba qué método de `app/customer_service.py` se ejecuta.

```python
from unittest.mock import AsyncMock

import pytest
from pydantic_ai import ModelResponse, TextPart, ToolCallPart, models
from pydantic_ai.models.function import FunctionModel

from app import agent as agent_module
from app import tools as agent_tools
from app.schemas import CustomerFieldValue, CustomerVerification


models.ALLOW_MODEL_REQUESTS = False


@pytest.mark.parametrize(
    ("prompt", "tool_name", "tool_arguments"),
    [
        (
            "¿El declarante es cliente?",
            "verify_customer_tool",
            {"national_id": "123456785"},
        ),
        (
            "¿Cuál es el correo del declarante?",
            "get_customer_profile_tool",
            {
                "national_id": "123456785",
                "requested_field": "email",
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_claims_agent_selects_customer_tool(
    monkeypatch,
    prompt,
    tool_name,
    tool_arguments,
):
    verify_service = AsyncMock(
        return_value=CustomerVerification(
            customer_found=True,
            customer_id="CUST-000123",
        )
    )
    profile_service = AsyncMock(
        return_value=CustomerFieldValue(
            requested_field="email",
            value="ana@example.com",
        )
    )
    monkeypatch.setattr(
        agent_tools,
        "verify_claimant_customer",
        verify_service,
    )
    monkeypatch.setattr(
        agent_tools,
        "get_claimant_customer_profile",
        profile_service,
    )

    def choose_expected_tool(messages, info):
        if any(
            part.part_kind == "tool-return"
            for message in messages
            for part in message.parts
        ):
            return ModelResponse(
                parts=[TextPart("Respuesta de prueba")]
            )
        return ModelResponse(
            parts=[ToolCallPart(tool_name, tool_arguments)]
        )

    with agent_module.agent.override(
        model=FunctionModel(choose_expected_tool),
    ):
        await agent_module.agent.run(prompt)

    if tool_name == "verify_customer_tool":
        verify_service.assert_awaited_once_with("123456785")
        profile_service.assert_not_awaited()
    else:
        profile_service.assert_awaited_once_with(
            "123456785",
            "email",
        )
        verify_service.assert_not_awaited()
```

---

## Test de Conversation Memory + MCP

Crear una sesión:

    SESSION-A

Turno 1:

    "¿El declarante es cliente?"

Esperado:

    verify_customer

Turno 2:

    "¿Cuál es su correo?"

Esperado:

    get_customer_profile

La segunda llamada no debe incluir:

    ConversationSession

como argumento MCP.

Registrar los argumentos de cada Tool en un fake o spy y comprobar que `verify_customer` recibe sólo `national_id` y `get_customer_profile` recibe `national_id` más `requested_field`; nunca deben incluir `customer_id`, `session_id`, summary ni mensajes. Para el aislamiento, ejecutar ambos turnos en `SESSION-A` y una consulta independiente en `SESSION-B`; verificar que el segundo contexto no hereda referencias ni datos del primero.

El test del servicio puede aislar la frontera MCP y comprobar sus argumentos sin invocar un LLM:

```python
from app import customer_service


@pytest.mark.asyncio
async def test_customer_service_sends_only_explicit_mcp_arguments(monkeypatch):
    calls = []

    async def fake_call_customer_mcp_tool(tool_name, arguments):
        calls.append((tool_name, arguments))
        if tool_name == "verify_customer":
            return {
                "customer_found": True,
                "customer_id": "CUST-000123",
            }
        return {"email": "ana@example.com"}

    monkeypatch.setattr(
        customer_service,
        "CUSTOMER_INTEGRATION_PROVIDER",
        "mcp",
        raising=False,
    )
    monkeypatch.setattr(
        customer_service,
        "call_customer_mcp_tool",
        fake_call_customer_mcp_tool,
    )

    await customer_service.verify_claimant_customer("123456785")
    await customer_service.get_claimant_customer_profile(
        "123456785",
        "email",
    )

    assert calls == [
        (
            "verify_customer",
            {"national_id": "123456785"},
        ),
        (
            "get_customer_profile",
            {
                "national_id": "123456785",
                "requested_field": "email",
            },
        ),
    ]
    assert all("session_id" not in arguments for _, arguments in calls)
    assert all("customer_id" not in arguments for _, arguments in calls)
```

Probar continuidad y aislamiento de sesión con el servicio real de memoria y un agente determinista:

```python
from types import SimpleNamespace

from app import conversation_memory, conversation_service, customer_service


@pytest.mark.asyncio
async def test_conversation_sessions_keep_mcp_context_isolated(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        conversation_memory,
        "CONVERSATION_STORAGE_PATH",
        tmp_path,
    )
    monkeypatch.setattr(
        customer_service,
        "CUSTOMER_INTEGRATION_PROVIDER",
        "mcp",
        raising=False,
    )

    mcp_calls = []
    prompts = []

    async def fake_call_customer_mcp_tool(tool_name, arguments):
        mcp_calls.append((tool_name, dict(arguments)))
        if tool_name == "verify_customer":
            return {
                "customer_found": True,
                "customer_id": "CUST-000123",
            }
        return {"email": "ana@example.com"}

    async def fake_agent_run(prompt):
        prompts.append(prompt)
        if "¿Cuál es su correo?" in prompt:
            await customer_service.get_claimant_customer_profile(
                "123456785",
                "email",
            )
            return SimpleNamespace(output="ana@example.com")

        national_id = (
            "999999999"
            if "CONTEXTO-B" in prompt
            else "123456785"
        )
        await customer_service.verify_claimant_customer(national_id)
        return SimpleNamespace(output="Sí, está registrado.")

    monkeypatch.setattr(
        customer_service,
        "call_customer_mcp_tool",
        fake_call_customer_mcp_tool,
    )
    monkeypatch.setattr(
        conversation_service.agent,
        "run",
        fake_agent_run,
    )

    session_a = conversation_memory.create_session(
        claim_number="CLM-A"
    )
    session_b = conversation_memory.create_session(
        claim_number="CLM-B"
    )

    await conversation_service.process_conversation_turn(
        session_id=session_a.session_id,
        message="¿El declarante es cliente? CONTEXTO-A",
    )
    await conversation_service.process_conversation_turn(
        session_id=session_b.session_id,
        message="¿El declarante es cliente? CONTEXTO-B",
    )
    response_a = await conversation_service.process_conversation_turn(
        session_id=session_a.session_id,
        message="¿Cuál es su correo?",
    )

    assert response_a == "ana@example.com"
    assert "CONTEXTO-A" in prompts[2]
    assert "CONTEXTO-B" not in prompts[2]
    assert mcp_calls == [
        (
            "verify_customer",
            {"national_id": "123456785"},
        ),
        (
            "verify_customer",
            {"national_id": "999999999"},
        ),
        (
            "get_customer_profile",
            {
                "national_id": "123456785",
                "requested_field": "email",
            },
        ),
    ]
    assert all("session_id" not in arguments for _, arguments in mcp_calls)
    assert all("customer_id" not in arguments for _, arguments in mcp_calls)
```

---

## Test de aislamiento de sesiones

La prueba `test_conversation_sessions_keep_mcp_context_isolated` crea `SESSION-A` y `SESSION-B`, comprueba que el turno de A conserva sólo su propio contexto y que las Tools compartidas nunca reciben estado de conversación.

---

## Test de MCP unavailable

Detener Customer MCP Server.

La aplicación debe producir:

    McpUnavailable

y responder funcionalmente:

    sistema de clientes no disponible

No:

    cliente no encontrado

Comprobar también que `GET /health/customer-mcp` devuelve `503` si no se puede iniciar el proceso MCP.

La prueba unitaria del cliente que fuerza un error de arranque `stdio` está incluida en `test_customer_mcp_server.py`. Verificar además el mapeo HTTP del endpoint health. En el archivo `tests/integration/test_customer_mcp.py` agregar:

```python
from fastapi import HTTPException
from app import health
from app.mcp.errors import McpUnavailable


@pytest.mark.asyncio
async def test_customer_mcp_health_returns_503_when_unavailable(monkeypatch):
    monkeypatch.setattr(
        health,
        "list_customer_mcp_tools",
        AsyncMock(side_effect=McpUnavailable("offline")),
    )

    with pytest.raises(HTTPException) as error:
        await health.customer_mcp_health()

    assert error.value.status_code == 503
```

---

## Test de Customer API unavailable

Mantener MCP Server activo.

Detener:

    Customer API

La llamada:

    Claims Agent
        ↓
    MCP
        ↓
    Customer API

debe distinguir correctamente que:

    MCP está disponible

pero:

    Customer API no

Verificar que se propaga como `McpCustomerApiUnavailable` (y luego como el error de integración que consume Claims Agent), no como `McpUnavailable` ni como cliente inexistente.

Añadir un caso para `CUSTOMER_API_ERROR` y otro para `McpInvalidResponse`, de modo que indisponibilidad, error de negocio/transporte, not found y respuesta malformada mantengan resultados diferenciados.

Comprobar el código MCP seguro usando el cliente MCP in-process y un mock del cliente REST. En el archivo `tests/integration/test_customer_mcp.py` agregar:

```python
from app.customer_client import CustomerApiUnavailable
from app.mcp import customer_server
from mcp import Client

@pytest.mark.asyncio
async def test_customer_api_unavailable_is_not_customer_not_found(monkeypatch):
    monkeypatch.setattr(
        customer_server,
        "verify_customer_from_api",
        AsyncMock(side_effect=CustomerApiUnavailable("offline")),
    )

    async with Client(customer_server.mcp) as client:
        result = await client.call_tool(
            "verify_customer",
            {"national_id": "123456785"},
        )

    error_text = " ".join(
        block.text
        for block in result.content
        if hasattr(block, "text")
    )
    assert result.is_error is True
    assert "CUSTOMER_API_UNAVAILABLE" in error_text
    assert "CUSTOMER_NOT_FOUND" not in error_text
```

Para comprobar el mapeo completo del MCP Client sobre `stdio`, arrancar el proceso con una URL de Customer API que rechace conexiones y verificar la excepción de aplicación:

```python
import pytest

from app.mcp import customer_client
from app.mcp.errors import McpCustomerApiUnavailable


@pytest.mark.asyncio
async def test_stdio_client_maps_customer_api_failure(monkeypatch):
    parameters = customer_client.SERVER_PARAMETERS.model_copy(
        update={
            "env": {
                **customer_client.SERVER_PARAMETERS.env,
                "CUSTOMER_API_BASE_URL": "http://127.0.0.1:1",
                "CUSTOMER_API_TIMEOUT_SECONDS": "0.2",
            }
        }
    )
    monkeypatch.setattr(
        customer_client,
        "SERVER_PARAMETERS",
        parameters,
    )

    with pytest.raises(McpCustomerApiUnavailable):
        await customer_client.call_customer_mcp_tool(
            "verify_customer",
            {"national_id": "123456785"},
        )
```

---

## Capas de error

Podemos observar:

    Claims Agent
        │
        ▼
    MCP Client
        │
        ├── MCP unavailable
        │
        ▼
    MCP Server
        │
        ▼
    Customer API
        │
        ├── API unavailable
        ├── not found
        └── success

Estas condiciones no son equivalentes.

---

## Retirar test de perfil de PoC 10

Antes de ejecutar la suite, eliminar de `tests/unit/test_customer_service.py` la función `test_customer_profile_must_match_claimant` incorporada en PoC 10. Retirar también `CustomerApiError`, `CustomerProfile` y `CustomerVerification` de los imports del archivo si ya no los utiliza otro test de ese módulo.

La prueba quedó obsoleta porque el servicio ya no llama directamente a `verify_customer` y `get_customer_profile` REST ni compara allí el `national_id`; ahora delega en `call_customer_mcp_tool`. Si se conserva, los mocks antiguos no interceptan esa llamada y el test intenta iniciar el MCP Server real, pudiendo terminar en `McpUnavailable`.

La validación de identidad no se elimina: se conserva en `tests/unit/test_customer_mcp_server.py`, en `test_get_customer_profile_rejects_mismatched_identity`, que comprueba que la Tool MCP rechaza un perfil cuyo `national_id` no coincide con el declarante. Esa es la capa que ahora realiza y controla la comprobación.

## Servicios para tests de integración

Antes de ejecutar `tests/integration`, deben estar disponibles:

    Ollama

    Qdrant

La configuración, los modelos y los comandos de arranque ya están descritos en las PoC 2, 3 y 6. Los tests no requieren iniciar Claims API ni Customer Mock API: llaman al código de aplicación directamente y simulan Customer API. El test que usa `stdio` inicia Customer MCP como proceso hijo. `test_process_document` se omite si no se configura `TEST_DOCUMENT_ID`.

---

## Ejecución de los tests

Desde la raíz del proyecto, ejecutar primero los tests unitarios y después los de integración:

```bash
uv run pytest tests/unit -v
uv run pytest tests/integration -v
```

Los tests unitarios no requieren Customer API real. Los tests de integración verifican el contrato MCP, el transporte `stdio`, el mapeo de errores y la interacción con Conversation Memory según los servicios simulados por cada test.

---

# 11. Selección del provider REST/MCP y rollback

No eliminaremos el cliente REST existente:

    app/customer_client.py

El MCP Server lo reutiliza:

    MCP Tool
        ↓
    app/customer_client.py
        ↓
    Customer API

Esto evita duplicar lógica HTTP.

---

## Selección del provider

Se va a introducir en el módulo de configuración existente:

    CUSTOMER_INTEGRATION_PROVIDER

con valores:

    rest

    mcp

Y para esta PoC se va a utilizar el provider MCP:

    CUSTOMER_INTEGRATION_PROVIDER=mcp

---

## Configuración

En `app/config.py`, agregar:

```python
import os


CUSTOMER_INTEGRATION_PROVIDER = os.getenv(
    "CUSTOMER_INTEGRATION_PROVIDER",
    "mcp",
).strip().lower()

if CUSTOMER_INTEGRATION_PROVIDER not in {"rest", "mcp"}:
    raise ValueError(
        "CUSTOMER_INTEGRATION_PROVIDER must be 'rest' or 'mcp'"
    )
```

Esto permite rollback durante las pruebas.

---

## Provider REST

Si:

    CUSTOMER_INTEGRATION_PROVIDER=rest

Customer Service utiliza:

    app/customer_client.py

---

## Provider MCP

Si:

    CUSTOMER_INTEGRATION_PROVIDER=mcp

Customer Service utiliza en MCP Client:

    app/mcp/customer_client.py

Las dos operaciones del Customer Service mantienen el contrato de dominio y seleccionan el provider explícitamente. Esta implementación también incorpora el manejo de excepciones: traduce los errores de Customer API comunicados por MCP a los errores de integración que consume Claims Agent y convierte las respuestas MCP inválidas en `McpInvalidResponse`. Para ello, se modifica el archivo `app/customer_service.py` para incluir la lógica de selección del provider y el mapeo de errores:

```python
from pydantic import ValidationError
from typing import Literal

from app.config import CUSTOMER_INTEGRATION_PROVIDER
from app.customer_client import (
    CustomerApiError,
    CustomerApiUnavailable,
    CustomerNotFound,
    get_customer_profile as get_customer_profile_from_api,
    normalize_national_id,
    verify_customer as verify_customer_from_api,
)
from app.schemas import (
    CustomerFieldValue,
    CustomerProfile,
    CustomerVerification,
)
from app.mcp.customer_client import call_customer_mcp_tool
from app.mcp.errors import (
    McpCustomerApiError,
    McpCustomerApiUnavailable,
    McpCustomerNotFound,
    McpInvalidResponse,
)


async def verify_claimant_customer(
    national_id: str,
) -> CustomerVerification:
    if CUSTOMER_INTEGRATION_PROVIDER == "rest":
        return await verify_customer_from_api(national_id)

    try:
        result = await call_customer_mcp_tool(
            tool_name="verify_customer",
            arguments={"national_id": national_id},
        )
    except McpCustomerApiUnavailable as exc:
        raise CustomerApiUnavailable() from exc
    except McpCustomerApiError as exc:
        raise CustomerApiError() from exc
    try:
        return CustomerVerification.model_validate(result)
    except ValidationError as exc:
        raise McpInvalidResponse(
            "verify_customer devolvió una respuesta no válida"
        ) from exc


async def get_claimant_customer_profile(
    national_id: str,
    requested_field: Literal["email", "phone_number", "address"],
) -> CustomerFieldValue:
    if CUSTOMER_INTEGRATION_PROVIDER == "rest":
        verification = await verify_customer_from_api(national_id)
        if not verification.customer_found or not verification.customer_id:
            raise CustomerNotFound("Claimant is not a customer")

        profile = await get_customer_profile_from_api(
            verification.customer_id,
            requested_field,
        )
        if normalize_national_id(profile.national_id) != normalize_national_id(
            national_id
        ):
            raise CustomerApiError(
                "Customer profile does not match the claimant"
            )
        return CustomerFieldValue(
            requested_field=requested_field,
            value=getattr(profile, requested_field),
        )

    try:
        result = await call_customer_mcp_tool(
            tool_name="get_customer_profile",
            arguments={
                "national_id": national_id,
                "requested_field": requested_field,
            },
        )
    except McpCustomerApiUnavailable as exc:
        raise CustomerApiUnavailable() from exc
    except McpCustomerNotFound as exc:
        raise CustomerNotFound() from exc
    except McpCustomerApiError as exc:
        raise CustomerApiError() from exc
    if not isinstance(result, dict) or set(result) != {requested_field}:
        raise McpInvalidResponse(
            "get_customer_profile devolvió una respuesta no válida"
        )
    try:
        return CustomerFieldValue.model_validate(
            {
                "requested_field": requested_field,
                "value": result[requested_field],
            }
        )
    except ValidationError as exc:
        raise McpInvalidResponse(
            "get_customer_profile devolvió una respuesta no válida"
        ) from exc
```

Adaptar únicamente los paths de imports al módulo real de configuración y a la ubicación existente de los modelos; no duplicar `CustomerVerification`, `CustomerProfile` ni `CustomerFieldValue`. Ambos providers devuelven `CustomerFieldValue` al agente, aunque REST utilice `CustomerProfile` internamente. Mapear `McpCustomerApiUnavailable`, `McpCustomerApiError` y `McpCustomerNotFound` a los errores de integración ya utilizados por Claims Agent, conservando las diferencias entre indisponibilidad, fallo de API y perfil inexistente.
Como `CUSTOMER_INTEGRATION_PROVIDER` ya está definido e importado en este punto, agregar el test de traducción del error del provider en `tests/unit/test_customer_service.py`:

```python
from unittest.mock import AsyncMock

import pytest

from app import customer_service
from app.customer_client import CustomerApiUnavailable
from app.mcp.errors import McpCustomerApiUnavailable


@pytest.mark.asyncio
async def test_customer_service_maps_mcp_unavailable(monkeypatch):
    monkeypatch.setattr(
        customer_service,
        "CUSTOMER_INTEGRATION_PROVIDER",
        "mcp",
    )
    monkeypatch.setattr(
        customer_service,
        "call_customer_mcp_tool",
        AsyncMock(side_effect=McpCustomerApiUnavailable("offline")),
    )

    with pytest.raises(CustomerApiUnavailable):
        await customer_service.get_claimant_customer_profile(
            "123456785",
            "email",
        )
```

---

## Motivo para mantener ambos temporalmente

Esto permite comparar:

    REST directo

contra:

    MCP

sin modificar:

    Claims Analyst Agent

ni:

    ConversationSession

También proporciona:

    rollback

durante la PoC.

---

## Retirar el camino temporal cuando termine la evaluación

La coexistencia es útil para:

    evaluación

    pruebas

    migración

Posteriormente puede eliminarse el provider que ya no corresponda.

---

## Arquitectura de providers

    Claims Analyst Agent
             │
             ▼
       Customer Service
             │
      CUSTOMER_INTEGRATION_PROVIDER
             │
        ┌────┴────┐
        │         │
       REST      MCP
        │         │
        │         ▼
        │     MCP Server
        │         │
        └────┬────┘
             ▼
       Customer API

---

# 12. Capacidades que permanecen fuera de MCP

No mover todavía:

    calculate_deductible

    calculate_reserve

a MCP.

Estas Tools son:

    lógica local determinística

No existe necesidad de exponerlas mediante un protocolo externo en esta PoC.

---

## Claim RAG tampoco pasa a MCP

Mantener:

    Claim RAG

como capacidad interna.

MCP se utiliza aquí para:

    integración con sistemas externos

No para convertir indiscriminadamente todas las funciones en MCP Tools.

---

## Secure RAG tampoco se modifica

El flujo:

    retrieval
        ↓
    content guardrail
        ↓
    safe context

continúa igual.

MCP no sustituye:

    Secure RAG

---

## ConversationSession tampoco cambia

No modificar:

    ConversationMessage

    ConversationSession

    summary

    recent messages

La introducción de MCP debe ser transparente para:

    Conversation Memory

---

# 13. Identidad, observabilidad y logs

En esta PoC el MCP Server se ejecuta localmente.

Todavía no incorporamos:

    Entra ID

    delegated identity

    OBO

Cuando se incorpore identidad, MCP deberá respetar:

    authenticated user context

sin convertir:

    session_id

en una credencial.

---

## session_id no es identidad

Una regla que debe mantenerse en PoC posteriores:

    session_id
        !=
    user identity

Conocer:

    session_id

no debe otorgar acceso a:

    CustomerFieldValue

La autorización se resolverá mediante:

    authenticated identity

en la PoC correspondiente.

---

## Observabilidad futura

Preparar las capas para propagar como metadata:

    correlation_id

    session_id

    claim_number

pero mantenerlos separados de:

    Tool arguments

Ejemplo futuro:

    telemetry:
        session_id=...

    tool arguments:
        national_id=...

---

## Logs

No registrar:

    CustomerProfile completo

    conversation history completo

    tokens

Los logs MCP pueden registrar:

    tool name

    duration

    success/failure

sin volcar:

    PII

---

# 14. Superficie REST y documentación API

La API pública continúa exponiendo:

    POST /sessions

    GET /sessions/{session_id}

    DELETE /sessions/{session_id}

    POST /assistant/query

Además:

    GET /health/customer

    GET /health/customer-mcp

MCP Tools no tienen que convertirse en endpoints REST públicos.
Conservar las rutas de documentación existentes de FastAPI; si no se personalizaron, utilizar `/docs` para Swagger UI y `/openapi.json` para el esquema.

---

## OpenAPI

OpenAPI continúa describiendo:

    Claims API

No describe directamente:

    MCP protocol

Por tanto:

    /api-docs/openapi.json

contendrá:

    REST contracts

mientras MCP mantiene sus propios contratos de Tools.
OpenAPI incluye los modelos de respuesta de los health checks y sus respuestas `503`. Las llamadas `verify_customer` y `get_customer_profile` se describen mediante el contrato MCP, no como endpoints REST.

---

## No exponer MCP al frontend

El frontend futuro no debe llamar:

    Customer MCP Server

directamente.

El flujo será:

    Frontend
        ↓
    Claims API
        ↓
    Claims Analyst Agent
        ↓
    MCP

---

# 15. Ejecución y validación manual

Levantar:

    Ollama

    Qdrant

Después, iniciar Customer Mock API y Claims API en terminales separadas desde la raíz del backend:

```powershell
uv run fastapi dev customer_mock/main.py --port 8081
```

```powershell
uv run fastapi dev app/main.py
```

El MCP Server con transporte `stdio` lo inicia Claims API como proceso hijo al conectar. No iniciar otra instancia manual para esta ejecución normal. `uv run python -m app.mcp.customer_server` queda como comprobación aislada del entry point; la prueba de protocolo se realiza a través del MCP Client o de los tests de integración.

---

## Verificar MCP

Comprobar:

    GET /health/customer-mcp

Esperado:

```json
{
  "status": "ok",
  "server": "customer-mcp",
  "tools": [
    "verify_customer",
    "get_customer_profile"
  ]
}
```

---

## Crear sesión

Ejecutar:

    POST /sessions

Body:

```json
{
  "claim_number": "CLM-000123"
}
```

Guardar:

    session_id

---

## Verificar cliente mediante conversación

En este paso se consulta si el declarante es cliente de la compañía mediante la conversación con el Claims Analyst Agent. Como no se tiene acceso al national-id del declarante, hay que incluirlo en la conversación para que el Claims Analyst Agent pueda realizar la verificación correspondiente. Se utiliza el valor `123456785` ya que está en el sistema de pruebas.

Ejecutar:

    POST /assistant/query

```json
{
  "session_id": "<session-id>",
  "message": "¿El declarante con identificador nacional 123456785 es cliente de la compañía?"
}
```

Flujo esperado:

    ConversationSession
        ↓
    Claims Agent
        ↓
    ClaimData
        ↓
    national_id
        ↓
    verify_customer
        ↓
    MCP
        ↓
    Customer API
        ↓
    CustomerVerification

---

## Segundo turno

Enviar:

```json
{
  "session_id": "<session-id>",
  "message": "¿Cuál es su correo?"
}
```

El Claims Analyst Agent obtiene `national_id` desde `ClaimData` y llama a `get_customer_profile` con `requested_field="email"`; el servidor devuelve el correo solicitado, no todos los datos de contacto.

Flujo:

    Conversation Memory
        ↓
    referencia "su"
        ↓
    Claims Agent
        ↓
    get_customer_profile
        ↓
    MCP
        ↓
    Customer API
        ↓
    CustomerFieldValue
        ↓
    email

---

## Verificar memoria

Ejecutar:

    GET
    /sessions/<session-id>

Debe contener:

    preguntas

    respuestas

pero no una copia estructurada adicional de:

    CustomerProfile

---

## Probar rollback REST

Configurar:

    CUSTOMER_INTEGRATION_PROVIDER=rest

Reiniciar Claims API.

Repetir las consultas.

El comportamiento funcional debería mantenerse.

---

## Probar MCP nuevamente

Configurar:

    CUSTOMER_INTEGRATION_PROVIDER=mcp

Repetir.

El contrato funcional debe permanecer:

    CustomerVerification

    CustomerFieldValue

---

Los comandos para ejecutar tests unitarios y de integración se indican al final del punto 10.

---

## Test end-to-end

El flujo completo será:

    documentos
        ↓
    ClaimData
        ↓
    ConversationSession
        ↓
    User question
        ↓
    Claims Analyst Agent
        ↓
    Customer Service
        ↓
    MCP Client
        ↓
    Customer MCP Server
        ↓
    Customer API
        ↓
    Customer System
        ↓
    CustomerVerification /
    CustomerFieldValue
        ↓
    Claims Analyst Agent
        ↓
    Response
        ↓
    Conversation Memory

---

# 16. Resultado arquitectónico y evolución futura

Antes:

    Claims Agent
        ↓
    Customer Service
        ↓
    REST
        ↓
    Customer API

Ahora:

    Claims Agent
        ↓
    Customer Service
        ↓
    MCP
        ↓
    Customer MCP Server
        ↓
    REST
        ↓
    Customer API

---

## Qué no cambia

No cambian:

    ConversationSession

    ClaimData

    CustomerVerification

    CustomerProfile

    CustomerFieldValue

    Customer API

    Claim RAG

    Corporate RAG

    Secure RAG

    EmbeddingGemma

    Qdrant

    deterministic Tools

---

## Separación arquitectónica

A partir de esta PoC quedan establecidas las siguientes fronteras:

    Agent → System
        =
    MCP

    Conversation continuity
        =
    ConversationSession

    Claim facts
        =
    ClaimData

    Document evidence
        =
    Secure RAG

    Corporate customer truth
        =
    Customer System

    Deterministic calculations
        =
    Python Tools

---

## Principio de mínimo contexto

El Claims Analyst Agent puede conocer:

    Conversation Summary

    Recent Messages

    ClaimData

    Secure RAG evidence

Pero cuando llama una Tool MCP debe reducir ese contexto a:

    parámetros explícitos

Por ejemplo:

    conversación completa
        ↓
    Claims Agent reasoning
        ↓
    national_id
        ↓
    MCP Tool

No:

    conversación completa
        ↓
    MCP Tool

---

## Preparación para A2A

Esta separación será especialmente importante cuando posteriormente incorporemos:

    Policy Agent

mediante:

    A2A

Tendremos:

    Agent → System
        =
    MCP

    Agent → Agent
        =
    A2A

---

## Diferencia MCP vs A2A

MCP se utilizará para:

    Claims Agent
        ↓
    Customer System

Posteriormente A2A se utilizará para:

    Claims Agent
        ↓
    Policy Agent

No utilizar:

    A2A
        para Customer API

ni:

    MCP
        para simular innecesariamente
        un agente especializado

---

## Ownership de ConversationSession

La conversación continúa perteneciendo a:

    Claims Analyst Agent

No a:

    Customer MCP Server

No a:

    Customer API

No a:

    futuras Tools

Esto evita múltiples historiales independientes.

---

# 17. Criterios de éxito y estado final

La PoC se considera validada si:

    Customer MCP Server
        → inicia

    Tool Discovery
        → funciona

    verify_customer
        → está disponible

    get_customer_profile
        → está disponible

    Claims Agent
        → utiliza MCP

    Customer API
        → continúa siendo source of truth

    CustomerVerification
        → mantiene contrato

    CustomerProfile
        → se mantiene como modelo interno de Customer API

    CustomerFieldValue
        → contiene únicamente el campo solicitado

    ConversationSession
        → mantiene continuidad

    ConversationSession
        → no se envía a MCP

    session_id
        → no se usa como credencial

    data minimization
        → se mantiene

    MCP unavailable
        → se distingue

    Customer API unavailable
        → se distingue

    cliente inexistente
        → se distingue

    REST rollback
        → funciona

    tests unitarios
        → pasan

    tests de integración
        → pasan

---

## Resultado esperado

Al finalizar:

                              ANALISTA
                                 │
                                 ▼
                         Conversation
                                 │
                            session_id
                                 │
                                 ▼
                      Conversation Memory
                                 │
                    summary + recent messages
                                 │
                                 ▼
                       Claims Analyst Agent
                                 │
                  ┌──────────────┼──────────────┐
                  │              │              │
                  ▼              ▼              ▼
             Secure RAG     Python Tools    Customer
                                             Service
                                                │
                                                ▼
                                           MCP Client
                                                │
                                                ▼
                                      Customer MCP Server
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          │                                           │
                          ▼                                           ▼
                  verify_customer                           get_customer_profile
                          │                                           │
                          └─────────────────────┬─────────────────────┘
                                                ▼
                                         Customer Client
                                                │
                                                ▼
                                           REST API
                                                │
                                                ▼
                                         Customer System

La capacidad principal validada por esta PoC es:

    AGENT
        ↓
    MCP
        ↓
    SYSTEM

manteniendo simultáneamente:

    ConversationSession
        → conversación

    ClaimData
        → hechos

    Secure RAG
        → evidencia

    Customer System
        → datos corporativos

    Python Tools
        → cálculos

El principio central queda:

    CONVERSATION
        ↓
    AGENT INTERPRETS CONTEXT
        ↓
    EXPLICIT TOOL ARGUMENTS
        ↓
    MCP
        ↓
    SYSTEM OF RECORD

y no:

    CONVERSATION HISTORY
        ↓
    MCP SERVER
        ↓
    SYSTEM

Esto prepara la arquitectura para las siguientes etapas, donde tendremos dos fronteras claramente diferenciadas:

    Agent → System
        = MCP

    Agent → Agent
        = A2A

sin perder la noción única de:

    ConversationSession

propiedad del Claims Analyst Agent.