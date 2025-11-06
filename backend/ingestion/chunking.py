"""
Text chunking with token-based splitting and overlap.

Implements length-based chunking with configurable size and overlap parameters.
"""

import re
from typing import List, Dict, Any

from backend.utils.config import settings
from backend.utils.logger import logger


class Chunk:
    """Represents a text chunk with metadata."""
    def __init__(
        self,
        text: str,
        chunk_index: int,
        file: str,
        page: int,
        metadata: Dict[str, Any]
    ):
        self.text = text
        self.chunk_index = chunk_index
        self.file = file
        self.page = page
        self.metadata = metadata
    
    def get_id(self) -> str:
        """
        Generate a unique ID for this chunk.
        
        Format: {file_name}_p{page}_c{chunk_index}
        Example: "document.pdf_p1_c0"
        
        Returns:
            Unique chunk identifier
        """
        # Remove file extension and sanitize file name
        file_base = self.file.rsplit('.', 1)[0] if '.' in self.file else self.file
        file_base = file_base.replace(' ', '_').replace('/', '_')
        
        return f"{file_base}_p{self.page}_c{self.chunk_index}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary format."""
        return {
            "chunk_id": self.get_id(),
            "text": self.text,
            "chunk_index": self.chunk_index,
            "file": self.file,
            "page": self.page,
            **self.metadata
        }


def estimate_tokens(text: str) -> int:
    """
    Rough token count estimation using character-based heuristic.
    
    For English text, approximately 4 characters = 1 token.
    This is a reasonable approximation for GPT models.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Simple heuristic: ~4 characters per token for English
    # This is slightly conservative to avoid over-chunking
    return max(1, len(text) // 4)


def chunk_text(
    text: str,
    file_name: str,
    page_num: int,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[Chunk]:
    """
    Split text into overlapping chunks of approximately target token length.
    
    Strategy:
    1. Split text into sentences
    2. Combine sentences until reaching target chunk size
    3. Maintain overlap by including last N tokens from previous chunk
    4. Handle edge cases (very long sentences, empty text)
    
    Args:
        text: Text to chunk
        file_name: Source file name
        page_num: Source page number
        chunk_size: Target tokens per chunk (default from settings)
        chunk_overlap: Overlap tokens between chunks (default from settings)
        
    Returns:
        List of Chunk objects
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    # Handle empty or whitespace-only text
    if not text or not text.strip():
        logger.warning(f"Empty text for {file_name} page {page_num}, skipping chunking")
        return []
    
    logger.info(f"Chunking text from {file_name} page {page_num} "
                f"(~{estimate_tokens(text)} tokens, target size: {chunk_size}, overlap: {chunk_overlap})")
    
    # Convert token counts to approximate character counts
    chunk_size_chars = chunk_size * 4
    chunk_overlap_chars = chunk_overlap * 4
    
    # Split text into sentences (improved regex for better sentence detection)
    sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
    sentences = sentence_endings.split(text)
    
    # If no sentences detected (no proper punctuation), fall back to paragraph splitting
    if len(sentences) == 1:
        # Try splitting on double newlines
        sentences = text.split('\n\n')
        if len(sentences) == 1:
            # Last resort: split on single newlines
            sentences = text.split('\n')
    
    chunks = []
    current_chunk = ""
    chunk_index = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Check if adding this sentence would exceed chunk size
        potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
        
        if len(current_chunk) > 0 and len(potential_chunk) > chunk_size_chars:
            # Current chunk is full, save it
            if current_chunk.strip():
                chunk = Chunk(
                    text=current_chunk.strip(),
                    chunk_index=chunk_index,
                    file=file_name,
                    page=page_num,
                    metadata={
                        "token_estimate": estimate_tokens(current_chunk),
                        "char_count": len(current_chunk)
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap from previous chunk
                # Take last N characters to maintain context
                if chunk_overlap_chars > 0 and len(current_chunk) > chunk_overlap_chars:
                    # Try to find a sentence boundary within the overlap region
                    overlap_start = len(current_chunk) - chunk_overlap_chars
                    overlap_text = current_chunk[overlap_start:]
                    
                    # Look for sentence start in overlap
                    sentence_starts = re.finditer(r'[.!?]\s+', overlap_text)
                    last_sentence_start = None
                    for match in sentence_starts:
                        last_sentence_start = match.end()
                    
                    if last_sentence_start:
                        current_chunk = overlap_text[last_sentence_start:] + " " + sentence
                    else:
                        current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk = sentence
        else:
            # Add sentence to current chunk
            current_chunk = potential_chunk
        
        # Handle extremely long sentences that exceed chunk size by themselves
        if len(current_chunk) > chunk_size_chars * 2:
            # Split the long sentence on whitespace
            words = current_chunk.split()
            temp_chunk = ""
            
            for word in words:
                if len(temp_chunk) + len(word) + 1 <= chunk_size_chars:
                    temp_chunk = temp_chunk + " " + word if temp_chunk else word
                else:
                    if temp_chunk.strip():
                        chunk = Chunk(
                            text=temp_chunk.strip(),
                            chunk_index=chunk_index,
                            file=file_name,
                            page=page_num,
                            metadata={
                                "token_estimate": estimate_tokens(temp_chunk),
                                "char_count": len(temp_chunk),
                                "split_type": "word_boundary"
                            }
                        )
                        chunks.append(chunk)
                        chunk_index += 1
                    temp_chunk = word
            
            current_chunk = temp_chunk
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunk = Chunk(
            text=current_chunk.strip(),
            chunk_index=chunk_index,
            file=file_name,
            page=page_num,
            metadata={
                "token_estimate": estimate_tokens(current_chunk),
                "char_count": len(current_chunk)
            }
        )
        chunks.append(chunk)
    
    logger.info(f"Created {len(chunks)} chunks from {file_name} page {page_num}")
    
    return chunks


def chunk_documents(pages: List[Any], file_name: str) -> List[Chunk]:
    """
    Chunk all pages from a document.
    
    Args:
        pages: List of DocumentPage objects
        file_name: Source file name
        
    Returns:
        List of all chunks from the document
    """
    all_chunks = []
    
    for page in pages:
        page_chunks = chunk_text(
            text=page.text,
            file_name=file_name,
            page_num=page.page_num
        )
        all_chunks.extend(page_chunks)
    
    logger.info(f"Created {len(all_chunks)} chunks from {file_name}")
    return all_chunks

