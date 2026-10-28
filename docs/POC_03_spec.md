# PoC 3 — Tool Calling y cálculos determinísticos

## Objetivo

Evolucionar el asistente para que, además de conversar y extraer información estructurada, pueda ejecutar **funciones determinísticas implementadas por la aplicación** mediante Tool Calling.

Hasta esta etapa existen dos capacidades diferenciadas:

    Chat
      │
      ▼
    Pydantic AI
      │
      ▼
    LLM

y:

    Structured Extraction
      │
      ▼
    extract_claim_data()
      │
      ▼
    Ollama Native API
      │
      ▼
    ClaimData

En esta PoC se agrega un tercer tipo de capacidad:

    Business Tools
      │
      ▼
    Python determinístico

La arquitectura será:

                         FastAPI
                            │
               ┌────────────┼────────────┐
               │            │            │
               ▼            ▼            ▼
             Chat      Extraction      Tools
               │            │            │
               ▼            ▼            ▼
          Pydantic AI  extract_claim_data() Python
               │            │            │
               ▼            ▼            ▼
    qwen2.5-instruct:7b   ClaimData     cálculos

El objetivo es separar claramente:

    interpretación / orquestación
            │
            ▼
           LLM

de:

    extracción estructurada
            │
            ▼
    extract_claim_data()

y de:

    cálculo / reglas determinísticas
            │
            ▼
          Tools

El razonamiento es que una plataforma de apoyo a analistas no debería depender del razonamiento generativo para ejecutar cálculos cuando éstos pueden expresarse como reglas determinísticas, trazables y testeables.

El modelo puede decidir:

    "Necesito calcular el deducible."

pero no debería calcularlo libremente.

Debe invocar:

    calculate_deductible()

Del mismo modo, para una reserva preliminar debe invocar:

    calculate_reserve()

Esto reduce:

- variabilidad;
- errores aritméticos;
- falta de trazabilidad;
- dependencia innecesaria del LLM.

---

## Alcance

Esta PoC incorpora:

- Tool Calling con Pydantic AI.
- `qwen2.5-instruct:7b` como modelo de chat y Tool Calling.
- Tools locales implementadas en Python.
- Argumentos tipados.
- Resultados tipados.
- Cálculo experimental de deducible.
- Cálculo experimental de reserva preliminar.
- Identificación de información faltante.
- Integración con `ClaimData`.
- Reutilización de `extract_claim_data()`.
- Swagger UI.
- OpenAPI.

Se mantienen:

- FastAPI.
- Pydantic AI.
- Ollama.
- Structured Extraction de la PoC 2.
- modelo canónico ACORD-aligned.

No se incorporan todavía:

- Policy Core.
- Customer API.
- pólizas reales.
- condicionado real.
- determinación de cobertura.
- documentos.
- OCR.
- RAG.
- Guardrails técnicos.
- MCP.
- A2A.
- persistencia.

Los cálculos de esta PoC son **reglas simplificadas de laboratorio**.

No representan reglas reales de negocio de una compañía de seguros.

---

# 1. Cambio de modelo para Tool Calling

En la PoC anterior se utilizó:

    phi4-mini

como modelo conversacional.

Para esta PoC se reemplaza por:

    hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF:Q4_K_M

renombrado localmente como:

    qwen2.5-instruct:7b

El motivo del cambio es utilizar un modelo con mejor comportamiento práctico para:

    Tool Calling

en esta etapa.

La capacidad crítica ya no es únicamente:

    conversar

sino:

    interpretar petición
        │
        ▼
    seleccionar tool
        │
        ▼
    generar argumentos
        │
        ▼
    utilizar resultado
        │
        ▼
    responder

Por ello el modelo debe ser fiable especialmente en:

- selección de tools;
- generación de argumentos;
- encadenamiento de tools;
- seguimiento estricto de instrucciones.

---

# 2. Descargar el modelo

Ejecutar:

    ollama run hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF:Q4_K_M

La primera ejecución descargará el modelo.

Comprobar:

    ollama list

