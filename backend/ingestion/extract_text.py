"""
Text extraction from PDF, DOCX, and TXT files.

Handles document parsing and metadata extraction for supported formats.
"""

from pathlib import Path
from typing import Dict, List, Optional

import fitz  # PyMuPDF

from backend.utils.logger import logger


class DocumentPage:
    """Represents a page or section of a document."""
    def __init__(self, page_num: int, text: str, metadata: Optional[Dict] = None):
        self.page_num = page_num
        self.text = text
        self.metadata = metadata or {}


def extract_from_pdf(file_path: Path) -> List[DocumentPage]:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        List of DocumentPage objects with page-level text
    
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF is corrupted or cannot be read
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    pages = []
    
    try:
        # Open the PDF document
        pdf_document = fitz.open(str(file_path))
        
        logger.info(f"PDF opened successfully: {pdf_document.page_count} pages")
        
        # Iterate through each page
        for page_num in range(pdf_document.page_count):
            try:
                # Get the page
                page = pdf_document[page_num]
                
                # Extract text from the page
                text = page.get_text()
                
                # Skip completely empty pages but log them
                if not text.strip():
                    logger.warning(f"Page {page_num + 1} is empty in {file_path.name}")
                    text = ""  # Keep empty pages for proper indexing
                
                # Create metadata for the page
                metadata = {
                    "file_name": file_path.name,
                    "total_pages": pdf_document.page_count,
                }
                
                # Create DocumentPage object (using 1-based page numbering)
                doc_page = DocumentPage(
                    page_num=page_num + 1,
                    text=text,
                    metadata=metadata
                )
                
                pages.append(doc_page)
                
            except Exception as e:
                logger.error(f"Error extracting page {page_num + 1} from {file_path.name}: {e}")
                # Continue with other pages even if one fails
                continue
        
        # Close the PDF document
        pdf_document.close()
        
        logger.info(f"Successfully extracted {len(pages)} pages from {file_path.name}")
        
    except Exception as e:
        logger.error(f"Failed to open or process PDF {file_path}: {e}")
        raise Exception(f"PDF extraction failed: {e}")
    
    return pages


def extract_from_docx(file_path: Path) -> List[DocumentPage]:
    """
    Extract text from a DOCX file.
    
    Args:
        file_path: Path to DOCX file
        
    Returns:
        List of DocumentPage objects (typically single page)
        
    TODO: Implement using python-docx
    - Open document and extract paragraphs
    - Optionally detect section breaks
    - Combine into coherent text blocks
    - Return as DocumentPage(s)
    """
    logger.info(f"Extracting text from DOCX: {file_path}")
    return []


def extract_from_txt(file_path: Path) -> List[DocumentPage]:
    """
    Extract text from a plain text file.
    
    Args:
        file_path: Path to TXT file
        
    Returns:
        List with single DocumentPage
        
    TODO: Implement simple text reading
    - Read file with UTF-8 encoding
    - Handle encoding errors
    - Return as single page
    """
    logger.info(f"Extracting text from TXT: {file_path}")
    return []


def extract_text(file_path: Path) -> List[DocumentPage]:
    """
    Extract text from a document file based on its extension.
    
    Args:
        file_path: Path to document file
        
    Returns:
        List of DocumentPage objects
        
    Raises:
        ValueError: If file format is not supported
    """
    suffix = file_path.suffix.lower()
    
    extractors = {
        ".pdf": extract_from_pdf,
        ".docx": extract_from_docx,
        ".txt": extract_from_txt,
    }
    
    extractor = extractors.get(suffix)
    if not extractor:
        raise ValueError(f"Unsupported file format: {suffix}")
    
    return extractor(file_path)

