"""
Session state management for Streamlit UI.
Centralized state handling for the extraction workflow.
"""
import streamlit as st


def init_session_state():
    """
    Initialize session state variables on first load.
    """
    # Phase 1: Extraction
    if 'folder_path' not in st.session_state:
        st.session_state.folder_path = None
    
    if 'extraction_status' not in st.session_state:
        st.session_state.extraction_status = 'not_run'  # 'not_run' | 'running' | 'completed' | 'error'
    
    if 'extraction_output_path' not in st.session_state:
        st.session_state.extraction_output_path = None
    
    if 'extraction_message' not in st.session_state:
        st.session_state.extraction_message = None
    
    # Phase 2: API Key & Analysis
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = None
    
    if 'api_key_validated' not in st.session_state:
        st.session_state.api_key_validated = False
    
    if 'api_validation_message' not in st.session_state:
        st.session_state.api_validation_message = None
    
    # Analysis history: list of dicts with {intent, timestamp, output_path}
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    
    if 'selected_analysis_idx' not in st.session_state:
        st.session_state.selected_analysis_idx = 0
    
    # Hydrate state from disk on first load
    _hydrate_state_from_disk()


def _hydrate_state_from_disk():
    """
    Check disk for existing extraction output and update session state accordingly.
    This allows the UI to resume from where it left off after restart.
    """
    import os
    from pathlib import Path
    
    # Only hydrate on first load (not already set)
    if st.session_state.extraction_status != 'not_run':
        return
    
    # Check if extraction output exists
    output_dir = Path('output')
    index_file = output_dir / 'index.json'
    
    if index_file.exists():
        # Extraction has already been completed
        st.session_state.extraction_status = 'completed'
        st.session_state.extraction_output_path = str(output_dir)
        st.session_state.extraction_message = "Extraction output detected on disk (previously completed)"
        
        # Also check for existing semantic analysis results
        _hydrate_semantic_results(output_dir)


def _hydrate_semantic_results(output_dir: Path):
    """
    Detect existing semantic analysis JSON files and add them to history.
    """
    import json
    from datetime import datetime
    
    # Find all semantic analysis files
    semantic_files = sorted(output_dir.glob('semantic_analysis_*.json'))
    
    for semantic_file in semantic_files:
        try:
            # Load the file to extract metadata
            with open(semantic_file, 'r') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            intent = metadata.get('intent', 'Unknown intent')
            timestamp = metadata.get('generated_at', metadata.get('timestamp', 'Unknown'))
            
            # Check if already in history (by output path)
            already_added = any(
                h['output_path'] == str(semantic_file) 
                for h in st.session_state.analysis_history
            )
            
            if not already_added:
                # Add to history
                st.session_state.analysis_history.append({
                    'intent': intent,
                    'timestamp': timestamp,
                    'output_path': str(semantic_file)
                })
        
        except Exception:
            # Skip files that can't be loaded
            continue
    
    # Set selected index to most recent
    if st.session_state.analysis_history:
        st.session_state.selected_analysis_idx = len(st.session_state.analysis_history) - 1


def set_folder_path(path: str):
    """Set the selected folder path."""
    st.session_state.folder_path = path


def start_extraction():
    """Mark extraction as running."""
    st.session_state.extraction_status = 'running'
    st.session_state.extraction_message = None


def complete_extraction(success: bool, message: str, output_path: str = None):
    """
    Mark extraction as completed.
    
    Args:
        success: Whether extraction succeeded
        message: Status message to display
        output_path: Path to output directory if successful
    """
    if success:
        st.session_state.extraction_status = 'completed'
        st.session_state.extraction_output_path = output_path
    else:
        st.session_state.extraction_status = 'error'
    
    st.session_state.extraction_message = message


def lock_extraction() -> bool:
    """
    Check if extraction section should be locked.
    
    Returns:
        True if extraction is completed and section should be disabled
    """
    return st.session_state.extraction_status == 'completed'


def is_extraction_running() -> bool:
    """Check if extraction is currently running."""
    return st.session_state.extraction_status == 'running'


def get_extraction_status() -> str:
    """Get current extraction status."""
    return st.session_state.extraction_status


def reset_extraction():
    """Reset extraction state (for debugging/testing)."""
    st.session_state.extraction_status = 'not_run'
    st.session_state.extraction_output_path = None
    st.session_state.extraction_message = None


# Phase 2: API Key Management

def set_api_key(api_key: str):
    """Store API key in session state."""
    st.session_state.gemini_api_key = api_key


def validate_api_key_success(message: str = None):
    """Mark API key as validated."""
    st.session_state.api_key_validated = True
    st.session_state.api_validation_message = message or "API key validated successfully"


def validate_api_key_failure(message: str):
    """Mark API key as invalid."""
    st.session_state.api_key_validated = False
    st.session_state.api_validation_message = message


def is_api_key_validated() -> bool:
    """Check if API key has been validated."""
    return st.session_state.api_key_validated


def get_api_key() -> str:
    """Get stored API key."""
    return st.session_state.gemini_api_key


# Phase 2: Analysis History Management

def add_analysis_result(intent: str, timestamp: str, output_path: str):
    """
    Add a new analysis result to history.
    
    Args:
        intent: User's natural language intent
        timestamp: ISO timestamp of analysis
        output_path: Path to semantic analysis output file
    """
    st.session_state.analysis_history.append({
        'intent': intent,
        'timestamp': timestamp,
        'output_path': output_path
    })
    # Auto-select the newest analysis
    st.session_state.selected_analysis_idx = len(st.session_state.analysis_history) - 1


def get_analysis_history() -> list:
    """Get list of all analysis results."""
    return st.session_state.analysis_history


def get_selected_analysis():
    """Get currently selected analysis result."""
    if not st.session_state.analysis_history:
        return None
    idx = st.session_state.selected_analysis_idx
    if 0 <= idx < len(st.session_state.analysis_history):
        return st.session_state.analysis_history[idx]
    return None


# Safe getters with fallbacks

def get_extraction_output_path_safe() -> str:
    """Get extraction output path with fallback."""
    return st.session_state.get('extraction_output_path', 'output')


def has_extraction_output() -> bool:
    """Check if extraction has produced output."""
    import os
    from pathlib import Path
    output_path = get_extraction_output_path_safe()
    index_file = Path(output_path) / 'index.json'
    return index_file.exists()

