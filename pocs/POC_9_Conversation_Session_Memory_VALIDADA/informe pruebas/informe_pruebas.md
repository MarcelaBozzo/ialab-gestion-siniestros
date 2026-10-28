# Informe de pruebas

## 1. Identificación

- **PoC:** PoC 9 — Conversation Session Memory.
- **Objetivo:** incorporar memoria conversacional persistente dentro de una sesión para mantener continuidad entre interacciones sucesivas del analista.
- **Capacidad a validar:** creación, persistencia, recuperación, aislamiento, compactación y uso del contexto conversacional, manteniendo separada la memoria de ClaimData, Secure RAG y tools.

## 2. Configuración final

- **Tecnologías:** FastAPI, Pydantic AI, Ollama, Pydantic, almacenamiento local JSON y componentes heredados de PoC 8, incluidos Secure RAG, Qdrant y tools determinísticas.
- **Modelos disponibles y usados durante la sesión:** `qwen2.5-instruct:7b`, `qwen2.5-extraction:1.5b` y `embeddinggemma:latest`.
- **Entorno observado durante las pruebas:** Python 3.14.7, `uv` 0.12.18 y Pydantic AI 2.54.0.
- **Dependencias relevantes:** definidas en `pyproject.toml`; no se incorporaron tecnologías nuevas.
- **Cambios respecto de la definición original:**
  - Se mantuvo la arquitectura y el alcance definidos para PoC 9.
  - Se cambió la estrategia de salida estructurada de los guardrails a `PromptedOutput(...)` para compatibilidad con Pydantic AI 2.54.0 y el modelo local.
  - Se reforzó en `conversation_service.py` que la memoria solo puede usarse como contexto y no como evidencia verificada.
  - Se agregó la misma regla al `system_prompt` del Claims Analyst Agent porque el refuerzo solo a nivel del mensaje conversacional no fue suficiente.
  - No se cambió el modelo conversacional ni se agregó una integración automática nueva entre `/assistant/query`, ClaimData y Secure RAG.

## 3. Pruebas realizadas

### 3.1 Instalación de dependencias
- **Qué se validó:** que el proyecto pudiera preparar su entorno con `uv`.
- **Entrada:** `uv sync`.
- **Resultado esperado:** instalación sin errores.
- **Resultado obtenido:** dependencias instaladas correctamente.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.2 Disponibilidad de modelos locales
- **Qué se validó:** presencia de los modelos requeridos en Ollama.
- **Entrada:** `ollama list`.
- **Resultado esperado:** disponibilidad de `qwen2.5-instruct:7b` y modelos heredados necesarios.
- **Resultado obtenido:** disponibles `qwen2.5-instruct:7b`, `qwen2.5-extraction:1.5b` y `embeddinggemma:latest`, entre otros aliases instalados.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.3 Tests unitarios de memoria
- **Qué se validó:** creación y carga de sesión, append de mensajes, aislamiento, mensajes recientes, contexto, compactación y manejo de fallos del agente/resumen.
- **Entrada:** `uv run pytest tests/unit -v`.
- **Resultado esperado:** todos los tests unitarios en `PASSED`.
- **Resultado obtenido:** `9 passed` en la ejecución registrada inicialmente. Tras las correcciones posteriores, la usuaria confirmó una nueva ejecución con los 9 tests aprobados; no quedó pegada en el chat la salida completa de esa última corrida.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no fue necesaria para estos tests.

### 3.4 Integración conversacional con Ollama — primera ejecución
- **Qué se validó:** continuidad conversacional y manejo de sesión inexistente.
- **Entrada:** `uv run pytest tests/integration/test_conversation_service.py -v`.
- **Resultado esperado:** 2 tests aprobados.
- **Resultado obtenido:** `test_unknown_session_fails` pasó, pero `test_conversation_remembers_previous_turn` falló antes de completar el turno.
- **Estado:** **FALLÓ**.
- **Corrección aplicada:** ver sección 4.1.

