# Informe de pruebas

## 1. Identificación

- **PoC:** PoC 2 — Modelo estructurado del siniestro automotriz.
- **Objetivo:** evolucionar la PoC 1 para transformar una descripción de siniestro en lenguaje natural en un modelo estructurado, tipado y validado.
- **Capacidad a validar:** convertir información no estructurada de un siniestro automotriz en `ClaimData` mediante Structured Output, JSON Schema, parsing y validación Pydantic, manteniendo el chat de la PoC 1.

## 2. Configuración final

- **Tecnologías:** FastAPI, Pydantic AI para chat, Pydantic para tipado y validación, Ollama local, API OpenAI-compatible de Ollama para chat, API nativa `/api/chat` para extracción, `httpx.AsyncClient` y JSON Schema explícito.
- **Modelo de chat:** `phi4-mini`.
- **Modelo de extracción final:** `qwen2.5:7b-instruct`.
- **Dependencias relevantes:** `fastapi[standard]`, `httpx`, `pydantic-ai-slim[openai]`.
- **Cambio respecto de la definición original:** la PoC proponía `qwen2.5-extraction:1.5b`. Ese modelo falló la prueba de datos ausentes y el refuerzo del prompt no corrigió el comportamiento. La misma prueba pasó con `qwen2.5:7b-instruct`, que quedó como configuración final validada.
- **Correcciones incorporadas:** ajuste del validator de `ClaimData` para detectar extracciones realmente vacías y refuerzo del prompt del chat para mantener su rol ante preguntas de cobertura.

## 3. Pruebas realizadas

