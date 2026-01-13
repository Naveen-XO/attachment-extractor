# USER JOURNEY: Document Extraction System
## Complete Step-by-Step Guide

---

## Journey Overview

```
START
  |
  ├─► [ONE-TIME SETUP] → Install dependencies
  |
  ├─► [EVERY TIME] → Provide folder path → System extracts → Review results
  |
  └─► [OPTIONAL] → Enable AI for advanced analysis
```

---

## PHASE 1: ONE-TIME SETUP (Do This Once)

### Step 1.1: Install Python Dependencies

```powershell
cd c:\Users\Navee\OneDrive\Desktop\attachment-extractor
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed pytesseract, PyPDF2, pdf2image, pillow, opencv-python, ...
```

### Step 1.2: Install External Tools

**Tesseract OCR** (for image/scanned PDF processing)
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Install to default location: `C:\Program Files\Tesseract-OCR`
- Add to PATH or note installation location

**Poppler** (for PDF to image conversion)
- Download: https://github.com/oschwartz10612/poppler-windows/releases
- Extract to: `C:\poppler\` (or any location)
- Add `C:\poppler\Library\bin` to PATH

### Step 1.3: Verify Setup

```powershell
# Check feature flags
python check_flags.py
```

**Expected Output:**
```
============================================================
FEATURE FLAG STATUS
============================================================
ENABLE_AI = False
Mode: DISABLED (extraction-only)
============================================================
```

```powershell
# Run verification
python verify_extraction_mode.py
```

**Expected Output:**
```
[SUCCESS] ALL VERIFICATIONS PASSED!

Confirmed:
  [OK] ZERO AI module imports when ENABLE_AI=false
  [OK] ZERO LLM API calls when ENABLE_AI=false
  [OK] Proper feature flag isolation
  [OK] API key optional when AI disabled

System is ready for EXTRACTION-ONLY mode.
```

---

## PHASE 2: EXTRACT DOCUMENTS (Every Time)

### Step 2.1: Prepare Your Document Folder

Organize your documents in a folder structure:

```
C:\Documents\MyAttachments\
├── invoice_001.pdf
├── receipt_scan.jpg
├── data.csv
├── subfolder\
│   ├── contract.pdf
│   └── scanned_form.png
└── ...
```

**Supported File Types:**
- ✅ PDFs (text-based or scanned)
- ✅ Images (JPG, PNG, TIFF)
- ✅ CSV files
- ⚠️ Audio files (logged but skipped)

### Step 2.2: Run Extraction

**Basic Command:**
```powershell
python src\main.py --input "C:\Documents\MyAttachments"
```

**With Test Mode (first 20 files only):**
```powershell
python src\main.py --input "C:\Documents\MyAttachments" --test-mode
```

**With Custom Output Location:**
```powershell
python src\main.py --input "C:\Documents\MyAttachments" --output "C:\Results"
```

**With Debug Logging:**
```powershell
python src\main.py --input "C:\Documents\MyAttachments" --log-level DEBUG
```

### Step 2.3: Watch Processing

**Console Output You'll See:**

```
================================================================================
Email Attachment Processing System - Starting
================================================================================
AI/LLM Mode: DISABLED (extraction-only mode)
Initializing components...
AI disabled - LLM modules will not be imported

Scanning input directory: C:\Documents\MyAttachments
Found 127 files:
  pdf: 45
  image: 62
  csv: 18
  audio: 2

Processing 127 files...
[1/127] Processing invoice_001.pdf
[2/127] Processing receipt_scan.jpg
[3/127] Processing data.csv
...
[127/127] Processing final_document.pdf

Generating index and summary...