### 3.5 Integración conversacional después de corregir salida estructurada
- **Qué se validó:** que el agente pudiera completar el turno y recordar “Providencia”.
- **Entrada:** test aislado `test_conversation_remembers_previous_turn` y luego archivo completo de integración.
- **Resultado esperado:** respuesta contextual con “Providencia” y 2 tests de integración aprobados.
- **Resultado obtenido:** test aislado `1 passed`; posteriormente el archivo completo terminó en `2 passed in 28.51s`.
- **Estado:** **CORREGIDO Y REPROBADO**.
- **Corrección aplicada:** uso de `PromptedOutput` en los tres agentes de guardrail estructurado.

### 3.6 Inicio de FastAPI
- **Qué se validó:** que la API levantara correctamente.
- **Entrada:** `uv run uvicorn app.main:app --reload`.
- **Resultado esperado:** `Application startup complete` y servicio en `127.0.0.1:8000`.
- **Resultado obtenido:** servidor iniciado correctamente.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.7 Creación de sesión
- **Qué se validó:** generación de UUID, asociación opcional a claim y sesión vacía inicial.
- **Entrada:** `POST /sessions` con `{"claim_number":"CLM-000123"}`.
- **Resultado esperado:** `session_id`, `claim_number`, timestamps, `summary:null`, `messages:[]`.
- **Resultado obtenido:** sesión creada con UUID y estructura esperada.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.8 Primer turno manual
- **Qué se validó:** que `/assistant/query` aceptara un turno y lo asociara a la sesión.
- **Entrada:** “El accidente que estamos comentando ocurrió en Providencia.”
- **Resultado esperado:** respuesta del agente y persistencia del turno.
- **Resultado obtenido:** el endpoint respondió y persistió el turno. La respuesta fue poco pertinente, porque pidió datos para deducible/reserva, pero el flujo técnico funcionó.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no se cambió ese comportamiento porque no era el objetivo central de PoC 9.

### 3.9 Continuidad conversacional manual
- **Qué se validó:** uso real del turno anterior para resolver una referencia.
- **Entrada:** “¿Dónde dijimos que ocurrió?” usando el mismo `session_id`.
- **Resultado esperado:** respuesta referida a Providencia.
- **Resultado obtenido:** “El accidente que estamos comentando ocurrió en Providencia.”
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió después del arreglo de guardrails.

### 3.10 Persistencia de los cuatro mensajes
- **Qué se validó:** que dos turnos completos quedaran almacenados en orden.
- **Entrada:** `GET /sessions/{session_id}`.
- **Resultado esperado:** 4 mensajes: user, assistant, user, assistant.
- **Resultado obtenido:** se recuperaron exactamente los 4 mensajes; `summary` seguía en `null`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.11 Persistencia después de reiniciar FastAPI
- **Qué se validó:** que una sesión sobreviviera al reinicio del servidor.
- **Entrada:** detener Uvicorn, volver a iniciarlo y ejecutar `GET /sessions/{session_id}`.
- **Resultado esperado:** misma sesión y mismos 4 mensajes.
- **Resultado obtenido:** sesión recuperada intacta después del reinicio.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.12 Aislamiento entre sesiones del mismo claim
- **Qué se validó:** que un mismo `claim_number` pudiera tener otra sesión sin heredar historial.
- **Entrada:** nueva `POST /sessions` con `CLM-000123` y luego “¿Dónde dijimos que ocurrió?”.
- **Resultado esperado:** sesión vacía inicialmente y ausencia de memoria de Providencia.
- **Resultado obtenido:** la nueva sesión nació con `messages:[]`; al consultar la ubicación, el agente pidió información adicional y no mencionó Providencia.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.13 Compactación unitaria con mock
- **Qué se validó:** mensajes antiguos → summary, mensajes recientes conservados y persistencia del resultado.
- **Entrada:** `test_compact_session_summarizes_old_messages` con trigger 4/recent 2 y summarizer simulado.
- **Resultado esperado:** summary esperado y solo 2 mensajes recientes.
- **Resultado obtenido:** `1 passed`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.14 Compactación real con Ollama
- **Qué se validó:** que el modelo local generara un resumen real y que se conservaran solo 2 mensajes recientes.
- **Entrada:** script manual con `CONVERSATION_SUMMARY_TRIGGER=4` y `CONVERSATION_RECENT_MESSAGES=2`.
- **Resultado esperado:** `summary` no nulo y 2 mensajes recientes.
- **Resultado obtenido:** `SUMMARY: user: Estamos revisando un accidente ocurrido en Providencia.` y dos mensajes recientes conservados.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió; se registró calidad de resumen básica como limitación.

