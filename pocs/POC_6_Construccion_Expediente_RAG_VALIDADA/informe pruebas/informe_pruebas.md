# Informe de pruebas

## 1. Identificación
- **PoC:** PoC 6 — Construcción automática del expediente y RAG documental.
- **Objetivo:** transformar documentos heterogéneos asociados a un siniestro automotriz en un expediente estructurado y consultable.
- **Capacidad a validar:** dos capacidades diferenciadas por la definición original: (1) construcción del expediente mediante extracción de texto/OCR, Structured Extraction y consolidación de `ClaimData`; y (2) recuperación semántica de evidencia documental mediante chunking, embeddings locales y Qdrant, manteniendo aislamiento por `ClaimNumber`.

## 2. Configuración final
- **Tecnologías:** FastAPI, Pydantic/Pydantic AI, Ollama local, Qdrant local, Tesseract OCR, `pypdf`, Pillow, `pytesseract`, `pypdfium2`, `qdrant-client`, `httpx`, pytest, pytest-asyncio y `uv`.
- **Modelos:** `qwen2.5-instruct:7b`, `qwen2.5-extraction:1.5b` y `embeddinggemma`.
- **Dependencias relevantes:** las declaradas en `proyecto/pyproject.toml`. Tesseract quedó con idioma español `spa`; Qdrant se ejecutó localmente y la colección observada fue `claim-documents-embeddinggemma`.
- **Cambios respecto de la definición original:** no se cambió la arquitectura ni se modificó código Python. Se instalaron/ajustaron componentes del entorno local (Tesseract + `spa`, Qdrant y aliases de modelos en Ollama). Para la regresión completa se utilizó `--import-mode=importlib` porque el comando estándar de pytest no pudo recolectar todos los tests por colisiones de nombres. Ese workaround no se persistió en `pyproject.toml`.

## 3. Pruebas realizadas

### Prueba 1 — Tests unitarios
- **Qué se validó:** lógica aislada de chunking, normalización, detección de OCR, conflictos e IDs determinísticos.
- **Entrada:** `uv run pytest tests/unit -v`.
- **Resultado esperado:** todos los tests unitarios pasan.
- **Resultado obtenido:** `12 passed`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 2 — Procesamiento documental sin `TEST_DOCUMENT_ID`
- **Qué se validó:** comportamiento del test de integración cuando no se entrega un documento real.
- **Entrada:** `tests/integration/test_document_processing.py` sin `TEST_DOCUMENT_ID`.
- **Resultado esperado:** el test requiere un documento real para ejecutarse.
- **Resultado obtenido:** `SKIPPED`.
- **Estado:** **FALLÓ** como intento de validación de la capacidad, porque no la ejercitó.
- **Corrección aplicada:** posteriormente se ejecutó con un `document_id` real.

### Prueba 3 — PDF inválido
- **Qué se validó:** procesamiento de un documento asociado a `CLM-000123`.
- **Entrada:** `denuncia.pdf` de aproximadamente 45 bytes.
- **Resultado esperado:** extraer texto si el archivo era un PDF válido.
- **Resultado obtenido:** `pypdf.errors.PdfReadError: startxref not found`.
- **Estado:** **FALLÓ**.
- **Corrección aplicada:** se descartó la muestra inválida y se reemplazó por un PDF sintético válido; no se modificó código.

### Prueba 4 — PDF digital válido
- **Qué se validó:** extracción real de texto desde PDF digital.
- **Entrada:** `proyecto/samples/denuncia_sintetica_poc6.pdf`, cargado como `CLAIM_REPORT`.
- **Resultado esperado:** documento encontrado, páginas > 0 y texto no vacío.
- **Resultado obtenido:** `test_process_document PASSED`, `1 passed`.
- **Estado:** **CORREGIDO Y REPROBADO**.
- **Corrección aplicada:** sustitución de la muestra defectuosa por una válida.

### Prueba 5 — EmbeddingGemma
- **Qué se validó:** generación local de embeddings de documento y consulta con dimensiones compatibles.
- **Entrada:** `tests/integration/test_embeddings.py`.
- **Resultado esperado:** embeddings generados correctamente.
- **Resultado obtenido:** `1 passed`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna durante la prueba.

