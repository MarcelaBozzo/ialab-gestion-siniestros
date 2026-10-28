# Informe de pruebas

## 1. Identificación

- **PoC:** PoC 7 — Póliza, condicionado y conocimiento corporativo.
- **Objetivo:** complementar los hechos del expediente con una póliza concreta y el condicionado aplicable, entregando información verificable sin automatizar una decisión de cobertura.
- **Capacidad a validar:** integración REST con Policy Core simulado; modelos estructurados de póliza y cobertura; vigencia y deducible determinísticos; Corporate RAG separado del Claim RAG; indexación, búsqueda filtrada y trazabilidad de evidencia corporativa.

## 2. Configuración final

- **Tecnologías:** FastAPI, Pydantic AI, Ollama, Qdrant, HTTPX, Pydantic, PyPDF y componentes heredados de procesamiento documental/OCR.
- **Modelos:** `qwen2.5-instruct:7b`, `qwen2.5-extraction:1.5b` y `embeddinggemma`.
- **Dependencias relevantes:** definidas en `proyecto/pyproject.toml`; Qdrant se ejecutó localmente en Docker Desktop; Ollama se ejecutó localmente.
- **Servicios usados durante la prueba:** Claims API en `localhost:8000`, Policy Core Mock en `localhost:8001`, Qdrant en `localhost:6333`, Ollama en `localhost:11434`.
- **Corpus:** 5 PDF ficticios en `data/corporate/conditions/`.
- **Cambios respecto de la definición original:** no fue necesario cambiar la arquitectura funcional ni agregar tecnologías a la PoC. Para disponer de Qdrant en el computador de prueba se instaló Docker Desktop y se levantó Qdrant como contenedor. Se mantuvo la configuración heredada de la PoC 6 para el modelo de extracción y EmbeddingGemma. Se detectó una inconsistencia de laboratorio entre ejemplos de `GLASS` para `AUTO_STANDARD` y la matriz del corpus, que asigna `GLASS_PLUS` a `AUTO_PREMIUM`; por ello las validaciones de aislamiento por cobertura se realizaron con `COLLISION`, que es consistente entre póliza, condicionado y matriz.

## 3. Pruebas realizadas

### Prueba 1 — consulta de póliza existente

- **Qué se validó:** integración `Claims API -> Policy Service -> Policy Core Mock` y devolución estructurada de una póliza.
- **Entrada:** `GET /policies/POL-123456`.
- **Resultado esperado:** HTTP 200 con `Policy` estructurada.
- **Resultado obtenido:** se devolvió `POL-123456`, estado `ACTIVE`, vigencia `2026-01-01` a `2026-12-31`, producto `AUTO_STANDARD`, vehículo y coberturas `COLLISION` y `GLASS` con sus parámetros.
- **Estado:** PASÓ.
- **Corrección aplicada:** no correspondió.

### Prueba 2 — póliza inexistente

- **Qué se validó:** que el sistema no invente una póliza inexistente.
- **Entrada:** `GET /policies/POL-999999`.
- **Resultado esperado:** HTTP 404 y `Policy not found`.
- **Resultado obtenido:** HTTP 404 con `{"detail":"Policy not found"}`.
- **Estado:** PASÓ.
- **Corrección aplicada:** no correspondió.

### Prueba 3 — vigencia determinística

- **Qué se validó:** evaluación por código de `effective_date <= LossDt <= expiration_date`.
- **Entrada:** póliza `2026-01-01` a `2026-12-31`; `LossDt=2026-09-05`.
- **Resultado esperado:** `True`.
- **Resultado obtenido:** el primer intento falló con `ModuleNotFoundError: No module named 'app'` porque el comando se ejecutó desde la carpeta personal. Después de entrar a la carpeta correcta del proyecto, devolvió `True`.
- **Estado:** CORREGIDO Y REPROBADO.
- **Corrección aplicada:** ejecutar el comando desde `POC_7_Poliza_Condicionado_Conocimiento_Corporativo`.

### Prueba 4 — cálculo determinístico del deducible

