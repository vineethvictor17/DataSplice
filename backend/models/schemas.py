"""
Pydantic models for API requests and responses.

Defines the structured output schema for query responses including
citations, subtopics, and confidence scores.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Reference to a specific chunk in the corpus."""
    chunk_id: str
    file: str
    page: int
    excerpt: Optional[str] = None


class Subtopic(BaseModel):
    """A thematic cluster of information with supporting citations."""
    title: str
    bullets: List[str]
    citations: List[Citation]


class QueryRequest(BaseModel):
    """User query request."""
    query: str
    top_k: Optional[int] = Field(default=12, ge=1, le=50)


class QueryResponse(BaseModel):
    """Structured response to a query with citations and confidence."""
    query: str
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    subtopics: List[Subtopic]
    citations_flat: List[Citation]
    raw: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
    """Response from document ingestion."""
    ok: bool
    added_chunks: int
    errors: List[str] = []


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    vector_db_ready: Optional[bool] = None


class StatsResponse(BaseModel):
    """Corpus statistics response."""
    chunk_count: int
    file_count: int
    files: List[str]


class ClearResponse(BaseModel):
    """Clear corpus response."""
    ok: bool
    message: str
    deleted_chunks: int

