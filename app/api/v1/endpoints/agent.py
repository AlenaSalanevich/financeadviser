"""
Financial Agent API Endpoints
Provides summary and recommendation generation
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.agent import FinancialAgent

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AgentRequest(BaseModel):
    """Base request model for agent operations"""
    query: str = Field(
        ...,
        description="Your question or request about financial data",
        min_length=5,
        max_length=500,
        examples=[
            "Summarize my spending for the last month",
            "What are my biggest expenses?",
            "How can I save money on groceries?",
        ]
    )
    k: int = Field(
        5,
        description="Number of relevant documents to retrieve for context",
        ge=1,
        le=20,
    )
    source: Optional[str] = Field(
        None,
        description="Filter analysis to specific document (e.g., 'statement_jan_2024.pdf')",
    )


class SummaryResponse(BaseModel):
    """Response model for spending summary"""
    summary: str = Field(..., description="Generated spending summary")
    query: str = Field(..., description="Original user query")
    documents_used: int = Field(..., description="Number of documents analyzed")
    sources: list[str] = Field(..., description="Source documents used")
    model: str = Field(default="unknown", description="AI model used for generation")

    model_config = {
        "json_schema_extra": {
            "example": {
                "summary": "# Executive Summary\n\nYour January spending totaled $3,456.78...",
                "query": "Summarize my January spending",
                "documents_used": 5,
                "sources": ["bank_statement_jan_2024.pdf"],
                "model": "gpt-4o-mini"
            }
        }
    }


class RecommendationsResponse(BaseModel):
    """Response model for financial recommendations"""
    recommendations: str = Field(..., description="Generated recommendations")
    query: str = Field(..., description="Original user query")
    documents_used: int = Field(..., description="Number of documents analyzed")
    sources: list[str] = Field(..., description="Source documents used")
    model: str = Field(..., description="AI model used for generation")

    model_config = {
        "json_schema_extra": {
            "example": {
                "recommendations": "# Financial Health Overview\n\nBased on your spending patterns...",
                "query": "How can I reduce my spending?",
                "documents_used": 5,
                "sources": ["bank_statement_jan_2024.pdf", "receipts_jan_2024.pdf"],
                "model": "gpt-4o-mini"
            }
        }
    }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate spending summary",
    description=(
            "Analyze your financial documents and generate a comprehensive spending summary.\n\n"
            "## What You Get\n"
            "- Executive overview of your spending\n"
            "- Detailed breakdown by category\n"
            "- Notable patterns and observations\n"
            "- Time-based analysis (if applicable)\n"
            "- Key financial statistics\n\n"
            "## How It Works\n"
            "1. Your query is used to retrieve relevant financial documents\n"
            "2. AI analyzes transaction patterns and spending categories\n"
            "3. Generates structured summary with actionable insights\n\n"
            "## Example Queries\n"
            "- \"Summarize my spending for January 2024\"\n"
            "- \"What did I spend on groceries last month?\"\n"
            "- \"Show me my restaurant expenses\"\n"
            "- \"Analyze my subscription services\""
    ),
    responses={
        200: {
            "description": "Summary generated successfully",
        },
        400: {
            "description": "Invalid request parameters",
        },
        500: {
            "description": "Server error during summary generation",
        },
    },
)
async def generate_summary(request: AgentRequest) -> SummaryResponse:
    """
    Generate AI-powered spending summary.

    Analyzes your financial documents using advanced AI to provide:
    - Comprehensive spending breakdown
    - Category-wise analysis
    - Pattern recognition
    - Temporal trends
    - Key insights

    Args:
        request: Summary generation request

    Returns:
        Structured spending summary with insights
    """
    try:
        logger.info("Summary request received: '%s'", request.query)

        # Initialize agent (uses model from settings)
        agent = FinancialAgent()

        # Generate summary
        result = await agent.generate_summary(
            query=request.query,
            k=request.k,
            source_filter=request.source,
        )

        logger.info("Summary generated successfully for query: '%s'", request.query)

        return SummaryResponse(**result)

    except Exception as e:
        logger.error("Error generating summary: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}",
        )


@router.get(
    "/summary",
    response_model=SummaryResponse,
    summary="Generate spending summary (GET)",
    description="Generate spending summary using GET method for simple queries.",
)
async def generate_summary_get(
        query: str = Query(
            ...,
            description="Your question about spending",
            min_length=5,
            max_length=500,
        ),
        k: int = Query(5, description="Number of documents to analyze", ge=1, le=20),
        source: Optional[str] = Query(None, description="Filter by source document"),
) -> SummaryResponse:
    """Generate spending summary (GET method)."""
    request = AgentRequest(query=query, k=k, source=source)
    return await generate_summary(request)


@router.post(
    "/recommendations",
    response_model=RecommendationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate financial recommendations",
    description=(
            "Get personalized financial recommendations based on your spending patterns.\n\n"
            "## What You Get\n"
            "- Financial health assessment\n"
            "- Prioritized recommendations (HIGH/MEDIUM/LOW)\n"
            "- Specific action steps for each recommendation\n"
            "- Estimated savings potential\n"
            "- Quick wins for immediate impact\n"
            "- Long-term optimization strategies\n\n"
            "## How It Works\n"
            "1. AI retrieves and analyzes your financial documents\n"
            "2. Identifies spending patterns and optimization opportunities\n"
            "3. Generates prioritized, actionable recommendations\n"
            "4. Calculates potential savings and benefits\n\n"
            "## Example Queries\n"
            "- \"How can I reduce my monthly expenses?\"\n"
            "- \"What subscriptions should I cancel?\"\n"
            "- \"Help me optimize my grocery spending\"\n"
            "- \"Where can I save money?\"\n"
            "- \"Analyze my entertainment expenses\""
    ),
    responses={
        200: {
            "description": "Recommendations generated successfully",
        },
        400: {
            "description": "Invalid request parameters",
        },
        500: {
            "description": "Server error during recommendation generation",
        },
    },
)
async def generate_recommendations(request: AgentRequest) -> RecommendationsResponse:
    """
    Generate AI-powered financial recommendations.

    Provides personalized, actionable advice including:
    - Spending optimization opportunities
    - Subscription management suggestions
    - Budget reallocation recommendations
    - Quick wins for immediate savings
    - Long-term financial strategies

    Args:
        request: Recommendations generation request

    Returns:
        Prioritized recommendations with action steps
    """
    try:
        logger.info("Recommendations request received: '%s'", request.query)

        # Initialize agent (uses model from settings)
        agent = FinancialAgent()

        # Generate recommendations
        result = await agent.generate_recommendations(
            query=request.query,
            k=request.k,
            source_filter=request.source,
        )

        logger.info("Recommendations generated successfully for query: '%s'", request.query)

        return RecommendationsResponse(**result)

    except Exception as e:
        logger.error("Error generating recommendations: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}",
        )


@router.get(
    "/recommendations",
    response_model=RecommendationsResponse,
    summary="Generate financial recommendations (GET)",
    description="Generate recommendations using GET method for simple queries.",
)
async def generate_recommendations_get(
        query: str = Query(
            ...,
            description="Your question about financial optimization",
            min_length=5,
            max_length=500,
        ),
        k: int = Query(5, description="Number of documents to analyze", ge=1, le=20),
        source: Optional[str] = Query(None, description="Filter by source document"),
) -> RecommendationsResponse:
    """Generate financial recommendations (GET method)."""
    request = AgentRequest(query=query, k=k, source=source)
    return await generate_recommendations(request)


@router.get(
    "/health",
    summary="Agent service health check",
    description=(
            "Check if the financial agent service is operational.\n\n"
            "Verifies:\n"
            "- Agent can be initialized\n"
            "- OpenAI API connection is working\n"
            "- Retrieval service is accessible\n"
            "- All required configurations are present"
    ),
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "agent",
                        "openai": "connected",
                        "retrieval": "accessible",
                        "model": "gpt-4o-mini"
                    }
                }
            }
        },
        503: {
            "description": "Service is unhealthy",
        }
    },
)
async def agent_health():
    """
    Health check for financial agent service.

    Validates:
    - Agent initialization
    - OpenAI API access
    - Retrieval service connection
    - Required configuration

    Returns:
        Health status information

    Raises:
        HTTPException: 503 if service is unhealthy
    """
    try:
        # Try initializing agent (tests OpenAI key, retrieval service, etc.)
        agent = FinancialAgent()

        # Verify retrieval service
        agent.retriever._ensure_initialized()

        logger.debug("Agent health check passed")

        return {
            "status": "healthy",
            "service": "agent",
            "openai": "connected",
            "retrieval": "accessible",
            "model": agent.model,
            "temperature": agent.temperature,
        }

    except Exception as e:
        logger.error("Agent health check failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}",
        )