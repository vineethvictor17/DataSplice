"""
ChromaDB vector store operations.

Manages persistent storage and retrieval of document embeddings.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.utils.config import settings
from backend.utils.logger import logger


class VectorStore:
    """
    Wrapper for ChromaDB operations.
    
    Handles collection management, upsert, and similarity search.
    """
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize ChromaDB client with persistent storage.
        
        Args:
            persist_directory: Path to persist vector data
        """
        self.persist_directory = persist_directory or settings.VECTOR_DB_PATH
        
        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection = None
        logger.info(f"ChromaDB client initialized at {self.persist_directory}")
    
    def get_or_create_collection(self, name: str = "datasplice_docs"):
        """
        Get existing collection or create new one.
        
        Uses cosine similarity for semantic search.
        
        Args:
            name: Collection name
            
        Returns:
            Collection object
        """
        try:
            self.collection = self.client.get_or_create_collection(
                name=name,
                metadata={
                    "hnsw:space": "cosine",  # Use cosine similarity
                    "description": "DataSplice document chunks with embeddings"
                }
            )
            
            count = self.collection.count()
            logger.info(f"Collection '{name}' ready with {count} documents")
            
            return self.collection
            
        except Exception as e:
            logger.error(f"Failed to get/create collection: {e}")
            raise
    
    def upsert_chunks(
        self,
        chunks: List[Any],
        embeddings: List[List[float]]
    ) -> int:
        """
        Insert or update chunks with embeddings in the vector store.
        
        Args:
            chunks: List of Chunk objects
            embeddings: Corresponding embedding vectors
            
        Returns:
            Number of chunks upserted
            
        Raises:
            ValueError: If chunks and embeddings lengths don't match
            Exception: If upsert operation fails
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized. Call get_or_create_collection() first.")
        
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) count mismatch"
            )
        
        if not chunks:
            logger.warning("No chunks to upsert")
            return 0
        
        logger.info(f"Upserting {len(chunks)} chunks to vector store")
        
        try:
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            
            for chunk, embedding in zip(chunks, embeddings):
                # Generate unique ID
                chunk_id = chunk.get_id()
                ids.append(chunk_id)
                
                # Document text
                documents.append(chunk.text)
                
                # Metadata (ChromaDB requires all values to be simple types)
                metadata = {
                    "file": chunk.file,
                    "page": int(chunk.page),
                    "chunk_index": int(chunk.chunk_index),
                    "token_estimate": chunk.metadata.get("token_estimate", 0),
                    "char_count": chunk.metadata.get("char_count", 0),
                }
                
                # Add optional metadata fields
                if "split_type" in chunk.metadata:
                    metadata["split_type"] = chunk.metadata["split_type"]
                
                metadatas.append(metadata)
            
            # ChromaDB has a batch size limit, so we'll chunk if needed
            batch_size = 5000  # Conservative batch size
            total_upserted = 0
            
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                batch_documents = documents[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                
                logger.info(f"Upserting batch {i//batch_size + 1} ({len(batch_ids)} items)")
                
                # Upsert to ChromaDB
                self.collection.upsert(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_documents,
                    metadatas=batch_metadatas
                )
                
                total_upserted += len(batch_ids)
            
            logger.info(f"Successfully upserted {total_upserted} chunks")
            return total_upserted
            
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            raise
    
    def query(
        self,
        query_embedding: List[float],
        top_k: int = 12,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query vector store for similar chunks using semantic search.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"file": "doc.pdf"})
            
        Returns:
            List of results with chunk text, metadata, and similarity scores
            Sorted by similarity (most similar first)
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized. Call get_or_create_collection() first.")
        
        # Check if collection is empty
        if self.collection.count() == 0:
            logger.warning("Collection is empty, no results to return")
            return []
        
        logger.info(f"Querying vector store for top {top_k} chunks")
        
        try:
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self.collection.count()),
                where=filter_metadata,
                include=["documents", "metadatas", "distances", "embeddings"]
            )
            
            # Parse results into structured format
            parsed_results = []
            
            # ChromaDB returns results as lists of lists (batch support)
            # We only sent one query, so we take the first element
            ids = results["ids"][0] if results["ids"] else []
            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []
            embeddings = results["embeddings"][0] if results["embeddings"] else []
            
            for idx, (chunk_id, document, metadata, distance) in enumerate(zip(ids, documents, metadatas, distances)):
                # Convert distance to similarity score (cosine distance -> similarity)
                # ChromaDB returns cosine distance (0 = identical, 2 = opposite)
                # Convert to similarity: 1 - (distance / 2)
                similarity = 1.0 - (distance / 2.0)
                
                result = {
                    "chunk_id": chunk_id,
                    "text": document,
                    "file": metadata.get("file"),
                    "page": metadata.get("page"),
                    "chunk_index": metadata.get("chunk_index"),
                    "distance": distance,
                    "similarity": similarity,
                    "metadata": metadata,
                    # Include the chunk's embedding for clustering/fusion
                    "embedding": embeddings[idx] if idx < len(embeddings) else None
                }
                
                parsed_results.append(result)
            
            logger.info(f"Retrieved {len(parsed_results)} results")
            
            # Results are already sorted by similarity (ChromaDB does this)
            return parsed_results
            
        except Exception as e:
            logger.error(f"Failed to query vector store: {e}")
            raise
    
    def count_documents(self) -> int:
        """
        Get total number of chunks in the collection.
        
        Returns:
            Chunk count
        """
        if not self.collection:
            logger.warning("Collection not initialized")
            return 0
        
        try:
            count = self.collection.count()
            return count
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
    
    def clear_collection(self, collection_name: str = "datasplice_docs"):
        """
        Delete all documents from the collection.
        
        Args:
            collection_name: Name of collection to clear
        """
        logger.warning(f"Clearing vector store collection: {collection_name}")
        
        try:
            # Delete the collection entirely
            self.client.delete_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' deleted")
            
            # Recreate empty collection
            self.get_or_create_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' recreated (empty)")
            
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise
    
    def get_document_files(self) -> List[str]:
        """
        Get list of unique file names in the collection.
        
        Returns:
            List of unique file names
        """
        if not self.collection:
            return []
        
        try:
            # Get all documents with their metadata
            results = self.collection.get(
                include=["metadatas"]
            )
            
            # Extract unique file names
            files = set()
            if results and results["metadatas"]:
                for metadata in results["metadatas"]:
                    if "file" in metadata:
                        files.add(metadata["file"])
            
            return sorted(list(files))
            
        except Exception as e:
            logger.error(f"Failed to get document files: {e}")
            return []


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """
    Get or create the global vector store instance.
    
    Returns:
        VectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        _vector_store.get_or_create_collection()
    return _vector_store

