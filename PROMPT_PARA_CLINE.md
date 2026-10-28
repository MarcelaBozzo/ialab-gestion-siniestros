# Primer prompt recomendado para Cline

Pega este texto en Cline después de abrir la carpeta raíz completa del proyecto:

> Revisa primero `00_LEEME_PRIMERO.md` y la estructura completa del repositorio. No refactorices ni cambies el diseño todavía. Quiero levantar este laboratorio local y verificar la integración del prototipo con el backend acumulativo de las PoC 1 a 11. Empieza comprobando prerrequisitos, dependencias y variables de entorno. Después ayúdame a levantar Customer Mock API, Ollama, Qdrant y Claims API. Verifica `/health`, `/health/customer`, `/health/customer-mcp` e `/integration/info`. Finalmente abre el prototipo servido por FastAPI y prueba una conversación. Si encuentras un error, corrígelo con el cambio mínimo posible y explícame en lenguaje simple qué cambiaste. No conviertas el frontend a Angular y no sustituyas las PoC validadas por una reescritura general.

## Segundo prompt, una vez que levante

> Ahora prueba el flujo integrado con un caso ficticio: crear sesión para `CLM-000123`, verificar si el declarante es cliente, pedir su correo en un segundo turno, calcular deducible/reserva cuando haya parámetros suficientes y comprobar que las decisiones sensibles siguen requiriendo revisión humana. Indícame qué PoC/capacidad intervino en cada paso y registra los fallos que queden pendientes.
