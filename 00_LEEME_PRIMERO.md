# LAB IA Insurance - compilado para VS Code + Cline

Este paquete reúne el prototipo visual y la evolución técnica de las PoC 1 a 11 en una sola carpeta de trabajo.

## Qué debes abrir en VS Code

Abre **la carpeta raíz completa `insurance-agentic-lab-cline`**, no sólo `frontend` ni sólo `backend`.

La estructura principal es:

- `frontend/`: prototipo visual v1.2. Se conserva como HTML/CSS/JavaScript; no requiere Angular.
- `backend/`: runtime integrado. Parte de la PoC 9 validada e incorpora la reconstrucción funcional de PoC 10 (Customer REST) y PoC 11 (MCP).
- `pocs/`: snapshots separados de las PoC, para consulta y comparación.
- `docs/`: especificaciones Markdown entregadas para PoC 1, 3, 10 y 11.
- `scripts/`: ayudas para revisar y levantar el laboratorio.

## Estado de cada PoC

| PoC | Estado en este paquete | Uso principal |
|---|---|---|
| 1 | Reconstruida desde MD | Agente local básico |
| 2 | Código validado recibido | Extracción estructurada |
| 3 | Reconstruida desde MD sobre PoC 2 | Tool Calling y cálculos determinísticos |
| 4 | Código validado recibido | Guardrails + Human-in-the-Loop |
| 5 | Código validado recibido | Ingesta y gestión documental |
| 6 | Código validado recibido | Expediente estructurado + RAG |
| 7 | Código validado recibido | Póliza y conocimiento corporativo |
| 8 | Código validado recibido | Secure RAG + trazabilidad |
| 9 | Código validado recibido | Memoria conversacional por sesión |
| 10 | Reconstruida desde MD | Customer System vía REST |
| 11 | Reconstruida desde MD | Customer System vía MCP |

**Importante:** PoC 10 y PoC 11 todavía no deben llamarse "validadas". Este compilado permite probarlas junto al prototipo.

## Cómo está integrada la solución

No se levantan 11 backends en cadena. Las PoC son acumulativas y PoC 9 ya contiene gran parte de las capacidades anteriores. Por eso `backend/` usa esa base y agrega las capas nuevas.

Flujo objetivo:

```text
Prototipo
   |
   v
FastAPI / Claims API
   |
   v
Claims Analyst Agent
   |-- Conversation Memory
   |-- Guardrails
   |-- Structured Extraction / ClaimData
   |-- Secure RAG
   |-- Tools determinísticas
   |-- Policy / conocimiento corporativo
   `-- Customer Service
          |-- REST (PoC 10)
          `-- MCP  (PoC 11)
                 |
                 v
          Customer API simulada
```

El frontend detecta automáticamente si el backend está disponible. Si no lo está, conserva el comportamiento de simulación local del prototipo.

## Primera meta con Cline

La primera meta NO es modificar arquitectura ni diseño. Es conseguir que el entorno local levante y verificar:

1. frontend accesible;
2. backend `/health` respondiendo;
3. Customer Mock API respondiendo;
4. sesión conversacional creada;
5. una consulta al asistente;
6. PoC 10 usando REST;
7. PoC 11 usando MCP;
8. sin romper los tests y capacidades de la base PoC 9.

Lee `PROMPT_PARA_CLINE.md` para el primer mensaje recomendado.
