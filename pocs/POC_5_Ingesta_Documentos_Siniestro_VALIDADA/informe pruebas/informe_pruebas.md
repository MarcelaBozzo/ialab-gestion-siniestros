# Informe de pruebas

## 1. Identificación
- **PoC:** 5 — Ingesta de documentos heterogéneos del siniestro.
- **Objetivo:** incorporar la capacidad de recibir, validar, clasificar de forma básica y almacenar los documentos que componen un expediente de siniestro automotriz, antes de interpretar su contenido con IA.
- **Capacidad a validar:** construir una base documental por `ClaimNumber`, con metadata, almacenamiento local, consulta, eliminación y separación entre expedientes.

## 2. Configuración final
- **Tecnologías:** Python 3.11+, FastAPI, Uvicorn, Pydantic, `python-multipart`, almacenamiento local en `data/claims/`, Swagger UI y OpenAPI.
- **Modelos:** no se utilizó ningún modelo de IA en la implementación standalone validada.
- **Dependencias relevantes:** `fastapi`, `uvicorn[standard]`, `python-multipart`, `pydantic`; para pruebas automáticas, `pytest` y `httpx` definidos como dependencias de desarrollo en `pyproject.toml`.
- **Configuración final:** `CLAIMS_STORAGE_PATH=./data/claims`, `MAX_DOCUMENT_SIZE_MB=10`, tipos MIME permitidos `application/pdf`, `image/jpeg`, `image/png`, patrón de `ClaimNumber` `[A-Za-z0-9_-]{1,64}`.
- **Cambios respecto de la definición original:** la PoC original estaba planteada como extensión del repositorio acumulado de PoC 1 a 4, donde se mantenían Pydantic AI, guardrails, Tool Calling, Ollama y `phi4-mini`. Ese repositorio acumulado no estuvo disponible en esta conversación, por lo que se validó una implementación autocontenida de la capacidad documental. Tampoco se generó `uv.lock`; para la ejecución local se usó `venv` + `pip`.

## 3. Pruebas realizadas

### Prueba 1 — Health, Swagger y OpenAPI
- **Qué se validó:** que la API levantara correctamente y publicara el contrato documental.
- **Entrada:** `GET /health`, `GET /swagger-ui`, `GET /api-docs/openapi.json`.
- **Resultado esperado:** HTTP 200 y presencia de los schemas `ClaimDocument`, `DocumentType` y rutas documentales.
- **Resultado obtenido:** correcto.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 2 — Carga, listado, consulta y eliminación
- **Qué se validó:** ciclo completo de un documento dentro de un expediente.
- **Entrada:** `CLM-000123`, `denuncia.pdf`, MIME `application/pdf`, tipo `CLAIM_REPORT`, contenido sintético.
- **Resultado esperado:** carga correcta, metadata, aparición en listado, consulta por `document_id`, eliminación y listado final vacío.
- **Resultado obtenido:** el ciclo completo pasó en la suite automática.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 3 — Aislamiento entre expedientes
- **Qué se validó:** que documentos de distintos siniestros no se mezclaran.
- **Entrada:** `CLM-000123` con `foto.jpg` / `DAMAGE_PHOTO` y `CLM-000456` con `parte.pdf` / `POLICE_REPORT`.
- **Resultado esperado:** cada consulta devuelve solo documentos de su propio `ClaimNumber`.
- **Resultado obtenido:** aislamiento correcto.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 4 — Tipo MIME no permitido
- **Qué se validó:** rechazo de formatos fuera del alcance.
- **Entrada:** `archivo.zip`, MIME `application/zip`, tipo `OTHER`.
- **Resultado esperado:** HTTP 400 con `Unsupported document type`.
- **Resultado obtenido:** rechazo correcto.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 5 — ClaimNumber inválido
- **Qué se validó:** rechazo de un identificador no permitido antes de utilizarlo como ruta de almacenamiento.
- **Entrada:** valor equivalente a `CLM/bad`, enviado en la prueba como `CLM%2Fbad`.
- **Resultado esperado según la definición original:** HTTP 400.
- **Resultado obtenido:** la petición fue rechazada con HTTP 404 por el enrutamiento de la URL. La suite automática acepta 400 o 404, por lo que pasa, pero el contrato exacto de HTTP 400 no quedó cumplido con este caso.
- **Estado:** **FALLÓ** respecto del código HTTP exacto definido originalmente; **sí se comprobó el rechazo**.
- **Corrección aplicada:** no se modificó el código durante esta sesión.