Debe aparecer inicialmente con un nombre similar a:

    hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF:Q4_K_M

---

# 3. Renombrar el modelo

Crear un alias local:

    ollama cp hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF:Q4_K_M qwen2.5-instruct:7b

Comprobar:

    ollama list

Debe aparecer:

    qwen2.5-instruct:7b

Probar:

    ollama run qwen2.5-instruct:7b

Enviar:

    Responde únicamente con OK

Salir:

    /bye

Una vez comprobado el alias, puede eliminarse la referencia larga:

    ollama rm hf.co/bartowski/Qwen2.5-7B-Instruct-GGUF:Q4_K_M

---

# 4. Configuración

Modificar:

    app/config.py

El modelo conversacional pasa a ser:

    LLM_MODEL = os.getenv(
        "LLM_MODEL",
        "qwen2.5-instruct:7b",
    )

El resto de configuración se mantiene.

Por ejemplo:

    EXTRACTION_MODEL = os.getenv(
        "EXTRACTION_MODEL",
        "qwen2.5-extraction:1.5b",
    )

    LLM_BASE_URL = os.getenv(
        "LLM_BASE_URL",
        "http://localhost:11434/v1",
    )

    LLM_API_KEY = os.getenv(
        "LLM_API_KEY",
        "local-dev",
    )

---

# 5. Variables de entorno

PowerShell:

    $env:LLM_MODEL="qwen2.5-instruct:7b"
    $env:EXTRACTION_MODEL="qwen2.5-extraction:1.5b"
    $env:LLM_BASE_URL="http://localhost:11434/v1"
    $env:LLM_API_KEY="local-dev"

Linux/macOS:

    export LLM_MODEL="qwen2.5-instruct:7b"
    export EXTRACTION_MODEL="qwen2.5-extraction:1.5b"
    export LLM_BASE_URL="http://localhost:11434/v1"
    export LLM_API_KEY="local-dev"

---

# 6. Arquitectura resultante

La arquitectura local queda:

                         FastAPI
                            │
               ┌────────────┼────────────┐
               │            │            │
               ▼            ▼            ▼
             Chat      Extraction      Tools
               │            │            │
               ▼            ▼            ▼
          Pydantic AI  extract_claim_data() Python
               │            │
               ▼            ▼
    qwen2.5-instruct:7b   qwen2.5-extraction:1.5b
               │            │
               └──────┬─────┘
                      ▼
                    Ollama

---

# 7. Separación de responsabilidades

## Chat / Tool orchestration

    qwen2.5-instruct:7b

Responsabilidad:

- conversación;
- identificar intención;
- seleccionar tool;
- construir argumentos;
- usar resultados de tools;
- responder al analista.

---

## Structured Extraction

    qwen2.5-extraction:1.5b

Responsabilidad:

- transformar texto en `ClaimData`;
- respetar JSON Schema;
- extraer hechos.

---

## Tools

    Python

Responsabilidad:

- cálculos;
- reglas determinísticas;
- resultados reproducibles.

---

# 8. Modelos de resultados de cálculo

Agregar en:

    app/schemas.py

    from decimal import Decimal


    class DeductibleCalculation(BaseModel):
        loss_amount: Decimal
        deductible_percentage: Decimal
        minimum_deductible: Decimal
        calculated_deductible: Decimal


    class ReserveCalculation(BaseModel):
        estimated_loss_amount: Decimal
        deductible_amount: Decimal
        calculated_reserve: Decimal

Estos modelos son contratos propios de la aplicación.

Posteriormente podrán relacionarse con:

    ClaimsFinancialSummary

---

# 9. Por qué utilizar Decimal

Los cálculos monetarios deben utilizar:

    Decimal

y no:

    float

para evitar errores de representación binaria.

Los importes deben producir resultados:

    determinísticos
    reproducibles
    testeables

---

# 10. Crear tools.py

Crear:

    app/tools.py

Importar:

    from decimal import Decimal

    from app.schemas import (
        DeductibleCalculation,
        ReserveCalculation,
    )

---

