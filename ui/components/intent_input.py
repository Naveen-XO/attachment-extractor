"""
Intent Input Component - Phase 2A: Intent-Driven Semantic Analysis

Allows user to specify natural language intent and run semantic analysis.
Supports multiple intents on the same extracted data.
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from state_manager import (
    is_api_key_validated,
    get_api_key,
    lock_extraction,
    add_analysis_result,
    get_analysis_history
)
from orchestrator import analyze_with_intent


# Example intents to show users
EXAMPLE_INTENTS = [
    "Identify all urgent or time-sensitive pickups",
    "Find documents with weight discrepancies or unusual values",
    "List all deliveries scheduled for this week",
    "Show documents mentioning delays, exceptions, or special handling",
    "Identify documents missing critical information",
    "Find all documents related to a specific customer or reference number",
    "Extract pricing and payment terms from invoices",
    "Identify documents requiring immediate action"
]


def render():
    """
    Render the intent input and analysis section.
    """
    st.header("🎯 Phase 2A: Intent-Driven Analysis")
    
    # Check prerequisites
    if not lock_extraction():
        st.info("⏳ Complete Phase 1 (Extraction) first")
        return
    
    if not is_api_key_validated():
        st.info("🔑 Validate your API key first (Section above)")
        return
    
    # Show analysis history summary
    history = get_analysis_history()
    if history:
        st.success(f"✅ {len(history)} analysis {'run' if len(history) == 1 else 'runs'} completed")
        
        # Analysis selector
        selected_idx = st.selectbox(
            "View Previous Analysis",
            range(len(history)),
            index=st.session_state.get('selected_analysis_idx', len(history) - 1),
            format_func=lambda i: f"{history[i]['timestamp']} - {history[i]['intent'][:60]}{'...' if len(history[i]['intent']) > 60 else ''}",
            help="Select a previous analysis to view in the Results Viewer below"
        )
        st.session_state.selected_analysis_idx = selected_idx
    else:
        st.info("ℹ️ Enter your analysis intent below")
    
    st.markdown("---")
    
    # Intent input
    st.subheader("Specify Your Intent")
    
    intent = st.text_area(
        "What would you like to understand from the extracted documents?",
        height=100,
        placeholder="Example: Identify all urgent deliveries that need immediate attention...",
        help="Describe what you want to learn or extract from your documents in natural language"
    )
    
    # Show examples
    with st.expander("💡 Example Intents"):
        st.markdown("**Click an example to copy:**")
        for idx, example in enumerate(EXAMPLE_INTENTS):
            if st.button(f"📋 {example}", key=f"example_{idx}"):
                st.session_state.intent_example = example
                st.rerun()
    
    # Handle example selection
    if 'intent_example' in st.session_state:
        intent = st.session_state.intent_example
        del st.session_state.intent_example
    
    st.markdown("---")
    
    # Analysis controls
    st.subheader("Run Analysis")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        analyze_button = st.button(
            "▶️ Analyze",
            disabled=not intent or len(intent.strip()) < 10,
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        if not intent or len(intent.strip()) < 10:
            st.caption("Enter an intent (at least 10 characters)")
        else:
            st.caption(f"Ready to analyze with your custom intent")
    
    # Handle analysis
    if analyze_button and intent:
        # Get knowledge path from Phase 1
        knowledge_path = st.session_state.get('extraction_output_path')
        if not knowledge_path:
            knowledge_path = "output"  # Default
        
        index_file = Path(knowledge_path) / "index.json"
        
        if not index_file.exists():
            st.error(f"❌ Extraction output not found at {index_file}")
            return
        
        # Run analysis
        with st.spinner(f"🔄 Running semantic analysis with your intent..."):
            api_key = get_api_key()
            success, message, output_path = analyze_with_intent(
                str(index_file),
                api_key,
                intent
            )
        
        if success:
            # Add to history
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            add_analysis_result(intent, timestamp, output_path)
            
            st.success(f"✅ {message}")
            st.caption(f"Results saved to: `{output_path}`")
            
            # Auto-rerun to update history display
            st.rerun()
        else:
            st.error(f"❌ {message}")
    
    # Show analysis history
    if history:
        st.markdown("---")
        st.subheader("Analysis History")
        
        for idx, analysis in enumerate(reversed(history)):
            with st.expander(f"🕒 {analysis['timestamp']} - Analysis #{len(history) - idx}"):
                st.markdown(f"**Intent:** {analysis['intent']}")
                st.caption(f"**Output:** `{analysis['output_path']}`")
                
                # Preview button (for Phase 2B)
                st.caption("_Results viewer coming in Phase 2B_")
    
    # Help section
    with st.expander("ℹ️ How Intent-Driven Analysis Works"):
        st.markdown("""
        **Phase 2: Intelligence (Human-Guided)**
        
        This is where you apply semantic reasoning to your already-extracted data.
        
        **What happens when you click "Analyze":**
        
        1. **No re-extraction** - Uses existing data from `output/index.json`
        2. **Intent-aware prompting** - Your intent guides the AI's analysis
        3. **Document understanding** - AI reads each document's extracted text
        4. **Observation extraction** - Identifies relevant information matching your intent
        5. **Reasoning** - Explains why each observation matters
        6. **Results storage** - Saves to timestamped JSON file
        
        **Key features:**
        
        - ✅ **Multiple intents** - Run different analyses on same data
        - ✅ **No re-processing** - Phase 1 data is reused
        - ✅ **Timestamped outputs** - Each analysis stored separately
        - ✅ **Context-aware** - AI understands your specific business need
        
        **Performance:**
        - ~2-3 seconds per document
        - 100 documents ≈ 5-10 minutes
        - 1000 documents ≈ 30-60 minutes
        
        **What you get:**
        - Document type classification
        - Key observations with confidence scores
        - Operational reasoning
        - Actionability hints
        
        **Next step (Phase 2B):**
        - Results viewer UI
        - Filters and search
        - Export capabilities
        """)
