import io
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

UPLOAD_URL = "/api/v1/data/upload"
MINIMAL_PDF = b"%PDF-1.4 minimal"


def _pdf_file(
    content: bytes = MINIMAL_PDF,
    filename: str = "test.pdf",
    content_type: str = "application/pdf",
) -> dict:
    return {"file": (filename, io.BytesIO(content), content_type)}


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_pdf_success(client: AsyncClient) -> None:
    with patch(
        "app.api.v1.endpoints.data.embed_pdf",
        new_callable=AsyncMock,
        return_value=5,
    ):
        response = await client.post(UPLOAD_URL, files=_pdf_file())

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "test.pdf"
    assert body["size_bytes"] == len(MINIMAL_PDF)
    assert body["chunks_stored"] == 5
    assert "uploaded successfully" in body["message"] or "uploaded and embedded" in body["message"]


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_wrong_content_type(client: AsyncClient) -> None:
    response = await client.post(
        UPLOAD_URL, files=_pdf_file(content_type="text/plain")
    )
    assert response.status_code == 400
    assert "Invalid content type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_missing_pdf_extension(client: AsyncClient) -> None:
    response = await client.post(
        UPLOAD_URL, files=_pdf_file(filename="document.txt")
    )
    assert response.status_code == 400
    assert ".pdf" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient) -> None:
    response = await client.post(UPLOAD_URL, files=_pdf_file(content=b""))
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_oversized_file(client: AsyncClient) -> None:
    oversized = b"x" * (50 * 1024 * 1024 + 1)
    response = await client.post(UPLOAD_URL, files=_pdf_file(content=oversized))
    assert response.status_code == 413
    assert "50 MB" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Service error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_service_error(client: AsyncClient) -> None:
    with patch(
        "app.api.v1.endpoints.data.embed_pdf",
        new_callable=AsyncMock,
        side_effect=RuntimeError("connection refused"),
    ):
        response = await client.post(UPLOAD_URL, files=_pdf_file())

    assert response.status_code == 500
    assert "Failed to process" in response.json()["detail"]