# 11. Tool calculate_deductible

Agregar:

    def calculate_deductible(
        loss_amount: Decimal,
        deductible_percentage: Decimal,
        minimum_deductible: Decimal,
    ) -> DeductibleCalculation:
        """
        Calcula un deducible porcentual con mínimo.

        Regla experimental utilizada únicamente
        para esta PoC.
        """

        percentage_amount = (
            loss_amount
            * deductible_percentage
            / Decimal("100")
        )

        calculated_deductible = max(
            percentage_amount,
            minimum_deductible,
        )

        calculated_deductible = min(
            calculated_deductible,
            loss_amount,
        )

        return DeductibleCalculation(
            loss_amount=loss_amount,
            deductible_percentage=deductible_percentage,
            minimum_deductible=minimum_deductible,
            calculated_deductible=calculated_deductible,
        )

---

# 12. Regla experimental de deducible

La fórmula será:

    porcentaje =
        loss_amount
        × deductible_percentage
        / 100

Después:

    deductible =
        max(
            porcentaje,
            minimum_deductible
        )

con límite:

    deductible <= loss_amount

Ejemplo:

    loss_amount
        = 2.000.000

    deductible_percentage
        = 10

    minimum_deductible
        = 150.000

Resultado:

    calculated_deductible
        =
    200.000

---

# 13. Tool calculate_reserve

Agregar:

    def calculate_reserve(
        estimated_loss_amount: Decimal,
        deductible_amount: Decimal,
    ) -> ReserveCalculation:
        """
        Calcula una reserva preliminar simplificada.

        Regla experimental utilizada únicamente
        para esta PoC.
        """

        calculated_reserve = max(
            estimated_loss_amount
            - deductible_amount,
            Decimal("0"),
        )

        return ReserveCalculation(
            estimated_loss_amount=estimated_loss_amount,
            deductible_amount=deductible_amount,
            calculated_reserve=calculated_reserve,
        )

---

# 14. Regla experimental de reserva preliminar

Para esta PoC:

    reserve =
        estimated_loss_amount
        -
        deductible_amount

Ejemplo:

    estimated_loss_amount
        = 2.000.000

    deductible
        = 200.000

Resultado:

    calculated_reserve
        =
    1.800.000

Esta fórmula es únicamente demostrativa.

---

# 15. Tool get_missing_claim_information

Agregar:

    def get_missing_claim_information(
        loss_dt: str | None = None,
        loss_desc: str | None = None,
        policy_number: str | None = None,
        vehicle_plate: str | None = None,
    ) -> list[str]:

        missing: list[str] = []

        if not loss_dt:
            missing.append("LossDt")

        if not loss_desc:
            missing.append("LossDesc")

        if not policy_number:
            missing.append("PolicyNumber")

        if not vehicle_plate:
            missing.append("vehicle_plate")

        return missing

Se utiliza terminología ACORD cuando corresponde:

    LossDt
    LossDesc
    PolicyNumber

Se mantiene:

    vehicle_plate

como concepto propio.

---

# 16. Registrar las tools

Modificar:

    app/agent.py

Importar:

    from app.tools import (
        calculate_deductible,
        calculate_reserve,
        get_missing_claim_information,
    )

El modelo de chat continúa construyéndose mediante:

    chat_model = OpenAIChatModel(
        LLM_MODEL,
        provider=provider,
    )

Con:

    LLM_MODEL
        =
    qwen2.5-instruct:7b

---

# 17. System Prompt del agente

El `system_prompt` debe reforzar explícitamente el uso obligatorio de tools para cálculos.

