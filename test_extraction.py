"""
Quick test script for PDF extraction.

Usage:
    python test_extraction.py path/to/your.pdf
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.ingestion.extract_text import extract_from_pdf


def test_pdf_extraction(pdf_path: str):
    """Test PDF extraction on a given file."""
    file_path = Path(pdf_path)
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return
    
    print(f"\n📄 Testing PDF extraction: {file_path.name}")
    print("=" * 60)
    
    try:
        pages = extract_from_pdf(file_path)
        
        print(f"✅ Successfully extracted {len(pages)} pages")
        print()
        
        # Display summary of each page
        for page in pages:
            text_preview = page.text[:100].replace('\n', ' ')
            char_count = len(page.text)
            word_count = len(page.text.split())
            
            print(f"Page {page.page_num}:")
            print(f"  - Characters: {char_count}")
            print(f"  - Words: {word_count}")
            print(f"  - Preview: {text_preview}...")
            print(f"  - Metadata: {page.metadata}")
            print()
        
        # Overall statistics
        total_chars = sum(len(p.text) for p in pages)
        total_words = sum(len(p.text.split()) for p in pages)
        
        print("=" * 60)
        print(f"📊 Total Statistics:")
        print(f"  - Total pages: {len(pages)}")
        print(f"  - Total characters: {total_chars:,}")
        print(f"  - Total words: {total_words:,}")
        print(f"  - Avg words per page: {total_words // len(pages) if pages else 0}")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_extraction.py path/to/your.pdf")
        print("\nExample:")
        print("  python test_extraction.py data/samples/sample.pdf")
        sys.exit(1)
    
    test_pdf_extraction(sys.argv[1])

