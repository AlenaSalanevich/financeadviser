"""
Search API Endpoints
Handles document search and retrieval requests
"""
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.retriever import DocumentRetriever
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Request/Response Models
class RetrievalRequest(BaseModel):
    """Request model for document retrieval"""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    k: int = Field(4, description="Number of documents to retrieve", ge=1, le=20)
    source: Optional[str] = Field(None, description="Filter by source filename")


class DocumentResponse(BaseModel):
    """Response model for a single document"""
    content: str = Field(..., description="Document content")
    source: str = Field(..., description="Source filename")
    page: int = Field(..., description="Page number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RetrievalResponse(BaseModel):
    """Response model for retrieval results"""
    query: str = Field(..., description="Original query")
    documents: List[DocumentResponse] = Field(..., description="Retrieved documents")
    count: int = Field(..., description="Number of documents returned")


class RetrievalWithScoresResponse(BaseModel):
    """Response model for retrieval with scores"""
    query: str
    results: List[Dict[str, Any]]
    count: int


@router.post("/search", response_model=RetrievalResponse)
async def search_documents(request: RetrievalRequest):
    """
    Search for relevant documents based on query.

    Args:
        request: RetrievalRequest containing query and parameters

    Returns:
        RetrievalResponse with matching documents

    Example:
        POST /api/v1/retrieval/search
        {
            "query": "What is portfolio diversification?",
            "k": 5,
            "source": "investment_guide.pdf"
        }
    """
    try:
        logger.info("Received search request for query: '%s'", request.query)

        retriever = DocumentRetriever()

        filter_dict = None
        if request.source:
            filter_dict = {"source": request.source}

        documents = await retriever.retrieve(
            query=request.query,
            k=request.k,
            filter_dict=filter_dict,
        )

        # Format response
        doc_responses = [
            DocumentResponse(
                content=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                page=doc.metadata.get("page", 0),
                metadata=doc.metadata,
            )
            for doc in documents
        ]

        logger.info("Returning %d documents for query: '%s'", len(doc_responses), request.query)

        return RetrievalResponse(
            query=request.query,
            documents=doc_responses,
            count=len(doc_responses),
        )

    except Exception as e:
        logger.error("Error during document retrieval: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")


@router.get("/search", response_model=RetrievalResponse)
async def search_documents_get(
        query: str = Query(..., description="Search query", min_length=1),
        k: int = Query(4, description="Number of documents", ge=1, le=20),
        source: Optional[str] = Query(None, description="Filter by source"),
):
    """
    Search for relevant documents (GET method).

    Args:
        query: Search query string
        k: Number of documents to retrieve
        source: Optional source filename filter

    Returns:
        RetrievalResponse with matching documents

    Example:
        GET /api/v1/retrieval/search?query=machine%20learning&k=5
    """
    request = RetrievalRequest(query=query, k=k, source=source)
    return await search_documents(request)


@router.post("/search-with-scores", response_model=RetrievalWithScoresResponse)
async def search_with_scores(request: RetrievalRequest):
    """
    Search for documents with similarity scores.

    Args:
        request: RetrievalRequest

    Returns:
        Documents with relevance scores (lower = more similar)

    Example:
        POST /api/v1/retrieval/search-with-scores
        {
            "query": "risk management strategies",
            "k": 3
        }
    """
    try:
        logger.info("Received search with scores request: '%s'", request.query)

        retriever = DocumentRetriever()

        filter_dict = None
        if request.source:
            filter_dict = {"source": request.source}

        results = await retriever.retrieve_with_scores(
            query=request.query,
            k=request.k,
            filter_dict=filter_dict,
        )

        # Format results
        formatted_results = [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page", 0),
                "score": float(score),
                "metadata": doc.metadata,
            }
            for doc, score in results
        ]

        logger.info("Returning %d documents with scores", len(formatted_results))

        return RetrievalWithScoresResponse(
            query=request.query,
            results=formatted_results,
            count=len(formatted_results),
        )

    except Exception as e:
        logger.error("Error during scored retrieval: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")


@router.get("/health")
async def retrieval_health():
    """Check if retrieval service is operational"""
    try:
        # Test embeddings initialization
        retriever = DocumentRetriever()
        retriever._ensure_initialized()

        return {
            "status": "healthy",
            "service": "retrieval",
            "embeddings": "initialized",
            "vector_store": "connected",
        }
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")