- **Qué se validó:** cálculo por Python, no por el LLM.
- **Entrada:** pérdida `2.000.000`, deducible `10%`, mínimo `150.000`.
- **Resultado esperado:** `200000`.
- **Resultado obtenido:** `200000`.
- **Estado:** PASÓ.
- **Corrección aplicada:** no correspondió.

### Prueba 5 — indexación del corpus corporativo

- **Qué se validó:** procesamiento de los PDF corporativos y persistencia en la colección separada `corporate-knowledge`.
- **Entrada:** `POST /knowledge/index` con los 5 PDF incluidos en el proyecto.
- **Resultado esperado:** 5 documentos indexados, 0 omitidos; la cantidad de chunks podía variar.
- **Resultado obtenido:** `indexed_documents=5`, `indexed_chunks=21`, `skipped_documents=0`.
- **Estado:** PASÓ.
- **Corrección aplicada:** no correspondió.

### Prueba 6 — retrieval por producto y cobertura

- **Qué se validó:** búsqueda filtrada por `AUTO_STANDARD` y `COLLISION`.
- **Entrada:** consulta “¿Qué indica el condicionado sobre daños por colisión?”, `product_code=AUTO_STANDARD`, `coverage_cd=COLLISION`.
- **Resultado esperado:** chunks de `AUTO_STANDARD` etiquetados `COLLISION`, sin mezcla con `AUTO_PREMIUM`.
- **Resultado obtenido:** se recuperó `AUTO_STANDARD_2026`, página 2, `coverage_cd=COLLISION`, con contenido de `STD-COV-01` sobre daños por colisión.
- **Estado:** PASÓ.
- **Corrección aplicada:** no correspondió.

### Prueba 7 — aislamiento entre productos

- **Qué se validó:** que el filtro por `product_code=AUTO_STANDARD` impida recuperar contenido de `AUTO_PREMIUM` aunque la consulta mencione “vehículo de reemplazo”, concepto propio del producto Premium.
- **Entrada:** consulta “vehículo de reemplazo por reparación”, `product_code=AUTO_STANDARD`, sin filtro de cobertura.
- **Resultado esperado:** ningún resultado con `product_code=AUTO_PREMIUM` ni `document_id=AUTO_PREMIUM_2026`.
- **Resultado obtenido:** la evidencia compartida devolvió chunks de `AUTO_STANDARD_2026`; no apareció contenido de `AUTO_PREMIUM_2026`.
- **Estado:** PASÓ.
- **Corrección aplicada:** no correspondió.

### Prueba 8 — aislamiento por cobertura

- **Qué se validó:** que `coverage_cd=COLLISION` limite la recuperación a chunks con ese código.
- **Entrada:** misma consulta de colisión con `product_code=AUTO_STANDARD`, `coverage_cd=COLLISION`.
- **Resultado esperado:** resultados `COLLISION`, sin otras coberturas ni `null`.
- **Resultado obtenido:** se recuperó un chunk `AUTO_STANDARD_2026`, `coverage_cd=COLLISION`, página 2, correspondiente a `STD-COV-01`.
- **Estado:** PASÓ.
- **Corrección aplicada:** no correspondió.

### Prueba 9 — trazabilidad de evidencia corporativa

- **Qué se validó:** presencia de metadata suficiente para rastrear la evidencia a su fuente.
- **Entrada:** consulta “daños por colisión”, `AUTO_STANDARD`, `COLLISION`, `limit=1`.
- **Resultado esperado:** `document_id`, `product_code`, `coverage_cd`, `page`, `chunk_index` y `content`.
- **Resultado obtenido:** `AUTO_STANDARD_2026`, `AUTO_STANDARD`, `COLLISION`, página 2, `chunk_index=1` y texto fuente.
- **Estado:** PASÓ.
- **Corrección aplicada:** no correspondió.

### Prueba 10 — contrato OpenAPI