Configurar:

    agent = Agent(
        model=chat_model,
        tools=[
            calculate_deductible,
            calculate_reserve,
            get_missing_claim_information,
        ],
        system_prompt=(
            "Eres un asistente para analistas de siniestros "
            "de seguros generales, especializado en la rama "
            "automotriz. "

            "Tu función es ayudar al analista a comprender, "
            "organizar y analizar información relacionada con "
            "un siniestro. "

            "Cuando el usuario solicite calcular un deducible, "
            "DEBES utilizar siempre la tool "
            "calculate_deductible. "
            "Nunca calcules el deducible directamente mediante "
            "razonamiento propio. "

            "Cuando el usuario solicite calcular una reserva "
            "preliminar, DEBES utilizar siempre la tool "
            "calculate_reserve. "
            "Nunca calcules la reserva directamente mediante "
            "razonamiento propio. "

            "Si el usuario solicita calcular primero el "
            "deducible y después la reserva preliminar, utiliza "
            "primero calculate_deductible y después "
            "calculate_reserve utilizando el resultado anterior. "

            "Nunca inventes parámetros requeridos por una tool. "
            "Si falta información necesaria para ejecutar un "
            "cálculo, indica únicamente qué dato falta. "

            "Cuando una tool de cálculo devuelva un resultado, "
            "responde únicamente con el resultado final solicitado. "
            "No expliques la fórmula, los pasos del cálculo, "
            "el razonamiento ni cómo se obtuvo el valor. "

            "Para un cálculo de deducible, responde únicamente "
            "con el valor del deducible. "

            "Para un cálculo de reserva preliminar, responde "
            "únicamente con el valor de la reserva preliminar. "

            "Si se solicitan ambos cálculos, responde únicamente "
            "con el deducible y la reserva preliminar, claramente "
            "identificados, sin explicación adicional. "

            "Las reglas de cálculo disponibles en esta PoC son "
            "experimentales y no representan reglas reales de "
            "una compañía de seguros. "

            "No determines cobertura. "
            "No apruebes ni rechaces siniestros. "
            "No simules una resolución formal. "

            "Responde siempre en español."
        ),
    )

---

# 18. Regla de respuesta para cálculos

La política de respuesta será:

## Deducible

Request:

    Calcula el deducible...

Respuesta:

    200000

No:

    El deducible es 200000 porque
    2000000 × 10 % = 200000...

---

## Reserva preliminar

Request:

    Calcula la reserva preliminar...

Respuesta:

    1800000

No:

    La reserva se calcula restando...

---

## Ambos cálculos

Request:

    Calcula deducible y reserva preliminar.

Respuesta:

    Deducible: 200000
    Reserva preliminar: 1800000

Sin explicación adicional.

---

# 19. Por qué restringir la respuesta

El objetivo es demostrar que:

    razonamiento
        +
    cálculo

pueden ocurrir internamente sin que el modelo genere una explicación innecesaria.

Esto permite producir respuestas:

- concisas;
- consistentes;
- más fáciles de consumir;
- más fáciles de integrar con frontend;
- menos variables entre ejecuciones.

La lógica del cálculo sigue estando en las tools.

---

# 20. No modificar extract_claim_data()

La función de extracción de la PoC 2 permanece igual.

    async def extract_claim_data(
        description: str,
    ) -> ClaimData:
        ...

No debe convertirse en una tool en esta etapa.

Su responsabilidad continúa siendo:

    Structured Extraction

---

# 21. Tool Calling versus Structured Extraction

La arquitectura distingue:

    extract_claim_data()
        │
        ▼
    hechos del siniestro

de:

    calculate_deductible()
        │
        ▼
    cálculo

y:

    calculate_reserve()
        │
        ▼
    cálculo

No deben mezclarse estas responsabilidades.

---

# 22. Flujo de cálculo de deducible

Request:

    "La pérdida estimada es 2.000.000,
    el deducible es 10 % con mínimo de
    150.000. Calcula el deducible."

Flujo:

    FastAPI
       │
       ▼
    Pydantic AI
       │
       ▼
    qwen2.5-instruct:7b
       │
       │ tool call
       ▼
    calculate_deductible()
       │
       ▼
    200000
       │
       ▼
    qwen2.5-instruct:7b
       │
       ▼
    200000

---

# 23. Probar cálculo de deducible

Ejecutar:

    uv run fastapi dev app/main.py

Request:

    POST http://localhost:8000/chat

