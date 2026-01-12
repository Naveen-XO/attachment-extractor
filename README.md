# Email Attachment Processing System

A local Windows-based system for extracting workflow-critical fields from email attachments using hybrid pattern matching and LLM-powered semantic extraction.

## Overview

This system processes email attachments (PDFs, images, CSVs) to extract structured data needed for operations workflow. It uses:

- **Pattern-based extraction** for speed and reliability
- **LLM semantic extraction** (Google Gemini) as fallback for complex cases
- **Tesseract OCR** for scanned documents and images
- **Intelligent file routing** with signal detection for images
- **Conservative confidence scoring** with actionable determination

## Features

✅ **Hybrid Extraction**: Pattern matching + LLM fallback for best accuracy  
✅ **Local Processing**: All processing happens on your Windows machine  
✅ **Smart Image Filtering**: Skips logos/signatures while processing meaningful content  
✅ **CSV Support**: Row-by-row extraction with intelligent column mapping  
✅ **Safe to Rerun**: Idempotent processing with clear logging  
✅ **Confidence Scoring**: Every field tagged with confidence (0.0-1.0)  
✅ **Actionable Flagging**: Records marked as actionable when 3 key fields meet threshold

## Quick Start

### 1. Prerequisites

**Python 3.8+** installed

**Required External Dependencies:**

1. **Tesseract OCR** (for image and scanned PDF processing)
   - Download: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to default location or note the installation path
   - Add to PATH or use `--tesseract-path` flag

2. **Poppler** (for PDF to image conversion)
   - Download: https://github.com/oschwartz10612/poppler-windows/releases
   - Extract and add `bin` folder to PATH

3. **Google Gemini API Key** (for LLM semantic extraction)
   - Get free API key: https://makersuite.google.com/app/apikey
   - Set as environment variable `GOOGLE_API_KEY` or pass via `--gemini-api-key`

### 2. Install Python Dependencies

```powershell
cd c:\Users\Navee\OneDrive\Desktop\attachment-extractor
pip install -r requirements.txt
```

### 3. Set Up Input Directory

The system expects to read from an input directory containing your email attachments. You can either:

**Option A: Create a symlink** (recommended)
```powershell
New-Item -ItemType SymbolicLink -Path ".\input" -Target "C:\Users\Navee\Downloads\Email Attachments-20260110T194622Z-1-001"
```

**Option B: Specify path directly** when running:
```powershell
python src\main.py --input "C:\Users\Navee\Downloads\Email Attachments-20260110T194622Z-1-001"
```

### 4. Set API Key

```powershell
$env:GOOGLE_API_KEY = "your-gemini-api-key-here"
```

Or add to your PowerShell profile for persistence.

### 5. Run Test Mode

Process first 20 files to validate setup:

```powershell
python src\main.py --input ".\input" --test-mode
```

### 6. Run Full Processing

```powershell
python src\main.py --input ".\input"
```

## Configuration

All configuration files are in the `config/` directory:

### `config/thresholds.json`

Controls confidence thresholds and processing rules:

- `field_confidence_threshold`: `0.75` (fields below this are flagged)
- `image_text_minimum_chars`: `50` (minimum text to process image)
- `required_fields_for_actionable`: 3 fields required
  - `pickup_number`
  - `scheduled_date`
  - `weight`

Optional fields (extracted but not required for actionable):
- `material`
- `weight_unit`
- `reference_number`

### `config/field_patterns.json`

Regex patterns and keywords for pattern-based extraction. Customize these if your documents use different formats or terminology.

### `config/file_extensions.json`

File type mappings. Add extensions if you have additional file types.

## Output Structure

```
output/
├── records/              # Individual JSON files (one per record)
│   ├── rec_00001.json
│   ├── rec_00002.json
│   └── ...
├── index.json            # Combined index of all records
└── summary.txt           # Human-readable summary report
```

### JSON Schema

Each record has this structure:

```json
{
  "record_id": "rec_00001",
  "source_file": "path/to/file.pdf",
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
      "extraction_method": "llm"
    },
    "weight": {
      "value": 450.0,
      "confidence": 0.92,
      "extraction_method": "pattern"
    },
    // ... other fields
  },
  "actionable": true,
  "notes": "Used hybrid extraction (pattern + LLM); Extracted 6/6 fields",
  "metadata": {
    "processed_at": "2026-01-11T02:30:00+05:30",
    "processing_time_ms": 1234,
    "extraction_method": "hybrid",
    "average_confidence": 0.91,
    "ocr_quality": 0.85
  }
}
```

## Logs

All logs are in the `logs/` directory:

- `processing.log` - Detailed processing log
- `skipped_files.log` - Files that were skipped (with reasons)
- `low_confidence.log` - Records with fields below threshold
- `errors.log` - Errors encountered

## Command-Line Options

