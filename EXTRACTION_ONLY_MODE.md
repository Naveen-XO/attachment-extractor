# EXTRACTION-ONLY MODE - Implementation Summary

## Overview

This system now supports **EXTRACTION-ONLY MODE** via a feature flag that completely isolates AI/LLM functionality without removing it from the codebase.

## Feature Flag Configuration

**Location**: `config/feature_flags.json`

**Default**: `ENABLE_AI: false`

```json
{
  "ENABLE_AI": false
}
```

## Behavior When ENABLE_AI=false (EXTRACTION-ONLY MODE)

### ✅ What Runs
- Full document traversal (recursive folder scanning)
- OCR on all supported files (PDFs, images, scans via Tesseract)
- Pattern-based field extraction (regex + keyword matching)
- Raw text extraction exactly as OCR returns it
- Metadata preservation (filename, page number, document boundaries)
- Existing output structure (JSON records, index, summary)

### 🚫 What Does NOT Run
- **ZERO AI module imports** - `llm_extractor.py` and `semantic_analyzer.py` are never loaded
- **ZERO LLM API calls** - No calls to Google Gemini or any other AI service
- **ZERO AI-based enrichment** - No semantic interpretation, classification, or reasoning
- **ZERO post-processing** - `semantic_postprocess.py` exits immediately with clear message

## Behavior When ENABLE_AI=true (FULL AI MODE)

### ✅ What Changes
- LLM modules (`llm_extractor.py`, `semantic_analyzer.py`) are imported on-demand
- Google Gemini API is initialized and available for use
- LLM fallback extraction triggers when pattern matching is insufficient
- Semantic post-processing can be run via `semantic_postprocess.py`

## Technical Implementation

### 1. Lazy/Conditional Imports
AI modules are **only imported at runtime when needed**:

```python
# main.py - AI modules imported conditionally
if enable_ai:
    from extractors.llm_extractor import LLMExtractor
    llm_extractor = LLMExtractor(logger, api_key=api_key)
else:
    llm_extractor = None  # No import, no instantiation
```

### 2. No-op Handling
When AI is disabled, the `field_extractor` receives `None` for `llm_extractor`:

```python
# field_extractor.py
self.ai_enabled = llm_extractor is not None

if self.ai_enabled and should_trigger_llm:
    # LLM logic here - never executed when ai_enabled=False
    pass
```

### 3. Early Exit for Semantic Processing
```python
# semantic_postprocess.py
if not enable_ai:
    print("SEMANTIC ANALYSIS DISABLED")
    return 0  # Exit before importing SemanticAnalyzer
```

## Modified Files

1. **`config/feature_flags.json`** - NEW - Feature flag configuration
2. **`src/main.py`** - Conditional LLM import, flag loading, API key optional when AI disabled
3. **`src/extractors/field_extractor.py`** - Accept None for llm_extractor, check ai_enabled flag
4. **`semantic_postprocess.py`** - Early exit when AI disabled, conditional import

## Files NOT Modified (AI Logic Preserved)

- `src/extractors/llm_extractor.py` - Unchanged, not loaded when AI disabled
- `src/extractors/semantic_analyzer.py` - Unchanged, not loaded when AI disabled
- All OCR and pattern extraction logic - Unchanged
- Output format and structure - Unchanged

## Running the System

### Extraction-Only Mode (Default)
```powershell
# No API key required when ENABLE_AI=false
python src\main.py --input "path\to\input"
```

### Full AI Mode
```powershell
# 1. Edit config/feature_flags.json -> set ENABLE_AI: true
# 2. Set API key
$env:GOOGLE_API_KEY = "your-key-here"

# 3. Run normally
python src\main.py --input "path\to\input"
```

### Running Semantic Post-Processing
```powershell
# Only works when ENABLE_AI=true
python semantic_postprocess.py
```

## Verification Commands

### Confirm ZERO LLM Calls in Logs
```powershell
# After running in ENABLE_AI=false mode:
Select-String -Path logs\processing.log -Pattern "LLM|Gemini|semantic"
# Should only show: "AI disabled - LLM extraction skipped"
```

### Confirm AI Modules Not Imported
```powershell
# Check for import errors when google.generativeai is not installed
# With ENABLE_AI=false, system should run without the genai package
pip uninstall -y google-generativeai

# This should still work:
python src\main.py --input "test_path" --test-mode
```

### Confirm Pattern Extraction Still Works
```powershell
# Run test mode and verify records are created
python src\main.py --input "path\to\input" --test-mode

# Check output/index.json for extracted fields
# extraction_method should be "pattern" or "none", never "llm" or "hybrid"
```

## Mental Model

```
ENABLE_AI = false:
  Input → OCR → Pattern Matching → Output
  (Deterministic document digitization pipeline)

ENABLE_AI = true:
  Input → OCR → Pattern Matching → [LLM Fallback if needed] → Output
  (Hybrid extraction with AI assistance)
```

## Guarantees

### When ENABLE_AI=false:
1. ✅ **ZERO AI module imports** - Confirmed via conditional import blocks
2. ✅ **ZERO LLM API calls** - Confirmed via `llm_extractor = None` and `ai_enabled = False`
3. ✅ **Full OCR functionality** - OCR modules always imported and active
4. ✅ **Pattern extraction active** - Text parsing always runs
5. ✅ **No API key required** - System runs without GOOGLE_API_KEY
6. ✅ **Same output format** - JSON structure unchanged

### When ENABLE_AI=true:
1. ✅ **Full AI functionality** - All modules loaded and active
2. ✅ **Hybrid extraction** - Pattern + LLM fallback
3. ✅ **Semantic analysis available** - Post-processing enabled
4. ✅ **API key required** - Validates at startup

## Troubleshooting

### "AI disabled - LLM modules will not be imported"
- ✅ **Expected** - This confirms AI is properly disabled
- System is running in extraction-only mode

### "ERROR: Google Gemini API key required when ENABLE_AI=true"
- Set feature flag to `false` OR provide API key
- API key only required when AI is enabled

### Semantic postprocess shows "SEMANTIC ANALYSIS DISABLED"
- ✅ **Expected** when ENABLE_AI=false
- Enable AI in feature_flags.json to use semantic features

## Future Enhancements

To re-enable AI:
1. Edit `config/feature_flags.json`
2. Change `"ENABLE_AI": false` to `"ENABLE_AI": true`
3. Provide Google Gemini API key
4. Restart the pipeline

No code changes needed - pure configuration toggle.

---

**Last Updated**: 2026-01-13  
**Mode**: EXTRACTION-FIRST with AI isolated and unreachable by default
