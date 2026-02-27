import asyncio
from io import BytesIO
from urllib.parse import urlparse

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from pypdf import PdfReader

from app.config import settings
from app.core.vector_store import get_embeddings, get_vector_store_connection_string, _safe_db_url
from app.core.logging import get_logger

logger = get_logger(__name__)

def _embed_pdf_sync(pdf_bytes: bytes, filename: str) -> int:
    """
    Synchronous function to parse PDF and embed into vector store.

    Args:
        pdf_bytes: PDF file content as bytes
        filename: Name of the PDF file

    Returns:
        Number of document chunks embedded

    Raises:
        RuntimeError: If database URL is not configured
    """
    connection_string = get_vector_store_connection_string()

    logger.debug("Parsing PDF '%s' (%d bytes)", filename, len(pdf_bytes))
    reader = PdfReader(BytesIO(pdf_bytes))

    pages: list[Document] = []
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(
                Document(
                    page_content=text,
                    metadata={"source": filename, "page": page_num},
                )
            )

    if not pages:
        logger.warning("No extractable text found in '%s' — skipping embedding", filename)
        return 0

    logger.debug("Extracted %d page(s) from '%s'", len(pages), filename)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = splitter.split_documents(pages)
    logger.debug("Split into %d chunk(s)", len(docs))

    embeddings = get_embeddings()

    logger.debug(
        "Connecting to PGVector at %s", _safe_db_url(connection_string)
    )
    logger.debug("Sending %d chunk(s) to OpenAI embeddings (%s)", len(docs), settings.embedding_model_id)
    PGVector.from_documents(
        docs,
        embeddings,
        collection_name="pdf_documents",
        connection=connection_string,
        use_jsonb=True,
    )
    logger.debug("PGVector upsert complete for '%s'", filename)

    return len(docs)


async def embed_pdf(pdf_bytes: bytes, filename: str) -> int:
    """
    Asynchronously embed PDF document into vector store.

    Args:
        pdf_bytes: PDF file content as bytes
        filename: Name of the PDF file

    Returns:
        Number of document chunks embedded

    Example:
        >>> from app.services.loader import embed_pdf
        >>> with open("document.pdf", "rb") as f:
        ...     pdf_bytes = f.read()
        >>> num_chunks = await embed_pdf(pdf_bytes, "document.pdf")
        >>> print(f"Embedded {num_chunks} chunks")
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _embed_pdf_sync, pdf_bytes, filename)