================================================================================
Processing Complete!
================================================================================
Total files: 127
Processed: 125
Skipped: 2
Records created: 348
Total time: 127.4 seconds
Output directory: output
================================================================================
```

**What's Happening Behind the Scenes:**

| File Type | Process Flow |
|-----------|-------------|
| **PDF (text)** | Extract text → Pattern match → Output JSON |
| **PDF (scanned)** | OCR → Extract text → Pattern match → Output JSON |
| **Image** | OCR → Check text length → Pattern match → Output JSON or Skip |
| **CSV** | Map columns → Extract row-by-row → Output JSON |
| **Audio** | Log and skip |

---

## PHASE 3: REVIEW RESULTS

### Step 3.1: Check the Summary

```powershell
cat output\summary.txt
```

**Example Summary:**
```
================================================================================
EXTRACTION SUMMARY
================================================================================
Processed: 2026-01-13 16:15:00

Total Files: 127
Processed: 125
Skipped: 2
Records Created: 348

By File Type:
  PDF: 45 files → 45 records
  Image: 62 files → 41 records (21 skipped - low content)
  CSV: 18 files → 262 records
  Audio: 2 files → 0 records (skipped)

Actionable Records: 142 / 348 (40.8%)

Fields Extracted:
  pickup_number: 156 records
  scheduled_date: 189 records
  weight: 178 records
  material: 203 records
  weight_unit: 165 records
  reference_number: 134 records

Average Processing Time: 1.01 seconds/file
Total Processing Time: 127.4 seconds
================================================================================
```

### Step 3.2: Explore Output Files

**Output Structure:**
```
output/
├── index.json              ← All records in one file
├── summary.txt             ← Human-readable summary (above)
└── records/                ← Individual JSON files
    ├── rec_00001.json
    ├── rec_00002.json
    ├── rec_00003.json
    └── ...
```

### Step 3.3: View Individual Records

```powershell
cat output\records\rec_00001.json
```

**Example Record:**
```json
{
  "record_id": "rec_00001",
  "source_file": "C:\\Documents\\MyAttachments\\invoice_001.pdf",
  "source_row": null,
  "file_type": "pdf",
  "extracted_fields": {
    "pickup_number": {
      "value": "PKG-2026-00123",
      "confidence": 0.95,
      "extraction_method": "pattern"
    },
    "scheduled_date": {
      "value": "2026-01-15",
      "confidence": 0.90,
      "extraction_method": "pattern"
    },
    "weight": {
      "value": 450.0,
      "confidence": 0.92,
      "extraction_method": "pattern"
    },
    "weight_unit": {
      "value": "kg",
      "confidence": 0.95,
      "extraction_method": "pattern"
    },
    "material": {
      "value": "Mixed Recyclables",
      "confidence": 0.85,
      "extraction_method": "pattern"
    },
    "reference_number": {
      "value": "REF-ABC-789",
      "confidence": 0.88,
      "extraction_method": "pattern"
    }
  },
  "actionable": true,
  "notes": "Used pattern-based extraction; Extracted 6/6 fields",
  "metadata": {
    "processed_at": "2026-01-13T16:15:23+05:30",
    "processing_time_ms": 1234,
    "extraction_method": "pattern",
    "average_confidence": 0.91,
    "ocr_quality": 1.0
  }
}
```

### Step 3.4: Filter and Analyze

**Get Only Actionable Records:**
```powershell
# Using jq (install from https://jqlang.github.io/jq/)
jq '[.records[] | select(.actionable == true)]' output\index.json > actionable_only.json
```

**Count Records by Source:**
```powershell
jq '.records | group_by(.file_type) | map({type: .[0].file_type, count: length})' output\index.json
```

**Export to CSV:**
```powershell
python analyze_results.py --input output\index.json --output results.csv
```

### Step 3.5: Review Logs

**Processing Log:**
```powershell
cat logs\processing.log
```

**Low Confidence Records:**
```powershell
cat logs\low_confidence.log
```

**Skipped Files:**
```powershell
cat logs\skipped_files.log
```

**Errors:**
```powershell
cat logs\errors.log
```

---

## PHASE 4 (OPTIONAL): ENABLE AI FOR ADVANCED ANALYSIS

### When You Might Want AI:

- ❌ Pattern extraction confidence is low on many records
- ❌ Complex document formats not matching patterns
- ❌ Need semantic understanding of document content
- ❌ Want document classification and categorization

### Step 4.1: Get Google Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key (looks like: `AIzaSyC...`)

### Step 4.2: Enable AI in Config

Edit `config/feature_flags.json`:

```json
{
  "ENABLE_AI": true
}
```

### Step 4.3: Set API Key

```powershell
# Set for current session
$env:GOOGLE_API_KEY = "AIzaSyC_your_actual_key_here"