### Prueba 6 — Tamaño máximo
- **Qué se validó:** rechazo de un archivo por encima del límite.
- **Entrada:** en el test se ajustó temporalmente el límite a 1 MB y se envió 1 MB + 1 byte.
- **Resultado esperado:** HTTP 400 con `Document exceeds maximum allowed size`.
- **Resultado obtenido:** rechazo correcto.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna. La configuración final sigue en 10 MB.

### Prueba 7 — Nombre físico basado en document_id
- **Qué se validó:** que el archivo no se guarde físicamente con el nombre original entregado por el usuario.
- **Entrada:** `parte_policial.pdf`, tipo `POLICE_REPORT`.
- **Resultado esperado:** almacenamiento como `<document_id>.pdf` y `<document_id>.metadata.json`.
- **Resultado obtenido:** correcto; el nombre original no se utilizó como nombre físico.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna.

### Prueba 8 — Ejecución real con Uvicorn
- **Qué se validó:** que la PoC funcionara como servidor local y no solo dentro de pruebas unitarias.
- **Entrada:** servidor Uvicorn, acceso a `/health`, `/swagger-ui`, `/api-docs/openapi.json`, carga de un PDF controlado y listado posterior.
- **Resultado esperado:** servidor accesible y documento recuperable.
- **Resultado obtenido:** correcto.
- **Estado:** **PASÓ**.
- **Corrección aplicada:** ninguna en código.

### Prueba 9 — Prueba manual en Swagger realizada por la usuaria
- **Qué se validó:** que una persona no técnica pudiera cargar y luego consultar un documento desde Swagger UI.
- **Entrada:** `claim_number=CLM-000123`, `document_type=OTHER`, archivo local `apelacion.pdf`.
- **Resultado esperado:** POST exitoso y posterior GET con el documento asociado al expediente.
- **Resultado obtenido:** primero Swagger mostró que `claim_number` era requerido; se volvió a completar el campo. Luego Terminal mostró `POST /claims/CLM-000123/documents ... 200 OK` y la usuaria confirmó que el GET posterior también quedó OK.
- **Estado:** **CORREGIDO Y REPROBADO**.
- **Corrección aplicada:** se reingresó correctamente `claim_number`; no hubo cambio de código.

### Control final de la suite
Antes de generar este respaldo se volvió a ejecutar la suite automática sobre la versión incluida en `proyecto/`: **7 tests pasaron**. Este resultado confirma la suite tal como está implementada, con la salvedad ya indicada de que el test de `ClaimNumber` inválido acepta tanto HTTP 400 como 404.

## 4. Hallazgos y correcciones
- **Problemas encontrados:** el entorno usado para construir la PoC no pudo generar `uv.lock` por falta de acceso al índice de paquetes; Swagger mostró inicialmente el campo `claim_number` como requerido en la prueba manual; cerrar Terminal detuvo Uvicorn y, por lo tanto, `localhost`; no se contó con el repositorio acumulado de PoC 1 a 4.
- **Correcciones realizadas:** para ejecutar localmente se utilizó `venv` + `pip`; se reingresó `claim_number` en Swagger; al cerrar Terminal se volvió a activar el entorno y levantar Uvicorn.
- **Resultado después de volver a probar:** la carga manual devolvió HTTP 200, el listado posterior fue confirmado como correcto y la suite final volvió a pasar con 7 tests.
- **Correcciones de código:** no fue necesario aplicar una corrección de lógica de negocio durante la prueba manual. El comportamiento 404 del caso de `ClaimNumber` con slash codificado quedó documentado y no fue corregido en esta sesión.

