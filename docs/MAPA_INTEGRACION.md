# Mapa de integración PoC 1-11

| Capacidad | PoC de referencia | En runtime integrado |
|---|---:|---|
| Agente conversacional local | 1 | `backend/app/agent.py` |
| Structured Extraction / ClaimData | 2 | `backend/app/agent.py`, `schemas.py` |
| Tool Calling / deducible / reserva | 3 | `backend/app/tools.py` |
| Guardrails + HITL | 4 | `backend/app/guardrails.py`, `conversation_service.py` |
| Ingesta documental | 5 | `backend/app/documents.py` |
| Expediente + OCR/RAG | 6 | `document_processing.py`, `retrieval.py`, `vector_store.py` |
| Póliza + condicionado | 7 | `policies.py`, `policy_core.py`, `corporate_knowledge.py` |
| Secure RAG | 8 | `secure_rag.py` |
| Memoria conversacional | 9 | `conversation_memory.py`, `conversation_service.py` |
| Customer REST | 10 | `customer_client.py`, `customer_service.py`, `customer_mock/` |
| Customer MCP | 11 | `app/mcp/`, `health.py` |

## Fronteras que no deben confundirse

- Conversation Memory = contexto de conversación.
- ClaimData = hechos estructurados del siniestro.
- Secure RAG = evidencia documental segura.
- Customer System = fuente corporativa ficticia para datos de cliente.
- Python Tools = cálculos determinísticos.
- MCP = frontera agente-sistema para PoC 11; no almacena conversación.