### Prueba 6 — Integración con Qdrant
- **Qué se validó:** indexación y almacenamiento de chunks.
- **Entrada:** `tests/integration/test_vector_store.py`.
- **Resultado esperado:** colección disponible e indexación correcta.
- **Resultado obtenido:** `1 passed`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 7 — Retrieval aislado por `ClaimNumber`
- **Qué se validó:** que la búsqueda semántica no mezcle documentos de siniestros distintos.
- **Entrada:** `tests/integration/test_retrieval.py`.
- **Resultado esperado:** todos los resultados pertenecen al claim consultado.
- **Resultado obtenido:** `1 passed`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 8 — Procesamiento completo del claim, primer intento
- **Qué se validó:** `process_claim_documents()` sobre todos los documentos de `CLM-000123`.
- **Entrada:** claim que aún contenía el PDF inválido de 45 bytes.
- **Resultado esperado:** construir el expediente completo.
- **Resultado obtenido:** `PdfReadError: startxref not found`.
- **Estado:** **FALLÓ**.
- **Corrección aplicada:** se eliminó por API el documento inválido y se verificó que ya no quedara asociado al claim.

### Prueba 9 — Procesamiento completo del claim, repetición
- **Qué se validó:** el mismo flujo completo después de limpiar el documento defectuoso.
- **Entrada:** `CLM-000123` sin el PDF inválido.
- **Resultado esperado:** `PASSED`.
- **Resultado obtenido:** `test_process_claim_documents PASSED`, `1 passed`.
- **Estado:** **CORREGIDO Y REPROBADO**.
- **Corrección aplicada:** limpieza de datos de prueba; no hubo cambio de código.

### Prueba 10 — OCR sobre PNG
- **Qué se validó:** OCR real sobre imagen.
- **Entrada:** `proyecto/samples/scan_poc6_valido.png`, cargado como `POLICE_REPORT`. Antes se descartó un `scan.png` heredado de solo 99 bytes por no ser una muestra representativa.
- **Resultado esperado:** texto utilizable mediante Tesseract.
- **Resultado obtenido:** el test pasó y se recuperaron fecha, ubicación y antecedentes. La patente esperada `ABCD12` fue leída como `ABODI2`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** se sustituyó la muestra de 99 bytes por una imagen sintética válida; no se modificó OCR ni código.

### Prueba 11 — OCR sobre PDF escaneado
- **Qué se validó:** detección de PDF sin texto digital suficiente y uso de OCR.
- **Entrada:** `proyecto/samples/scan_poc6_valido.pdf`, generado a partir de la imagen sintética y cargado como `OTHER`.
- **Resultado esperado:** texto recuperado mediante OCR.
- **Resultado obtenido:** test `PASSED`; se recuperaron fecha, ubicación y patente `ABCD12`, con errores menores de espaciado.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna de código.

### Prueba 12 — Construcción del expediente por API
- **Qué se validó:** `POST /claims/CLM-000123/process` devuelve `claim_number`, `claim_data`, `evidence` y `conflicts`.
- **Entrada:** expediente con denuncia digital, PNG OCR y PDF escaneado OCR.
- **Resultado esperado:** consolidar datos consistentes y registrar conflictos cuando existan diferencias.
- **Resultado obtenido:** se devolvieron los cuatro bloques. Se consolidaron `loss_dt = 2026-09-05` y `loss_location_desc = Avenida Providencia, Santiago`; se registraron conflictos en `PolicyNumber`, `ClaimsOccurrence.LossDesc` y `VehInfo.vehicle_plate`.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna. Se registró como hallazgo que Structured Extraction confundió `ClaimNumber` con `PolicyNumber` y que hubo diferencias de patente derivadas de OCR/datos de prueba.

