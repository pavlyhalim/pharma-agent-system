"""
Google Gemini service with grounding capabilities.

Uses the latest Gemini 2.5 Flash model with Google Search grounding
for enhanced, real-time information retrieval and reduced hallucinations.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from google import genai
from google.genai import types
import os
import logging
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service for Google Gemini API with grounding support.

    Features:
    - Gemini 2.5 Flash (1M context, fast, supports grounding)
    - Google Search grounding for real-time information
    - Citation extraction from grounding metadata
    - Structured output support
    """

    def __init__(self, api_key: Optional[str] = None, rate_limit_rpm: int = 14):
        """
        Initialize Gemini service with rate limiting.

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            rate_limit_rpm: Requests per minute limit (default 14, max 15 for gemini-2.5-flash-lite)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        # Rate limiting: Track requests per minute
        self.rate_limit_rpm = rate_limit_rpm
        self.request_times: deque = deque()  # Track timestamps of requests
        self.rate_limit_lock = asyncio.Lock()

        logger.info(f"Rate limiting set to {self.rate_limit_rpm} requests per minute")

        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not set. Gemini service will not be available.")
            self.client = None
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if Gemini service is available."""
        return self.client is not None

    async def _enforce_rate_limit(self):
        """
        Enforce rate limiting by tracking requests per minute.

        Implements sliding window rate limiting:
        - Removes requests older than 60 seconds
        - If at limit, waits until oldest request expires
        - Adds current request timestamp

        gemini-2.5-flash-lite limits:
        - 15 RPM (requests per minute)
        - 250K TPM (tokens per minute)
        - 1K RPD (requests per day)
        """
        async with self.rate_limit_lock:
            current_time = datetime.now()
            minute_ago = current_time - timedelta(seconds=60)

            # Remove requests older than 1 minute
            while self.request_times and self.request_times[0] < minute_ago:
                self.request_times.popleft()

            # If we're at the rate limit, wait until we can make another request
            if len(self.request_times) >= self.rate_limit_rpm:
                # Calculate how long to wait (oldest request + 60s - now)
                oldest_request = self.request_times[0]
                wait_until = oldest_request + timedelta(seconds=60)
                wait_seconds = (wait_until - current_time).total_seconds()

                if wait_seconds > 0:
                    logger.info(
                        f"Rate limit reached ({len(self.request_times)}/{self.rate_limit_rpm} RPM). "
                        f"Waiting {wait_seconds:.2f}s..."
                    )
                    await asyncio.sleep(wait_seconds + 0.1)  # Add 100ms buffer

                    # Remove the oldest request after waiting
                    self.request_times.popleft()

            # Record this request
            self.request_times.append(datetime.now())
            logger.debug(f"Rate limit status: {len(self.request_times)}/{self.rate_limit_rpm} RPM")

    async def _retry_with_exponential_backoff(
        self,
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> Any:
        """
        Retry a function with exponential backoff for rate limit errors.

        Implements exponential backoff strategy for Gemini API rate limits:
        - Gemini 2.5 Flash free tier: 10 RPM (requests per minute)
        - On 429 error, extracts retryDelay from error or uses exponential backoff
        - Retry delays: 1s, 2s, 4s, 8s, ...

        Args:
            func: Async function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff

        Returns:
            Result from successful function call

        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                error_str = str(e)

                # Check if it's a rate limit or service unavailable error (both should retry)
                is_retryable = any([
                    "429" in error_str,
                    "503" in error_str,
                    "RESOURCE_EXHAUSTED" in error_str,
                    "UNAVAILABLE" in error_str,
                    "overloaded" in error_str.lower(),
                    "Quota exceeded" in error_str.lower(),
                    "rate limit" in error_str.lower(),
                    "too many requests" in error_str.lower()
                ])

                if is_retryable:
                    if attempt < max_retries:
                        # Extract retry delay from error message if available
                        retry_delay = base_delay * (2 ** attempt)  # Exponential backoff

                        # Try to parse retryDelay from error message
                        if "retry in" in error_str.lower():
                            try:
                                # Extract number from "Please retry in 9.7211133s"
                                parts = error_str.lower().split("retry in")
                                if len(parts) > 1:
                                    delay_str = parts[1].strip().split("s")[0]
                                    parsed_delay = float(delay_str)
                                    retry_delay = max(retry_delay, parsed_delay)
                            except:
                                pass  # Use exponential backoff if parsing fails

                        logger.warning(
                            f"API error (attempt {attempt + 1}/{max_retries + 1}). "
                            f"Retrying in {retry_delay:.2f}s... Error: {error_str[:200]}"
                        )
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"API retries exhausted after {max_retries + 1} attempts. Error: {error_str[:300]}")
                        raise
                else:
                    # Not a rate limit error, raise immediately
                    logger.error(f"Gemini API error (non-rate-limit): {error_str[:500]}")
                    raise

        # Should not reach here, but raise last exception if we do
        raise last_exception

    async def generate_with_grounding(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate content with Google Search grounding and retry logic.

        Args:
            prompt: User prompt
            model: Gemini model to use (default: gemini-2.0-flash-exp)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum output tokens
            system_instruction: Optional system instruction

        Returns:
            Dictionary with text, citations, and grounding metadata
        """
        if not self.is_available():
            raise RuntimeError("Gemini service not available. Check GOOGLE_API_KEY.")

        # Enforce rate limiting before API call
        await self._enforce_rate_limit()

        # Configure grounding tool
        grounding_tool = types.Tool(google_search=types.GoogleSearch())

        # Build config
        config = types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction
        )

        # Wrap API call with retry logic
        async def _generate():
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=prompt,
                config=config
            )

            # Extract text (handle None case)
            text = ""
            if hasattr(response, 'text') and response.text is not None:
                text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to extract from candidates if text is None
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text += part.text
            
            # Extract grounding metadata
            grounding_metadata = self._extract_grounding_metadata(response)

            # Extract citations (handle None case)
            citations = self._extract_citations(grounding_metadata) or []

            logger.info(f"Gemini generated {len(text)} chars with {len(citations)} citations")
            
            # Log warning if empty response with grounding enabled
            if not text and grounding_metadata:
                logger.warning(f"Gemini returned empty text despite grounding enabled. "
                             f"Search queries: {grounding_metadata.get('web_search_queries', [])}")

            return {
                "text": text,
                "citations": citations,
                "grounding_metadata": grounding_metadata,
                "model": model
            }

        # Use retry wrapper for rate limit compliance
        result = await self._retry_with_exponential_backoff(_generate, max_retries=3)
        
        # If grounding returned empty text, try again WITHOUT grounding as fallback
        if not result["text"] or len(result["text"].strip()) < 50:
            logger.warning("Grounding returned empty/minimal text. Retrying WITHOUT grounding...")
            try:
                fallback_text = await self.generate_without_grounding(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_instruction=system_instruction
                )
                if fallback_text and len(fallback_text.strip()) > 50:
                    logger.info(f"Fallback without grounding succeeded: {len(fallback_text)} chars")
                    result["text"] = fallback_text
                    result["citations"] = []  # No citations without grounding
            except Exception as e:
                logger.error(f"Fallback without grounding also failed: {e}")
        
        return result

    async def generate_without_grounding(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate content without grounding (faster, no citations).

        Args:
            prompt: User prompt
            model: Gemini model to use
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            system_instruction: Optional system instruction

        Returns:
            Generated text
        """
        if not self.is_available():
            raise RuntimeError("Gemini service not available. Check GOOGLE_API_KEY.")

        # Enforce rate limiting before API call
        await self._enforce_rate_limit()

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction
        )

        # Wrap with retry logic for rate limit handling
        async def _generate():
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=prompt,
                config=config
            )

            # Extract text with better handling
            text = ""
            if hasattr(response, 'text') and response.text is not None:
                text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to extract from candidates if text is None
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text += part.text
            
            return text

        try:
            return await self._retry_with_exponential_backoff(_generate, max_retries=3)
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.0
    ) -> Any:
        """
        Generate structured output using JSON schema with retry logic.

        Args:
            prompt: User prompt
            response_schema: Pydantic model or JSON schema
            model: Gemini model to use
            temperature: Sampling temperature

        Returns:
            Parsed object matching schema
        """
        if not self.is_available():
            raise RuntimeError("Gemini service not available. Check GOOGLE_API_KEY.")

        # Enforce rate limiting before API call
        await self._enforce_rate_limit()

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=temperature
        )

        # Wrap API call with retry logic
        async def _generate():
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=prompt,
                config=config
            )
            return response.parsed if hasattr(response, 'parsed') else None

        # Use retry wrapper for rate limit compliance
        return await self._retry_with_exponential_backoff(_generate, max_retries=3)

    async def analyze_with_context(
        self,
        prompt: str,
        context_documents: List[str],
        model: str = "gemini-2.0-flash-exp",
        use_grounding: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze with both document context and optional web grounding.

        Args:
            prompt: Analysis prompt
            context_documents: List of context strings (e.g., abstracts)
            model: Gemini model
            use_grounding: Enable Google Search grounding

        Returns:
            Analysis results with citations
        """
        # Combine context and prompt
        full_prompt = "Context:\n\n"
        for i, doc in enumerate(context_documents[:10], 1):  # Limit to 10 docs
            full_prompt += f"Document {i}:\n{doc}\n\n"

        full_prompt += f"\nQuestion: {prompt}"

        if use_grounding:
            return await self.generate_with_grounding(
                prompt=full_prompt,
                model=model,
                temperature=0.1
            )
        else:
            text = await self.generate_without_grounding(
                prompt=full_prompt,
                model=model,
                temperature=0.1
            )
            return {"text": text, "citations": []}

    def _extract_grounding_metadata(self, response) -> Dict[str, Any]:
        """
        Extract grounding metadata from response.

        Returns:
            Dictionary with search queries, chunks, and supports
        """
        if not hasattr(response, 'grounding_metadata'):
            return {}

        metadata = response.grounding_metadata

        # Handle None metadata (known Gemini API issue)
        if metadata is None:
            logger.warning("Grounding metadata is None (known Gemini API issue)")
            return {}

        # Extract attributes with proper None handling
        # Gemini API sometimes returns None for these attributes even with grounding enabled
        web_search_queries = getattr(metadata, 'web_search_queries', None) or []
        grounding_chunks_raw = getattr(metadata, 'grounding_chunks', None) or []
        grounding_supports_raw = getattr(metadata, 'grounding_supports', None) or []

        return {
            "web_search_queries": web_search_queries,
            "grounding_chunks": [
                {
                    "uri": chunk.web.uri if hasattr(chunk, 'web') else None,
                    "title": chunk.web.title if hasattr(chunk, 'web') else None
                }
                for chunk in grounding_chunks_raw
            ],
            "grounding_supports": [
                {
                    "segment": {
                        "start_index": support.segment.start_index if hasattr(support, 'segment') else None,
                        "end_index": support.segment.end_index if hasattr(support, 'segment') else None,
                        "text": support.segment.text if hasattr(support, 'segment') else None
                    },
                    "grounding_chunk_indices": getattr(support, 'grounding_chunk_indices', None) or [],
                    "confidence_scores": getattr(support, 'confidence_scores', None) or []
                }
                for support in grounding_supports_raw
            ]
        }

    def _extract_citations(self, grounding_metadata: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract unique citations from grounding metadata.

        Returns:
            List of citations with title and URL
        """
        # Defensive handling: .get() can return None if key exists with None value
        chunks = grounding_metadata.get("grounding_chunks")

        # Safety check: ensure chunks is a valid list before iteration
        if not chunks or not isinstance(chunks, list):
            logger.debug("No valid grounding_chunks found in metadata")
            return []

        citations = []
        seen_uris = set()

        for chunk in chunks:
            # Ensure chunk is a dictionary before accessing keys
            if not isinstance(chunk, dict):
                logger.warning(f"Invalid chunk type: {type(chunk)}, expected dict")
                continue

            uri = chunk.get("uri")
            title = chunk.get("title")

            if uri and uri not in seen_uris:
                citations.append({
                    "title": title or "Untitled",
                    "url": uri
                })
                seen_uris.add(uri)

        return citations

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-2.0-flash-exp",
        use_grounding: bool = False
    ) -> Dict[str, Any]:
        """
        Multi-turn chat with optional grounding.

        Args:
            messages: List of {"role": "user"/"model", "content": "..."}
            model: Gemini model
            use_grounding: Enable Google Search grounding

        Returns:
            Response with text and optional citations
        """
        if not self.is_available():
            raise RuntimeError("Gemini service not available.")

        # Convert to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

        config = None
        if use_grounding:
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(tools=[grounding_tool])

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=contents,
                config=config
            )

            text = response.text if hasattr(response, 'text') else ""

            if use_grounding:
                grounding_metadata = self._extract_grounding_metadata(response)
                citations = self._extract_citations(grounding_metadata)
                return {"text": text, "citations": citations, "grounding_metadata": grounding_metadata}
            else:
                return {"text": text, "citations": []}

        except Exception as e:
            logger.error(f"Gemini chat failed: {e}")
            raise
