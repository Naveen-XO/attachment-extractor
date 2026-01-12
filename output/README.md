# Output Directory Structure

This directory contains all processing results.

## Files

### Individual Records
`records/rec_00001.json`, `rec_00002.json`, etc.

Each file contains a single extraction record with:
- Source file path
- Extracted fields with confidence scores
- Actionable status (true/false)
- Processing metadata

### Combined Index
`index.json`

Contains all records in a single file for easy filtering and analysis.

### Summary Report
`summary.txt`

Human-readable summary with:
- File count statistics
- Actionable vs. non-actionable breakdown
- Extraction method distribution
- Low-confidence records flagged for review

## Record Schema

Each record follows this structure:

```json
{
  "record_id": "rec_00001",
  "source_file": "path/to/source/file.pdf",
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
    "processed_at": "2026-01-11T02:43:00+05:30",
    "processing_time_ms": 1234,
    "extraction_method": "pattern",
    "average_confidence": 0.91,
    "ocr_quality": 1.0
  }
}
```

## Filtering Records

### Get only actionable records (using jq)

```powershell
jq '.records[] | select(.actionable == true)' index.json
```

### Count actionable records

```powershell
jq '[.records[] | select(.actionable == true)] | length' index.json
```

### Find high-confidence records

```powershell
jq '.records[] | select(.metadata.average_confidence >= 0.9)' index.json
```

### Export actionable to new file

```powershell
jq '{records: [.records[] | select(.actionable == true)]}' index.json > actionable_only.json
```

## Field Definitions

- **pickup_number**: Unique identifier for the pickup
- **scheduled_date**: Date scheduled for pickup (YYYY-MM-DD format)
- **weight**: Numeric weight value
- **weight_unit**: Unit of measurement (kg, lbs, or tons)
- **material**: Type of material or waste
- **reference_number**: Reference or order number

## Actionable Logic

A record is marked `actionable: true` if these 3 required fields meet confidence threshold (0.75):
1. pickup_number
2. scheduled_date
3. weight

The other fields (material, weight_unit, reference_number) are optional.

## Confidence Scores

- **1.0**: Exact pattern match (very high confidence)
- **0.9**: LLM high certainty or strong keyword match
- **0.75**: Threshold for actionable status
- **0.5-0.7**: Medium confidence (inferred or fuzzy match)
- **< 0.5**: Low confidence (should be reviewed)

Records with any field below 0.75 are logged to `logs/low_confidence.log`.
