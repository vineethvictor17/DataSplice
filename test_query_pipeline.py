"""
Test script for the complete query pipeline:
Vector Retrieval → Clustering/Fusion → LLM Synthesis

Usage:
    python test_query_pipeline.py "your question here"

Note: Requires documents to be ingested first and OPENAI_API_KEY set
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.retrieval.vector_store import get_vector_store
from backend.retrieval.fusion import fuse_retrieved_chunks
from backend.synthesis.llm_summarizer import synthesize_response, extract_flat_citations
from backend.synthesis.confidence import calculate_confidence, get_confidence_label
from backend.ingestion.embedding import embed_query
from backend.utils.config import settings


def test_query_pipeline(query: str):
    """
    Test the complete query pipeline with a user question.
    
    Args:
        query: User's research question
    """
    print("\n🔬 Testing Complete Query Pipeline")
    print("=" * 70)
    print(f"Query: '{query}'")
    print("=" * 70)
    
    if not settings.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not set in .env")
        return False
    
    try:
        # Step 1: Get vector store
        print("\n📚 Step 1: Connecting to Vector Store")
        print("─" * 70)
        
        store = get_vector_store()
        doc_count = store.count_documents()
        
        if doc_count == 0:
            print("❌ Vector store is empty!")
            print("   Please run test_vector_store.py first to ingest documents.")
            return False
        
        print(f"✓ Connected to vector store")
        print(f"  Documents in corpus: {doc_count}")
        print(f"  Files: {store.get_document_files()}")
        
        # Step 2: Generate query embedding and retrieve
        print("\n🔍 Step 2: Semantic Search")
        print("─" * 70)
        
        query_embedding = embed_query(query)
        print(f"✓ Generated query embedding (dim: {len(query_embedding)})")
        
        top_k = settings.TOP_K
        results = store.query(query_embedding, top_k=top_k)
        
        print(f"✓ Retrieved {len(results)} chunks")
        
        if not results:
            print("⚠️  No results found for this query")
            return False
        
        # Show top 3 results
        print(f"\n  Top 3 results:")
        for i, result in enumerate(results[:3], 1):
            print(f"    {i}. {result['file']} (p.{result['page']}) - "
                  f"similarity: {result['similarity']:.3f}")
            print(f"       {result['text'][:80]}...")
        
        # Step 3: Cluster and fuse chunks
        print("\n🎯 Step 3: Clustering & Fusion")
        print("─" * 70)
        
        n_clusters = settings.CLUSTERS
        max_per_cluster = 3
        
        clustered = fuse_retrieved_chunks(
            results,
            n_clusters=n_clusters,
            max_per_cluster=max_per_cluster
        )
        
        print(f"✓ Organized into {len(clustered)} clusters")
        for cluster_id, chunks in clustered.items():
            print(f"  Cluster {cluster_id}: {len(chunks)} chunks")
        
        # Step 4: LLM Synthesis
        print("\n🤖 Step 4: LLM Synthesis")
        print("─" * 70)
        
        print(f"Calling {settings.LLM_MODEL}...")
        
        llm_response = synthesize_response(query, clustered)
        
        print(f"✓ Synthesis complete")
        print(f"  Model: {llm_response['model']}")
        print(f"  Tokens used: {llm_response['usage'].get('total_tokens', 0)}")
        print(f"  Subtopics: {len(llm_response.get('subtopics', []))}")
        
        # Step 5: Calculate confidence
        print("\n📊 Step 5: Confidence Scoring")
        print("─" * 70)
        
        citations_flat = extract_flat_citations(llm_response)
        confidence = calculate_confidence(llm_response, citations_flat)
        confidence_label = get_confidence_label(confidence)
        
        print(f"✓ Confidence calculated: {confidence:.2f} ({confidence_label})")
        print(f"  Total citations: {len(citations_flat)}")
        print(f"  Subtopics: {len(llm_response.get('subtopics', []))}")
        
        # Step 6: Display Results
        print("\n" + "=" * 70)
        print("📝 QUERY RESULTS")
        print("=" * 70)
        
        print(f"\n**Summary:**")
        print(llm_response.get('summary', 'No summary generated'))
        
        print(f"\n**Confidence:** {confidence:.1%} ({confidence_label})")
        
        subtopics = llm_response.get('subtopics', [])
        if subtopics:
            print(f"\n**Findings ({len(subtopics)} subtopics):**")
            for i, subtopic in enumerate(subtopics, 1):
                print(f"\n{i}. {subtopic.get('title', 'Untitled')}")
                for bullet in subtopic.get('bullets', []):
                    print(f"   • {bullet}")
                
                citations = subtopic.get('citations', [])
                if citations:
                    print(f"   Sources: ", end="")
                    sources = [f"{c.get('file')} (p.{c.get('page')})" 
                              for c in citations[:2]]
                    print(", ".join(sources))
        
        if llm_response.get('limitations'):
            print(f"\n**Limitations:**")
            print(f"  {llm_response['limitations']}")
        
        print(f"\n**Citations ({len(citations_flat)} unique):**")
        for i, citation in enumerate(citations_flat[:10], 1):
            print(f"  [{i}] {citation['file']}, page {citation['page']} "
                  f"(chunk: {citation['chunk_id']})")
        
        if len(citations_flat) > 10:
            print(f"  ... and {len(citations_flat) - 10} more")
        
        print("\n" + "=" * 70)
        print("✅ PIPELINE TEST SUCCESSFUL!")
        print("=" * 70)
        
        # Summary stats
        print(f"\nPipeline Statistics:")
        print(f"  Chunks retrieved: {len(results)}")
        print(f"  Clusters formed: {len(clustered)}")
        print(f"  Chunks used in synthesis: {sum(len(c) for c in clustered.values())}")
        print(f"  Subtopics generated: {len(subtopics)}")
        print(f"  Citations: {len(citations_flat)}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Total tokens: {llm_response['usage'].get('total_tokens', 0)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_sample_queries():
    """Run a few sample queries to demonstrate the pipeline."""
    sample_queries = [
        "What is the main topic of these documents?",
        "What are the key findings or conclusions?",
        "What methodology was used?",
    ]
    
    print("\n🎯 Running Sample Queries")
    print("=" * 70)
    
    for i, query in enumerate(sample_queries, 1):
        print(f"\n\n{'=' * 70}")
        print(f"QUERY {i}/{len(sample_queries)}")
        print(f"{'=' * 70}")
        
        success = test_query_pipeline(query)
        
        if not success:
            print(f"\n⚠️  Query {i} failed or returned no results")
            break
        
        if i < len(sample_queries):
            input("\nPress Enter to continue to next query...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # User provided a query
        query = " ".join(sys.argv[1:])
        success = test_query_pipeline(query)
    else:
        # Run sample queries
        print("No query provided. Running sample queries...")
        print("Usage: python test_query_pipeline.py 'your question here'")
        print("\nMake sure you've ingested documents first:")
        print("  python test_vector_store.py path/to/your.pdf")
        
        run_sample_queries()
    
    sys.exit(0 if success else 1)