- **Qué se validó:** publicación de endpoints y schemas nuevos.
- **Entrada:** `GET /api-docs/openapi.json`.
- **Resultado esperado:** `GET /policies/{policy_number}`, `POST /knowledge/index`, `POST /knowledge/search`, y schemas `Policy`, `Coverage`, `CorporateKnowledgeChunk`, `CorporateKnowledgeSearchRequest`.
- **Resultado obtenido:** todos los endpoints y schemas esperados aparecieron en OpenAPI.
- **Estado:** PASÓ.
- **Corrección aplicada:** la primera evidencia pegada estaba truncada antes del endpoint de pólizas; se revisó posteriormente la salida completa y se confirmó su presencia. No hubo cambio de código.

### Prueba 11 — Swagger UI

- **Qué se validó:** disponibilidad de la documentación navegable.
- **Entrada:** `HEAD /swagger-ui`.
- **Resultado esperado:** HTTP 200.
- **Resultado obtenido:** HTTP 200 OK, `content-type: text/html`.
- **Estado:** PASÓ.
- **Corrección aplicada:** no correspondió.

### Prueba 12 — `PolicyNumber` ausente

- **Qué se validó:** que un `ClaimData` válido pueda tener `policy_number=None` y que la ausencia se reconozca sin inventar una póliza.
- **Entrada:** primer intento con `ClaimData(policy_number=None)`; segundo intento con `claim_number`, `loss_desc` y `policy_number=None`.
- **Resultado esperado:** `PolicyNumber missing` para un `ClaimData` válido sin póliza.
- **Resultado obtenido:** el primer intento falló por el validador de `ClaimData` con “No claim information could be extracted”, ya que no había información de siniestro. Con datos mínimos válidos de siniestro, el resultado fue `PolicyNumber missing`.
- **Estado:** CORREGIDO Y REPROBADO.
- **Corrección aplicada:** corregir el dato de prueba para representar un siniestro válido sin `PolicyNumber`; no se modificó el código del proyecto.

### Prueba 13 — ausencia de decisión automática de cobertura

- **Qué se validó:** que el contrato expuesto no incorpore `coverage_proposal`, funcionalidad fuera de alcance.
- **Entrada:** búsqueda de `coverage_proposal` en OpenAPI.
- **Resultado esperado:** ninguna coincidencia.
- **Resultado obtenido:** no hubo coincidencias.
- **Estado:** PASÓ.
- **Corrección aplicada:** no correspondió.

## 4. Hallazgos y correcciones

- **Qdrant no estaba disponible al inicio.** `curl http://localhost:6333/collections` devolvió error de conexión. Se comprobó que Docker no estaba instalado. Se instaló Docker Desktop, se inició el motor y se levantó Qdrant con `docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant`. Después, `/collections` respondió correctamente con una lista vacía, como correspondía antes de indexar.
- **Docker Desktop instalado pero no iniciado.** `docker info` mostró que el cliente existía pero el daemon no estaba corriendo. Se abrió Docker Desktop, se verificaron sus procesos y luego `docker info` mostró el servidor activo.
- **Ejecución desde carpeta incorrecta.** La prueba de vigencia falló por no encontrar `app`. Se corrigió el directorio de trabajo y se reprobaron las mismas condiciones, obteniendo `True`.
- **Dato de prueba inválido para `ClaimData`.** La primera prueba de `PolicyNumber missing` creó un objeto sin información de siniestro y Pydantic lo rechazó. Se corrigió el dato de prueba, no el código, y la prueba pasó.
- **Inconsistencia de laboratorio en cobertura de cristales.** La póliza simulada de `AUTO_STANDARD` incluye `GLASS`, mientras que la matriz corporativa del corpus ubica `GLASS_PLUS` en `AUTO_PREMIUM`. Para no validar una combinación ambigua, las pruebas de aislamiento por cobertura se realizaron con `COLLISION`.

## 5. Desviaciones respecto de la PoC original

