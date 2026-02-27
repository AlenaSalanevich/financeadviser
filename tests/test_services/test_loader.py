from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from app.services.loader import embed_pdf


def _make_pdf_bytes(text: str) -> bytes:
    """Return a minimal in-memory PDF whose first page contains *text*."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    if text:
        # Write text onto the page via a content stream
        page.merge_page(page)  # no-op; we inject content below
        stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
        from pypdf.generic import EncodedStreamObject

        content = EncodedStreamObject()
        content.set_data(stream)
        page["/Contents"] = content
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_embed_pdf_returns_chunk_count() -> None:
    with (
        patch("app.services.loader.PGVector") as mock_pgvector,
        patch("app.services.loader.OpenAIEmbeddings") as mock_embeddings,
        patch("app.services.loader.PdfReader") as mock_reader,
    ):
        # Set up a fake page with extractable text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "A" * 1500  # > chunk_size → 2 chunks
        mock_reader.return_value.pages = [mock_page]

        mock_pgvector.from_documents.return_value = MagicMock()
        mock_embeddings.return_value = MagicMock()

        result = await embed_pdf(b"fake-pdf-bytes", "test.pdf")

    assert result == 2
    mock_pgvector.from_documents.assert_called_once()


@pytest.mark.asyncio
async def test_embed_pdf_empty_text() -> None:
    with (
        patch("app.services.loader.PGVector") as mock_pgvector,
        patch("app.services.loader.OpenAIEmbeddings"),
        patch("app.services.loader.PdfReader") as mock_reader,
    ):
        # Page with no extractable text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_reader.return_value.pages = [mock_page]

        result = await embed_pdf(b"fake-pdf-bytes", "empty.pdf")

    assert result == 0
    mock_pgvector.from_documents.assert_not_called()
