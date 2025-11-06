"""
Evidence table component for displaying citations.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any


def render_evidence_table(citations: List[Dict[str, Any]]):
    """
    Render a table of evidence citations with expandable excerpts.
    
    Args:
        citations: List of citation dictionaries
        
    TODO: Enhanced evidence display
    - Add pagination for large citation lists
    - Add filtering by source file
    - Add sorting options (by file, page, relevance)
    - Show full chunk text in expandable rows
    - Highlight query terms in excerpts
    """
    if not citations:
        st.info("No citations available")
        return
    
    st.markdown(f"**{len(citations)} sources cited**")
    
    # Convert to dataframe for display
    table_data = []
    for i, citation in enumerate(citations, 1):
        table_data.append({
            "#": i,
            "File": citation.get("file", "Unknown"),
            "Page": citation.get("page", "—"),
            "Chunk ID": citation.get("chunk_id", "")[:20] + "...",
        })
    
    df = pd.DataFrame(table_data)
    
    # Display as interactive table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Optional: expandable excerpts
    with st.expander("📄 View excerpts"):
        for i, citation in enumerate(citations, 1):
            if citation.get("excerpt"):
                st.markdown(f"**[{i}] {citation['file']} (p. {citation['page']})**")
                st.text(citation['excerpt'][:300] + "...")
                st.markdown("---")

