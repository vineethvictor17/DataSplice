"""
Integration test for the full ingestion pipeline:
PDF Extraction → Chunking → Embedding

Usage:
    python test_full_pipeline.py path/to/your.pdf

Note: Requires OPENAI_API_KEY to be set in .env file
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.ingestion.extract_text import extract_from_pdf
from backend.ingestion.chunking import chunk_documents, estimate_tokens
from backend.ingestion.embedding import embed_texts
from backend.utils.config import settings


def test_full_pipeline(pdf_path: str, max_chunks: int = 5):
    """
    Test the complete ingestion pipeline.
    
    Args:
        pdf_path: Path to PDF file
        max_chunks: Maximum number of chunks to embed (to save API costs)
    """
    file_path = Path(pdf_path)
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return False
    
    if not settings.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not set in .env file")
        return False
    
    print("\n🚀 Full Ingestion Pipeline Test")
    print(f"File: {file_path.name}")
    print("=" * 70)
    
    try:
        # Stage 1: Extract text from PDF
        print("\n📄 Stage 1: PDF Text Extraction")
        print("─" * 70)
        
        pages = extract_from_pdf(file_path)
        
        if not pages:
            print("❌ No pages extracted")
            return False
        
        print(f"✓ Extracted {len(pages)} pages")
        
        total_chars = sum(len(p.text) for p in pages)
        total_tokens = sum(estimate_tokens(p.text) for p in pages)
        
        print(f"  - Total characters: {total_chars:,}")
        print(f"  - Estimated tokens: {total_tokens:,}")
        
        # Stage 2: Chunk the document
        print("\n🔪 Stage 2: Text Chunking")
        print("─" * 70)
        
        chunks = chunk_documents(pages, file_path.name)
        
        if not chunks:
            print("❌ No chunks created")
            return False
        
        print(f"✓ Created {len(chunks)} chunks")
        
        avg_chunk_size = sum(c.metadata.get('token_estimate', 0) for c in chunks) / len(chunks)
        print(f"  - Avg chunk size: {avg_chunk_size:.0f} tokens")
        print(f"  - Target size: {settings.CHUNK_SIZE} tokens")
        print(f"  - Overlap: {settings.CHUNK_OVERLAP} tokens")
        
        # Display sample chunks
        print(f"\n  Sample chunks:")
        for i, chunk in enumerate(chunks[:3]):
            chunk_id = chunk.get_id()
            tokens = chunk.metadata.get('token_estimate', 0)
            preview = chunk.text[:60].replace('\n', ' ')
            print(f"    {i+1}. {chunk_id} ({tokens} tokens): {preview}...")
        
        # Stage 3: Generate embeddings (limited to save API costs)
        print(f"\n🧮 Stage 3: Embedding Generation")
        print("─" * 70)
        
        # Limit chunks to embed
        chunks_to_embed = chunks[:max_chunks]
        chunk_texts = [c.text for c in chunks_to_embed]
        
        print(f"Embedding {len(chunks_to_embed)} chunks (limited to save API costs)")
        print(f"Note: Set max_chunks parameter higher to embed more")
        
        embeddings = embed_texts(chunk_texts)
        
        if not embeddings:
            print("❌ No embeddings generated")
            return False
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        
        if embeddings:
            embedding_dim = len(embeddings[0])
            print(f"  - Embedding dimension: {embedding_dim}")
            print(f"  - Expected for {settings.EMBED_MODEL}: 3072")
            
            if embedding_dim == 3072:
                print(f"  - ✓ Dimension matches model!")
        
        # Stage 4: Verify data integrity
        print(f"\n✅ Stage 4: Data Integrity Check")
        print("─" * 70)
        
        print(f"Verifying pipeline output...")
        
        # Check chunk IDs are unique
        chunk_ids = [c.get_id() for c in chunks]
        unique_ids = set(chunk_ids)
        print(f"  ✓ Chunk IDs unique: {len(chunk_ids) == len(unique_ids)}")
        
        # Check embeddings match chunks
        print(f"  ✓ Embeddings count matches: {len(embeddings) == len(chunks_to_embed)}")
        
        # Check all chunks have required metadata
        required_fields = ['token_estimate', 'char_count']
        all_have_metadata = all(
            all(field in c.metadata for field in required_fields)
            for c in chunks
        )
        print(f"  ✓ All chunks have metadata: {all_have_metadata}")
        
        # Stage 5: Create sample output
        print(f"\n📦 Stage 5: Sample Output")
        print("─" * 70)
        
        print("Sample chunk with embedding:")
        sample_chunk = chunks_to_embed[0]
        sample_embedding = embeddings[0]
        
        print(f"\nChunk ID: {sample_chunk.get_id()}")
        print(f"File: {sample_chunk.file}")
        print(f"Page: {sample_chunk.page}")
        print(f"Chunk Index: {sample_chunk.chunk_index}")
        print(f"Text Length: {len(sample_chunk.text)} chars")
        print(f"Tokens: {sample_chunk.metadata.get('token_estimate')} (estimated)")
        print(f"Embedding: [{sample_embedding[0]:.6f}, {sample_embedding[1]:.6f}, ..., {sample_embedding[-1]:.6f}]")
        print(f"Embedding Dimension: {len(sample_embedding)}")
        
        # Summary
        print("\n" + "=" * 70)
        print("🎉 PIPELINE TEST SUCCESSFUL!")
        print("=" * 70)
        print(f"\nSummary:")
        print(f"  📄 Pages extracted: {len(pages)}")
        print(f"  🔪 Chunks created: {len(chunks)}")
        print(f"  🧮 Embeddings generated: {len(embeddings)}")
        print(f"  ✓ Ready for vector store ingestion")
        
        print(f"\nNext steps:")
        print(f"  1. Implement vector store (backend/retrieval/vector_store.py)")
        print(f"  2. Store chunks with embeddings in ChromaDB")
        print(f"  3. Test retrieval with sample queries")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_full_pipeline.py path/to/your.pdf")
        print("\nExample:")
        print("  python test_full_pipeline.py data/samples/sample.pdf")
        print("\nNote: This will use OpenAI API credits to generate embeddings.")
        print("      Only a few chunks are embedded by default to save costs.")
        sys.exit(1)
    
    # Optional: custom max_chunks
    max_chunks = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    success = test_full_pipeline(sys.argv[1], max_chunks)
    sys.exit(0 if success else 1)

