from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.documents as documents
from app.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(documents, "CLAIMS_STORAGE_PATH", tmp_path / "claims")
    return TestClient(app)


def upload(client: TestClient, claim: str, name: str, mime: str, doc_type: str, data: bytes):
    return client.post(
        f"/claims/{claim}/documents",
        data={"document_type": doc_type},
        files={"file": (name, data, mime)},
    )


def test_health_and_openapi(client: TestClient):
    assert client.get("/health").status_code == 200
    assert client.get("/swagger-ui").status_code == 200
    schema = client.get("/api-docs/openapi.json")
    assert schema.status_code == 200
    data = schema.json()
    assert "/claims/{claim_number}/documents" in data["paths"]
    assert "ClaimDocument" in data["components"]["schemas"]
    assert "DocumentType" in data["components"]["schemas"]


def test_upload_list_get_and_delete(client: TestClient):
    response = upload(
        client,
        "CLM-000123",
        "denuncia.pdf",
        "application/pdf",
        "CLAIM_REPORT",
        b"%PDF-1.4\nPoC5 sample\n%%EOF",
    )
    assert response.status_code == 200
    doc = response.json()
    assert doc["claim_number"] == "CLM-000123"
    assert doc["document_type"] == "CLAIM_REPORT"
    assert doc["original_filename"] == "denuncia.pdf"
    assert doc["content_type"] == "application/pdf"
    assert doc["size_bytes"] > 0

    document_id = doc["document_id"]

    listed = client.get("/claims/CLM-000123/documents")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    metadata = client.get(f"/claims/CLM-000123/documents/{document_id}")
    assert metadata.status_code == 200
    assert metadata.json()["document_id"] == document_id

    deleted = client.delete(f"/claims/CLM-000123/documents/{document_id}")
    assert deleted.status_code == 204
    assert client.get("/claims/CLM-000123/documents").json() == []


def test_multiple_types_and_claim_isolation(client: TestClient):
    a = upload(client, "CLM-000123", "foto.jpg", "image/jpeg", "DAMAGE_PHOTO", b"jpegdata")
    b = upload(client, "CLM-000456", "parte.pdf", "application/pdf", "POLICE_REPORT", b"pdfdata")
    assert a.status_code == 200
    assert b.status_code == 200

    docs_a = client.get("/claims/CLM-000123/documents").json()
    docs_b = client.get("/claims/CLM-000456/documents").json()
    assert len(docs_a) == 1 and docs_a[0]["claim_number"] == "CLM-000123"
    assert len(docs_b) == 1 and docs_b[0]["claim_number"] == "CLM-000456"


def test_unsupported_type(client: TestClient):
    response = upload(client, "CLM-000123", "archivo.zip", "application/zip", "OTHER", b"zipdata")
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported document type"


def test_invalid_claim_number(client: TestClient):
    # Encoded slash keeps the invalid value in a single path parameter for the test.
    response = upload(client, "CLM%2Fbad", "denuncia.pdf", "application/pdf", "CLAIM_REPORT", b"pdf")
    assert response.status_code in {400, 404}


def test_size_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(documents, "MAX_DOCUMENT_SIZE_MB", 1)
    response = upload(
        client,
        "CLM-000123",
        "grande.pdf",
        "application/pdf",
        "CLAIM_REPORT",
        b"x" * (1024 * 1024 + 1),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Document exceeds maximum allowed size"


def test_physical_storage_uses_document_id(client: TestClient):
    response = upload(client, "CLM-000123", "parte_policial.pdf", "application/pdf", "POLICE_REPORT", b"pdf")
    doc = response.json()
    claim_path = documents.CLAIMS_STORAGE_PATH / "CLM-000123" / "documents"
    names = sorted(p.name for p in claim_path.iterdir())
    assert f"{doc['document_id']}.pdf" in names
    assert f"{doc['document_id']}.metadata.json" in names
    assert "parte_policial.pdf" not in names