- No se incorporaron funcionalidades nuevas ni se cambió la arquitectura definida.
- Qdrant tuvo que levantarse mediante Docker Desktop porque no estaba disponible localmente y Homebrew no ofrecía una fórmula de Qdrant en el computador usado.
- La cantidad observada de chunks fue `21`, no el valor ilustrativo `84` del documento. Esto no es una desviación funcional: la propia definición indica que el número depende de la extracción y de `CHUNK_SIZE`/`CHUNK_OVERLAP`.
- No se validó `GLASS` como caso principal de filtro por cobertura debido a la inconsistencia entre ejemplos de la definición/póliza y la matriz del corpus. Se usó `COLLISION`.
- No se modificó código durante la sesión de pruebas. Las correcciones fueron de entorno, directorio de ejecución y preparación correcta de un dato de prueba.

## 6. Limitaciones

### Limitaciones detectadas

- Una búsqueda vectorial filtrada puede devolver el contenido semánticamente más cercano disponible aunque la pregunta no tenga una respuesta exacta dentro del producto filtrado. En la prueba de aislamiento por producto, la consulta sobre “vehículo de reemplazo” devolvió contenido de `AUTO_STANDARD`; el aislamiento funcionó, pero la relevancia semántica no implica existencia de esa prestación en el producto.
- Existe una inconsistencia de laboratorio entre `GLASS` de `AUTO_STANDARD` y `GLASS_PLUS` de `AUTO_PREMIUM` en las fuentes de prueba.
- `section` quedó `null` en la evidencia recuperada porque esta PoC solo debe poblarla cuando exista metadata fiable.

### Elementos fuera de alcance

- Customer API real.
- Policy Core corporativo real.
- Autenticación, Entra ID y OBO.
- MCP y A2A.
- Secure RAG completo e inspección avanzada de indirect prompt injection.
- Determinación autónoma de cobertura.
- Aprobación o rechazo del siniestro.
- Envío de comunicaciones.

### Cosas que todavía no podemos afirmar

- Que la solución funcione contra sistemas corporativos reales.
- Que una cobertura presente en la póliza implique que un siniestro particular esté cubierto.
- Que el retrieval siempre entregue la cláusula más útil ante consultas ambiguas o sin respuesta exacta.
- Que los códigos de cobertura usados sean códigos ACORD corporativos validados; son valores de laboratorio.
- Que existan controles completos de seguridad para documentos corporativos no confiables; Secure RAG queda pendiente.

## 7. Recomendaciones para una implementación real

- Sustituir el Policy Core Mock por la integración corporativa manteniendo la misma frontera de servicio, porque la separación HTTP fue validada.
- Validar un catálogo corporativo único de `CoverageCd` antes de producción para eliminar discrepancias como `GLASS`/`GLASS_PLUS`.
- Añadir una estrategia explícita de “sin evidencia suficiente” o umbral de relevancia para evitar interpretar como respuesta un chunk que solo sea el más cercano dentro de un filtro.
- Mantener vigencia y deducible como reglas determinísticas fuera del LLM.
- Mantener la separación entre Claim RAG y Corporate RAG y conservar metadata de provenance.
- Implementar Secure RAG antes de confiar en documentos corporativos como contexto del agente.

## 8. Resultado final

- **Qué se probó:** consulta de pólizas, tratamiento de pólizas inexistentes, vigencia y deducible por reglas, indexación de 5 documentos corporativos, retrieval por producto/cobertura, trazabilidad y documentación de API.
- **Qué funcionó:** los servicios locales se integraron, los 5 PDF se indexaron en `corporate-knowledge`, los filtros aislaron producto y cobertura, y la evidencia conservó documento, página y contenido fuente.
- **Qué quedó validado:** la plataforma puede aportar póliza y condicionado como fuentes verificables y separadas sin convertir esa evidencia en una decisión automática de cobertura.
- **Principal limitación:** el entorno y los datos son de laboratorio; además, el retrieval puede devolver el mejor resultado disponible aunque no exista una respuesta exacta dentro del filtro.
- **Conclusión:** la PoC cumplió su objetivo de demostración para integración, retrieval y trazabilidad. La decisión de cobertura, las integraciones corporativas reales y los controles avanzados de seguridad quedan para etapas posteriores.
