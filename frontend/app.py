"""
DataSplice Streamlit frontend.

Main application interface for uploading documents and querying the corpus.
"""

import streamlit as st
import json
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontend.components.panels import render_sidebar
from frontend.components.evidence import render_evidence_table
from frontend.components.metrics import render_confidence_meter
from frontend.utils.api import BackendClient

# Page config
st.set_page_config(
    page_title="DataSplice",
    page_icon="📚",
    layout="wide"
)

# Initialize backend client
@st.cache_resource
def get_backend_client():
    """Get or create backend API client."""
    return BackendClient()

client = get_backend_client()

# Initialize session state
if "query_response" not in st.session_state:
    st.session_state.query_response = None

def main():
    """Main application flow."""
    
    # Title
    st.title("📚 DataSplice")
    st.markdown("*Research assistant with citation-backed summaries*")
    
    # Sidebar: upload and corpus management
    with st.sidebar:
        st.header("Document Corpus")
        
        uploaded_files = render_sidebar(client)
        
        # TODO: Display corpus statistics
        # - Number of documents
        # - Number of chunks
        # - Clear corpus button
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Ask a Question")
        
        # Query input panel with form for Enter key support
        with st.form(key="query_form", clear_on_submit=False):
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
            
            # Submit button (also submits on Enter in text area)
            submitted = st.form_submit_button("🔍 Generate", type="primary", use_container_width=True)
        
        if submitted and query_text:
            with st.spinner("Analyzing corpus..."):
                try:
                    # Call backend /query endpoint
                    response = client.query(query_text, top_k=top_k)
                    
                    if "error" in response:
                        st.error(f"Query failed: {response.get('summary', 'Unknown error')}")
                    else:
                        st.session_state.query_response = response
                        st.success("✓ Summary generated!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Display results
        if st.session_state.query_response:
            response = st.session_state.query_response
            
            st.markdown("---")
            st.subheader("Summary")
            
            # Summary card
            st.markdown(f"**Query:** {response['query']}")
            st.write(response['summary'])
            
            # Subtopics
            if response.get('subtopics'):
                st.markdown("### Key Findings")
                for subtopic in response['subtopics']:
                    with st.expander(f"**{subtopic['title']}**", expanded=True):
                        for bullet in subtopic['bullets']:
                            st.markdown(f"- {bullet}")
                        
                        if subtopic.get('citations'):
                            st.caption(
                                f"Sources: {', '.join(set(c['file'] for c in subtopic['citations']))}"
                            )
            
            # Evidence table
            if response.get('citations_flat'):
                st.markdown("### Evidence")
                render_evidence_table(response['citations_flat'])
            
            # Download button
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(response, indent=2),
                file_name="datasplice_response.json",
                mime="application/json"
            )
    
    with col2:
        # Confidence meter
        if st.session_state.query_response:
            render_confidence_meter(st.session_state.query_response['confidence'])
            
            # Metadata
            st.markdown("### Response Metadata")
            response = st.session_state.query_response
            st.metric("Citations", len(response.get('citations_flat', [])))
            st.metric("Subtopics", len(response.get('subtopics', [])))
            
            if response.get('raw'):
                st.caption(f"Model: {response['raw'].get('model', 'N/A')}")


if __name__ == "__main__":
    main()

