"""
Backend API client for frontend.

Simple HTTP client to interact with FastAPI backend.
"""

import requests
from typing import List, Dict, Any, Optional
import os


class BackendClient:
    """Client for DataSplice backend API."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize backend client.
        
        Args:
            base_url: Backend URL (default: http://localhost:8000)
        """
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://localhost:8000")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check backend health.
        
        Returns:
            Health status response
            
        TODO: Implement health check
        - GET /health
        - Handle connection errors
        - Return status
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def ingest(self, files: List[Any]) -> Dict[str, Any]:
        """
        Upload and ingest documents.
        
        Args:
            files: List of Streamlit UploadedFile objects
            
        Returns:
            Ingestion response with chunk count and errors
        """
        try:
            # Prepare files for upload
            files_data = []
            for uploaded_file in files:
                # Reset file pointer to beginning
                uploaded_file.seek(0)
                files_data.append(
                    ("files", (uploaded_file.name, uploaded_file, uploaded_file.type))
                )
            
            # POST to /ingest endpoint
            response = requests.post(
                f"{self.base_url}/ingest",
                files=files_data,
                timeout=300  # 5 minutes for large files
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            return {"ok": False, "added_chunks": 0, "errors": ["Request timed out"]}
        except requests.exceptions.RequestException as e:
            return {"ok": False, "added_chunks": 0, "errors": [f"Request failed: {str(e)}"]}
        except Exception as e:
            return {"ok": False, "added_chunks": 0, "errors": [f"Error: {str(e)}"]}
    
    def query(self, query_text: str, top_k: int = 12) -> Dict[str, Any]:
        """
        Query the document corpus.
        
        Args:
            query_text: User's question
            top_k: Number of chunks to retrieve
            
        Returns:
            Query response with summary and citations
        """
        try:
            # POST to /query endpoint
            response = requests.post(
                f"{self.base_url}/query",
                json={"query": query_text, "top_k": top_k},
                timeout=60  # 60 seconds for LLM generation
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            return {
                "query": query_text,
                "summary": "Request timed out. Please try again.",
                "confidence": 0.0,
                "subtopics": [],
                "citations_flat": [],
                "error": "timeout"
            }
        except requests.exceptions.RequestException as e:
            error_detail = "Unknown error"
            try:
                error_detail = response.json().get("detail", str(e))
            except:
                error_detail = str(e)
            
            return {
                "query": query_text,
                "summary": f"Query failed: {error_detail}",
                "confidence": 0.0,
                "subtopics": [],
                "citations_flat": [],
                "error": str(e)
            }
        except Exception as e:
            return {
                "query": query_text,
                "summary": f"Error: {str(e)}",
                "confidence": 0.0,
                "subtopics": [],
                "citations_flat": [],
                "error": str(e)
            }
    
    def get_corpus_stats(self) -> Dict[str, Any]:
        """
        Get corpus statistics from vector store.
        
        Returns:
            Stats including document count and chunk count
        """
        try:
            response = requests.get(f"{self.base_url}/stats", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"chunk_count": 0, "file_count": 0, "files": [], "error": str(e)}
    
    def clear_corpus(self) -> Dict[str, Any]:
        """
        Clear the entire corpus.
        
        WARNING: This action is irreversible and will delete all documents.
        
        Returns:
            Success status with deletion count
        """
        try:
            response = requests.delete(f"{self.base_url}/corpus", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_detail = "Unknown error"
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_detail = e.response.json().get("detail", str(e))
            except:
                error_detail = str(e)
            
            return {
                "ok": False,
                "message": f"Failed to clear corpus: {error_detail}",
                "deleted_chunks": 0
            }
        except Exception as e:
            return {
                "ok": False,
                "message": f"Error: {str(e)}",
                "deleted_chunks": 0
            }

