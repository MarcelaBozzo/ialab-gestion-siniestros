# PoC 5 — Ingesta de documentos heterogéneos del siniestro

## Objetivo
Validar que la plataforma pueda recibir documentos de un siniestro, aplicar controles básicos, generar metadata, almacenarlos y asociarlos al `ClaimNumber` correcto antes de interpretar su contenido con IA.

## Requisitos
- Python 3.11 o superior.
- `pip`.
- Navegador web para usar Swagger UI.

## Instalación
Desde la carpeta `proyecto/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Modelos necesarios
Esta versión validada de la PoC 5 **no necesita un modelo de IA** para ejecutar la capacidad documental. La definición acumulada original mencionaba Ollama y `phi4-mini` como componentes heredados de PoC anteriores, pero ese repositorio acumulado no estuvo disponible ni fue validado en esta sesión.

## Cómo ejecutar
Desde `proyecto/`, con el entorno virtual activado:

```bash
uvicorn app.main:app --reload
```

Mantén la Terminal abierta mientras uses la PoC.

## Endpoints o forma de probar
Abrir Swagger UI en:

```text
http://localhost:8000/swagger-ui
```

Endpoints principales:

- `GET /health`
- `POST /claims/{claim_number}/documents`
- `GET /claims/{claim_number}/documents`
- `GET /claims/{claim_number}/documents/{document_id}`
- `DELETE /claims/{claim_number}/documents/{document_id}`

Formatos permitidos en esta PoC: PDF, JPG/JPEG y PNG. El límite configurado por defecto es 10 MB.