### Prueba 13 — Búsqueda RAG por API
- **Qué se validó:** recuperar evidencia pertinente a `¿Dónde ocurrió el accidente?` sin salir de `CLM-000123`.
- **Entrada:** `POST /claims/CLM-000123/context/search` con `limit=5`.
- **Resultado esperado:** chunks relevantes del mismo claim, idealmente con Avenida Providencia/Santiago.
- **Resultado obtenido:** se recuperaron tres chunks de `CLM-000123`; todos contenían evidencia pertinente y cubrían PDF digital, PDF escaneado e imagen OCR.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 14 — Reprocesamiento sin duplicar chunks
- **Qué se validó:** que reprocesar el expediente no duplique puntos en Qdrant.
- **Entrada:** conteo por `CLM-000123`, reprocesamiento y segundo conteo.
- **Resultado esperado:** mismo conteo antes y después.
- **Resultado obtenido:** `3` chunks antes y `3` después.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 15 — DELETE completo
- **Qué se validó:** eliminar archivo físico, metadata y chunks vectoriales.
- **Entrada:** documento PDF escaneado usado en la prueba.
- **Resultado esperado:** HTTP 204, ausencia en metadata, 0 chunks y ausencia física.
- **Resultado obtenido:** HTTP `204 No Content`; dejó de aparecer en el listado; Qdrant pasó de `1` chunk a `0`; el archivo físico ya no fue encontrado.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 16 — Regresión conjunta por carpetas
- **Qué se validó:** ejecución conjunta de unitarios e integración.
- **Entrada:** `uv run pytest tests/unit tests/integration -v`.
- **Resultado esperado:** recolección y ejecución completa.
- **Resultado obtenido:** 3 errores de collection por `import file mismatch` en tests con nombres repetidos.
- **Estado:** **FALLÓ**.
- **Corrección aplicada:** se probó el comando oficial definido por la PoC.

### Prueba 17 — Regresión con el comando original de la PoC
- **Qué se validó:** `uv run pytest -v`.
- **Entrada:** suite completa.
- **Resultado esperado:** todos los tests recolectados.
- **Resultado obtenido:** nuevamente 3 errores de collection por `import file mismatch`.
- **Estado:** **FALLÓ**.
- **Corrección aplicada:** se eliminaron `__pycache__` y `.pyc` y se reintentó.

### Prueba 18 — Regresión después de limpiar cachés
- **Qué se validó:** descartar caché como causa del problema de importación.
- **Entrada:** limpieza de `__pycache__` y `.pyc`, seguida de `uv run pytest -v`.
- **Resultado esperado:** que la colección funcionara si el problema era caché.
- **Resultado obtenido:** los mismos 3 errores de collection.
- **Estado:** **FALLÓ**.
- **Corrección aplicada:** se cambió solo el modo de importación por CLI; no se editó `pyproject.toml`.

### Prueba 19 — Regresión completa con `importlib`
- **Qué se validó:** ejecutar toda la suite evitando la colisión de nombres.
- **Entrada:** `uv run pytest -v --import-mode=importlib`.
- **Resultado esperado:** recolectar y ejecutar todos los tests.
- **Resultado obtenido:** `17 items`; `16 passed, 1 skipped in 9.39s`.
- **Estado:** **CORREGIDO Y REPROBADO**.
- **Corrección aplicada:** `--import-mode=importlib` como workaround de ejecución. No se persistió una modificación en el proyecto.

## 4. Hallazgos y correcciones
### Problemas encontrados
1. PDF de prueba inválido de 45 bytes que provocaba `PdfReadError`.
2. Imagen heredada de 99 bytes no adecuada como muestra OCR.
3. OCR sobre PNG confundió `ABCD12` con `ABODI2`.
4. Structured Extraction interpretó `ClaimNumber` como `PolicyNumber` en parte de la evidencia.
5. La suite estándar de pytest tiene colisiones de importación por nombres repetidos entre `tests/unit` y `tests/integration`.

### Correcciones realizadas
- Se retiró del claim el PDF inválido.
- Se crearon y usaron muestras sintéticas válidas para PDF digital, PNG OCR y PDF escaneado OCR.
- Se instaló Tesseract con soporte `spa`.
- Se dejó Qdrant funcionando localmente.
- Se dejaron disponibles en Ollama los nombres de modelos requeridos por la PoC.
- Para la suite completa se utilizó `--import-mode=importlib`.
- **No se modificó código Python ni `pyproject.toml` durante la sesión.**

### Resultado después de volver a probar
- El procesamiento documental pasó con archivos válidos.
- El procesamiento completo del claim pasó al retirar el archivo corrupto.
- OCR en PNG y PDF escaneado funcionó, con limitaciones de calidad observadas.
- La regresión completa logró ejecutarse con `16 passed, 1 skipped` usando `--import-mode=importlib`.

