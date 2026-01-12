"""
Streamlit UI for Email Attachment Extraction System

Phase 1: Folder Selection & Extraction ONLY
Local-first, Windows-compatible UI layer.
"""
import streamlit as st
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import UI components
import state_manager
from components import folder_selector, api_key_manager, intent_input, results_viewer


def main():
    """Main application entry point."""
    
    # Page configuration
    st.set_page_config(
        page_title="Attachment Extraction System",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    state_manager.init_session_state()
    
    # App header
    st.title("📄 Email Attachment Extraction System")
    st.caption("Local-first document processing and knowledge extraction")
    
    st.markdown("---")
    
    # Main content area
    # Phase 1: Folder Selection & Extraction
    folder_selector.render()
    
    st.markdown("---")
    
    # Phase 2A: API Key Management
    api_key_manager.render()
    
    st.markdown("---")
    
    # Phase 2A: Intent Input
    intent_input.render()
    
    # Phase 2B: Results Viewer (shows if analysis results exist)
    if state_manager.get_analysis_history():
        st.markdown("---")
        results_viewer.render()
    
    st.markdown("---")
    
    # Footer information
    with st.expander("ℹ️ About this system"):
        st.markdown("""
        ### Local-First Document Processing
        
        This system processes email attachments (PDFs, images, CSVs) to extract structured data.
        
        **Architecture:**
        - **Phase 1:** Perception - Extract knowledge from documents (OCR, patterns)
        - **Phase 2A:** Intelligence - Analyze with custom intents (semantic reasoning)
        - **Phase 2B (Coming):** Results Viewer - Visualize and filter results
        
        **Current Features:**
        - ✅ Local processing (Windows)
        - ✅ OCR for scanned documents
        - ✅ Pattern-based field extraction
        - ✅ CSV row-by-row processing
        - ✅ Confidence scoring
        - ✅ API key validation
        - ✅ Intent-driven semantic analysis
        - ✅ Multiple intent runs on same data
        
        **Data Storage:**
        - All results saved to `output/` directory
        - Individual records in JSON format
        - Timestamped semantic analysis results
        - Summary reports generated
        - Logs in `logs/` directory
        
        **Privacy:**
        - All processing happens on your laptop
        - API calls only to Google Gemini (text only, no files)
        - No authentication required
        - Single-user local system
        """)
    
    # System status in sidebar
    with st.sidebar:
        st.header("System Status")
        
        # Check dependencies
        from orchestrator import check_dependencies
        deps_ok, deps_message = check_dependencies()
        
        if deps_ok:
            st.success("✅ All dependencies OK")
        else:
            st.error("⚠️ Dependencies missing")
            st.caption(deps_message)
        
        st.markdown("---")
        
        # Session info
        st.subheader("Current Session")
        st.caption(f"**Extraction Status:** {state_manager.get_extraction_status()}")
        
        if st.session_state.get('folder_path'):
            st.caption(f"**Selected Folder:** {Path(st.session_state.folder_path).name}")
        
        if st.session_state.get('extraction_output_path'):
            st.caption(f"**Output:** {st.session_state.extraction_output_path}")
        
        # Phase 2A status
        if state_manager.is_api_key_validated():
            st.caption("**API Key:** ✅ Validated")
        
        analysis_count = len(state_manager.get_analysis_history())
        if analysis_count > 0:
            st.caption(f"**Analyses Run:** {analysis_count}")
        
        st.markdown("---")
        
        # Debug controls (optional, can remove in production)
        with st.expander("🔧 Debug Controls"):
            if st.button("Reset Extraction State"):
                state_manager.reset_extraction()
                st.rerun()


if __name__ == "__main__":
    main()