### 3.15 Persistencia del resumen real
- **Qué se validó:** que el summary de Ollama quedara almacenado en JSON.
- **Entrada:** `GET /sessions/d8156519-0d93-44d8-a741-b192436ab4a1`.
- **Resultado esperado:** mismo summary y 2 mensajes recientes.
- **Resultado obtenido:** summary persistido y dos mensajes recuperados.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.16 Eliminación de sesión
- **Qué se validó:** ciclo de vida de borrado y desaparición efectiva de la memoria.
- **Entrada:** `DELETE /sessions/{session_id}` y luego `GET` con `-i`.
- **Resultado esperado:** delete sin cuerpo y recuperación posterior en 404.
- **Resultado obtenido:** el GET posterior devolvió `HTTP/1.1 404 Not Found` y `{"detail":"Conversation session not found"}`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.17 Sesión inexistente en `/assistant/query`
- **Qué se validó:** que un UUID inexistente no cree ni continúe una sesión silenciosamente.
- **Entrada:** `POST /assistant/query` con `11111111-1111-1111-1111-111111111111`.
- **Resultado esperado:** 404.
- **Resultado obtenido:** `HTTP/1.1 404 Not Found`, `Conversation session not found`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.18 Swagger UI
- **Qué se validó:** exposición de las rutas de conversación.
- **Entrada:** `http://127.0.0.1:8000/swagger-ui`.
- **Resultado esperado:** `POST /sessions`, `GET /sessions/{session_id}`, `DELETE /sessions/{session_id}`, `POST /assistant/query`.
- **Resultado obtenido:** los cuatro endpoints se observaron en Swagger.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.19 OpenAPI
- **Qué se validó:** exposición de contratos de conversación.
- **Entrada:** `http://127.0.0.1:8000/api-docs/openapi.json`.
- **Resultado esperado:** `ConversationMessage`, `ConversationSession`, `CreateConversationSessionRequest`, `ConversationRequest`, `ConversationResponse`.
- **Resultado obtenido:** los cinco schemas aparecieron en el JSON OpenAPI.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió.

### 3.20 Memoria no debe convertirse en verdad de negocio — primera prueba
- **Qué se validó:** que una afirmación del usuario sobre “5 UF” no fuera confirmada solo por estar en la conversación.
- **Entrada:** primero “El deducible de este siniestro es 5 UF.” y luego “¿Entonces el deducible confirmado es 5 UF?”.
- **Resultado esperado:** recordar que se mencionaron 5 UF, pero no confirmarlos sin ClaimData/evidencia/tool.
- **Resultado obtenido:** el agente respondió “Sí, la información proporcionada indica que el deducible confirmado es 5 UF.”
- **Estado:** **FALLÓ**.
- **Corrección aplicada:** se reforzó la regla en el prompt construido por `conversation_service.py`.

### 3.21 Reprueba después del primer refuerzo
- **Qué se validó:** si la regla añadida al prompt del servicio evitaba elevar memoria a verdad.
- **Entrada:** misma pregunta de confirmación en la sesión existente.
- **Resultado esperado:** no confirmar.
- **Resultado obtenido:** volvió a responder que el deducible estaba confirmado.
- **Estado:** **FALLÓ**.
- **Corrección aplicada:** se concluyó que la regla debía estar también en las instrucciones de mayor prioridad del agente; se añadió al `system_prompt` de `app/agent.py`.

