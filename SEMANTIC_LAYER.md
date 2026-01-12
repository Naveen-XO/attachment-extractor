# Semantic Document Interpretation Layer

## Overview

The semantic interpretation layer is a **post-processing module** that analyzes documents to extract operationally relevant information beyond predefined fields.

**Purpose**: Handle the 51% of documents where pattern extraction found no usable fields.

---

## How It Works

### 1. **Input Sources**
- Extracted OCR/PDF/CSV text (reused, not re-extracted)
- Existing pattern-extracted fields
- File metadata (filename, type, confidence)

### 2. **Analysis Process**
For each document, the semantic analyzer:

1. **Determines document type**
   - logistics/pickup/delivery
   - invoice
   - confirmation
   - report/summary
   - label
   - contract
   - internal_note
   - unknown

2. **Identifies key observations**
   - ANY operationally relevant information
   - Not limited to predefined fields
   - Includes: identifiers, dates, quantities, amounts, entities, locations, schedules, exceptions

3. **Provides operational context**
   - Why each observation matters
   - Actionability hint for the document

### 3. **Output Format**

```json
{
  "document_type": "logistics/pickup/delivery",
  "key_observations": [
    {
      "label": "Pickup Reference",
      "value": "PKG-2026-1234",
      "category": "identifier",
      "confidence": 0.95,
      "reasoning": "Primary tracking number for shipment coordination"
    },
    {
      "label": "Scheduled Collection",
      "value": "2026-01-15",
      "category": "date",
      "confidence": 0.90,
      "reasoning": "Critical deadline for logistics scheduling"
    }
  ],
  "actionability_hint": "Document contains pickup scheduling information requiring coordination with logistics team"
}
```

---

## Usage

### Basic Usage (Analyze Low-Confidence Records)

```powershell
python semantic_postprocess.py --gemini-api-key "your-api-key"
```

This will:
- Load `output/index.json`
- Analyze only records with confidence < 0.75
- Save results to `output/semantic_analysis.json`

### Analyze All Documents

```powershell
python semantic_postprocess.py --all --gemini-api-key "your-api-key"
```

### Limit Processing (Test Mode)

```powershell
python semantic_postprocess.py --max-documents 20 --gemini-api-key "your-api-key"
```

### Custom Paths

```powershell
python semantic_postprocess.py `
  --index output/index.json `
  --output output/semantic_results.json `
  --gemini-api-key "your-api-key"
```

---

## When Semantic Analysis Runs

The analyzer automatically skips documents when:

- **Insufficient text** (< 50 characters)
- **High pattern confidence** (≥ 0.75) - pattern extraction was sufficient
- **Boilerplate detected** - privacy policies, terms, copyright notices
- **Noise documents** - logos, headers without content

---

## Integration with Existing Pipeline

**Semantic analysis is ADDITIVE**, not a replacement:

1. ✅ **Existing pipeline unchanged** - OCR, pattern extraction work as before
2. ✅ **Reuses extracted text** - No re-running of OCR or PDF parsing
3. ✅ **Separate output file** - `semantic_analysis.json` doesn't overwrite existing records
4. ✅ **Optional layer** - Can be run independently after main processing

---

## Output Structure

### Semantic Analysis File
```
output/semantic_analysis.json
```

```json
{
  "metadata": {
    "generated_at": "2026-01-11 14:30:00",
    "source_index": "output/index.json",
    "total_records": 2059,
    "analyzed": 845,
    "skipped": 1214,
    "processing_time_seconds": 1234.5
  },
  "semantic_analysis": {
    "rec_00001": {
      "document_type": "invoice",
      "key_observations": [...],
      "actionability_hint": "..."
    },
    "rec_00343": {...}
  }
}
```

---

## Observation Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `identifier` | Reference numbers, IDs | PKG-1234, INV-5678 |
| `date` | Temporal information | 2026-01-15, Jan 15 2026 |
| `quantity` | Amounts, counts | 100 units, 50 items |
| `amount` | Monetary values | $1,234.56, €500 |
| `entity` | Companies, people | ACME Corp, John Smith |
| `location` | Addresses, places | 123 Main St, Warehouse A |
| `note` | Exceptions, special instructions | Urgent, Delayed |
| `other` | Other relevant information | - |

---

## Performance Characteristics

**Speed:**
- ~2-3 seconds per document (LLM call)
- ~1,000 documents = 30-50 minutes
- Can be run in background/overnight

**Batching:**
- Analyzes documents sequentially
- Progress logged every 10 documents
- Safe to interrupt and resume

**Cost\:**
- Uses Google Gemini API (paid service)
- ~$0.001-0.002 per document (estimate)
- Test with `--max-documents` first

---

## Example Use Cases

### 1. Recovering Value from "Failed" Extractions

Pattern extraction found nothing, but semantic analysis discovers:
- Invoice number in non-standard format
- Delivery address in unstructured text
- Special handling instructions

### 2. Document Classification

Automatically categorize documents for routing:
- Invoices → Accounts Payable
- Pickup confirmations → Logistics
- Internal notes → Archive

### 3. Exception Detection

Find documents mentioning:
- Delays
- Damages
- Special requests
- Urgent items

---

## Configuration

Edit `src/extractors/semantic_analyzer.py` to adjust:

```python
# Minimum text length for analysis
self.min_text_length = 50

# Pattern confidence threshold (skip if above)
# In should_analyze() method:
if pattern_confidence >= 0.75:
    return False
```

---

## Logging

Semantic analysis logs to the same log directory:
- `logs/processing.log` - Analysis decisions
- Debug level shows skip reasons

---

## Future Enhancements

**Potential improvements:**
1. **Text caching** - Store extracted text during initial processing
2. **Parallel processing** - Analyze multiple documents simultaneously
3. **Custom prompts** - Industry-specific analysis rules
4. **Hybrid output** - Merge semantic results into original records
5. **Active learning** - Improve patterns based on semantic findings

---

## Command Reference

```powershell
# Full command with all options
python semantic_postprocess.py `
  --index output/index.json `
  --output output/semantic_analysis.json `
  --gemini-api-key "your-key" `
  --all `
  --max-documents 100 `
  --log-level DEBUG
```

**Arguments:**
- `--index` - Path to index.json (default: output/index.json)
- `--output` - Output file (default: output/semantic_analysis.json)
- `--gemini-api-key` - API key (or use GOOGLE_API_KEY env var)
- `--all` - Analyze all documents (not just low-confidence)
- `--max-documents N` - Limit to first N documents
- `--log-level` - DEBUG|INFO|WARNING|ERROR

---

## Troubleshooting

**"No text available for record"**
- Currently, text needs to be re-extracted from source files
- PDF text is extracted quickly
- Images would need OCR (skipped for now)
- Consider caching text during initial processing

**"Semantic analysis skipped"**
- Check logs for reason (insufficient text, high confidence, boilerplate)
- Use `--log-level DEBUG` to see skip decisions

**API errors**
- Verify API key is correct
- Check Google Gemini API quotas
- Try with `--max-documents 5` first

---

## Notes

- This is a **post-processing layer** - run AFTER initial extraction
- Does NOT replace pattern extraction
- Focuses on the 51% of documents with low/no pattern matches
- Flexible output schema captures any relevant information
- Designed for human review of operational intelligence