## 5. Desviaciones respecto de la PoC original
1. La definición original indica `uv run pytest -v` para todos los tests; ese comando no funcionó por `import file mismatch`. La validación conjunta se logró con `uv run pytest -v --import-mode=importlib`. La configuración permanente quedó pendiente.
2. Para disponer del nombre `qwen2.5-extraction:1.5b` localmente se utilizó un modelo Qwen2.5 1.5B Instruct GGUF y un alias de Ollama. No se realizó benchmark comparativo.
3. Las pruebas se realizaron con documentos sintéticos/controlados; no se probaron documentos reales de producción.
4. No se reemplazaron FastAPI, Pydantic AI, Ollama, Qdrant, Tesseract ni EmbeddingGemma.

## 6. Limitaciones
### Limitaciones detectadas
- OCR no fue 100 % preciso y puede confundir caracteres críticos.
- Structured Extraction puede confundir campos semánticamente cercanos; se observó `ClaimNumber` interpretado como `PolicyNumber`.
- La lógica de conflictos detecta discrepancias, pero no determina cuál valor es verdadero.
- El valor consolidado puede quedar `null` cuando no existe un valor consistente.
- El comando estándar de regresión completa de pytest continúa requiriendo un ajuste permanente.

### Elementos fuera de alcance
Según la definición original no se incorporaron Policy Core, Customer API, condicionado, Corporate RAG, Secure RAG, MCP, A2A, Azure AI Search ni Azure OpenAI. `search_claim_documents()` sigue siendo capacidad de aplicación y no Tool del agente. Los chunks recuperados no pasan todavía por Content Guardrail.

### Cosas que todavía no podemos afirmar
- Que OCR sea suficientemente preciso para automatizar identificadores críticos sin validación.
- Que Structured Extraction sea suficientemente preciso para operar sin controles adicionales.
- Que el desempeño observado con documentos sintéticos represente documentos reales y variados.
- Que el sistema resuelva automáticamente qué documento contiene el dato verdadero ante un conflicto.
- Que exista Secure RAG o Content Guardrail sobre el contenido recuperado.
- Que retrieval pueda ser invocado por el agente vía Tool Calling.
- Que `uv run pytest -v` funcione sin un ajuste permanente de configuración.
- Que exista integración con sistemas corporativos fuera del alcance definido.

## 7. Recomendaciones para una implementación real
1. Agregar validaciones determinísticas de formato para identificadores críticos como patente, `ClaimNumber` y `PolicyNumber`.
2. Reforzar schema/prompt y tests de Structured Extraction para diferenciar explícitamente `ClaimNumber` y `PolicyNumber`.
3. Incorporar revisión humana para conflictos o campos críticos cuando existan valores inconsistentes o baja confianza.
4. Crear tests automáticos de OCR con letras/números visualmente similares, distintas resoluciones, inclinación y ruido.
5. Comparar modelos de extracción con un benchmark antes de seleccionar uno para uso real.
6. Registrar fuente documental, texto extraído, valor estructurado, modelo/versión y conflictos para auditoría.
7. Resolver permanentemente la configuración de pytest y volver a validar el comando estándar de la PoC.
8. Incorporar controles de contenido antes de reutilizar retrieval como contexto de un agente, coherente con la limitación de Secure RAG observada.

## 8. Resultado final
Se probó un flujo local que recibe documentos de un siniestro, lee PDF e imágenes, utiliza OCR cuando corresponde, extrae información, construye un expediente, conserva evidencia, detecta discrepancias e indexa el contenido para búsqueda semántica aislada por siniestro.

**Qué funcionó:** procesamiento documental, OCR de PNG y PDF escaneado, Structured Extraction con las limitaciones descritas, consolidación, detección de conflictos, embeddings, Qdrant, retrieval aislado, reprocesamiento sin duplicados y borrado completo.

**Qué quedó validado:** la plataforma puede transformar documentos heterogéneos en información estructurada y consultable y registrar conflictos cuando existen valores distintos, sin mezclar el contenido entre claims en la búsqueda probada.

**Principal limitación:** OCR y Structured Extraction pueden introducir errores en datos críticos; la arquitectura expone evidencia y conflictos, pero no garantiza por sí sola que el dato extraído sea correcto.

**Conclusión:** la PoC demostró la viabilidad técnica y funcional del expediente documental local y de la recuperación semántica por siniestro en un escenario controlado. Para una implementación real se requieren controles de calidad adicionales, validación determinística/humana en campos críticos, pruebas con documentos reales y resolver de forma permanente la configuración de pytest.