```
python src\main.py [OPTIONS]

Required:
  --input PATH              Path to directory with email attachments

Optional:
  --output PATH             Output directory (default: output)
  --log-level LEVEL         DEBUG|INFO|WARNING|ERROR (default: INFO)
  --test-mode               Process only first 20 files
  --gemini-api-key KEY      Google Gemini API key (or set GOOGLE_API_KEY)
  --tesseract-path PATH     Path to tesseract.exe if not in PATH
```

## How It Works

### File Processing Flow

```
1. File Discovery
   └─> Scan input directory recursively
   └─> Catalog by type (audio, image, pdf, csv)

2. File Routing
   ├─> Audio → Skip and log
   ├─> Image → OCR check + signal detection → Extract or skip
   ├─> PDF → Text extraction → OCR if scanned → Extract
   └─> CSV → Column mapping → Row-by-row extraction

3. Field Extraction (for PDFs/Images)
   ├─> Pattern matching (fast)
   ├─> If insufficient → LLM semantic extraction
   └─> Merge results (higher confidence wins)

4. Confidence Scoring
   ├─> Pattern match: 0.9-1.0 (exact) to 0.4-0.6 (fuzzy)
   ├─> LLM extraction: 0.9 (high) to 0.4 (low certainty)
   └─> CSV mapping: 1.0 (exact) to 0.6 (inferred)

5. Actionable Determination
   └─> Check: pickup_number, scheduled_date, weight ≥ 0.75

6. Output Generation
   ├─> Individual JSON per record
   ├─> Combined index.json
   └─> Summary report
```

### Extraction Methods

**Pattern-based**: Fast regex matching with keyword proximity
- Best for: Structured documents with consistent formatting
- Confidence: High when exact patterns match

**LLM semantic**: Google Gemini 1.5 Flash with structured prompts
- Triggered when: Pattern extraction finds < 3 fields with confidence ≥ 0.5
- Best for: Unstructured text, varied formats, complex layouts
- Confidence: Varies based on LLM certainty

**CSV mapping**: Column header matching with synonyms
- Best for: Tabular data
- Confidence: Based on header match quality

**Hybrid**: Combines pattern + LLM, chooses higher confidence
- Best for: Mixed document types
- Most accurate but slower

## Troubleshooting

### "Tesseract not found"
- Install Tesseract from link above
- Add to PATH or use `--tesseract-path` flag

### "Poppler not found"  
- Install Poppler from link above
- Add `bin` folder to PATH
- Restart PowerShell

### "API key invalid"
- Verify key at https://makersuite.google.com/app/apikey
- Check environment variable: `echo $env:GOOGLE_API_KEY`

### Low accuracy / Many non-actionable records
- Review `low_confidence.log`
- Adjust patterns in `config/field_patterns.json`
- Lower threshold in `config/thresholds.json` (not recommended)
- Check if documents are very low quality (rescan at higher DPI)

### Processing very slow
- Disable `--test-mode` check if it's on
- LLM fallback adds 1-2 seconds per file
- OCR on large PDFs can take 10-30 seconds per page
- Consider processing in batches

## Performance

**Typical processing times** (estimate):
- CSV: ~50ms per row
- PDF (text): ~200-500ms
- PDF (scanned): ~5-15 seconds per page
- Image (with text): ~1-3 seconds
- Image (low content): ~100ms (skipped)

**For 6000 files** (mixed types):
- Expected time: 2-6 hours
- Parallelization: Not currently implemented (could be added)

## Security & Privacy

- All processing happens locally on your machine
- No data sent to cloud except LLM API calls:
  - Only extracted text (max 3000 chars) sent to Google Gemini
  - No files uploaded, only text content
- API key should be kept private
- Logs may contain extracted data - review before sharing

## Next Steps After Processing

1. **Review Summary**: Check `output/summary.txt`
2. **Spot Check Records**: Open a few JSON files in `output/records/`
3. **Filter Actionable**: Use `jq` or Python to filter `index.json` for `actionable: true`
4. **Review Low Confidence**: Check `logs/low_confidence.log`
5. **Manual Verification**: Review flagged records
6. **Adjust if Needed**: Update thresholds or patterns and rerun

## Example: Filter Actionable Records

Using `jq` (install from https://jqlang.github.io/jq/):

```powershell
# Get all actionable records
jq '.records[] | select(.actionable == true)' output\index.json

# Count actionable records
jq '[.records[] | select(.actionable == true)] | length' output\index.json

# Export to new file
jq '{records: [.records[] | select(.actionable == true)]}' output\index.json > actionable_only.json
```

## Support & Feedback

Review the implementation plan and walkthrough documents in the project for detailed technical documentation.

For issues:
1. Check `logs/errors.log`
2. Run with `--log-level DEBUG`
3. Test with `--test-mode` on a small subset

## License

This is a custom implementation for internal use.
