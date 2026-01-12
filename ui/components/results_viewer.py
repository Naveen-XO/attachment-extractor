"""
Results Viewer Component - Phase 2B: Semantic Analysis Results Display

Displays semantic analysis results with filtering and grouping.
"""
import streamlit as st
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from state_manager import (
    get_analysis_history,
    get_selected_analysis,
    has_extraction_output
)


def load_semantic_results(output_path: str) -> Dict[str, Any]:
    """
    Load semantic analysis results from JSON file.
    
    Args:
        output_path: Path to semantic analysis JSON file
    
    Returns:
        Parsed JSON data or None if loading fails
    """
    try:
        with open(output_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load results: {str(e)}")
        return None


def render():
    """
    Render the semantic analysis results viewer.
    """
    st.header("📊 Phase 2B: Results Viewer")
    
    # Check prerequisites
    history = get_analysis_history()
    
    if not history:
        st.info("ℹ️ No semantic analysis results yet. Run an intent analysis first (Section above).")
        return
    
    st.markdown("---")
    
    # Analysis selector
    st.subheader("Select Analysis")
    
    selected = get_selected_analysis()
    
    if not selected:
        st.warning("No analysis selected")
        return
    
    # Display selected analysis metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Timestamp", selected['timestamp'])
    with col2:
        st.caption("**Intent:**")
        st.caption(f"_{selected['intent'][:100]}..._" if len(selected['intent']) > 100 else f"_{selected['intent']}_")
    with col3:
        st.caption("**Output File:**")
        st.caption(f"`{Path(selected['output_path']).name}`")
    
    # Load results
    data = load_semantic_results(selected['output_path'])
    
    if not data:
        st.error("❌ Failed to load semantic analysis results")
        return
    
    metadata = data.get('metadata', {})
    semantic_analysis = data.get('semantic_analysis', {})
    
    # Display summary metrics
    st.markdown("---")
    st.subheader("Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Documents", metadata.get('total_records', 0))
    with col2:
        st.metric("Analyzed", metadata.get('analyzed', 0))
    with col3:
        st.metric("Skipped", metadata.get('skipped', 0))
    with col4:
        analysis_rate = (metadata.get('analyzed', 0) / max(metadata.get('total_records', 1), 1)) * 100
        st.metric("Analysis Rate", f"{analysis_rate:.0f}%")
    
    st.markdown("---")
    
    # Filters
    st.subheader("Filters")
    
    # Collect all unique document types and categories
    all_doc_types = set()
    all_categories = set()
    
    for record_id, result in semantic_analysis.items():
        if result.get('document_type'):
            all_doc_types.add(result['document_type'])
        for obs in result.get('key_observations', []):
            if obs.get('category'):
                all_categories.add(obs['category'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        doc_type_filter = st.multiselect(
            "Document Type",
            sorted(all_doc_types),
            help="Filter by document type"
        )
    
    with col2:
        category_filter = st.multiselect(
            "Observation Category",
            sorted(all_categories),
            help="Filter by observation category"
        )
    
    with col3:
        min_confidence = st.slider(
            "Minimum Confidence",
            0.0, 1.0, 0.0,
            help="Show only observations above this confidence threshold"
        )
    
    st.markdown("---")
    
    # Display results
    st.subheader("Document Results")
    
    # Get source file mapping from extraction index
    source_files = _load_source_file_mapping()
    
    displayed_count = 0
    
    for record_id, result in semantic_analysis.items():
        doc_type = result.get('document_type', 'unknown')
        
        # Apply document type filter
        if doc_type_filter and doc_type not in doc_type_filter:
            continue
        
        observations = result.get('key_observations', [])
        
        # Filter observations by category and confidence
        filtered_obs = []
        for obs in observations:
            if obs.get('confidence', 0) < min_confidence:
                continue
            if category_filter and obs.get('category') not in category_filter:
                continue
            filtered_obs.append(obs)
        
        # Skip if no observations pass filters
        if category_filter and not filtered_obs:
            continue
        
        displayed_count += 1
        
        # Get source filename
        source_file = source_files.get(record_id, record_id)
        filename = Path(source_file).name if source_file else record_id
        
        # Document expander
        with st.expander(f"📄 {filename} [{doc_type}]", expanded=displayed_count <= 3):
            # Document type badge
            st.markdown(f"**Document Type:** `{doc_type}`")
            
            # Key observations
            if filtered_obs:
                st.markdown("**Key Observations:**")
                
                for idx, obs in enumerate(filtered_obs):
                    col_left, col_right = st.columns([4, 1])
                    
                    with col_left:
                        label = obs.get('label', 'Observation')
                        value = obs.get('value', 'N/A')
                        category = obs.get('category', 'other')
                        reasoning = obs.get('reasoning', '')
                        
                        st.markdown(f"**{label}:** {value}")
                        st.caption(f"_{reasoning}_")
                        st.caption(f"Category: `{category}`")
                    
                    with col_right:
                        confidence = obs.get('confidence', 0.0)
                        st.metric("Confidence", f"{confidence:.0%}")
                    
                    if idx < len(filtered_obs) - 1:
                        st.markdown("---")
            else:
                st.caption("_No observations match the current filters_")
            
            # Actionability hint
            actionability = result.get('actionability_hint', '')
            if actionability:
                st.info(f"💡 **Actionability:** {actionability}")
            
            # Raw JSON (collapsed by default)
            with st.expander("🔍 View Raw JSON"):
                st.json(result)
    
    # Show count
    if displayed_count == 0:
        st.warning("⚠️ No documents match the current filters")
    else:
        st.success(f"✅ Displaying {displayed_count} document(s)")
    
    # Help section
    with st.expander("ℹ️ How to use the Results Viewer"):
        st.markdown("""
        **Understanding the Results**
        
        Each document shows:
        - **Document Type**: Classification of the document
        - **Key Observations**: Important information extracted
        - **Confidence**: How certain the AI is about each observation
        - **Reasoning**: Why this observation matters
        - **Actionability**: What you might need to do
        
        **Using Filters:**
        - **Document Type**: Show only specific types (invoice, logistics, etc.)
        - **Category**: Filter observations by type (identifier, date, amount, etc.)
        - **Confidence**: Hide low-confidence observations
        
        **Tips:**
        - Start with high confidence threshold (0.7+) to see clear signals
        - Lower threshold to explore tentative findings
        - Use document type filter to focus on specific workflows
        - Review raw JSON for full details if needed
        """)


def _load_source_file_mapping() -> Dict[str, str]:
    """Load mapping of record_id to source_file from extraction index."""
    try:
        from state_manager import get_extraction_output_path_safe
        index_path = Path(get_extraction_output_path_safe()) / 'index.json'
        
        if not index_path.exists():
            return {}
        
        with open(index_path, 'r') as f:
            data = json.load(f)
        
        mapping = {}
        for record in data.get('records', []):
            record_id = record.get('record_id')
            source_file = record.get('source_file')
            if record_id and source_file:
                mapping[record_id] = source_file
        
        return mapping
    
    except Exception:
        return {}