### 3.22 Reprueba con system prompt corregido
- **Qué se validó:** separación entre dato conversado y dato confirmado en una sesión nueva.
- **Entrada:** nueva sesión; “El deducible de este siniestro es 5 UF.”; luego “¿Entonces el deducible confirmado es 5 UF?”.
- **Resultado esperado:** indicar que fue mencionado pero no confirmado.
- **Resultado obtenido:** en una primera corrida, el agente indicó correctamente que “se ha mencionado ... pero este dato no está confirmado”, aunque terminó con texto extraño en otro idioma. Se repitió desde una nueva sesión limpia: la respuesta final fue “Sí, se mencionó que el deducible ... es 5 UF, pero necesito confirmar...”. La distinción funcional quedó corregida, aunque el “Sí” inicial sigue siendo ambiguo.
- **Estado:** **CORREGIDO Y REPROBADO**.
- **Corrección aplicada:** regla de memoria como contexto/no verdad incorporada tanto en `conversation_service.py` como en el `system_prompt` del agente.

### 3.23 Regresión final
- **Qué se validó:** que las correcciones finales no rompieran los tests existentes.
- **Entrada:** suite unitaria y suite de integración de conversación.
- **Resultado esperado:** 9 unitarios y 2 de integración aprobados.
- **Resultado obtenido:** la usuaria confirmó ambas ejecuciones finales como aprobadas; no quedó pegada en el chat la salida detallada de esas dos últimas corridas. Antes del último ajuste del system prompt sí quedó registrada una ejecución completa de integración con `2 passed`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** no correspondió después de la reprueba final.

## 4. Hallazgos y correcciones

### 4.1 Incompatibilidad de salida estructurada en guardrails
- **Problema:** con Pydantic AI 2.54.0, el modelo local devolvió una estructura anidada `{"RequestClassification": {...}}` mientras `GuardrailDecision` esperaba `classification` y `reason` en la raíz. Esto terminó en `ValidationError` y `UnexpectedModelBehavior: Exceeded maximum output retries (1)`.
- **Corrección:** cambiar los `output_type` de `input_guardrail_agent`, `output_guardrail_agent` y `content_guardrail_agent` a `PromptedOutput(...)`.
- **Resultado después de probar nuevamente:** la prueba aislada de continuidad quedó en `1 passed` y luego el archivo completo de integración en `2 passed`.

### 4.2 Memoria elevada incorrectamente a dato confirmado
- **Problema:** el modelo confirmó “5 UF” basándose solo en una afirmación previa de la conversación.
- **Primera corrección:** regla explícita en el prompt de `conversation_service.py` indicando que memoria es contexto y no business truth.
- **Resultado:** insuficiente; al reprobar, el modelo siguió confirmando el dato.
- **Corrección final:** añadir la regla también al `system_prompt` del Claims Analyst Agent.
- **Resultado después de probar nuevamente:** en sesión limpia, el agente distinguió entre “se mencionó” y “confirmado”. Persistió una ambigüedad de redacción por el “Sí” inicial.

### 4.3 Variabilidad del modelo local
- **Problema:** una de las respuestas posteriores a la corrección terminó con texto extraño en chino relacionado con una herramienta.
- **Corrección:** no se cambió código por ese evento aislado; se repitió la prueba desde una sesión nueva.
- **Resultado:** la siguiente ejecución fue limpia. Se conserva como limitación de calidad/estabilidad del modelo local.

### 4.4 Respuesta poco pertinente en el primer turno manual
- **Problema:** ante una frase sobre ubicación, el agente pidió datos para deducible/reserva.
- **Corrección:** no se modificó, porque no impidió validar memoria de sesión y cambiar ese comportamiento habría ampliado el alcance funcional de esta PoC.
- **Resultado:** la continuidad posterior sí recordó correctamente Providencia.

## 5. Desviaciones respecto de la PoC original

- Se requirió una adaptación de compatibilidad de Pydantic AI (`PromptedOutput`) que no estaba descrita en la definición original.
- La regla “memory is context, not business truth” debió reforzarse también en el `system_prompt` del agente para lograr el comportamiento esperado con el modelo local.
- No se incorporó ni simuló una nueva integración automática entre memoria conversacional y Secure RAG/ClaimData; se mantuvo la integración mínima del agente heredado, tal como permitía la definición cuando esos componentes aún no estaban conectados al chat conversacional.
- No se validó autorización por propietario/analista para sesiones ni control de acceso cruzado a `claim_number`. El proyecto heredado no contiene un mecanismo de autenticación/autorización en esos endpoints y esta sesión no implementó uno.
- No se cambió el modelo `qwen2.5-instruct:7b` definido para conversación.