## 5. Desviaciones respecto de la PoC original
- No se validó la integración acumulada con agente, Pydantic AI, Structured Output, Tool Calling, guardrails, Ollama ni `phi4-mini`, porque el repositorio de las PoC anteriores no estuvo disponible.
- No se generó `uv.lock`; la versión respaldada utiliza `pyproject.toml` y `requirements.txt`.
- El caso probado de `ClaimNumber` inválido devuelve HTTP 404 y no el HTTP 400 especificado originalmente.
- El límite de tamaño se validó automáticamente reduciendo temporalmente el límite a 1 MB; no se hizo una carga manual real de más de 10 MB.
- No se probaron manualmente uno por uno todos los tipos documentales definidos. La suite cubrió `CLAIM_REPORT`, `DAMAGE_PHOTO`, `POLICE_REPORT` y `OTHER`; no se ejecutó una prueba específica de `DRIVER_LICENSE` ni `REPAIR_ESTIMATE`.

## 6. Limitaciones

### Limitaciones detectadas
- La PoC local depende de que Uvicorn siga ejecutándose; cerrar Terminal detiene el servicio.
- No existe un lockfile de dependencias generado.
- El contrato de error de `ClaimNumber` inválido no está fijado estrictamente en la prueba actual.

### Elementos fuera de alcance
- OCR.
- Extracción de texto o hechos desde documentos.
- Clasificación automática del tipo documental.
- Embeddings y RAG.
- Análisis multimodal.
- Uso de LLM para almacenar archivos.
- Autenticación y autorización documental.
- Customer API, Policy Core, MCP y A2A.
- Almacenamiento productivo.
- Antivirus, sandboxing y validación del contenido real por magic bytes.

### Cosas que todavía no podemos afirmar
- Que el sistema interprete correctamente el contenido de los documentos.
- Que el MIME declarado corresponda realmente al contenido físico del archivo.
- Que la solución sea segura, escalable o apta para producción.
- Que la integración PoC 1 a PoC 5 funcione de extremo a extremo.
- Que todos los tipos documentales hayan sido probados manualmente.
- Que un `ClaimNumber` inválido siempre devuelva HTTP 400.

## 7. Recomendaciones para una implementación real
- Integrar este módulo en el repositorio acumulado y ejecutar regresión completa de PoC 1 a 5.
- Ajustar y probar de forma estricta el contrato de error para `ClaimNumber` inválido.
- Incorporar validación del contenido real del archivo, además del MIME declarado.
- Agregar controles de seguridad para documentos no confiables, como antivirus o sandboxing.
- Incorporar autenticación y autorización para el acceso a expedientes.
- Sustituir el almacenamiento local por una alternativa productiva con respaldo y auditoría.
- Generar un lockfile en un entorno con acceso al índice de paquetes.
- Mantener los tests de carga, aislamiento, errores y eliminación al incorporar capacidades posteriores.

## 8. Resultado final
Se validó que la PoC puede recibir documentos permitidos, asociarlos a un siniestro, generar metadata e identificadores, almacenarlos, listarlos, consultarlos y eliminarlos sin mezclar expedientes. También se comprobó manualmente desde Swagger una carga y consulta exitosa.

La suite automática final pasa con **7 tests**, pero existe una desviación relevante: el caso probado de `ClaimNumber` inválido es rechazado con HTTP 404 y no con el HTTP 400 indicado originalmente. La principal limitación de esta versión es que valida solo la gestión documental standalone: no interpreta documentos con IA ni demuestra la integración acumulada con las PoC anteriores.
