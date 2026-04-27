"""
Financial Agent Service (Anthropic)
Orchestrates retrieval and LLM generation for summaries and recommendations
"""
from typing import List, Dict, Any, Optional

import anthropic
from langchain_core.documents import Document

from app.config import settings
from app.core.logging import get_logger
from data.prompts.v1.prompt import (
    format_context_for_prompt,
    get_summary_prompt,
    get_recommendations_prompt,
)
from app.services.retriever import DocumentRetriever

logger = get_logger(__name__)


class AnthropicFinancialAgent:
    """
    Financial advisory agent that combines retrieval and LLM generation.

    This agent:
    1. Retrieves relevant financial documents based on user query
    2. Formats context for LLM
    3. Generates summaries or recommendations using Anthropic Claude
    """

    def __init__(
            self,
            model: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 2000,
    ):
        """
        Initialize the financial agent.

        Args:
            model: Anthropic model to use (defaults to settings.anthropic_model_id)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        self.model = model or settings.anthropic_model_id
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not configured. "
                "Set it in your environment or .env file."
            )

        # Initialize retriever
        self.retriever = DocumentRetriever()

        # Initialize Anthropic async client
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        logger.info(
            "AnthropicFinancialAgent initialized (model=%s, temp=%.2f, max_tokens=%d)",
            self.model,
            self.temperature,
            self.max_tokens,
        )

    async def _retrieve_context(
            self,
            query: str,
            k: int = 5,
            source_filter: Optional[str] = None,
    ) -> List[Document]:
        """
        Retrieve relevant documents for the query.

        Args:
            query: User query
            k: Number of documents to retrieve
            source_filter: Optional source filename filter

        Returns:
            List of relevant documents
        """
        logger.info("Retrieving context for query: '%s' (k=%d)", query, k)

        filter_dict = None
        if source_filter:
            filter_dict = {"source": source_filter}

        documents = await self.retriever.retrieve(
            query=query,
            k=k,
            filter_dict=filter_dict,
        )

        logger.info("Retrieved %d documents", len(documents))
        return documents

    async def _generate_completion(
            self,
            system_prompt: str,
            user_message: str,
    ) -> str:
        """
        Generate completion using Anthropic Claude.

        Args:
            system_prompt: System instructions
            user_message: User message/query

        Returns:
            Generated response text
        """
        logger.debug("Generating completion with model: %s", self.model)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message},
                ],
            )

            content = response.content[0].text

            usage = response.usage
            logger.info(
                "Completion generated (tokens: %d input + %d output)",
                usage.input_tokens,
                usage.output_tokens,
            )

            return content

        except Exception as e:
            logger.error("Anthropic API error: %s", str(e), exc_info=True)
            raise

    async def generate_summary(
            self,
            query: str,
            k: int = 5,
            source_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate spending summary based on query.

        Args:
            query: User query about their spending
            k: Number of documents to retrieve for context
            source_filter: Optional filter by source document

        Returns:
            Dictionary containing:
                - summary: Generated summary text
                - documents_used: Number of documents used
                - sources: List of source documents
                - query: Original query
                - model: Model used for generation
        """
        logger.info("Generating summary for query: '%s'", query)

        documents = await self._retrieve_context(query, k, source_filter)

        if not documents:
            logger.warning("No documents found for query: '%s'", query)
            return {
                "summary": (
                    "I couldn't find any financial documents matching your query. "
                    "Please ensure you have uploaded relevant financial documents "
                    "(bank statements, receipts, transaction records) before requesting a summary."
                ),
                "documents_used": 0,
                "sources": [],
                "query": query,
                "model": self.model,
            }

        context_prompt = format_context_for_prompt(documents, query)
        system_prompt = get_summary_prompt(context_prompt)

        summary = await self._generate_completion(
            system_prompt=system_prompt,
            user_message=query,
        )

        sources = list(set(doc.metadata.get("source", "unknown") for doc in documents))

        logger.info("Summary generated successfully (%d documents used)", len(documents))

        return {
            "summary": summary,
            "documents_used": len(documents),
            "sources": sources,
            "query": query,
            "model": self.model,
        }

    async def generate_recommendations(
            self,
            query: str,
            k: int = 5,
            source_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate financial recommendations based on query.

        Args:
            query: User query about financial advice/recommendations
            k: Number of documents to retrieve for context
            source_filter: Optional filter by source document

        Returns:
            Dictionary containing:
                - recommendations: Generated recommendations text
                - documents_used: Number of documents used
                - sources: List of source documents
                - query: Original query
                - model: Model used for generation
        """
        logger.info("Generating recommendations for query: '%s'", query)

        documents = await self._retrieve_context(query, k, source_filter)

        if not documents:
            logger.warning("No documents found for query: '%s'", query)
            return {
                "recommendations": (
                    "I couldn't find any financial documents matching your query. "
                    "To provide personalized recommendations, please upload your financial documents "
                    "(bank statements, transaction records, expense reports) first."
                ),
                "documents_used": 0,
                "sources": [],
                "query": query,
                "model": self.model,
            }

        context_prompt = format_context_for_prompt(documents, query)
        system_prompt = get_recommendations_prompt(context_prompt)

        recommendations = await self._generate_completion(
            system_prompt=system_prompt,
            user_message=query,
        )

        sources = list(set(doc.metadata.get("source", "unknown") for doc in documents))

        logger.info("Recommendations generated successfully (%d documents used)", len(documents))

        return {
            "recommendations": recommendations,
            "documents_used": len(documents),
            "sources": sources,
            "query": query,
            "model": self.model,
        }

    async def generate_custom_analysis(
            self,
            query: str,
            analysis_type: str,
            k: int = 5,
            source_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate custom financial analysis.

        Args:
            query: User query
            analysis_type: Type of analysis ("summary" or "recommendations")
            k: Number of documents to retrieve
            source_filter: Optional source filter

        Returns:
            Analysis results dictionary
        """
        if analysis_type == "summary":
            return await self.generate_summary(query, k, source_filter)
        elif analysis_type == "recommendations":
            return await self.generate_recommendations(query, k, source_filter)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
