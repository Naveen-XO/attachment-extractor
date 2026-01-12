"""
Export extracted data to LLM-friendly formats (Markdown + JSON).
Designed for copy-pasting into ChatGPT for manual analysis.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def load_extraction_data(index_path: str) -> Dict[str, Any]:
    """Load the extraction index."""
    with open(index_path, 'r') as f:
        return json.load(f)


def format_confidence(conf: float) -> str:
    """Format confidence as percentage with visual indicator."""
    percentage = conf * 100
    if conf >= 0.75:
        indicator = "✓"
    elif conf >= 0.5:
        indicator = "~"
    else:
        indicator = "?"
    return f"{percentage:.0f}% {indicator}"


def extract_full_text(source_file: str, file_type: str) -> tuple[str, str]:
    """
    Extract full raw text from source file.
    
    Returns:
        Tuple of (full_text, extraction_note)
    """
    from pathlib import Path
    
    source_path = Path(source_file)
    
    if not source_path.exists():
        return "", f"Source file not found: {source_file}"
    
    try:
        if file_type == 'pdf':
            # Extract text from PDF
            import PyPDF2
            text_parts = []
            with open(source_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(f"[Page {page_num}]\n{page_text}")
            
            full_text = "\n\n".join(text_parts)
            if full_text.strip():
                return full_text, f"Extracted from {len(reader.pages)} PDF page(s)"
            else:
                return "", "PDF appears to be scanned (no extractable text - OCR was used)"
        
        elif file_type == 'csv':
            # Read entire CSV
            with open(source_path, 'r', encoding='utf-8-sig') as f:
                csv_content = f.read()
            return csv_content, f"Complete CSV file content"
        
        elif file_type == 'image':
            # For images, we rely on OCR output which should be in the record
            # We'll load it from the record JSON
            return "", "Image file (OCR text in extraction output)"
        
        else:
            return "", f"Unsupported file type: {file_type}"
    
    except Exception as e:
        return "", f"Error extracting text: {str(e)}"


def load_record_full_text(record_id: str, output_dir: Path) -> str:
    """
    Load full extracted text from individual record JSON file.
    This includes OCR output for images.
    """
    import json
    
    record_file = output_dir / 'records' / f'{record_id}.json'
    
    if not record_file.exists():
        return ""
    
    try:
        with open(record_file, 'r') as f:
            record_data = json.load(f)
        
        # Check for extracted_text field (OCR output)
        extracted_text = record_data.get('extracted_text', '')
        if extracted_text:
            return extracted_text
        
        # Fallback: try to reconstruct from fields
        return ""
    
    except Exception:
        return ""



def create_markdown_export(data: Dict[str, Any], output_path: Path, output_dir: Path):
    """Create a comprehensive Markdown export with FULL document text."""
    
    records = data.get('records', [])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("# Document Extraction Export - Full Text Edition\n\n")
        f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Documents:** {len(records)}\n\n")
        f.write("This export includes COMPLETE document text plus structured extracted fields.\n\n")
        
        # Summary statistics
        f.write("## Summary Statistics\n\n")
        
        actionable = sum(1 for r in records if r.get('actionable', False))
        file_types = {}
        extraction_methods = {}
        
        for record in records:
            ft = record.get('file_type', 'unknown')
            file_types[ft] = file_types.get(ft, 0) + 1
            
            method = record.get('metadata', {}).get('extraction_method', 'unknown')
            extraction_methods[method] = extraction_methods.get(method, 0) + 1
        
        f.write(f"- **Actionable Records:** {actionable} ({actionable/len(records)*100:.1f}%)\n")
        f.write(f"- **Non-Actionable:** {len(records) - actionable}\n\n")
        
        f.write("**File Types:**\n")
        for ft, count in sorted(file_types.items(), key=lambda x: -x[1]):
            f.write(f"- {ft}: {count}\n")
        f.write("\n")
        
        f.write("**Extraction Methods:**\n")
        for method, count in sorted(extraction_methods.items(), key=lambda x: -x[1]):
            f.write(f"- {method}: {count}\n")
        f.write("\n")
        
        f.write("---\n\n")
        
        # Individual documents
        f.write("## Extracted Documents\n\n")
        
        for idx, record in enumerate(records, 1):
            record_id = record.get('record_id', f'rec_{idx}')
            source_file = record.get('source_file', 'Unknown')
            file_type = record.get('file_type', 'unknown')
            actionable = record.get('actionable', False)
            notes = record.get('notes', '')
            metadata = record.get('metadata', {})
            fields = record.get('extracted_fields', {})
            
            filename = Path(source_file).name if source_file else 'Unknown'
            
            # Document header
            f.write(f"### {idx}. {filename}\n\n")
            f.write(f"**ID:** `{record_id}`\n\n")
            f.write(f"**Type:** {file_type} | **Actionable:** {'✅ Yes' if actionable else '❌ No'}\n\n")
            
            # Metadata
            f.write("**Processing Info:**\n")
            f.write(f"- Extraction Method: {metadata.get('extraction_method', 'unknown')}\n")
            f.write(f"- Average Confidence: {metadata.get('average_confidence', 0):.1%}\n")
            if 'ocr_quality' in metadata:
                f.write(f"- OCR Quality: {metadata['ocr_quality']:.1%}\n")
            f.write(f"- Processing Time: {metadata.get('processing_time_ms', 0):.0f}ms\n\n")
            
            # === FULL RAW TEXT ===
            f.write("#### 📄 Full Document Text\n\n")
            
            # Try to get full text from source file first
            full_text, text_note = extract_full_text(source_file, file_type)
            
            # If no text from file, try record JSON (for OCR output)
            if not full_text:
                full_text = load_record_full_text(record_id, output_dir)
                if full_text:
                    text_note = "OCR extracted text from image"
            
            if full_text:
                # Write full text in a code block for readability
                f.write("```\n")
                f.write(full_text.strip())
                f.write("\n```\n\n")
                f.write(f"*Text extraction note: {text_note}*\n\n")
            else:
                f.write("*No readable text available*\n\n")
                if text_note:
                    f.write(f"*Note: {text_note}*\n\n")
            
            # === STRUCTURED FIELDS ===
            f.write("#### 📋 Structured Extracted Fields\n\n")
            
            if not fields or all(f.get('value') is None for f in fields.values()):
                f.write("*No structured fields extracted*\n\n")
            else:
                f.write("| Field | Value | Confidence | Method |\n")
                f.write("|-------|-------|------------|--------|\n")
                
                for field_name, field_data in fields.items():
                    value = field_data.get('value')
                    if value is not None:
                        conf = field_data.get('confidence', 0)
                        method = field_data.get('extraction_method', 'unknown')
                        f.write(f"| **{field_name}** | {value} | {format_confidence(conf)} | {method} |\n")
                
                f.write("\n")
            
            # Notes
            if notes:
                f.write(f"**Processing Notes:** {notes}\n\n")
            
            # Source row (for CSV)
            if record.get('source_row') is not None:
                f.write(f"**Source CSV Row:** {record['source_row']}\n\n")
            
            f.write("---\n\n")
            
            # Progress indicator every 100 documents
            if idx % 100 == 0:
                print(f"   Processed {idx}/{len(records)} documents...")
        
        # Footer with instructions
        f.write("## How to Use This Export with ChatGPT\n\n")
        f.write("This export contains COMPLETE document text plus structured extracted data.\n\n")
        
        f.write("### Quick Start\n")
        f.write("1. Copy the entire content of this file (Ctrl+A, Ctrl+C)\n")
        f.write("2. Paste into ChatGPT\n")
        f.write("3. Ask ANY question about your documents\n\n")
        
        f.write("### Example Prompts\n\n")
        f.write("**Text-Based Analysis (NEW!):**\n")
        f.write("- \"Find all documents mentioning 'urgent' or 'expedite'\"\n")
        f.write("- \"Which documents contain email addresses?\"\n")
        f.write("- \"Identify documents with specific addresses or locations\"\n")
        f.write("- \"Find documents mentioning customer names\"\n")
        f.write("- \"Search for documents with special handling instructions\"\n")
        f.write("- \"What documents contain pricing or cost information?\"\n\n")
        
        f.write("**Structured Field Analysis:**\n")
        f.write("- \"Show me all actionable documents\"\n")
        f.write("- \"Which documents have pickup_number extracted with high confidence?\"\n")
        f.write("- \"Find documents with weight above 1000\"\n")
        f.write("- \"List documents missing critical fields\"\n\n")
        
        f.write("**Combined Analysis:**\n")
        f.write("- \"Find PDFs about deliveries scheduled for next week\"\n")
        f.write("- \"Which CSV rows mention hazardous materials?\"\n")
        f.write("- \"Show documents with both low confidence AND urgent keywords\"\n")
        f.write("- \"Identify documents that might be invoices based on text content\"\n\n")
        
        f.write("**Advanced Reasoning:**\n")
        f.write("- \"What patterns do you see across document types?\"\n")
        f.write("- \"Summarize key information from scanned vs text PDFs\"\n")
        f.write("- \"Recommend which documents need manual review\"\n")
        f.write("- \"Identify potential data quality issues\"\n")


def create_json_export(data: Dict[str, Any], output_path: Path):
    """Create a structured JSON export optimized for LLM copy-paste."""
    
    records = data.get('records', [])
    
    export_data = {
        'metadata': {
            'exported_at': datetime.now().isoformat(),
            'total_documents': len(records),
            'summary': {
                'actionable': sum(1 for r in records if r.get('actionable', False)),
                'non_actionable': sum(1 for r in records if not r.get('actionable', False)),
            }
        },
        'documents': []
    }
    
    for record in records:
        doc = {
            'id': record.get('record_id'),
            'filename': Path(record.get('source_file', '')).name,
            'file_type': record.get('file_type'),
            'actionable': record.get('actionable', False),
            'extraction_method': record.get('metadata', {}).get('extraction_method'),
            'average_confidence': record.get('metadata', {}).get('average_confidence'),
            'fields': {}
        }
        
        # Flatten fields for easier reading
        for field_name, field_data in record.get('extracted_fields', {}).items():
            if field_data.get('value') is not None:
                doc['fields'][field_name] = {
                    'value': field_data['value'],
                    'confidence': f"{field_data.get('confidence', 0):.1%}",
                    'method': field_data.get('extraction_method')
                }
        
        if record.get('notes'):
            doc['notes'] = record['notes']
        
        export_data['documents'].append(doc)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)


def create_readme(output_dir: Path):
    """Create README with instructions."""
    
    readme_path = output_dir / 'README.md'
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("# LLM Export - Usage Guide\n\n")
        f.write("This folder contains exports of your extracted document data in formats optimized for manual LLM analysis.\n\n")
        
        f.write("## Files\n\n")
        f.write("- **`full_export.md`** - Comprehensive Markdown format (recommended for ChatGPT)\n")
        f.write("- **`full_export.json`** - Structured JSON format (for programmatic use or Claude)\n")
        f.write("- **`README.md`** - This file\n\n")
        
        f.write("## How to Use\n\n")
        f.write("### Option 1: ChatGPT (Recommended)\n\n")
        f.write("1. Open `full_export.md` in a text editor\n")
        f.write("2. Copy the entire file contents (Ctrl+A, Ctrl+C)\n")
        f.write("3. Paste into ChatGPT\n")
        f.write("4. Ask questions about your documents\n\n")
        
        f.write("### Option 2: Claude or Other LLMs\n\n")
        f.write("1. Use `full_export.json` for structured data\n")
        f.write("2. Or use `full_export.md` - works with most LLMs\n\n")
        
        f.write("## Example Questions to Ask\n\n")
        f.write("**Finding Documents:**\n")
        f.write("- \"Show me all actionable documents\"\n")
        f.write("- \"Find documents with pickup_number starting with 'PKG'\"\n")
        f.write("- \"List PDFs that were processed using OCR\"\n\n")
        
        f.write("**Data Quality:**\n")
        f.write("- \"Which documents have low confidence scores?\"\n")
        f.write("- \"What fields are missing most often?\"\n")
        f.write("- \"Show documents with extraction errors\"\n\n")
        
        f.write("**Analysis:**\n")
        f.write("- \"Summarize by document type\"\n")
        f.write("- \"What are the most common materials?\"\n")
        f.write("- \"Calculate total weight across all documents\"\n")
        f.write("- \"Find duplicates or near-duplicates\"\n\n")
        
        f.write("**Recommendations:**\n")
        f.write("- \"What patterns do you see in failed extractions?\"\n")
        f.write("- \"How can I improve extraction accuracy?\"\n")
        f.write("- \"What additional fields should I extract?\"\n\n")
        
        f.write("## Tips\n\n")
        f.write("- Start with broad questions, then narrow down\n")
        f.write("- Ask the LLM to format results as tables for easier reading\n")
        f.write("- Request follow-up analysis on interesting subsets\n")
        f.write("- Use the confidence scores to filter for high-quality data\n")
        f.write("- Combine with your domain knowledge for better insights\n\n")
        
        f.write("## Data Fields Explained\n\n")
        f.write("- **pickup_number**: Shipment/pickup reference ID\n")
        f.write("- **scheduled_date**: Scheduled pickup or delivery date\n")
        f.write("- **weight**: Item weight (numeric)\n")
        f.write("- **weight_unit**: Unit of measurement (kg, lbs, tons)\n")
        f.write("- **material**: Type of material being handled\n")
        f.write("- **reference_number**: Additional reference or tracking number\n\n")
        
        f.write("- **Confidence**: 0-100% (75%+ = high confidence)\n")
        f.write("- **Actionable**: Document has required fields above confidence threshold\n")
        f.write("- **Extraction Method**: pattern (regex), OCR (scanned), csv_mapping, llm (AI)\n\n")


def main():
    """Main export function."""
    
    print("=" * 60)
    print("LLM-Friendly Export Generator")
    print("=" * 60)
    print()
    
    # Paths
    index_path = Path('output/index.json')
    output_dir = Path('output/exports')
    
    # Check if index exists
    if not index_path.exists():
        print(f"[X] Error: {index_path} not found")
        print("   Run extraction first before exporting")
        return 1
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[+] Output directory: {output_dir}")
    print()
    
    # Load data
    print("[*] Loading extraction data...")
    data = load_extraction_data(index_path)
    record_count = len(data.get('records', []))
    print(f"   Found {record_count} records")
    print()
    
    # Create exports
    print("[*] Creating Markdown export with full text...")
    md_path = output_dir / 'full_export.md'
    create_markdown_export(data, md_path, Path('output'))
    print(f"   [OK] Created: {md_path}")
    print()
    
    print("[*] Creating JSON export...")
    json_path = output_dir / 'full_export.json'
    create_json_export(data, json_path)
    print(f"   [OK] Created: {json_path}")
    print()
    
    print("[*] Creating README...")
    create_readme(output_dir)
    print(f"   [OK] Created: {output_dir / 'README.md'}")
    print()
    
    # Summary
    print("=" * 60)
    print("[SUCCESS] Export Complete!")
    print("=" * 60)
    print()
    print(f"Files created in: {output_dir.absolute()}")
    print()
    print("Next steps:")
    print("1. Open full_export.md")
    print("2. Copy all content (Ctrl+A, Ctrl+C)")
    print("3. Paste into ChatGPT")
    print("4. Ask questions about your documents!")
    print()
    print("See README.md for example prompts and tips.")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
