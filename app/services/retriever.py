"""
Document Retrieval Service
Handles semantic search and document retrieval from vector store
"""
import asyncio
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from app.core.vector_store import get_vector_store, get_embeddings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentRetriever:
    """
    Service for retrieving relevant documents based on queries.
    Uses PGVector for semantic search with OpenAI embeddings.
    """

    def __init__(self, collection_name: str = "pdf_documents"):
        """
        Initialize the document retriever.

        Args:
            collection_name: Name of the vector store collection to search
        """
        self.collection_name = collection_name
        self._vector_store = None
        self._embeddings = None

    def _ensure_initialized(self):
        """Lazy initialization of vector store and embeddings."""
        if self._embeddings is None:
            logger.debug("Initializing embeddings for retriever")
            self._embeddings = get_embeddings()

        if self._vector_store is None:
            logger.debug("Initializing vector store for retriever")
            self._vector_store = get_vector_store(
                collection_name=self.collection_name,
                embeddings=self._embeddings,
            )

    def _retrieve_sync(
            self,
            query: str,
            k: int = 4,
            filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Synchronous retrieval of relevant documents.

        Args:
            query: User query string
            k: Number of documents to retrieve
            filter_dict: Optional metadata filters

        Returns:
            List of relevant documents with metadata
        """
        self._ensure_initialized()

        logger.info("Retrieving documents for query: '%s' (k=%d)", query, k)

        if filter_dict:
            logger.debug("Applying filters: %s", filter_dict)
            results = self._vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter_dict,
            )
        else:
            results = self._vector_store.similarity_search(
                query=query,
                k=k,
            )

        logger.info("Retrieved %d document(s)", len(results))
        return results

    async def retrieve(
            self,
            query: str,
            k: int = 4,
            filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Asynchronously retrieve relevant documents based on query.

        Args:
            query: User query string
            k: Number of documents to retrieve (default: 4)
            filter_dict: Optional metadata filters (e.g., {"source": "filename.pdf"})

        Returns:
            List of relevant Document objects with page_content and metadata

        Example:
            >>> retriever = DocumentRetriever()
            >>> docs = await retriever.retrieve("What is machine learning?", k=3)
            >>> for doc in docs:
            ...     print(doc.page_content)
            ...     print(doc.metadata)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._retrieve_sync,
            query,
            k,
            filter_dict,
        )

    def _retrieve_with_scores_sync(
            self,
            query: str,
            k: int = 4,
            filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[Document, float]]:
        """
        Synchronous retrieval with relevance scores.

        Args:
            query: User query string
            k: Number of documents to retrieve
            filter_dict: Optional metadata filters

        Returns:
            List of tuples (Document, score) where score is similarity score
        """
        self._ensure_initialized()

        logger.info("Retrieving documents with scores for query: '%s' (k=%d)", query, k)

        if filter_dict:
            logger.debug("Applying filters: %s", filter_dict)
            results = self._vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict,
            )
        else:
            results = self._vector_store.similarity_search_with_score(
                query=query,
                k=k,
            )

        logger.info("Retrieved %d document(s) with scores", len(results))
        return results

    async def retrieve_with_scores(
            self,
            query: str,
            k: int = 4,
            filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[Document, float]]:
        """
        Asynchronously retrieve documents with relevance scores.

        Args:
            query: User query string
            k: Number of documents to retrieve
            filter_dict: Optional metadata filters

        Returns:
            List of tuples (Document, similarity_score)
            Lower scores indicate higher similarity

        Example:
            >>> retriever = DocumentRetriever()
            >>> results = await retriever.retrieve_with_scores("AI ethics", k=3)
            >>> for doc, score in results:
            ...     print(f"Score: {score:.4f}")
            ...     print(doc.page_content[:100])
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._retrieve_with_scores_sync,
            query,
            k,
            filter_dict,
        )

    def get_retriever(
            self,
            k: int = 4,
            search_type: str = "similarity",
            search_kwargs: Optional[Dict[str, Any]] = None,
    ) -> VectorStoreRetriever:
        """
        Get a LangChain retriever object for use in chains.

        Args:
            k: Number of documents to retrieve
            search_type: Type of search ("similarity" or "mmr")
            search_kwargs: Additional search arguments

        Returns:
            VectorStoreRetriever: LangChain retriever object

        Example:
            >>> retriever = DocumentRetriever()
            >>> lc_retriever = retriever.get_retriever(k=5)
            >>> # Use in LangChain chains
            >>> from langchain.chains import RetrievalQA
            >>> qa_chain = RetrievalQA.from_chain_type(
            ...     llm=llm,
            ...     retriever=lc_retriever
            ... )
        """
        self._ensure_initialized()

        if search_kwargs is None:
            search_kwargs = {"k": k}
        else:
            search_kwargs["k"] = k

        logger.debug(
            "Creating LangChain retriever (search_type=%s, kwargs=%s)",
            search_type,
            search_kwargs,
        )

        return self._vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

    async def retrieve_by_source(
            self,
            query: str,
            source_filename: str,
            k: int = 4,
    ) -> List[Document]:
        """
        Retrieve documents filtered by source filename.

        Args:
            query: User query string
            source_filename: Filename to filter by
            k: Number of documents to retrieve

        Returns:
            List of relevant documents from the specified source

        Example:
            >>> retriever = DocumentRetriever()
            >>> docs = await retriever.retrieve_by_source(
            ...     "financial metrics",
            ...     "annual_report_2023.pdf",
            ...     k=5
            ... )
        """
        filter_dict = {"source": source_filename}
        return await self.retrieve(query, k=k, filter_dict=filter_dict)

    def _format_results_sync(
            self,
            documents: List[Document],
    ) -> List[Dict[str, Any]]:
        """Format documents as dictionaries."""
        formatted = []
        for doc in documents:
            formatted.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page", 0),
            })
        return formatted

    async def retrieve_formatted(
            self,
            query: str,
            k: int = 4,
            filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents and return as formatted dictionaries.

        Args:
            query: User query string
            k: Number of documents to retrieve
            filter_dict: Optional metadata filters

        Returns:
            List of dictionaries with 'content', 'metadata', 'source', 'page'

        Example:
            >>> retriever = DocumentRetriever()
            >>> results = await retriever.retrieve_formatted("investment strategy")
            >>> for result in results:
            ...     print(f"Source: {result['source']}, Page: {result['page']}")
            ...     print(result['content'])
        """
        documents = await self.retrieve(query, k=k, filter_dict=filter_dict)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._format_results_sync,
            documents,
        )


# Convenience function for simple retrieval
async def retrieve_documents(
        query: str,
        k: int = 4,
        collection_name: str = "pdf_documents",
        filter_dict: Optional[Dict[str, Any]] = None,
) -> List[Document]:
    """
    Convenience function for simple document retrieval.

    Args:
        query: User query string
        k: Number of documents to retrieve
        collection_name: Vector store collection name
        filter_dict: Optional metadata filters

    Returns:
        List of relevant documents

    Example:
        >>> from app.services.retriever import retrieve_documents
        >>> docs = await retrieve_documents("What is LangChain?", k=3)
    """
    retriever = DocumentRetriever(collection_name=collection_name)
    return await retriever.retrieve(query, k=k, filter_dict=filter_dict)