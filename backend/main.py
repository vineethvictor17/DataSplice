"""
FastAPI application for DataSplice backend.

Provides endpoints for health checks, document ingestion, and query processing.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pathlib import Path
import shutil

from backend.models.schemas import (
    HealthResponse,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    Subtopic,
    Citation,
    StatsResponse,
    ClearResponse
)
from backend.utils.config import ensure_directories, settings
from backend.utils.logger import logger

# Import pipeline components
from backend.ingestion.extract_text import extract_text
from backend.ingestion.chunking import chunk_documents
from backend.ingestion.embedding import embed_texts, embed_query
from backend.retrieval.vector_store import get_vector_store
from backend.retrieval.fusion import fuse_retrieved_chunks
from backend.synthesis.llm_summarizer import synthesize_response, extract_flat_citations
from backend.synthesis.confidence import calculate_confidence

app = FastAPI(title="DataSplice API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application resources."""
    logger.info("Starting DataSplice backend...")
    ensure_directories()
    
    # Initialize vector store connection
    try:
        store = get_vector_store()
        doc_count = store.count_documents()
        logger.info(f"Vector store connected: {doc_count} documents in corpus")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
    
    logger.info("Backend ready")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status and vector DB readiness
    """
    try:
        store = get_vector_store()
        doc_count = store.count_documents()
        vector_db_ready = True
        logger.info(f"Health check: {doc_count} documents in vector store")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        vector_db_ready = False
    
    return HealthResponse(status="ok", vector_db_ready=vector_db_ready)


@app.get("/stats", response_model=StatsResponse)
async def get_corpus_stats():
    """
    Get corpus statistics.
    
    Returns:
        Chunk count, file count, and list of files in corpus
    """
    try:
        store = get_vector_store()
        chunk_count = store.count_documents()
        files = store.get_document_files()
        file_count = len(files)
        
        logger.info(f"Stats: {chunk_count} chunks, {file_count} files")
        
        return StatsResponse(
            chunk_count=chunk_count,
            file_count=file_count,
            files=files
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get corpus stats: {str(e)}")


@app.delete("/corpus", response_model=ClearResponse)
async def clear_corpus():
    """
    Clear the entire corpus by deleting all documents from the vector store.
    
    WARNING: This action is irreversible and will delete all ingested documents.
    
    Returns:
        Clear response with deletion status
    """
    try:
        store = get_vector_store()
        
        # Get count before clearing
        deleted_chunks = store.count_documents()
        
        # Clear the collection
        store.clear_collection()
        
        logger.warning(f"Corpus cleared: {deleted_chunks} chunks deleted")
        
        return ClearResponse(
            ok=True,
            message=f"Successfully cleared corpus. Deleted {deleted_chunks} chunks.",
            deleted_chunks=deleted_chunks
        )
    except Exception as e:
        logger.error(f"Failed to clear corpus: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear corpus: {str(e)}")


@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents(files: List[UploadFile] = File(...)):
    """
    Ingest multiple documents into the vector store.
    
    Accepts PDF, DOCX, and TXT files. Extracts text, chunks, embeds,
    and stores in ChromaDB with metadata.
    
    Args:
        files: List of uploaded files
        
    Returns:
        Ingestion results with chunk count and any errors
    """
    logger.info(f"Received {len(files)} files for ingestion")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    total_chunks_added = 0
    errors = []
    
    for uploaded_file in files:
        try:
            # Validate file type
            file_ext = Path(uploaded_file.filename).suffix.lower()
            if file_ext not in ['.pdf', '.docx', '.txt']:
                errors.append(f"{uploaded_file.filename}: Unsupported file type {file_ext}")
                continue
            
            logger.info(f"Processing file: {uploaded_file.filename}")
            
            # Step 1: Save uploaded file to disk
            upload_path = Path(settings.UPLOAD_DIR) / uploaded_file.filename
            with upload_path.open("wb") as buffer:
                shutil.copyfileobj(uploaded_file.file, buffer)
            
            logger.info(f"Saved to {upload_path}")
            
            # Step 2: Extract text from document
            try:
                pages = extract_text(upload_path)
                logger.info(f"Extracted {len(pages)} pages from {uploaded_file.filename}")
            except Exception as e:
                errors.append(f"{uploaded_file.filename}: Text extraction failed - {str(e)}")
                continue
            
            if not pages:
                errors.append(f"{uploaded_file.filename}: No text extracted")
                continue
            
            # Step 3: Chunk the document
            try:
                chunks = chunk_documents(pages, uploaded_file.filename)
                logger.info(f"Created {len(chunks)} chunks from {uploaded_file.filename}")
            except Exception as e:
                errors.append(f"{uploaded_file.filename}: Chunking failed - {str(e)}")
                continue
            
            if not chunks:
                errors.append(f"{uploaded_file.filename}: No chunks created")
                continue
            
            # Step 4: Generate embeddings
            try:
                chunk_texts = [chunk.text for chunk in chunks]
                embeddings = embed_texts(chunk_texts)
                logger.info(f"Generated {len(embeddings)} embeddings for {uploaded_file.filename}")
            except Exception as e:
                errors.append(f"{uploaded_file.filename}: Embedding generation failed - {str(e)}")
                continue
            
            if len(embeddings) != len(chunks):
                errors.append(
                    f"{uploaded_file.filename}: Embedding count mismatch "
                    f"(chunks: {len(chunks)}, embeddings: {len(embeddings)})"
                )
                continue
            
            # Step 5: Upsert to vector store
            try:
                store = get_vector_store()
                added = store.upsert_chunks(chunks, embeddings)
                total_chunks_added += added
                logger.info(f"Upserted {added} chunks from {uploaded_file.filename} to vector store")
            except Exception as e:
                errors.append(f"{uploaded_file.filename}: Vector store upsert failed - {str(e)}")
                continue
            
        except Exception as e:
            logger.error(f"Error processing {uploaded_file.filename}: {e}")
            errors.append(f"{uploaded_file.filename}: {str(e)}")
    
    success = total_chunks_added > 0
    
    logger.info(
        f"Ingestion complete: {total_chunks_added} chunks added, "
        f"{len(errors)} errors"
    )
    
    return IngestResponse(
        ok=success,
        added_chunks=total_chunks_added,
        errors=errors
    )


@app.post("/query", response_model=QueryResponse)
async def query_corpus(request: QueryRequest):
    """
    Query the document corpus and generate a structured response.
    
    Pipeline:
    1. Retrieve top-k chunks from vector store
    2. Cluster and deduplicate chunks (fusion.py)
    3. Synthesize structured summary with LLM (llm_summarizer.py)
    4. Calculate confidence score (confidence.py)
    
    Args:
        request: Query text and optional top_k parameter
        
    Returns:
        Structured response with summary, subtopics, and citations
    """
    logger.info(f"Processing query: {request.query[:100]}...")
    
    try:
        # Check if vector store has documents
        store = get_vector_store()
        doc_count = store.count_documents()
        
        if doc_count == 0:
            raise HTTPException(
                status_code=400,
                detail="No documents in corpus. Please ingest documents first."
            )
        
        logger.info(f"Querying corpus with {doc_count} documents")
        
        # Step 1: Embed the query
        try:
            query_embedding = embed_query(request.query)
            logger.info("Query embedded successfully")
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to embed query: {str(e)}")
        
        # Step 2: Retrieve top-k chunks from vector store
        try:
            top_k = request.top_k or settings.TOP_K
            retrieved_chunks = store.query(query_embedding, top_k=top_k)
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks")
        except Exception as e:
            logger.error(f"Vector retrieval failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve chunks: {str(e)}")
        
        if not retrieved_chunks:
            return QueryResponse(
                query=request.query,
                summary="No relevant information found in the corpus for this query.",
                confidence=0.0,
                subtopics=[],
                citations_flat=[]
            )
        
        # Step 3: Cluster and fuse chunks
        try:
            clustered_chunks = fuse_retrieved_chunks(
                retrieved_chunks,
                n_clusters=settings.CLUSTERS,
                max_per_cluster=3
            )
            logger.info(f"Clustered into {len(clustered_chunks)} groups")
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to cluster chunks: {str(e)}")
        
        # Step 4: Generate structured summary with LLM
        try:
            llm_response = synthesize_response(request.query, clustered_chunks)
            logger.info("LLM synthesis complete")
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")
        
        # Step 5: Extract flat citations and calculate confidence
        try:
            citations_flat = extract_flat_citations(llm_response)
            confidence = calculate_confidence(llm_response, citations_flat)
            logger.info(f"Confidence calculated: {confidence:.2f}")
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            # Non-critical, continue with default values
            citations_flat = []
            confidence = 0.5
        
        # Step 6: Build response with proper schema
        subtopics = []
        for subtopic_data in llm_response.get("subtopics", []):
            citations = [
                Citation(
                    chunk_id=c.get("chunk_id", ""),
                    file=c.get("file", ""),
                    page=c.get("page", 0),
                    excerpt=c.get("excerpt", "")
                )
                for c in subtopic_data.get("citations", [])
            ]
            
            subtopics.append(
                Subtopic(
                    title=subtopic_data.get("title", ""),
                    bullets=subtopic_data.get("bullets", []),
                    citations=citations
                )
            )
        
        citations_flat_schema = [
            Citation(
                chunk_id=c.get("chunk_id", ""),
                file=c.get("file", ""),
                page=c.get("page", 0)
            )
            for c in citations_flat
        ]
        
        logger.info(
            f"Query complete: {len(subtopics)} subtopics, "
            f"{len(citations_flat_schema)} citations, "
            f"confidence={confidence:.2f}"
        )
        
        return QueryResponse(
            query=request.query,
            summary=llm_response.get("summary", ""),
            confidence=confidence,
            subtopics=subtopics,
            citations_flat=citations_flat_schema,
            raw={
                "model": llm_response.get("model"),
                "usage": llm_response.get("usage", {})
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

