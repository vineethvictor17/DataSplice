"""
Generate embeddings using OpenAI's embedding API.

Handles batching and rate limiting for efficient embedding generation.
"""

from typing import List
import time

from openai import OpenAI, OpenAIError, RateLimitError

from backend.utils.config import settings
from backend.utils.logger import logger


# Initialize OpenAI client
_client = None


def get_openai_client() -> OpenAI:
    """
    Get or create the OpenAI client instance.
    
    Returns:
        Configured OpenAI client
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    global _client
    
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not set. Please add it to your .env file."
            )
        
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI client initialized")
    
    return _client


def embed_texts(
    texts: List[str],
    batch_size: int = 100,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenAI API.
    
    Processes texts in batches to handle rate limits and large datasets efficiently.
    Includes retry logic for transient failures.
    
    Args:
        texts: List of text strings to embed
        batch_size: Number of texts per API call (OpenAI allows up to 2048)
        max_retries: Maximum number of retry attempts for failed batches
        retry_delay: Initial delay between retries (doubles each retry)
        
    Returns:
        List of embedding vectors (each is list of floats) in same order as input
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set
        OpenAIError: If API calls fail after all retries
    """
    if not texts:
        return []
    
    # Filter out empty texts and track their indices
    valid_texts = []
    valid_indices = []
    for i, text in enumerate(texts):
        if text and text.strip():
            valid_texts.append(text.strip())
            valid_indices.append(i)
        else:
            logger.warning(f"Skipping empty text at index {i}")
    
    if not valid_texts:
        logger.warning("All texts are empty, returning empty list")
        return []
    
    logger.info(
        f"Generating embeddings for {len(valid_texts)} texts "
        f"using model {settings.EMBED_MODEL}"
    )
    
    client = get_openai_client()
    all_embeddings = []
    
    # Process texts in batches
    total_batches = (len(valid_texts) + batch_size - 1) // batch_size
    
    for batch_idx in range(0, len(valid_texts), batch_size):
        batch_texts = valid_texts[batch_idx:batch_idx + batch_size]
        current_batch_num = (batch_idx // batch_size) + 1
        
        logger.info(
            f"Processing batch {current_batch_num}/{total_batches} "
            f"({len(batch_texts)} texts)"
        )
        
        # Retry logic for this batch
        for attempt in range(max_retries):
            try:
                # Call OpenAI embeddings API
                response = client.embeddings.create(
                    model=settings.EMBED_MODEL,
                    input=batch_texts,
                    encoding_format="float"
                )
                
                # Extract embeddings from response
                # Response.data is a list of embedding objects, sorted by index
                batch_embeddings = [item.embedding for item in response.data]
                
                # Verify we got the right number of embeddings
                if len(batch_embeddings) != len(batch_texts):
                    raise ValueError(
                        f"Expected {len(batch_texts)} embeddings, "
                        f"got {len(batch_embeddings)}"
                    )
                
                all_embeddings.extend(batch_embeddings)
                
                # Log token usage if available
                if hasattr(response, 'usage') and response.usage:
                    logger.info(
                        f"Batch {current_batch_num} complete. "
                        f"Tokens used: {response.usage.total_tokens}"
                    )
                
                # Success - break retry loop
                break
                
            except RateLimitError as e:
                wait_time = retry_delay * (2 ** attempt)
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Rate limit hit on batch {current_batch_num}. "
                        f"Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Rate limit error after {max_retries} attempts: {e}")
                    raise
                    
            except OpenAIError as e:
                wait_time = retry_delay * (2 ** attempt)
                if attempt < max_retries - 1:
                    logger.warning(
                        f"API error on batch {current_batch_num}: {e}. "
                        f"Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error after {max_retries} attempts: {e}")
                    raise
                    
            except Exception as e:
                logger.error(f"Unexpected error on batch {current_batch_num}: {e}")
                raise
        
        # Small delay between batches to be nice to the API
        if current_batch_num < total_batches:
            time.sleep(0.1)
    
    logger.info(
        f"Successfully generated {len(all_embeddings)} embeddings "
        f"(dimension: {len(all_embeddings[0]) if all_embeddings else 0})"
    )
    
    # Reconstruct full list with None for empty inputs
    final_embeddings = [None] * len(texts)
    for i, embedding in zip(valid_indices, all_embeddings):
        final_embeddings[i] = embedding
    
    # Filter out None values (empty texts)
    final_embeddings = [e for e in final_embeddings if e is not None]
    
    return final_embeddings


def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a single query string.
    
    Args:
        query: Query text
        
    Returns:
        Embedding vector
    """
    embeddings = embed_texts([query])
    return embeddings[0] if embeddings else []

