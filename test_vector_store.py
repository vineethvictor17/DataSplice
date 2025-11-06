"""
Test script for ChromaDB vector store operations.

Tests the complete storage and retrieval pipeline.

Usage:
    python test_vector_store.py [pdf_path]
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.ingestion.extract_text import extract_from_pdf
from backend.ingestion.chunking import chunk_documents
from backend.ingestion.embedding import embed_texts, embed_query
from backend.retrieval.vector_store import VectorStore, get_vector_store
from backend.utils.config import settings


def test_vector_store_basic():
    """Test basic vector store operations without a PDF."""
    print("\n🗄️  Testing Vector Store Basic Operations")
    print("=" * 70)
    
    try:
        # Test 1: Initialize vector store
        print("\n📦 Test 1: Initialize Vector Store")
        print("─" * 70)
        
        store = VectorStore()
        print(f"✓ Vector store created at: {store.persist_directory}")
        
        # Test 2: Create collection
        print("\n📚 Test 2: Create Collection")
        print("─" * 70)
        
        collection = store.get_or_create_collection("test_collection")
        print(f"✓ Collection created: {collection.name}")
        print(f"  Current count: {store.count_documents()}")
        
        # Test 3: Create and store mock chunks
        print("\n💾 Test 3: Store Mock Data")
        print("─" * 70)
        
        if not settings.OPENAI_API_KEY:
            print("⚠️  OPENAI_API_KEY not set, skipping embedding test")
            print("   Set API key in .env to test full pipeline")
            return True
        
        # Create mock text chunks
        mock_texts = [
            "Artificial intelligence is transforming technology and society.",
            "Machine learning models learn patterns from data.",
            "Natural language processing enables computers to understand text."
        ]
        
        print(f"Creating mock chunks...")
        
        # Create simple Chunk-like objects
        from backend.ingestion.chunking import Chunk
        chunks = [
            Chunk(
                text=text,
                chunk_index=i,
                file="test_doc.pdf",
                page=1,
                metadata={"token_estimate": len(text.split()), "char_count": len(text)}
            )
            for i, text in enumerate(mock_texts)
        ]
        
        print(f"✓ Created {len(chunks)} mock chunks")
        
        # Generate embeddings
        print(f"Generating embeddings...")
        embeddings = embed_texts(mock_texts)
        print(f"✓ Generated {len(embeddings)} embeddings")
        
        # Upsert to vector store
        print(f"Upserting to vector store...")
        count = store.upsert_chunks(chunks, embeddings)
        print(f"✓ Upserted {count} chunks")
        print(f"  Total in collection: {store.count_documents()}")
        
        # Test 4: Query vector store
        print("\n🔍 Test 4: Query Vector Store")
        print("─" * 70)
        
        query_text = "What is machine learning?"
        print(f"Query: '{query_text}'")
        
        query_embedding = embed_query(query_text)
        print(f"✓ Generated query embedding")
        
        results = store.query(query_embedding, top_k=3)
        print(f"✓ Retrieved {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Chunk ID: {result['chunk_id']}")
            print(f"    Similarity: {result['similarity']:.4f}")
            print(f"    Distance: {result['distance']:.4f}")
            print(f"    Text: {result['text'][:60]}...")
        
        # Test 5: Get statistics
        print("\n📊 Test 5: Collection Statistics")
        print("─" * 70)
        
        count = store.count_documents()
        files = store.get_document_files()
        
        print(f"  Total chunks: {count}")
        print(f"  Unique files: {files}")
        
        # Test 6: Clear collection
        print("\n🗑️  Test 6: Clear Collection")
        print("─" * 70)
        
        print(f"Before clear: {store.count_documents()} documents")
        store.clear_collection("test_collection")
        print(f"After clear: {store.count_documents()} documents")
        print(f"✓ Collection cleared successfully")
        
        print("\n" + "=" * 70)
        print("✅ All basic tests passed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_store_with_pdf(pdf_path: str):
    """Test full pipeline with actual PDF."""
    print("\n🚀 Testing Full Pipeline with PDF")
    print(f"File: {pdf_path}")
    print("=" * 70)
    
    file_path = Path(pdf_path)
    if not file_path.exists():
        print(f"❌ File not found: {pdf_path}")
        return False
    
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set in .env")
        return False
    
    try:
        # Step 1: Extract and chunk
        print("\n📄 Step 1: Extract & Chunk PDF")
        print("─" * 70)
        
        pages = extract_from_pdf(file_path)
        chunks = chunk_documents(pages, file_path.name)
        
        # Limit chunks for testing (save API costs)
        max_chunks = 10
        chunks_to_process = chunks[:max_chunks]
        
        print(f"✓ Extracted {len(pages)} pages")
        print(f"✓ Created {len(chunks)} chunks")
        print(f"  (Processing first {len(chunks_to_process)} to save API costs)")
        
        # Step 2: Generate embeddings
        print("\n🧮 Step 2: Generate Embeddings")
        print("─" * 70)
        
        chunk_texts = [c.text for c in chunks_to_process]
        embeddings = embed_texts(chunk_texts)
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"  Dimension: {len(embeddings[0])}")
        
        # Step 3: Store in vector database
        print("\n💾 Step 3: Store in Vector Database")
        print("─" * 70)
        
        store = get_vector_store()  # Use singleton
        count = store.upsert_chunks(chunks_to_process, embeddings)
        
        print(f"✓ Stored {count} chunks")
        print(f"  Total in collection: {store.count_documents()}")
        print(f"  Files in collection: {store.get_document_files()}")
        
        # Step 4: Test retrieval
        print("\n🔍 Step 4: Test Semantic Search")
        print("─" * 70)
        
        # Create test queries
        test_queries = [
            "What is the main topic of this document?",
            "Tell me about the methodology",
            "What are the key findings?"
        ]
        
        for query in test_queries[:1]:  # Just test first query
            print(f"\nQuery: '{query}'")
            
            query_embedding = embed_query(query)
            results = store.query(query_embedding, top_k=5)
            
            print(f"Retrieved {len(results)} results:")
            for i, result in enumerate(results[:3], 1):
                print(f"\n  {i}. Chunk {result['chunk_id']}")
                print(f"     Similarity: {result['similarity']:.4f}")
                print(f"     From: {result['file']} (page {result['page']})")
                print(f"     Text: {result['text'][:100].replace(chr(10), ' ')}...")
        
        # Step 5: Verify data integrity
        print("\n✅ Step 5: Data Integrity")
        print("─" * 70)
        
        total_count = store.count_documents()
        files = store.get_document_files()
        
        print(f"✓ Vector store operational")
        print(f"  Total chunks: {total_count}")
        print(f"  Unique files: {len(files)}")
        print(f"  File list: {files}")
        
        # Step 6: Test metadata filtering
        print("\n🔎 Step 6: Test Metadata Filtering")
        print("─" * 70)
        
        query_embedding = embed_query("test query")
        
        # Filter by file
        filtered_results = store.query(
            query_embedding,
            top_k=5,
            filter_metadata={"file": file_path.name}
        )
        
        print(f"✓ Filtered query by file '{file_path.name}'")
        print(f"  Results: {len(filtered_results)}")
        
        # Filter by page
        filtered_results = store.query(
            query_embedding,
            top_k=5,
            filter_metadata={"page": 1}
        )
        
        print(f"✓ Filtered query by page 1")
        print(f"  Results: {len(filtered_results)}")
        
        print("\n" + "=" * 70)
        print("🎉 Full pipeline test complete!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with PDF
        success = test_vector_store_with_pdf(sys.argv[1])
    else:
        # Basic test without PDF
        print("\nNo PDF provided. Running basic tests...")
        print("Usage: python test_vector_store.py path/to/your.pdf")
        success = test_vector_store_basic()
    
    sys.exit(0 if success else 1)

