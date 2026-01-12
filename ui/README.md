# Streamlit UI - Phase 1

## Quick Start

### 1. Install Streamlit

```powershell
pip install streamlit
```

Or install all dependencies:
```powershell
pip install -r requirements.txt
```

### 2. Set API Key (Required for Extraction)

```powershell
$env:GOOGLE_API_KEY = "your-gemini-api-key-here"
```

### 3. Launch UI

```powershell
cd c:\Users\Navee\OneDrive\Desktop\attachment-extractor
streamlit run ui/app.py
```

The UI will open in your browser at `http://localhost:8501`

---

## Phase 1: Folder Selection & Extraction

This is the **perception-only** interface - no intelligence, no semantic analysis.

### What It Does

1. **Select Folder** - Choose a local folder containing your files
2. **Run Extraction** - Click button to start processing
3. **Monitor Progress** - See status updates in real-time
4. **Lock Section** - Once complete, extraction cannot be re-run

### What It Doesn't Do (Yet)

❌ API key input (uses environment variable)  
❌ Intent-based analysis  
❌ Results viewer  
❌ Semantic reasoning  

**These are Phase 2 features - deliberately NOT included.**

---

## How It Works

### UI Flow

```
User selects folder
    ↓
User clicks "Run Extraction"
    ↓
UI calls orchestrator.run_extraction()
    ↓
Orchestrator runs src/main.py as subprocess
    ↓
Extraction pipeline processes files
    ↓
Results written to output/index.json
    ↓
UI shows "Completed" and locks section
```

### Files Created

- `ui/app.py` - Main Streamlit application entry point
- `ui/state_manager.py` - Session state management
- `ui/orchestrator.py` - Bridge to backend (subprocess runner)
- `ui/components/folder_selector.py` - Phase 1 UI component

### Session State

The UI tracks:
- `folder_path` - Selected folder
- `extraction_status` - 'not_run' | 'running' | 'completed' | 'error'
- `extraction_output_path` - Path to output directory
- `extraction_message` - Status message

---

## Architecture Principles

### Strict Phase Separation

✅ **Phase 1 (This UI):** Perception  
   - Folder selection  
   - OCR + parsing  
   - Pattern extraction  
   - Runs once  
   - No API key needed (set via env)  

✅ **Phase 2 (Not Yet Built):** Intelligence  
   - API key input  
   - Intent specification  
   - Semantic reasoning  
   - Multiple intents on same data  

### UI as Thin Layer

The UI **orchestrates** but **does not process**.

All extraction logic stays in `src/main.py` - unchanged.

The UI just:
1. Calls extraction as subprocess
2. Displays status
3. Locks after completion

---

## Troubleshooting

### "GOOGLE_API_KEY environment variable not set"

Set it in PowerShell:
```powershell
$env:GOOGLE_API_KEY = "your-key-here"
```

Or add to your PowerShell profile for persistence.

### "Extraction script not found"

Make sure you're running from the project root:
```powershell
cd c:\Users\Navee\OneDrive\Desktop\attachment-extractor
streamlit run ui/app.py
```

### UI doesn't update after extraction

Click the "Refresh" button in Streamlit or press `R` in the browser.

### Want to re-run extraction

Use the "Reset Extraction State" button in the sidebar debug controls, or restart the Streamlit app.

---

## Next Steps (Phase 2)

After Phase 1 is validated:

1. **API Key Manager** - UI component for key input & validation
2. **Intent Input** - Text area for natural language intent
3. **Results Viewer** - Display semantic analysis results
4. **Intent-aware Semantic Analyzer** - Modify backend to accept intent

**Phase 2 is NOT implemented yet.**

---

## Technical Notes

### Subprocess Execution

Extraction runs as subprocess to avoid blocking Streamlit.

**Limitation:** Current implementation blocks during execution. For production, consider:
- Async execution with status polling
- Background worker threads
- Progress updates via log file monitoring

### State Persistence

Session state is **in-memory only**. Refreshing the page resets state.

For production, consider persisting to:
- `output/.ui_state.json`
- Browser local storage
- SQLite database

### Windows Compatibility

All paths use `os.path` and `Path` for cross-platform support.

Subprocess uses `sys.executable` to ensure correct Python interpreter.

---

## File Structure

```
ui/
├── app.py                          # Main entry point
├── state_manager.py                # Session state utilities
├── orchestrator.py                 # Backend bridge (subprocess runner)
└── components/
    ├── __init__.py
    └── folder_selector.py          # Phase 1 component
```

---

**Created:** January 11, 2026  
**Phase:** 1 of 2 (Perception only)  
**Status:** Ready for testing
