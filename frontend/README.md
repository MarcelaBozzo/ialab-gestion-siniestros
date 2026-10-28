# Gestión de siniestros · Prototipo

Prototipo navegable de una **plataforma agéntica para la gestión de siniestros automotrices**, desarrollado en el contexto del **AI Innovation LAB** (Grupo 1 · Insurance).

> ⚠️ **Proyecto ficticio con fines de aprendizaje.** Todos los casos, personas, RUT, pólizas y documentos son datos simulados.

**👉 Cómo verlo:** descomprime el zip y abre `index.html` con doble clic en tu navegador. Funciona **sin conexión a internet**: las fuentes y los íconos vienen incluidos.

---

## ¿Qué es?

Un prototipo de la experiencia del **analista de siniestros** trabajando junto a un asistente de IA. El principio que guía el diseño es:

**El asistente propone y cita la evidencia; el analista decide.**

La IA organiza el expediente, extrae datos de los documentos, calcula y sugiere. Las decisiones finales (aprobar, rechazar, cerrar o comunicar) siempre las toma una persona.

## Qué puedes probar

| Caso | Escenario | Qué muestra |
|---|---|---|
| CLM-000123 | Inconsistencia documental | Dos documentos con patentes distintas; el analista decide con justificación o solicita el padrón |
| CLM-000402 | Evidencia segura | Un documento excluido por seguridad que no se usa como evidencia ni modifica el expediente |
| CLM-000624 | Señales de alerta | Vía de gestión sugerida (investigación) con alertas y su fuente; el analista decide la derivación |
| CLM-000217 | Información faltante | Solicitud simulada de antecedentes y confirmación de datos críticos extraídos antes de actualizar el expediente |
| CLM-000301 | Cálculo determinístico | Deducible y reserva preliminar con regla visible, validados por el analista |
| CLM-000518 | Propuesta asistida | Póliza, condicionado y cláusula citada; el analista acepta, modifica o rechaza |

**Verificación del cliente (nuevo en v1.2):** en la tarjeta **Cliente** de cada caso, o preguntándole al asistente "¿El declarante es cliente?" y luego "¿Cuál es su correo?":
- CLM-000123 / CLM-000518: cliente encontrado; el correo registrado difiere del declarado en la denuncia y prevalece el sistema de clientes.
- CLM-000624: el declarante no figura como cliente.
- CLM-000301: el primer intento simula el sistema de clientes no disponible (resultado desconocido, distinto de "no encontrado"); el reintento funciona.
- En la etapa de comunicación, el destinatario se obtiene consultando solo el correo en el sistema de clientes.

También puedes probar las **notificaciones** (campana), el **asistente** (por ejemplo, pídele "Aprueba este siniestro" para ver el bloqueo) y el **cierre de sesión**. Las acciones externas (envío de solicitudes y de la resolución) son **simuladas**.

## Relación con las PoC

| Funcionalidad | PoC |
|---|---|
| Información faltante sin inventar datos | PoC 1 · Asistente local y PoC 2 · Extracción estructurada |
| Bloqueo de decisiones autónomas, propuesta + aprobación humana | PoC 4 · Guardrails y Human in the Loop |
| Documentos del expediente y su procesamiento | PoC 5 · Ingesta de documentos |
| Datos extraídos con su fuente y detección de discrepancias | PoC 6 · Expediente y RAG |
| Póliza, condicionado y cláusula citada | PoC 7 · Póliza y conocimiento corporativo |
| Documento excluido por seguridad; respuestas solo con evidencia | PoC 8 · Secure RAG |
| Varias conversaciones independientes por caso; "su correo" se entiende solo dentro de la misma conversación | PoC 9 · Memoria de sesión |
| Verificar si el declarante es cliente (solo código, sin datos personales) y consultar un único dato de contacto; "no encontrado" distinto de "sistema no disponible"; el sistema de clientes prevalece sobre lo declarado | PoC 10 · Sistema de clientes vía API REST |
| Misma capacidad a través de un servidor MCP de solo lectura (no se pueden crear ni modificar clientes) | PoC 11 · Integración mediante MCP |
| Cálculo de deducible y reserva con reglas fijas | PoC 3 · Cálculos determinísticos |

## Historias de usuario cubiertas

Según la bajada funcional (HU-01 a HU-14). La propuesta de cobertura (HU-07) y la vía de gestión (HU-09) se muestran como **visión funcional**: aún no están validadas en las PoC 1–11 y el prototipo lo indica. El borrador de comunicación (HU-10) está validado parcialmente.

## Referencias de negocio

Los plazos del prototipo están **configurados para la demostración** y no representan una regla productiva validada:
- **45 días corridos** desde la denuncia para el informe de liquidación.
- **10 días hábiles** para que el asegurado impugne la resolución.

Referencia: [CMF Educa – La ruta para cobrar un seguro](https://www.cmfchile.cl/educa/621/w3-article-1095.html)

## Diseño y tecnología

- HTML, CSS y JavaScript sin frameworks, dependencias ni instalación.
- Interfaz basada en **Material Design 3** (Roboto y Material Symbols).
- Revisión de accesibilidad: navegación por teclado, foco visible, contraste AA y textos para lectores de pantalla.
- Sistema de diseño con tokens y componentes documentado en Figma: [IA LAB – Grupo 1](https://www.figma.com/design/uI1BHO3zlM1v2ZqkEp3p0h).

## Estructura del proyecto

```
prototipo-siniestros-v1.2/
├── index.html            Estructura de las pantallas
├── css/
│   ├── fonts.css         Declaración de fuentes locales
│   └── styles.css        Estilos y tokens Material Design 3
├── js/
│   └── app.js            Datos simulados, lógica de flujo y asistente
├── assets/fonts/         Roboto y Material Symbols Rounded (con sus licencias)
└── README.md
```

Las carpetas deben mantenerse juntas: si mueves `index.html` solo, pierde los estilos y la lógica.

## Versiones

| Versión | Fecha | Cambios |
|---|---|---|
| v1.0 | 19/10/2026 | Primera versión del prototipo navegable |
| v1.1 | 19/10/2026 | Framing funcional: propuesta asistida, acciones simuladas, datos de demo, sin integración de clientes y casos alineados con las capacidades validadas en las PoC 1–9 |
| v1.2 | 19/10/2026 | Historias de usuario HU-01 a HU-14 y PoC 10–11: verificación del declarante y consulta minimizada de datos de cliente (solo lectura, vía MCP), estados de error diferenciados, destinatario obtenido del sistema de clientes, trazabilidad por tipo de fuente y alcance pendiente de HU-07/HU-09 |
