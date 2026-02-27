import asyncio
from io import BytesIO

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from pypdf import PdfReader

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _embed_pdf_sync(pdf_bytes: bytes, filename: str) -> int:
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

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model_id,
        openai_api_key=settings.open_api_key,
    )

    logger.debug("Sending %d chunk(s) to OpenAI embeddings (%s)", len(docs), settings.embedding_model_id)
    PGVector.from_documents(
        docs,
        embeddings,
        collection_name="pdf_documents",
        connection_string=settings.db_host,
        use_jsonb=True,
    )
    logger.debug("PGVector upsert complete for '%s'", filename)

    return len(docs)


async def embed_pdf(pdf_bytes: bytes, filename: str) -> int:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _embed_pdf_sync, pdf_bytes, filename)