## 6. Limitaciones

### Limitaciones detectadas
- La calidad de respuesta del modelo local es variable: se observó una respuesta poco pertinente, un resumen muy básico y un evento aislado de texto extraño.
- La formulación final de la prueba “5 UF” conserva un “Sí” inicial ambiguo, aunque inmediatamente diferencia el dato mencionado del dato confirmado.
- El proyecto usa almacenamiento JSON local, adecuado para desarrollo local y baja carga, no para concurrencia productiva.
- La sesión no incluye un `uv.lock` generado durante este empaquetado; la versión probada de Pydantic AI fue 2.54.0 y queda documentada, pero `pyproject.toml` conserva el rango original no fijado.

### Elementos fuera de alcance
- Memoria entre sesiones y perfil permanente del usuario.
- Personalización persistente y memoria semántica de largo plazo.
- PostgreSQL, Redis y Supabase.
- MCP, A2A, Angular, LiveKit y Azure.
- Expiración automática de sesiones.
- Alta concurrencia, múltiples instancias y resolución de carreras sobre la misma sesión.

### Cosas que todavía no podemos afirmar
- Que la memoria escale de forma segura a producción o múltiples instancias.
- Que exista autorización efectiva por usuario/analista sobre cada sesión o `claim_number`.
- Que `/assistant/query` consulte automáticamente ClaimData o Secure RAG para verificar cada hecho; esa integración no fue implementada ni probada aquí.
- Que la memoria proporcione verdad del expediente: se validó deliberadamente lo contrario.
- Que el modelo local mantenga siempre la misma calidad lingüística o formato de respuesta.
- Que todos los tests heredados de Secure RAG de PoC 8 hayan sido reejecutados en esta sesión; solo se probaron los indicados para PoC 9 y los flujos manuales registrados.

## 7. Recomendaciones para una implementación real

- Sustituir el almacenamiento JSON por una persistencia con control de concurrencia antes de operar con múltiples instancias o carga productiva.
- Implementar autenticación y autorización explícita por sesión y por `claim_number` antes de exponer estos endpoints a usuarios reales.
- Conectar de forma explícita la verificación de hechos sensibles a ClaimData, Secure RAG o tools, en vez de depender solo de instrucciones al modelo para distinguir memoria de evidencia.
- Mantener tests de regresión específicos para “dato mencionado vs. dato confirmado”, porque fue un fallo real encontrado durante esta PoC.
- Fijar o bloquear las versiones de dependencias para reproducibilidad una vez que el equipo decida el mecanismo de versionado; la compatibilidad observada fue con Pydantic AI 2.54.0.
- Evaluar la calidad del resumen conversacional con más casos antes de usarlo para sesiones largas en un entorno real.

## 8. Resultado final

- **Qué se probó:** memoria persistente por sesión, continuidad contextual, almacenamiento y recuperación de mensajes, aislamiento, reinicio de FastAPI, compactación/resumen, borrado, errores de sesión y contratos Swagger/OpenAPI.
- **Qué funcionó:** el agente recordó contexto previo, las sesiones persistieron y permanecieron aisladas, y la compactación redujo historial antiguo a un resumen persistente.
- **Qué quedó validado:** la capacidad de mantener continuidad dentro de una `ConversationSession` y, después de las correcciones, tratar la memoria como contexto sin elevarla automáticamente a verdad de negocio.
- **Principal limitación:** persistencia local y variabilidad del modelo local; además, la verificación automática contra ClaimData/Secure RAG no está conectada al endpoint conversacional.
- **Conclusión:** la PoC cumple su objetivo principal en entorno local. Queda preparada como base para etapas posteriores, pero no debe interpretarse todavía como una solución productiva ni como un mecanismo autoritativo de verificación del expediente.
