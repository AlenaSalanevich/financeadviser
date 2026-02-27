import asyncio
from io import BytesIO

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from pypdf import PdfReader

from app.config import settings


def _embed_pdf_sync(pdf_bytes: bytes, filename: str) -> int:
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
        return 0

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = splitter.split_documents(pages)

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model_id,
        openai_api_key=settings.open_api_key,
    )

    PGVector.from_documents(
        docs,
        embeddings,
        collection_name="pdf_documents",
        connection_string=settings.db_host,
    )

    return len(docs)


async def embed_pdf(pdf_bytes: bytes, filename: str) -> int:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _embed_pdf_sync, pdf_bytes, filename)
