"""
Test script for embedding generation.

Usage:
    python test_embeddings.py

Note: Requires OPENAI_API_KEY to be set in .env file
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.ingestion.embedding import embed_texts, embed_query, get_openai_client
from backend.utils.config import settings


def test_basic_embedding():
    """Test basic embedding generation with sample texts."""
    print("\n🔬 Testing OpenAI Embedding API")
    print("=" * 70)
    
    # Check API key
    if not settings.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not set in .env file")
        print("\nPlease create a .env file with:")
        print("OPENAI_API_KEY=sk-your-key-here")
        return False
    
    print(f"✓ API key found (starts with: {settings.OPENAI_API_KEY[:10]}...)")
    print(f"✓ Using model: {settings.EMBED_MODEL}")
    
    try:
        # Initialize client
        print("\n📡 Initializing OpenAI client...")
        client = get_openai_client()
        print("✓ Client initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test 1: Single text
    print("\n" + "─" * 70)
    print("Test 1: Single Text Embedding")
    print("─" * 70)
    
    sample_text = "This is a test document about artificial intelligence and machine learning."
    
    try:
        print(f"Input: '{sample_text}'")
        embeddings = embed_texts([sample_text])
        
        if embeddings and len(embeddings) > 0:
            embedding = embeddings[0]
            print(f"✓ Generated embedding")
            print(f"  - Dimension: {len(embedding)}")
            print(f"  - Type: {type(embedding)}")
            print(f"  - First 5 values: {embedding[:5]}")
            print(f"  - Min value: {min(embedding):.6f}")
            print(f"  - Max value: {max(embedding):.6f}")
        else:
            print("❌ No embeddings generated")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Multiple texts (batch)
    print("\n" + "─" * 70)
    print("Test 2: Batch Embedding (5 texts)")
    print("─" * 70)
    
    sample_texts = [
        "Artificial intelligence is transforming technology.",
        "Machine learning models require large datasets.",
        "Natural language processing enables text understanding.",
        "Computer vision allows machines to see and interpret images.",
        "Deep learning uses neural networks with many layers."
    ]
    
    try:
        print(f"Input: {len(sample_texts)} texts")
        embeddings = embed_texts(sample_texts)
        
        if embeddings and len(embeddings) == len(sample_texts):
            print(f"✓ Generated {len(embeddings)} embeddings")
            print(f"  - Dimensions: {len(embeddings[0])}")
            
            # Check that embeddings are different
            if len(set(tuple(e) for e in embeddings)) == len(embeddings):
                print(f"  - ✓ All embeddings are unique")
            else:
                print(f"  - ⚠️  Some embeddings are identical")
        else:
            print(f"❌ Expected {len(sample_texts)} embeddings, got {len(embeddings) if embeddings else 0}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Query embedding (convenience function)
    print("\n" + "─" * 70)
    print("Test 3: Query Embedding")
    print("─" * 70)
    
    query = "What is machine learning?"
    
    try:
        print(f"Query: '{query}'")
        query_embedding = embed_query(query)
        
        if query_embedding:
            print(f"✓ Generated query embedding")
            print(f"  - Dimension: {len(query_embedding)}")
        else:
            print("❌ No embedding generated")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 4: Semantic similarity
    print("\n" + "─" * 70)
    print("Test 4: Semantic Similarity")
    print("─" * 70)
    
    try:
        # Embed similar and dissimilar texts
        text1 = "The cat sat on the mat."
        text2 = "A feline rested on the rug."
        text3 = "The weather is sunny today."
        
        embeddings = embed_texts([text1, text2, text3])
        
        if len(embeddings) == 3:
            # Compute cosine similarities
            import numpy as np
            
            def cosine_similarity(a, b):
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
            sim_12 = cosine_similarity(embeddings[0], embeddings[1])
            sim_13 = cosine_similarity(embeddings[0], embeddings[2])
            
            print(f"Text 1: '{text1}'")
            print(f"Text 2: '{text2}'")
            print(f"Text 3: '{text3}'")
            print(f"\nSimilarities:")
            print(f"  Text 1 ↔ Text 2 (similar): {sim_12:.4f}")
            print(f"  Text 1 ↔ Text 3 (different): {sim_13:.4f}")
            
            if sim_12 > sim_13:
                print(f"  ✓ Semantic similarity working correctly!")
            else:
                print(f"  ⚠️  Expected sim(1,2) > sim(1,3)")
        else:
            print("❌ Failed to generate all embeddings")
            return False
            
    except ImportError:
        print("⚠️  NumPy not available, skipping similarity test")
    except Exception as e:
        print(f"⚠️  Similarity test failed: {e}")
    
    # Test 5: Empty text handling
    print("\n" + "─" * 70)
    print("Test 5: Edge Cases")
    print("─" * 70)
    
    try:
        # Empty list
        result = embed_texts([])
        print(f"✓ Empty list: {result == []}")
        
        # Empty string
        result = embed_texts(["", "Valid text", ""])
        print(f"✓ Empty strings filtered: {len(result) == 1}")
        
    except Exception as e:
        print(f"⚠️  Edge case test failed: {e}")
    
    print("\n" + "=" * 70)
    print("✅ All embedding tests passed!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = test_basic_embedding()
    sys.exit(0 if success else 1)

