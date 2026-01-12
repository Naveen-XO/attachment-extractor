# Email Attachment Processor - Quick Reference

## Installation

```powershell
# Run setup script (recommended)
.\setup.ps1

# Or manual install
pip install -r requirements.txt
python tests\check_dependencies.py
```

## Required Setup

1. **Tesseract OCR**: https://github.com/UB-Mannheim/tesseract/wiki
2. **Poppler**: https://github.com/oschwartz10612/poppler-windows/releases
3. **API Key**: `$env:GOOGLE_API_KEY = "your-key"`

## Basic Usage

```powershell
# Dry run (see what would be processed)
python src\main.py --input "path\to\files" --dry-run

# Test mode (process 20 files)
python src\main.py --input "path\to\files" --test-mode

# Full processing
python src\main.py --input "path\to\files"

# With custom output
python src\main.py --input "path\to\files" --output "my_output"
```

## Command Flags

| Flag | Description |
|------|-------------|
| `--input PATH` | Input directory (required) |
| `--output PATH` | Output directory (default: output) |
| `--test-mode` | Process only first 20 files |
| `--dry-run` | Show files without processing |
| `--log-level LEVEL` | DEBUG\|INFO\|WARNING\|ERROR |
| `--gemini-api-key KEY` | API key (or use env var) |
| `--tesseract-path PATH` | Path to tesseract.exe |

## File Processing

| Type | Action |
|------|--------|
| Audio (.mp3, .wav, etc.) | **Skipped** - logged only |
| CSV (.csv) | **Parsed** - one record per row |
| Images (.png, .jpg, etc.) | **OCR** - if text or signals detected |
| PDF (.pdf) | **Text extraction** or OCR if scanned |

## Output Files

| File | Contents |
|------|----------|
| `output/records/*.json` | Individual extraction records |
| `output/index.json` | All records combined |
| `output/summary.txt` | Human-readable summary |
| `logs/processing.log` | Detailed processing log |
| `logs/skipped_files.log` | Files that were skipped |
| `logs/low_confidence.log` | Records needing review |
| `logs/errors.log` | Processing errors |

## Configuration

Edit `config/*.json` files to customize:

- **thresholds.json**: Confidence thresholds, required fields
- **field_patterns.json**: Regex patterns for extraction
- **file_extensions.json**: File type mappings

## Confidence Thresholds

- **Required fields**: pickup_number, scheduled_date, weight
- **Optional fields**: material, weight_unit, reference_number
- **Threshold**: 0.75 (75% confidence)

Record is `actionable: true` only if all 3 required fields ≥ 0.75.

## Extraction Methods

1. **Pattern matching** - Fast, for structured documents
2. **LLM fallback** - Triggered if patterns find < 3 fields
3. **Hybrid** - Combines both, higher confidence wins

## Quick Checks

```powershell
# Check dependencies
python tests\check_dependencies.py

# Count total files
(Get-ChildItem -Recurse "path\to\files").Count

# View file types
Get-ChildItem -Recurse "path\to\files" | Group-Object Extension

# Check API key
echo $env:GOOGLE_API_KEY

# View first result
Get-Content output\records\rec_00001.json | ConvertFrom-Json

# Count actionable records (requires jq)
jq '[.records[] | select(.actionable == true)] | length' output\index.json
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tesseract not found | Install and add to PATH, or use `--tesseract-path` |
| API key error | Set `$env:GOOGLE_API_KEY` |
| Low accuracy | Review patterns in `config/field_patterns.json` |
| Too slow | LLM adds 1-2s/file; consider test mode first |
| Many non-actionable | Check `low_confidence.log`, adjust patterns |

## Performance

- CSV: ~50ms per row
- PDF (text): ~200-500ms
- PDF (scanned): ~5-15s per page
- Image: ~1-3s
- **6000 files**: ~2-6 hours estimated

## Next Steps After Processing

1. Review `output/summary.txt`
2. Spot-check sample JSON files
3. Filter for actionable: `jq '.records[] | select(.actionable == true)' output\index.json`
4. Review low confidence: Check `logs/low_confidence.log`
5. Adjust configuration if needed and rerun

## Support

See `README.md` for detailed documentation.
