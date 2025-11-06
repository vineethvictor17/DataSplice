"""
Chunk clustering and fusion for improved context.

Clusters retrieved chunks into subtopics and deduplicates similar content.
"""

from typing import List, Dict, Any
from collections import defaultdict

import numpy as np
from sklearn.cluster import KMeans

from backend.utils.config import settings
from backend.utils.logger import logger


def cluster_chunks(
    chunks: List[Dict[str, Any]],
    n_clusters: int = None
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Cluster chunks into thematic groups using K-Means on embeddings.
    
    Groups similar chunks together to form coherent subtopics.
    
    Args:
        chunks: Retrieved chunks with embeddings and metadata
        n_clusters: Number of clusters (default from settings.CLUSTERS)
        
    Returns:
        Dictionary mapping cluster_id -> list of chunks
    """
    n_clusters = n_clusters or settings.CLUSTERS
    
    if not chunks:
        return {}
    
    # Handle case where we have fewer chunks than requested clusters
    n_clusters = min(n_clusters, len(chunks))
    
    logger.info(f"Clustering {len(chunks)} chunks into {n_clusters} groups")
    
    # If only one cluster needed or only one chunk, return all in one cluster
    if n_clusters == 1 or len(chunks) == 1:
        return {0: chunks}
    
    try:
        # Extract embeddings from chunks
        # Embeddings should be stored in the chunk dict from vector store query
        embeddings = []
        for chunk in chunks:
            if "embedding" in chunk and chunk["embedding"]:
                embeddings.append(chunk["embedding"])
            else:
                # Fallback: if no embedding stored, we can't cluster properly
                logger.warning(f"Chunk {chunk.get('chunk_id')} missing embedding")
                # Return all chunks in one cluster
                return {0: chunks}
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings)
        
        # Perform K-Means clustering
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
            max_iter=300
        )
        
        cluster_labels = kmeans.fit_predict(embeddings_array)
        
        # Group chunks by cluster
        clustered = defaultdict(list)
        for chunk, label in zip(chunks, cluster_labels):
            clustered[int(label)].append(chunk)
        
        # Log cluster sizes
        cluster_sizes = {k: len(v) for k, v in clustered.items()}
        logger.info(f"Clustering complete. Cluster sizes: {cluster_sizes}")
        
        return dict(clustered)
        
    except Exception as e:
        logger.error(f"Clustering failed: {e}. Returning all chunks in single cluster.")
        return {0: chunks}


def deduplicate_chunks(
    chunks: List[Dict[str, Any]],
    threshold: float = 0.95
) -> List[Dict[str, Any]]:
    """
    Remove highly similar chunks within a cluster.
    
    Uses cosine similarity on embeddings to detect near-duplicates.
    Keeps the chunk with higher similarity score to the query.
    
    Args:
        chunks: List of chunks to deduplicate
        threshold: Similarity threshold (0-1) for considering duplicates
        
    Returns:
        Deduplicated list of chunks, preserving order by relevance
    """
    if len(chunks) <= 1:
        return chunks
    
    logger.info(f"Deduplicating {len(chunks)} chunks (threshold: {threshold})")
    
    try:
        # Extract embeddings
        embeddings = []
        for chunk in chunks:
            if "embedding" in chunk and chunk["embedding"]:
                embeddings.append(np.array(chunk["embedding"]))
            else:
                # If no embedding, can't deduplicate properly
                logger.warning("Missing embeddings for deduplication")
                return chunks
        
        # Track which chunks to keep
        keep_indices = []
        
        for i in range(len(chunks)):
            # Check if this chunk is too similar to any already kept chunk
            is_duplicate = False
            
            for j in keep_indices:
                # Compute cosine similarity between embeddings
                similarity = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )
                
                if similarity > threshold:
                    # This chunk is too similar to an already kept chunk
                    is_duplicate = True
                    logger.debug(
                        f"Chunk {i} is duplicate of {j} "
                        f"(similarity: {similarity:.3f})"
                    )
                    break
            
            if not is_duplicate:
                keep_indices.append(i)
        
        # Keep only non-duplicate chunks
        deduplicated = [chunks[i] for i in keep_indices]
        
        logger.info(
            f"Deduplication complete: {len(chunks)} -> {len(deduplicated)} chunks "
            f"({len(chunks) - len(deduplicated)} duplicates removed)"
        )
        
        return deduplicated
        
    except Exception as e:
        logger.error(f"Deduplication failed: {e}. Returning original chunks.")
        return chunks


def cap_chunks_per_cluster(
    clustered: Dict[int, List[Dict[str, Any]]],
    max_per_cluster: int = 3
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Limit the number of chunks per cluster.
    
    Args:
        clustered: Dictionary of cluster_id -> chunks
        max_per_cluster: Maximum chunks to keep per cluster
        
    Returns:
        Capped dictionary of clusters
    """
    capped = {}
    for cluster_id, chunks in clustered.items():
        # Keep top chunks by score (assuming sorted by relevance)
        capped[cluster_id] = chunks[:max_per_cluster]
    
    return capped


def fuse_retrieved_chunks(
    chunks: List[Dict[str, Any]],
    n_clusters: int = None,
    max_per_cluster: int = 3
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Apply fusion pipeline: cluster, deduplicate, and cap chunks.
    
    Args:
        chunks: Retrieved chunks from vector store
        n_clusters: Number of thematic clusters
        max_per_cluster: Maximum chunks per cluster
        
    Returns:
        Processed clusters ready for synthesis
        
    Pipeline:
    1. Cluster chunks into n_clusters groups
    2. Deduplicate within each cluster
    3. Cap to max_per_cluster per cluster
    """
    if not chunks:
        return {}
    
    # Cluster into subtopics
    clustered = cluster_chunks(chunks, n_clusters)
    
    # Deduplicate within each cluster
    for cluster_id in clustered:
        clustered[cluster_id] = deduplicate_chunks(clustered[cluster_id])
    
    # Cap chunks per cluster
    clustered = cap_chunks_per_cluster(clustered, max_per_cluster)
    
    logger.info(f"Fusion complete: {len(clustered)} clusters")
    return clustered

