"""
Financial Agent Service
Orchestrates retrieval and LLM generation for summaries and recommendations
"""
import asyncio
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document
from openai import AsyncOpenAI

from app.config import settings
from app.core.logging import get_logger
from data.prompts.v1.prompt import (
    format_context_for_prompt,
    get_summary_prompt,
    get_recommendations_prompt,
)
from app.services.retriever import DocumentRetriever

logger = get_logger(__name__)


class FinancialAgent:
    """
    Financial advisory agent that combines retrieval and LLM generation.

    This agent:
    1. Retrieves relevant financial documents based on user query
    2. Formats context for LLM
    3. Generates summaries or recommendations using OpenAI
    """
    # Models that use max_completion_tokens instead of max_tokens
    NEW_API_MODELS = {
        "gpt-4o",
        "gpt-4o-2024-08-06",
        "gpt-4o-mini",
        "gpt-4o-mini-2024-07-18",
        "o1-preview",
        "o1-mini",
        "o1",
    }

    def __init__(
            self,
            model: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 2000,
    ):
        """
        Initialize the financial agent.

        Args:
            model: OpenAI model to use (defaults to settings.model_id)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        # Use model from settings if not provided
        self.model = model or settings.model_id
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Validate OpenAI API key
        if not settings.open_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. "
                "Set it in your environment or .env file."
            )

        # Initialize retriever
        self.retriever = DocumentRetriever()

        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=settings.open_api_key)

        logger.info(
            "FinancialAgent initialized (model=%s, temp=%.2f, max_tokens=%d)",
            self.model,
            self.temperature,
            self.max_tokens,
        )

    def _uses_new_api(self) -> bool:
        """
        Check if the model uses the new API parameters.

        Returns:
            True if model uses max_completion_tokens, False if max_tokens
        """
        # Check if model name starts with any of the new API models
        model_lower = self.model.lower()
        return any(
            model_lower.startswith(new_model.lower())
            for new_model in self.NEW_API_MODELS
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
        Generate completion using OpenAI.

        Args:
            system_prompt: System instructions
            user_message: User message/query

        Returns:
            Generated response text
        """
        logger.debug("Generating completion with model: %s", self.model)

        try:
            # Prepare common parameters
            common_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": self.temperature,
            }

            # Add the appropriate token limit parameter based on model
            if self._uses_new_api():
                logger.debug("Using max_completion_tokens for model: %s", self.model)
                common_params["max_completion_tokens"] = self.max_tokens
            else:
                logger.debug("Using max_tokens for model: %s", self.model)
                common_params["max_tokens"] = self.max_tokens

            # Make API call
            response = await self.client.chat.completions.create(**common_params)

            content = response.choices[0].message.content

            # Log token usage
            usage = response.usage
            logger.info(
                "Completion generated (tokens: %d prompt + %d completion = %d total)",
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )

            return content

        except Exception as e:
            logger.error("OpenAI API error: %s", str(e), exc_info=True)
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

        Example:
            >>> agent = FinancialAgent()
            >>> result = await agent.generate_summary(
            ...     "Summarize my spending in January 2024"
            ... )
            >>> print(result['summary'])
        """
        logger.info("Generating summary for query: '%s'", query)

        # Retrieve relevant documents
        documents = await self._retrieve_context(query, k, source_filter)

        if not documents:
            logger.warning("No documents found for query: '%s'", query)
            # IMPORTANT: Always return 'model' field
            return {
                "summary": (
                    "I couldn't find any financial documents matching your query. "
                    "Please ensure you have uploaded relevant financial documents "
                    "(bank statements, receipts, transaction records) before requesting a summary."
                ),
                "documents_used": 0,
                "sources": [],
                "query": query,
                "model": self.model,  # ✓ Must be here
            }

        # Format context
        context_prompt = format_context_for_prompt(documents, query)
        system_prompt = get_summary_prompt(context_prompt)

        # Generate summary
        summary = await self._generate_completion(
            system_prompt=system_prompt,
            user_message=query,
        )

        # Extract unique sources
        sources = list(set(doc.metadata.get("source", "unknown") for doc in documents))

        logger.info("Summary generated successfully (%d documents used)", len(documents))

        # IMPORTANT: Always return 'model' field
        return {
            "summary": summary,
            "documents_used": len(documents),
            "sources": sources,
            "query": query,
            "model": self.model,  # ✓ Must be here
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

        Example:
            >>> agent = FinancialAgent()
            >>> result = await agent.generate_recommendations(
            ...     "How can I reduce my monthly spending?"
            ... )
            >>> print(result['recommendations'])
        """
        logger.info("Generating recommendations for query: '%s'", query)

        # Retrieve relevant documents
        documents = await self._retrieve_context(query, k, source_filter)

        if not documents:
            logger.warning("No documents found for query: '%s'", query)
            # IMPORTANT: Always return 'model' field
            return {
                "recommendations": (
                    "I couldn't find any financial documents matching your query. "
                    "To provide personalized recommendations, please upload your financial documents "
                    "(bank statements, transaction records, expense reports) first."
                ),
                "documents_used": 0,
                "sources": [],
                "query": query,
                "model": self.model,  # ✓ Must be here
            }

        # Format context
        context_prompt = format_context_for_prompt(documents, query)
        system_prompt = get_recommendations_prompt(context_prompt)

        # Generate recommendations
        recommendations = await self._generate_completion(
            system_prompt=system_prompt,
            user_message=query,
        )

        # Extract unique sources
        sources = list(set(doc.metadata.get("source", "unknown") for doc in documents))

        logger.info("Recommendations generated successfully (%d documents used)", len(documents))

        # IMPORTANT: Always return 'model' field
        return {
            "recommendations": recommendations,
            "documents_used": len(documents),
            "sources": sources,
            "query": query,
            "model": self.model,  # ✓ Must be here
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