| # | Qué se validó | Entrada | Resultado esperado | Resultado obtenido | Estado | Corrección aplicada |
|---|---|---|---|---|---|---|
| 1 | Disponibilidad del modelo original de extracción | `ollama list` | Ver `qwen2.5-extraction:1.5b` | Modelo instalado | **PASÓ** | No aplica |
| 2 | Ejecución básica del modelo 1.5B | “Responde únicamente con OK” | `OK` | `OK` | **PASÓ** | No aplica |
| 3 | Structured Output directo con 1.5B | Siniestro completo con fecha, hora, lugar, vehículo y póliza | JSON puro con datos explícitos | Extracción correcta y JSON sin Markdown | **PASÓ** | No aplica |
| 4 | Datos ausentes con 1.5B | “El Toyota Corolla patente ABCD12 sufrió daños.” | Póliza, fecha, hora y ubicación en `null` | Inventó póliza, fecha, hora y ubicación; alteró la patente | **FALLÓ** | Se reforzó el prompt y se repitió |
| 5 | Reprueba del 1.5B con prompt reforzado | Mismo caso incompleto | Datos ausentes en `null` y patente exacta | Persistieron invenciones y alteración de patente | **FALLÓ** | Se probó 7B como diagnóstico |
| 6 | Mismo caso con 7B | Mismo texto incompleto | `null` en campos ausentes y datos explícitos exactos | Cumplió el resultado esperado | **PASÓ** | 7B quedó como modelo final de extracción |
| 7 | Instalación de dependencias | `uv sync` | Instalar sin error | Dependencias instaladas correctamente | **PASÓ** | No aplica |
| 8 | Arranque de FastAPI | `uv run fastapi dev app/main.py` | Servidor activo | Aplicación iniciada en `127.0.0.1:8000` | **PASÓ** | No aplica |
| 9 | Health de extracción | `GET /health/extraction` | Estado `ok` con extracción real de fecha | `{"status":"ok","model":"qwen2.5:7b-instruct"}` | **PASÓ** | No aplica |
| 10 | Extracción completa integrada | `POST /claims/extract` con siniestro completo | `ClaimData` correcto | Póliza, fecha, hora, ubicación y vehículo correctos | **PASÓ** | No aplica |
| 11 | Datos faltantes integrados | “El Toyota Corolla patente ABCD12 sufrió daños.” | Campos ausentes en `null` | Resultado exacto esperado | **PASÓ** | No aplica |
| 12 | Alcance reducido para conductor | Texto con Juan Pérez y licencia | `claims_driver_info = null` | Quedó `null`; patente extraída | **PASÓ** | No aplica |
| 13 | Alcance reducido para terceros | Choque con María López y patente WXYZ34 | `claims_party_info = []` | Quedó `[]`; choque conservado en descripción | **PASÓ** | No aplica |
| 14 | No inferir códigos ACORD | Choque en Avenida Providencia | Códigos ACORD en `null` | `claim_type_cd`, `claim_status_cd` y `loss_cause_cd` quedaron `null` | **PASÓ** | No aplica |
| 15 | No decidir cobertura | Parabrisas roto + solicitud de cobertura | Extraer hechos sin decidir cobertura | Extrajo póliza y daño; no decidió cobertura | **PASÓ** | No aplica |
| 16 | No calcular deducible/reserva y rechazar extracción vacía | “El presupuesto es de 2.000.000. Calcula deducible y reserva.” | No calcular y fallar si no hay hechos del dominio | Inicialmente devolvió un `ClaimData` vacío | **FALLÓ** | Se corrigió el validator |
| 17 | Reprueba de extracción vacía | Mismo texto de deducible/reserva | Fallo explícito | `HTTP 500` + `Claim extraction failed` | **CORREGIDO Y REPROBADO** | Validator final en `app/schemas.py` |
| 18 | Swagger UI | `/swagger-ui` | Ver los 5 endpoints de la PoC | Endpoints visibles | **PASÓ** | No aplica |
| 19 | OpenAPI | `/api-docs/openapi.json` | Ver los 8 schemas definidos | Los 8 schemas aparecieron | **PASÓ** | No aplica |
| 20 | Health del chat | `GET /health/llm` | `200 OK` | Inicialmente `503` por falta de `phi4-mini` | **FALLÓ** | Se instaló `phi4-mini` |
| 21 | Reprueba health del chat | `GET /health/llm` | `200 OK` | `200 OK` + `model_response: OK` | **CORREGIDO Y REPROBADO** | Requisito de entorno corregido |
| 22 | Comportamiento del chat ante cobertura | Pregunta para confirmar cobertura | Español, sin decidir cobertura y dentro del rol | No decidió, pero respondió de forma genérica y agregó contenido ajeno | **FALLÓ** | Se reforzó el system prompt |
| 23 | Reprueba del chat | Misma pregunta de cobertura | No determinar cobertura y volver al rol de apoyo | Cumplió el comportamiento esperado | **CORREGIDO Y REPROBADO** | Prompt final en `app/agent.py` |
| 24 | Normalización de `"null"` | Estructura con `"null"`, `"NULL"` y valor real | Convertir strings nulos a `None` | Conversión correcta sin alterar el dato real | **PASÓ** | No aplica |
| 25 | Regresión final | Siniestro completo de la prueba principal | Mantener la extracción correcta tras los ajustes | Todos los campos principales siguieron correctos | **PASÓ** | No aplica |

## 4. Hallazgos y correcciones

### Modelo de extracción 1.5B

- **Problema:** produjo JSON correcto en el caso completo, pero inventó o alteró datos cuando faltaba información.
- **Corrección intentada:** prompt más explícito para prohibir inferencias y conservar identificadores.
- **Reprueba:** el problema persistió.
- **Resultado final:** el 1.5B no se considera corregido. La PoC final se validó con `qwen2.5:7b-instruct`.

### Extracción vacía aceptada

- **Problema:** un `veh_info` existente pero con todos sus campos en `null` hacía que `ClaimData` considerara válida una extracción sin hechos útiles.
- **Corrección:** se agregó una comprobación `has_vehicle` que exige al menos un dato real del vehículo.
- **Reprueba:** la solicitud sin hechos del dominio pasó a fallar explícitamente.
- **Resultado final:** corregido e incorporado en `app/schemas.py`.

### Chat demasiado genérico ante cobertura