# OR set permanently (add to PowerShell profile)
$profile  # Show profile path
notepad $profile  # Edit and add the line above
```

### Step 4.4: Run with AI Enabled

```powershell
python src\main.py --input "C:\Documents\MyAttachments"
```

**New Output:**
```
================================================================================
Email Attachment Processing System - Starting
================================================================================
AI/LLM Mode: ENABLED          ← Now says ENABLED
AI enabled - importing LLM modules...
LLM extractor initialized     ← AI modules loaded
```

**What Changes:**
- Pattern extraction runs first (fast)
- If confidence < threshold → LLM fallback triggered (slower)
- Higher accuracy on complex documents
- Hybrid extraction (pattern + LLM)

### Step 4.5: Run Semantic Post-Processing

Analyze existing results with AI:

```powershell
python semantic_postprocess.py --index output\index.json
```

**Output:**
```json
{
  "semantic_analysis": {
    "rec_00001": {
      "document_type": "Pickup Order",
      "key_observations": [
        "Commercial waste collection scheduled",
        "Contains weight and material specifications",
        "Includes reference numbers for tracking"
      ],
      "actionability_hint": "Ready for immediate processing",
      "confidence": 0.92
    }
  }
}
```

---

## COMMON SCENARIOS

### Scenario 1: "I Just Want to Extract Data Quickly"

**Solution:** Use extraction-only mode (default)

```powershell
python src\main.py --input "C:\MyFolder" --test-mode
```

- ✅ No AI delays
- ✅ No API key needed
- ✅ Fast pattern-based extraction
- ✅ Good for structured documents

### Scenario 2: "My Documents Have Low Confidence"

**Check the logs:**
```powershell
cat logs\low_confidence.log
```

**Options:**

a) **Adjust Patterns** (if formats are consistent):
   - Edit `config/field_patterns.json`
   - Add your specific keywords and patterns
   - Re-run extraction

b) **Enable AI** (if documents are varied):
   - Follow Phase 4 steps above
   - LLM will handle complex cases
   - Expect slower processing

### Scenario 3: "Processing is Too Slow"

**Current mode:**
- PDF (text): ~200-500ms each
- PDF (scanned): ~5-15 seconds per page
- Image: ~1-3 seconds each

**Speed it up:**
1. Use `--test-mode` for small batches
2. Filter out audio files beforehand
3. Keep AI disabled (extraction-only)
4. Process in smaller folder chunks

### Scenario 4: "I Want to Process Multiple Folders"

**Batch script:**
```powershell
# process_all.ps1
$folders = @(
    "C:\Batch1",
    "C:\Batch2",
    "C:\Batch3"
)

foreach ($folder in $folders) {
    $outputDir = "output_$(Split-Path $folder -Leaf)"
    python src\main.py --input $folder --output $outputDir
}
```

### Scenario 5: "Some Files Failed to Process"

**Check error log:**
```powershell
cat logs\errors.log
```

**Common issues:**
- Corrupted PDFs → Try re-downloading
- Unsupported image format → Convert to JPG/PNG
- OCR failed → Check Tesseract installation
- Permission denied → Check file access rights

---

## MENTAL MODEL

Think of the system as a **document → data pipeline**:

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT FOLDER                         │
│  (Your messy collection of documents)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 EXTRACTION PIPELINE                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Scan    │→ │   OCR    │→ │ Pattern  │             │
│  │  Files   │  │ (if img) │  │ Matching │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                    │                    │
│                         [AI disabled by default]        │
│                                    │                    │
│                         (optional: LLM fallback)        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  STRUCTURED OUTPUT                      │
│  • index.json (all data)                               │
│  • records/*.json (individual)                          │
│  • summary.txt (stats)                                  │
│  • logs/* (details)                                     │
└─────────────────────────────────────────────────────────┘
```