Body:

    {
      "message": "La pérdida estimada es de 2.000.000, el deducible es 10% con un mínimo de 150.000. Calcula el deducible."
    }

Resultado esperado:

    {
      "response": "200000"
    }

El modelo debe utilizar:

    calculate_deductible()

---

# 24. Probar deducible mínimo

Request:

    {
      "message": "La pérdida estimada es 500.000, el deducible es 10% con mínimo de 100.000. Calcula el deducible."
    }

Tool:

    calculate_deductible(
        loss_amount=500000,
        deductible_percentage=10,
        minimum_deductible=100000
    )

Resultado:

    100000

Respuesta esperada:

    {
      "response": "100000"
    }

---

# 25. Probar reserva preliminar

Request:

    {
      "message": "La pérdida estimada es 2.000.000 y el deducible es 200.000. Calcula la reserva preliminar."
    }

Debe utilizar:

    calculate_reserve()

Resultado:

    1800000

Respuesta esperada:

    {
      "response": "1800000"
    }

---

# 26. Probar Tool Calling encadenado

Request:

    {
      "message": "La pérdida estimada es 2.000.000, el deducible es 10% con mínimo de 150.000. Calcula el deducible y después la reserva preliminar."
    }

Flujo:

    qwen2.5-instruct:7b
        │
        ▼
    calculate_deductible()
        │
        ▼
    200000
        │
        ▼
    qwen2.5-instruct:7b
        │
        ▼
    calculate_reserve(
        2000000,
        200000
    )
        │
        ▼
    1800000
        │
        ▼
    respuesta

Resultado esperado:

    {
      "response": "Deducible: 200000\nReserva preliminar: 1800000"
    }

No debe incluir explicación.

---

# 27. Probar parámetros faltantes

Request:

    {
      "message": "La pérdida estimada es de 2.000.000. Calcula el deducible."
    }

Faltan:

    deductible_percentage
    minimum_deductible

El agente no debe inventarlos.

Debe responder únicamente con algo equivalente a:

    Faltan deductible_percentage y minimum_deductible.

No debe realizar ningún cálculo.

---

# 28. Probar información faltante

Request:

    {
      "message": "El vehículo ABCD12 sufrió una colisión. ¿Qué información básica falta para continuar?"
    }

El agente puede utilizar:

    get_missing_claim_information()

Resultado conceptual:

    LossDt
    PolicyNumber

En este caso sí puede responder con una explicación mínima porque no se trata de una tool de cálculo.

---

# 29. No seleccionar reglas de deducible con el LLM

Request:

    {
      "message": "¿Qué deducible debería aplicar a este siniestro?"
    }

Todavía no existe:

    Policy
    Coverage
    condicionado

El modelo no debe inventar:

    deductible_percentage
    minimum_deductible

Debe indicar que se necesita una fuente autorizada.

---

# 30. No determinar cobertura

Request:

    {
      "message": "El parabrisas está roto. ¿Está cubierto?"
    }

Todavía no existe:

    Policy Core
    Coverage
    condicionado
    RAG corporativo

El agente no debe emitir una determinación.

---

# 31. Tools sin efectos secundarios

Las tools de esta PoC son:

    calculate_deductible()
    calculate_reserve()
    get_missing_claim_information()

Todas son:

    locales
    determinísticas
    sin acceso externo
    sin escritura
    sin efectos secundarios

No existen:

    approve_claim()
    reject_claim()
    send_customer_communication()
    authorize_payment()

---

# 32. No ejecutar código generado

El patrón permitido es:

    qwen2.5-instruct:7b
          │
          ▼
      tool call
          │
          ▼
    función registrada
          │
          ▼
       resultado

Nunca:

    LLM
      │
      ▼
    genera Python
      │
      ▼
    exec()

---

# 33. Relación con ClaimData

La extracción sigue siendo:

    description
        │
        ▼
    extract_claim_data()
        │
        ▼
    ClaimData

Las tools pueden consumir posteriormente información derivada de ese modelo.

Por ejemplo:

    ClaimData
       │
       ├── LossDt
       ├── LossDesc
       ├── PolicyNumber
       └── vehicle_plate
              │
              ▼
    get_missing_claim_information()

