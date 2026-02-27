"""
Shared Vector Store and Embeddings Configuration
Provides reusable PGVector and OpenAI embeddings instances
"""
from typing import Optional
from urllib.parse import urlparse

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _safe_db_url(url: str) -> str:
    """Return the connection URL with the password replaced by ***."""
    try:
        parsed = urlparse(url)
        if parsed.password:
            return url.replace(parsed.password, "***", 1)
    except Exception:
        pass
    return url


def get_embeddings() -> OpenAIEmbeddings:
    """
    Get configured OpenAI embeddings instance.

    Returns:
        OpenAIEmbeddings: Configured embeddings model

    Raises:
        RuntimeError: If OpenAI API key is not configured
    """
    if not settings.open_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. "
            "Set it in your environment or .env file."
        )

    logger.debug("Initializing OpenAI embeddings with model: %s", settings.embedding_model_id)

    return OpenAIEmbeddings(
        model=settings.embedding_model_id,
        openai_api_key=settings.open_api_key,
    )


def get_vector_store(
        collection_name: str = "pdf_documents",
        embeddings: Optional[OpenAIEmbeddings] = None,
) -> PGVector:
    """
    Get configured PGVector store instance.

    Args:
        collection_name: Name of the collection/table in PGVector
        embeddings: Optional embeddings instance. If None, will create new one.

    Returns:
        PGVector: Configured vector store

    Raises:
        RuntimeError: If database URL is not configured
    """
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Set it to a PostgreSQL connection string, e.g. "
            "postgresql://user:password@host:5432/database"
        )

    if embeddings is None:
        embeddings = get_embeddings()

    logger.debug(
        "Connecting to PGVector at %s, collection: %s",
        _safe_db_url(settings.database_url),
        collection_name,
    )

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=settings.database_url,
        use_jsonb=True,
    )

    return vector_store


def get_vector_store_connection_string() -> str:
    """
    Get the database connection string for PGVector.

    Returns:
        str: Database connection string

    Raises:
        RuntimeError: If database URL is not configured
    """
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Set it to a PostgreSQL connection string."
        )

    return settings.database_url