**Extraction-Only Mode (Default):**
- Fast, deterministic, no AI overhead
- Perfect for structured documents with consistent patterns
- No API costs, no external dependencies

**AI-Enabled Mode (Optional):**
- Slower, but handles complex/varied documents
- Uses LLM when pattern matching fails
- Requires API key and internet connection

---

## DECISION TREE

```
Do you need AI?
│
├─ NO → Use EXTRACTION-ONLY mode (default)
│       └─ Fast, simple, no cost
│
└─ YES → When?
    │
    ├─ Documents are very inconsistent → Enable AI
    │   └─ Edit feature_flags.json, set API key
    │
    ├─ Low confidence in results → Try AI
    │   └─ Check logs first, then enable if needed
    │
    └─ Want semantic understanding → Enable AI
        └─ Run semantic_postprocess.py after extraction
```

---

## QUICK REFERENCE COMMANDS

| Task | Command |
|------|---------|
| **Extract (basic)** | `python src\main.py --input "C:\folder"` |
| **Extract (test mode)** | `python src\main.py --input "C:\folder" --test-mode` |
| **Check flags** | `python check_flags.py` |
| **Verify setup** | `python verify_extraction_mode.py` |
| **View summary** | `cat output\summary.txt` |
| **View logs** | `cat logs\processing.log` |
| **Enable AI** | Edit `config/feature_flags.json` → `ENABLE_AI: true` |
| **Set API key** | `$env:GOOGLE_API_KEY = "your-key"` |
| **Semantic analysis** | `python semantic_postprocess.py` |

---

## TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| **"Tesseract not found"** | Install Tesseract, add to PATH |
| **"Poppler not found"** | Install Poppler, add bin folder to PATH |
| **"No records created"** | Check logs/errors.log, verify file formats |
| **"Processing very slow"** | Use --test-mode, keep AI disabled, process smaller batches |
| **"Low confidence"** | Check logs/low_confidence.log, adjust patterns OR enable AI |
| **"API key error"** | Only needed if ENABLE_AI=true, set $env:GOOGLE_API_KEY |

---

## YOUR TYPICAL WORKFLOW

### Daily Use (Extraction-Only):

```powershell
# 1. Drop documents in folder
# 2. Run extraction
python src\main.py --input "C:\TodaysDocuments"

# 3. Check summary
cat output\summary.txt

# 4. Review results
code output\index.json  # or use Excel/pandas

# 5. Done!
```

**Time:** ~1-2 seconds per document  
**Cost:** $0 (no API calls)  
**Accuracy:** High (for structured documents)

### Weekly Review (With AI):

```powershell
# 1. Enable AI
# Edit config/feature_flags.json → ENABLE_AI: true

# 2. Set API key (once per session)
$env:GOOGLE_API_KEY = "your-key"

# 3. Process challenging documents
python src\main.py --input "C:\ComplexDocuments"

# 4. Run semantic analysis
python semantic_postprocess.py

# 5. Disable AI again
# Edit config/feature_flags.json → ENABLE_AI: false
```

**Time:** ~3-5 seconds per document (with LLM fallback)  
**Cost:** ~$0.001-0.01 per document (Gemini API)  
**Accuracy:** Higher (for complex/varied documents)

---

## NEXT STEPS

1. ✅ **Setup is already complete** (if you ran verification)
2. 📁 **Prepare your document folder**
3. ▶️ **Run extraction:** `python src\main.py --input "your-path"`
4. 📊 **Review results** in `output/` directory
5. 🔁 **Repeat as needed**

**You're ready to start extracting!**