- **Problema:** el chat no decidió cobertura, pero añadió contenido genérico no solicitado y se alejó del rol de apoyo al analista.
- **Corrección:** se reforzó el `system_prompt` para no agregar datos no disponibles, no decidir cobertura y continuar organizando los hechos.
- **Reprueba:** la misma pregunta quedó respondida dentro del rol esperado.
- **Resultado final:** corregido e incorporado en `app/agent.py`.

### Modelo de chat no instalado

- **Problema:** `/health/llm` devolvió `503` porque `phi4-mini` no estaba instalado localmente.
- **Corrección:** instalación de `phi4-mini` en Ollama.
- **Reprueba:** `/health/llm` devolvió `200 OK`.
- **Resultado final:** corregido como requisito de entorno, sin cambios de código.

## 5. Desviaciones respecto de la PoC original

- El modelo `qwen2.5-extraction:1.5b` fue reemplazado en la configuración final por `qwen2.5:7b-instruct` porque el primero no superó la prueba de información ausente.
- Se corrigió el validator de `ClaimData` para detectar correctamente un `veh_info` vacío.
- Se reforzó el prompt del chat tras observar una respuesta fuera del rol esperado.
- La arquitectura base no cambió: FastAPI + Pydantic AI para chat y API nativa de Ollama + JSON Schema + Pydantic para extracción.

## 6. Limitaciones

### Limitaciones detectadas

- El modelo 1.5B no mostró fiabilidad suficiente en datos ausentes; reforzar el prompt no corrigió la alucinación observada.
- Que el 7B haya pasado los casos ejecutados no demuestra que nunca pueda inventar o alterar información en otros escenarios.
- No existe una señal de confianza por campo en esta PoC.

### Fuera de alcance

- Tools.
- cálculos de deducible o reserva.
- Guardrails.
- documentos y OCR.
- RAG.
- Customer API y Policy Core.
- MCP y A2A.
- persistencia.
- decisión de cobertura.
- extracción estructurada de conductor y terceros en el JSON Schema mínimo.
- asignación de códigos ACORD sin catálogos y reglas controladas.

### Lo que todavía no podemos afirmar

- Que el extractor sea infalible ante cualquier redacción.
- Precisión, recall o tasa de alucinación sobre un conjunto representativo de casos.
- Comportamiento bajo carga, concurrencia o condiciones de producción.
- Integración con pólizas, coberturas, documentos o sistemas core reales.

## 7. Recomendaciones para una implementación real

- Construir un benchmark versionado de casos completos, incompletos y ambiguos antes de seleccionar definitivamente el modelo de extracción.
- Convertir los casos que fallaron en tests automáticos de regresión.
- Añadir validaciones determinísticas para campos críticos como póliza, patente, fecha y hora cuando corresponda.
- Versionar modelo y prompt para poder reproducir resultados.
- Incorporar observabilidad de parsing, validación y calidad por campo.
- Derivar a revisión humana los casos ambiguos o que no superen los controles, en lugar de completarlos automáticamente.

## 8. Resultado final

- **Qué se probó:** transformación de descripciones libres de siniestros en datos estructurados y validados, junto con el chat heredado de la PoC 1.
- **Qué funcionó:** con `qwen2.5:7b-instruct`, la extracción principal funcionó, los datos ausentes quedaron en `null`, los campos fuera de alcance no se inventaron y la extracción vacía fue rechazada después de la corrección.
- **Qué quedó validado:** el flujo FastAPI → Ollama → JSON Schema → parsing → normalización → Pydantic funcionó de punta a punta en los escenarios ejecutados; el chat con `phi4-mini` quedó operativo y no decidió cobertura.
- **Principal limitación:** el modelo 1.5B definido originalmente no alcanzó la fiabilidad requerida en la prueba de información ausente.
- **Conclusión:** la PoC valida, para los casos probados, la viabilidad de transformar información no estructurada de un siniestro automotriz en un modelo canónico, tipado y validado, manteniendo fuera de alcance las decisiones de cobertura, cálculos e integraciones avanzadas.