---

# 34. Relación con ClaimsFinancialSummary

Los contratos:

    DeductibleCalculation

    ReserveCalculation

son propios de la aplicación en esta etapa.

Más adelante podrán alimentar un modelo relacionado con:

    ClaimsFinancialSummary

No se implementa todavía el modelo financiero ACORD completo.

---

# 35. Swagger UI

Abrir:

    http://localhost:8000/swagger-ui

Los endpoints continúan incluyendo:

    GET  /health

    GET  /health/llm

    GET  /health/extraction

    POST /chat

    POST /claims/extract

Las tools son internas y no aparecen como endpoints REST.

---

# 36. OpenAPI

Abrir:

    http://localhost:8000/api-docs/openapi.json

OpenAPI continúa describiendo los contratos HTTP.

Las tools:

    calculate_deductible()

    calculate_reserve()

    get_missing_claim_information()

forman parte del contrato interno del agente, no del contrato REST.

---

# 37. Probar una petición sin tools

Request:

    {
      "message": "¿Qué función cumple un analista de siniestros automotrices?"
    }

El modelo puede responder directamente.

No debe ejecutar tools innecesariamente.

---

# 38. Verificación importante

Para comprobar que el modelo realmente está utilizando Tool Calling y no realizando el cálculo internamente, durante desarrollo conviene habilitar logging temporal alrededor de las funciones.

Por ejemplo:

    def calculate_deductible(...):
        print(
            "TOOL calculate_deductible called"
        )

        ...

y:

    def calculate_reserve(...):
        print(
            "TOOL calculate_reserve called"
        )

        ...

Al ejecutar:

    POST /chat

debe aparecer en consola:

    TOOL calculate_deductible called

o:

    TOOL calculate_reserve called

según corresponda.

El texto final correcto por sí solo no demuestra que el modelo haya utilizado la tool.

---

# 39. Criterio de éxito

Para considerar validada la PoC deben cumplirse al menos estos casos:

    cálculo deducible
        → tool utilizada

    cálculo reserva
        → tool utilizada

    cálculo encadenado
        → dos tools utilizadas

    parámetros faltantes
        → no inventados

    petición normal
        → no tool innecesaria

    respuesta de cálculo
        → sólo resultado

---

# 40. Resultado esperado

Al finalizar debe funcionar:

                           FastAPI
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
            Chat          Extraction         Tools
              │               │               │
              ▼               ▼               ▼
         Pydantic AI   extract_claim_data()  Python
              │               │               │
              ▼               ▼               │
    qwen2.5-instruct:7b Qwen2.5 Extraction    │
              │               │               │
              │               ▼               │
              │           ClaimData            │
              │                               │
              ├───────────────┬───────────────┤
              ▼               ▼               ▼
       calculate_        calculate_      get_missing_
       deductible()      reserve()       claim_information()
              │               │               │
              ▼               ▼               ▼
       cálculo exacto    cálculo exacto    datos faltantes
              │               │
              └──────────┬────┘
                         ▼
                qwen2.5-instruct:7b
                         │
                         ▼
                 resultado solamente
                         │
                         ▼
                      Analista

La capacidad principal validada por esta PoC es que el Claims Analyst Assistant pueda **orquestar funciones determinísticas mediante Tool Calling utilizando `qwen2.5-instruct:7b`**, sin realizar los cálculos directamente en el LLM.

La arquitectura mantiene la separación:

    qwen2.5-instruct:7b
        → conversación y Tool Calling

    qwen2.5-extraction:1.5b
        → Structured Extraction

    extract_claim_data()
        → frontera de extracción

    Tools Python
        → cálculos determinísticos

    ClaimData
        → modelo canónico del dominio

    Analista
        → conserva la decisión final

Para cálculos de:

    deducible

y:

    reserva preliminar

el modelo debe utilizar obligatoriamente las tools y devolver **únicamente el resultado solicitado**, sin explicar el procedimiento utilizado para obtenerlo.