"""
Folder Selector Component - Phase 1: Folder & Extraction

Allows user to select a folder and run extraction.
Once complete, section is locked.
"""
import streamlit as st
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from state_manager import (
    set_folder_path,
    start_extraction,
    complete_extraction,
    lock_extraction,
    is_extraction_running,
    get_extraction_status
)
from orchestrator import run_extraction


def render():
    """
    Render the folder selection and extraction section.
    """
    st.header("📁 Phase 1: Folder Selection & Extraction")
    
    # Check if section should be locked
    is_locked = lock_extraction()
    is_running = is_extraction_running()
    
    # Show status badge
    status = get_extraction_status()
    if status == 'not_run':
        st.info("ℹ️ Status: **Not Run**")
    elif status == 'running':
        st.warning("⚙️ Status: **Running...**")
    elif status == 'completed':
        st.success("✅ Status: **Completed**")
        st.caption("Section locked. Extraction has been completed.")
    elif status == 'error':
        st.error("❌ Status: **Error**")
    
    st.markdown("---")
    
    # Folder selection
    st.subheader("Select Input Folder")
    
    # Provide text input for folder path
    default_path = st.session_state.get('folder_path', '')
    folder_path = st.text_input(
        "Folder Path",
        value=default_path,
        placeholder="C:\\Users\\Navee\\Downloads\\Email Attachments-20260110T194622Z-1-001",
        disabled=is_locked,
        help="Enter the full path to the folder containing files to process"
    )
    
    # Update session state when path changes
    if folder_path and folder_path != st.session_state.get('folder_path'):
        set_folder_path(folder_path)
    
    # Validate folder exists
    folder_exists = folder_path and os.path.exists(folder_path) and os.path.isdir(folder_path)
    
    if folder_path:
        if folder_exists:
            # Count files in folder
            try:
                file_count = sum(1 for _ in Path(folder_path).rglob('*') if _.is_file())
                st.caption(f"✓ Folder found: {file_count} files detected")
            except PermissionError:
                st.caption(f"✓ Folder found (unable to count files - permission denied)")
            except Exception as e:
                st.caption(f"✓ Folder found (unable to count files)")
        else:
            st.error(f"❌ Folder not found or invalid path")
    
    st.markdown("---")
    
    # Extraction controls
    st.subheader("Run Extraction")
    
    # Show current status message if any
    if st.session_state.get('extraction_message'):
        if status == 'completed':
            st.success(st.session_state.extraction_message)
        elif status == 'error':
            st.error(st.session_state.extraction_message)
    
    # Run button
    col1, col2 = st.columns([1, 3])
    
    with col1:
        run_button = st.button(
            "▶️ Run Extraction",
            disabled=is_locked or is_running or not folder_exists or not folder_path,
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        if is_running:
            st.caption("Extraction is running. This may take several minutes...")
        elif is_locked:
            st.caption("Extraction already completed for this session.")
    
    # Handle button click
    if run_button and folder_path and folder_exists:
        # Mark as running
        start_extraction()
        
        # Show progress
        with st.spinner("Running extraction pipeline..."):
            # Actually run extraction
            success, message, output_path = run_extraction(folder_path)
            
            # Update state
            complete_extraction(success, message, output_path)
        
        # Force rerun to update UI
        st.rerun()
    
    # Help section
    with st.expander("ℹ️ How it works"):
        st.markdown("""
        **Phase 1: Perception (Machine Work)**
        
        This phase runs the extraction pipeline on your folder:
        
        1. **File Discovery** - Scans for PDFs, images, CSVs
        2. **OCR & Parsing** - Extracts text from documents
        3. **Pattern Extraction** - Identifies structured fields
        4. **Knowledge Storage** - Saves results to `output/index.json`
        
        **Important:**
        - This runs **once** per folder
        - No API key required for extraction
        - No intent required
        - Once complete, this section locks
        - Results stored locally in `output/` directory
        
        **After completion:**
        - View results in `output/summary.txt`
        - Individual records in `output/records/`
        - Logs in `logs/` directory
        """)
