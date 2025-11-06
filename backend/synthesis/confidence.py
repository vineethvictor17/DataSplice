"""
Confidence scoring for query responses.

Computes confidence based on evidence coherence and source diversity.
"""

from typing import Dict, Any, List
import math

from backend.utils.logger import logger


def count_distinct_sources(citations: List[Dict[str, Any]]) -> int:
    """
    Count unique source files in citations.
    
    Args:
        citations: List of citations
        
    Returns:
        Number of distinct files
    """
    files = set(c.get("file") for c in citations if c.get("file"))
    return len(files)


def compute_coverage_score(
    n_citations: int,
    n_subtopics: int,
    expected_min_citations: int = 4
) -> float:
    """
    Score based on citation count and subtopic coverage.
    
    Args:
        n_citations: Total number of citations
        n_subtopics: Number of subtopics
        expected_min_citations: Minimum expected citations
        
    Returns:
        Coverage score [0, 1]
    """
    if n_citations == 0:
        return 0.0
    
    # Reward meeting minimum threshold
    citation_score = min(n_citations / expected_min_citations, 1.0)
    
    # Reward balanced subtopic distribution
    balance_score = min(n_subtopics / 3.0, 1.0)
    
    return (citation_score * 0.7 + balance_score * 0.3)


def compute_diversity_score(n_distinct_sources: int, max_expected: int = 5) -> float:
    """
    Score based on number of distinct source documents.
    
    Args:
        n_distinct_sources: Number of unique files cited
        max_expected: Expected number of sources for max score
        
    Returns:
        Diversity score [0, 1]
    """
    if n_distinct_sources == 0:
        return 0.0
    
    # Logarithmic scaling to reward diversity
    return min(math.log(n_distinct_sources + 1) / math.log(max_expected + 1), 1.0)


def calculate_confidence(
    response: Dict[str, Any],
    citations_flat: List[Dict[str, Any]]
) -> float:
    """
    Calculate overall confidence score for a query response.
    
    Combines coverage and diversity heuristics to estimate reliability.
    
    Args:
        response: LLM synthesis response with subtopics
        citations_flat: Flat list of all citations
        
    Returns:
        Confidence score [0, 1]
        
    TODO: Enhance confidence calculation
    - Consider retrieval scores/distances from vector search
    - Penalize if LLM indicates limitations
    - Adjust for query complexity
    - Consider semantic coherence of retrieved chunks
    
    Current heuristic:
    - Coverage: sufficient citations across subtopics (40% weight)
    - Diversity: multiple distinct sources (40% weight)
    - Baseline: presence of any evidence (20% weight)
    """
    n_citations = len(citations_flat)
    n_subtopics = len(response.get("subtopics", []))
    n_sources = count_distinct_sources(citations_flat)
    
    # No evidence → low confidence
    if n_citations == 0:
        return 0.1
    
    # Component scores
    coverage = compute_coverage_score(n_citations, n_subtopics)
    diversity = compute_diversity_score(n_sources)
    
    # Weighted combination
    confidence = (
        coverage * 0.4 +
        diversity * 0.4 +
        0.2  # baseline for having any evidence
    )
    
    # Penalize if limitations noted
    if response.get("limitations"):
        confidence *= 0.9
    
    # Clamp to [0, 1]
    confidence = max(0.0, min(1.0, confidence))
    
    logger.info(
        f"Confidence: {confidence:.2f} "
        f"(citations={n_citations}, sources={n_sources}, subtopics={n_subtopics})"
    )
    
    return confidence


def get_confidence_label(score: float) -> str:
    """
    Convert numeric confidence to categorical label.
    
    Args:
        score: Confidence score [0, 1]
        
    Returns:
        "Low", "Medium", or "High"
    """
    if score < 0.4:
        return "Low"
    elif score < 0.7:
        return "Medium"
    else:
        return "High"

