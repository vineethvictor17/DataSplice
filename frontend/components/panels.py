"""
UI panels for file upload and query input.
"""

import streamlit as st
from typing import List, Optional


def render_sidebar(backend_client) -> Optional[List]:
    """
    Render sidebar with file upload and corpus management.
    
    Args:
        backend_client: BackendClient instance
        
    Returns:
        List of uploaded files or None
        
    TODO: Implement full sidebar functionality
    - File uploader for PDF/DOCX/TXT
    - Display current corpus count
    - Clear corpus button with confirmation
    - Status messages for upload success/failure
    """
    # Initialize stats in session state
    if "corpus_stats" not in st.session_state:
        st.session_state.corpus_stats = {"chunk_count": 0, "file_count": 0, "files": []}
    
    st.markdown("Upload documents to build your research corpus")
    
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Upload PDF, DOCX, or TXT files"
    )
    
    if uploaded_files:
        if st.button("📤 Ingest Documents", use_container_width=True):
            with st.spinner("Processing documents..."):
                try:
                    # Call backend /ingest endpoint
                    result = backend_client.ingest(uploaded_files)
                    
                    if result.get("ok"):
                        st.success(f"✓ Successfully ingested {result.get('added_chunks', 0)} chunks!")
                        if result.get("errors"):
                            st.warning(f"Warnings: {', '.join(result['errors'])}")
                        
                        # Refresh stats immediately after ingestion
                        try:
                            fresh_stats = backend_client.get_corpus_stats()
                            st.session_state.corpus_stats = fresh_stats
                        except Exception as e:
                            st.warning(f"Could not refresh stats: {e}")
                        
                        # Force rerun to update UI
                        st.rerun()
                    else:
                        st.error(f"Ingestion failed: {', '.join(result.get('errors', ['Unknown error']))}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # Display corpus stats (refresh on every render to stay current)
    try:
        # Always fetch fresh stats to ensure accuracy
        stats = backend_client.get_corpus_stats()
        # Update session state with fresh stats
        st.session_state.corpus_stats = stats
    except Exception as e:
        # Fallback to session state if fetch fails
        stats = st.session_state.corpus_stats
    
    # Display metrics (Streamlit will automatically update these on rerun)
    st.metric("Documents in Corpus", stats.get("file_count", 0))
    st.metric("Total Chunks", stats.get("chunk_count", 0))
    
    # Add refresh button for manual update
    if st.button("🔄 Refresh Stats", use_container_width=True, help="Manually refresh corpus statistics"):
        try:
            fresh_stats = backend_client.get_corpus_stats()
            st.session_state.corpus_stats = fresh_stats
            st.rerun()
        except Exception as e:
            st.error(f"Failed to refresh stats: {e}")
    
    # Clear corpus button with confirmation
    if "show_clear_confirm" not in st.session_state:
        st.session_state.show_clear_confirm = False
    
    if st.session_state.show_clear_confirm:
        st.warning("⚠️ **WARNING:** This will permanently delete all documents in the corpus!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Clear", use_container_width=True, type="primary"):
                with st.spinner("Clearing corpus..."):
                    try:
                        result = backend_client.clear_corpus()
                        
                        if result.get("ok"):
                            deleted_count = result.get("deleted_chunks", 0)
                            st.success(f"✓ Corpus cleared! Deleted {deleted_count} chunks.")
                            
                            # Reset confirmation state
                            st.session_state.show_clear_confirm = False
                            
                            # Clear session state stats
                            st.session_state.corpus_stats = {"chunk_count": 0, "file_count": 0, "files": []}
                            
                            # Clear query response if exists
                            if "query_response" in st.session_state:
                                st.session_state.query_response = None
                            
                            # Force rerun to update UI
                            st.rerun()
                        else:
                            st.error(f"Failed to clear corpus: {result.get('message', 'Unknown error')}")
                            st.session_state.show_clear_confirm = False
                    except Exception as e:
                        st.error(f"Error clearing corpus: {str(e)}")
                        st.session_state.show_clear_confirm = False
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_clear_confirm = False
                st.rerun()
    else:
        if st.button("🗑️ Clear Corpus", use_container_width=True, help="Delete all documents from the corpus"):
            st.session_state.show_clear_confirm = True
            st.rerun()
    
    return uploaded_files


def render_query_panel() -> str:
    """
    Render query input panel.
    
    Returns:
        Query text entered by user
    """
    st.subheader("Ask a Question")
    
    query_text = st.text_area(
        "Enter your research question",
        placeholder="What are the main findings about X?",
        height=100,
        help="Ask a specific question about your document corpus"
    )
    
    # Advanced options (collapsed by default)
    with st.expander("⚙️ Advanced Options"):
        top_k = st.slider(
            "Number of chunks to retrieve",
            min_value=5,
            max_value=30,
            value=12,
            help="More chunks = more context but slower processing"
        )
        
        # TODO: Store top_k in session state or pass to query function
    
    return query_text

