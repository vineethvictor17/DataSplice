"""
Test script for PDF extraction + chunking pipeline.

Usage:
    python test_chunking.py path/to/your.pdf
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.ingestion.extract_text import extract_from_pdf
from backend.ingestion.chunking import chunk_documents, estimate_tokens


def test_extraction_and_chunking(pdf_path: str):
    """Test the complete extraction and chunking pipeline."""
    file_path = Path(pdf_path)
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return
    
    print(f"\n📄 Testing PDF Extraction + Chunking Pipeline")
    print(f"File: {file_path.name}")
    print("=" * 70)
    
    try:
        # Step 1: Extract pages from PDF
        print("\n🔍 Step 1: Extracting text from PDF...")
        pages = extract_from_pdf(file_path)
        print(f"✅ Extracted {len(pages)} pages")
        
        # Display page statistics
        for page in pages:
            tokens = estimate_tokens(page.text)
            print(f"   Page {page.page_num}: {len(page.text)} chars, ~{tokens} tokens")
        
        # Step 2: Chunk the document
        print(f"\n🔪 Step 2: Chunking document...")
        chunks = chunk_documents(pages, file_path.name)
        print(f"✅ Created {len(chunks)} chunks")
        
        if not chunks:
            print("⚠️  No chunks created (possibly empty document)")
            return
        
        # Step 3: Display chunk statistics
        print(f"\n📊 Chunk Statistics:")
        print("-" * 70)
        
        total_tokens = 0
        chunk_sizes = []
        
        for i, chunk in enumerate(chunks[:10]):  # Show first 10 chunks
            tokens = chunk.metadata.get('token_estimate', 0)
            total_tokens += tokens
            chunk_sizes.append(tokens)
            
            preview = chunk.text[:80].replace('\n', ' ')
            
            print(f"\nChunk {i} (from page {chunk.page}):")
            print(f"  Tokens: {tokens}")
            print(f"  Chars: {chunk.metadata.get('char_count', 0)}")
            print(f"  Preview: {preview}...")
        
        if len(chunks) > 10:
            print(f"\n... and {len(chunks) - 10} more chunks")
            
            # Calculate stats for remaining chunks
            for chunk in chunks[10:]:
                tokens = chunk.metadata.get('token_estimate', 0)
                total_tokens += tokens
                chunk_sizes.append(tokens)
        
        # Overall statistics
        print("\n" + "=" * 70)
        print(f"📈 Overall Statistics:")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Total tokens: {total_tokens:,}")
        print(f"  Avg tokens/chunk: {total_tokens // len(chunks) if chunks else 0}")
        print(f"  Min chunk size: {min(chunk_sizes)} tokens")
        print(f"  Max chunk size: {max(chunk_sizes)} tokens")
        
        # Check if chunks are within expected range
        from backend.utils.config import settings
        target_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP
        
        print(f"\n⚙️  Configuration:")
        print(f"  Target chunk size: {target_size} tokens")
        print(f"  Chunk overlap: {overlap} tokens")
        
        # Validate chunk sizes
        too_small = sum(1 for s in chunk_sizes if s < target_size * 0.3)
        too_large = sum(1 for s in chunk_sizes if s > target_size * 1.5)
        just_right = len(chunk_sizes) - too_small - too_large
        
        print(f"\n✓ Chunk size distribution:")
        print(f"  Too small (<{int(target_size * 0.3)} tokens): {too_small}")
        print(f"  Just right: {just_right}")
        print(f"  Too large (>{int(target_size * 1.5)} tokens): {too_large}")
        
        # Test overlap (check first few chunks)
        print(f"\n🔗 Testing overlap between chunks:")
        for i in range(min(3, len(chunks) - 1)):
            chunk1_end = chunks[i].text[-100:]
            chunk2_start = chunks[i+1].text[:100]
            
            # Check if there's any common text
            overlap_found = False
            for j in range(50, 10, -1):
                if chunk1_end[-j:] in chunk2_start:
                    overlap_found = True
                    print(f"  ✓ Overlap found between chunk {i} and {i+1} (~{j} chars)")
                    break
            
            if not overlap_found:
                print(f"  ⚠️  No obvious overlap between chunk {i} and {i+1}")
        
        print("\n" + "=" * 70)
        print("✅ Pipeline test complete!")
        
    except Exception as e:
        print(f"❌ Error during pipeline: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_chunking.py path/to/your.pdf")
        print("\nExample:")
        print("  python test_chunking.py data/samples/sample.pdf")
        sys.exit(1)
    
    test_extraction_and_chunking(sys.argv[1])

