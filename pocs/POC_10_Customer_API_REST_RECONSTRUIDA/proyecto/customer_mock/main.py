from fastapi import FastAPI, HTTPException

app = FastAPI(title="Customer Mock API", version="0.1.0")

customers = {
    "999000010": {
        "customer_id": "CUST-000123",
        "national_id": "999000010",
        "full_name": "Alejandro Torres Munoz",
        "email": "a.torres@ejemplo.cl",
        "phone_number": "+56955550123",
        "address": "Av. Ejemplo 1234, Santiago",
    },
    "999000029": {
        "customer_id": "CUST-000217",
        "national_id": "999000029",
        "full_name": "Cliente Demo 217",
        "email": "cliente.217@ejemplo.cl",
        "phone_number": "+56955550217",
        "address": "Av. Demo 217, Santiago",
    },
    "999000037": {
        "customer_id": "CUST-000301",
        "national_id": "999000037",
        "full_name": "Cliente Demo 301",
        "email": "cliente.301@ejemplo.cl",
        "phone_number": "+56955550301",
        "address": "Av. Demo 301, Santiago",
    },
    "999000045": {
        "customer_id": "CUST-000402",
        "national_id": "999000045",
        "full_name": "Cliente Demo 402",
        "email": "cliente.402@ejemplo.cl",
        "phone_number": "+56955550402",
        "address": "Av. Demo 402, Santiago",
    },
}

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/customers/by-national-id/{national_id}")
async def find_customer(national_id: str) -> dict[str, str]:
    customer = customers.get(national_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer_id": customer["customer_id"]}

@app.get("/customers/{customer_id}")
async def customer_profile(customer_id: str, fields: str) -> dict[str, str | None]:
    customer = next((item for item in customers.values() if item["customer_id"] == customer_id), None)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    allowed_fields = {"email", "phone_number", "address"}
    requested_fields = set(fields.split(","))
    if not requested_fields or not requested_fields <= allowed_fields:
        raise HTTPException(status_code=400, detail="Invalid fields")
    identity_fields = {"customer_id", "national_id", "full_name"}
    return {key: value for key, value in customer.items() if key in identity_fields or key in requested_fields}
