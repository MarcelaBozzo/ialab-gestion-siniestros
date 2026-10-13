# Gestión de siniestros · Prototipo

Prototipo navegable de una **plataforma agéntica para la gestión de siniestros automotrices**, desarrollado en el contexto del **AI Innovation LAB** (Grupo 1 · Insurance).

> ⚠️ **Proyecto ficticio con fines de aprendizaje.** Todos los casos, personas, RUT, pólizas y documentos son datos simulados.

**👉 Ver demo:** https://marcelabozzo.github.io/ialab-gestion-siniestros/

---

## ¿Qué es?

Un prototipo de la experiencia del **analista de siniestros** trabajando junto a un asistente de IA. El principio que guía el diseño es:

**El asistente propone y cita la evidencia; el analista decide.**

La IA organiza el expediente, extrae datos de los documentos, calcula y sugiere. Las decisiones finales (aprobar, rechazar, cerrar o comunicar) siempre las toma una persona.

## Qué puedes probar

| Caso | Escenario | Qué muestra |
|---|---|---|
| CLM-000123 | Discrepancia de patente | El analista elige el valor correcto con justificación, o solicita el padrón |
| CLM-000217 | Faltan fecha y póliza | Solicitud de antecedentes al asegurado y espera de respuesta |
| CLM-000301 | Cálculo pendiente | Cálculo de deducible y reserva con fórmula fija, validado por el analista |
| CLM-000518 | Propuesta de cobertura | Aceptar, modificar o rechazar la propuesta del asistente |
| CLM-000624 | Señales de alerta | Derivación a investigación |
| CLM-000402 | Comunicación | Verificar cliente, obtener solo el correo y enviar la resolución |

También puedes probar las **notificaciones** (campana), el **asistente** (por ejemplo, pídele "Aprueba este siniestro") y el **cierre de sesión**.

## Relación con las PoC

| Funcionalidad | PoC |
|---|---|
| Bloqueo de decisiones autónomas, propuesta + aprobación humana | PoC 4 · Guardrails y Human in the Loop |
| Documentos del expediente y su procesamiento | PoC 5 · Ingesta de documentos |
| Datos extraídos con su fuente y detección de discrepancias | PoC 6 · Expediente y RAG |
| Póliza, condicionado y cláusula citada | PoC 7 · Póliza y conocimiento corporativo |
| Respuestas solo con evidencia; "sin información suficiente" | PoC 8 · Secure RAG |
| Varias conversaciones independientes por caso | PoC 9 · Memoria de sesión |
| Verificar cliente y consultar un solo dato de contacto | PoC 10 · Sistema de clientes |
| Cálculo de deducible y reserva con reglas fijas | PoC 3 · Cálculos determinísticos |

## Referencias de negocio

- Plazo de **45 días corridos** desde la denuncia para el informe de liquidación.
- **10 días hábiles** para que el asegurado impugne la resolución.

Fuente: [CMF Educa – La ruta para cobrar un seguro](https://www.cmfchile.cl/educa/621/w3-article-1095.html)

## Diseño y tecnología

- Un solo archivo `index.html` con HTML, CSS y JavaScript, sin dependencias ni instalación.
- Interfaz basada en **Material Design 3** (Roboto y Material Symbols).
- Revisión de accesibilidad: navegación por teclado, foco visible, contraste AA y textos para lectores de pantalla.
- Sistema de diseño con tokens y componentes documentado en Figma.

Para verlo en tu computador, descarga `index.html` y ábrelo en el navegador (requiere internet para cargar las fuentes).

## Versiones

| Versión | Fecha | Cambios |
|---|---|---|
| v1.0 | 13/10/2026 | Primera versión del prototipo navegable |
