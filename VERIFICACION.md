# Verificación realizada al generar el compilado

## Verificaciones que sí se pudieron ejecutar

- Compilación sintáctica de los archivos Python del workspace.
- Validación sintáctica del JavaScript del prototipo mediante Node.
- Revisión de estructura de carpetas y conservación de las PoC validadas.
- Inclusión de pruebas unitarias nuevas para Customer REST, Customer Service y Customer MCP.

## Verificación pendiente en el equipo local

No fue posible instalar las dependencias desde PyPI en el entorno donde se generó este paquete porque no dispone de acceso saliente a Internet. Por esa razón no se afirma que PoC 10/11 estén validadas ni que la suite completa haya pasado en runtime.

En el equipo local, Cline debe ejecutar primero:

```text
cd backend
uv sync
uv run pytest tests/unit -v
```

Después debe levantar los servicios y ejecutar los tests de integración.

## Criterio de estado

- PoC 2 y 4-9: se conserva el código marcado como VALIDADA en el material recibido.
- PoC 1 y 3: reconstruidas desde sus especificaciones Markdown.
- PoC 10 y 11: reconstruidas desde sus especificaciones Markdown y pendientes de validación integrada.
