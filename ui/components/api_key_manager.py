"""
API Key Manager Component - Phase 2A: API Key Input & Validation

Allows user to enter and validate Google Gemini API key.
Unlocks intent section after successful validation.
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from state_manager import (
    set_api_key,
    validate_api_key_success,
    validate_api_key_failure,
    is_api_key_validated,
    get_api_key,
    lock_extraction
)
from orchestrator import validate_api_key


def render():
    """
    Render the API key input and validation section.
    """
    st.header("🔑 Phase 2A: API Key Setup")
    
    # Only show this section if extraction is complete
    if not lock_extraction():
        st.info("⏳ Complete Phase 1 (Extraction) first before setting up API key.")
        return
    
    is_validated = is_api_key_validated()
    
    # Show validation status
    if is_validated:
        st.success("✅ API key validated and ready")
        if st.session_state.get('api_validation_message'):
            st.caption(st.session_state.api_validation_message)
    else:
        st.info("ℹ️ Enter your Google Gemini API key to enable semantic analysis")
    
    st.markdown("---")
    
    # API Key input
    st.subheader("Enter API Key")
    
    current_key = get_api_key() or ""
    api_key = st.text_input(
        "Google Gemini API Key",
        value=current_key,
        type="password",
        disabled=is_validated,
        help="Get your free API key at https://makersuite.google.com/app/apikey",
        placeholder="AIza..."
    )
    
    # Update session state when key changes
    if api_key and api_key != get_api_key():
        set_api_key(api_key)
    
    # Validation controls
    col1, col2 = st.columns([1, 3])
    
    with col1:
        validate_button = st.button(
            "🔍 Validate",
            disabled=is_validated or not api_key,
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        if is_validated:
            st.caption("✓ API key is valid and ready to use")
        elif not api_key:
            st.caption("Enter an API key to validate")
    
    # Handle validation
    if validate_button and api_key:
        with st.spinner("Validating API key..."):
            is_valid, message = validate_api_key(api_key)
            
            if is_valid:
                validate_api_key_success(message)
            else:
                validate_api_key_failure(message)
        
        # Force rerun to update UI
        st.rerun()
    
    # Show error message if validation failed
    if not is_validated and st.session_state.get('api_validation_message'):
        st.error(st.session_state.api_validation_message)
    
    # Help section
    with st.expander("ℹ️ About API Keys"):
        st.markdown("""
        **Google Gemini API Key**
        
        The semantic analysis layer uses Google's Gemini 1.5 Flash model to understand document content beyond pattern matching.
        
        **How to get an API key:**
        1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Sign in with your Google account
        3. Click "Create API Key"
        4. Copy the key and paste it here
        
        **Free tier includes:**
        - 15 requests per minute
        - 1 million tokens per minute
        - Sufficient for analyzing 1000+ documents
        
        **Security:**
        - API key is stored only in browser session
        - Not saved to disk
        - Cleared when you close the tab
        
        **What it's used for:**
        - Document type classification
        - Extracting key observations
        - Reasoning about operational context
        - Understanding unstructured content
        """)
