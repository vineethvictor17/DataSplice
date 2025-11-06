"""
LLM-based synthesis with structured JSON output.

Generates summaries with subtopics and citations using OpenAI's chat API.
"""

from typing import Dict, Any, List
import json

from openai import OpenAI

from backend.utils.config import settings
from backend.utils.logger import logger


# Initialize OpenAI client
_client = None


def get_openai_client() -> OpenAI:
    """Get or create OpenAI client instance."""
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment")
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


# JSON schema for structured output
SYNTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A concise 6-8 line prose summary answering the query"
        },
        "subtopics": {
            "type": "array",
            "description": "2-4 thematic subtopics with supporting points",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "bullets": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "citations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "string"},
                                "file": {"type": "string"},
                                "page": {"type": "integer"},
                                "excerpt": {"type": "string"}
                            },
                            "required": ["chunk_id", "file", "page", "excerpt"]
                        }
                    }
                },
                "required": ["title", "bullets", "citations"]
            }
        },
        "limitations": {
            "type": "string",
            "description": "Optional note on gaps or limitations in available evidence"
        }
    },
    "required": ["summary", "subtopics"]
}


def build_synthesis_prompt(
    query: str,
    clustered_chunks: Dict[int, List[Dict[str, Any]]]
) -> tuple[str, str]:
    """
    Build system and user prompts for LLM with query and clustered context.
    
    Args:
        query: User's question
        clustered_chunks: Chunks organized by cluster
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = """You are an expert research assistant that provides accurate, citation-backed summaries.

Your task is to answer questions based ONLY on the provided evidence. You must:
1. Generate a concise 6-8 line summary answering the query
2. Organize findings into 2-4 thematic subtopics
3. Include 2-4 bullet points per subtopic
4. Cite ALL sources using the exact chunk_id, file, page, and a relevant excerpt (20-50 words)
5. Only make claims that are directly supported by the evidence
6. Note any limitations if the evidence is incomplete or doesn't fully answer the query

Return ONLY valid JSON matching this structure:
{
  "summary": "6-8 line prose summary",
  "subtopics": [
    {
      "title": "Subtopic title",
      "bullets": ["Point 1", "Point 2"],
      "citations": [
        {"chunk_id": "doc_p1_c0", "file": "doc.pdf", "page": 1, "excerpt": "relevant quote"}
      ]
    }
  ],
  "limitations": "Optional note on gaps or limitations"
}"""

    # Build user prompt with evidence
    user_prompt = f"Query: {query}\n\n"
    user_prompt += "Evidence from the corpus:\n\n"
    
    # Format each cluster as a subtopic group
    for cluster_id, chunks in sorted(clustered_chunks.items()):
        user_prompt += f"--- Evidence Group {cluster_id + 1} ---\n"
        
        for i, chunk in enumerate(chunks, 1):
            chunk_id = chunk.get("chunk_id", "unknown")
            file = chunk.get("file", "unknown")
            page = chunk.get("page", "?")
            text = chunk.get("text", "")
            
            # Truncate very long chunks for the prompt
            if len(text) > 800:
                text = text[:800] + "..."
            
            user_prompt += f"\n[{i}] Chunk ID: {chunk_id}\n"
            user_prompt += f"    Source: {file}, Page {page}\n"
            user_prompt += f"    Text: {text}\n"
        
        user_prompt += "\n"
    
    user_prompt += "\nBased on this evidence, generate a comprehensive JSON response."
    
    return system_prompt, user_prompt


def synthesize_response(
    query: str,
    clustered_chunks: Dict[int, List[Dict[str, Any]]],
    model: str = None
) -> Dict[str, Any]:
    """
    Generate structured summary using LLM.
    
    Calls OpenAI with JSON mode to generate citation-backed summaries.
    
    Args:
        query: User's question
        clustered_chunks: Retrieved and clustered chunks
        model: LLM model name (default from settings)
        
    Returns:
        Parsed JSON response with summary, subtopics, citations, and metadata
        
    Raises:
        ValueError: If OpenAI API key not set
        Exception: If LLM call fails
    """
    model = model or settings.LLM_MODEL
    logger.info(f"Synthesizing response with {model}")
    
    if not clustered_chunks:
        logger.warning("No chunks provided for synthesis")
        return {
            "summary": "No relevant information found in the corpus.",
            "subtopics": [],
            "limitations": "No evidence available to answer this query.",
            "model": model,
            "usage": {}
        }
    
    try:
        # Get OpenAI client
        client = get_openai_client()
        
        # Build prompts
        system_prompt, user_prompt = build_synthesis_prompt(query, clustered_chunks)
        
        logger.info(f"Prompt length: ~{len(user_prompt)} chars")
        
        # Call OpenAI Chat API with JSON mode
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=2000   # Sufficient for structured response
        )
        
        # Extract response
        content = response.choices[0].message.content
        
        # Parse JSON
        try:
            parsed_response = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {content[:500]}...")
            raise ValueError(f"Invalid JSON from LLM: {e}")
        
        # Validate required fields
        if "summary" not in parsed_response:
            logger.warning("LLM response missing 'summary' field")
            parsed_response["summary"] = "Unable to generate summary."
        
        if "subtopics" not in parsed_response:
            logger.warning("LLM response missing 'subtopics' field")
            parsed_response["subtopics"] = []
        
        # Add metadata
        parsed_response["model"] = model
        parsed_response["usage"] = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        logger.info(
            f"Synthesis complete: {len(parsed_response.get('subtopics', []))} subtopics, "
            f"{response.usage.total_tokens} tokens used"
        )
        
        return parsed_response
        
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise


def extract_flat_citations(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract all citations into a flat list.
    
    Args:
        response: LLM synthesis response
        
    Returns:
        Deduplicated flat list of citations
    """
    citations_flat = []
    seen = set()
    
    for subtopic in response.get("subtopics", []):
        for citation in subtopic.get("citations", []):
            chunk_id = citation.get("chunk_id")
            if chunk_id and chunk_id not in seen:
                citations_flat.append({
                    "chunk_id": chunk_id,
                    "file": citation.get("file"),
                    "page": citation.get("page")
                })
                seen.add(chunk_id)
    
    return citations_flat

