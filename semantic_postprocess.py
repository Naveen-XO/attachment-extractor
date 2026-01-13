"""
Post-processing script to add semantic interpretation to existing extraction results.
Reuses existing OCR/PDF text without re-extracting.
"""
import argparse
import json
import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from logger import create_logger
# Note: SemanticAnalyzer imported conditionally based on ENABLE_AI flag


def load_text_cache(input_dir: Path, logger) -> dict:
    """
    Load text from original source files.
    Reuses existing extraction logic without re-running OCR.
    """
    logger.info("Building text cache from source files...")
    
    # For now, we'll need to re-extract text (but not re-run full pipeline)
    # In a production system, you'd cache this during initial extraction
    
    # Placeholder - will load from cached text if available
    text_cache = {}
    
    logger.warning("Text cache not yet implemented - will extract text on demand")
    return text_cache


def run_semantic_analysis(
    index_path: str,
    output_path: str,
    api_key: str,
    logger,
    filter_low_confidence: bool = True,
    max_documents: int = None
):
    """
    Run semantic analysis on existing extraction results.
    
    Args:
        index_path: Path to index.json
        output_path: Path to save semantic analysis results
        api_key: Google Gemini API key
        logger: Logger instance
        filter_low_confidence: Only analyze low-confidence extractions
        max_documents: Maximum number of documents to analyze
    """
    logger.info("=" * 80)
    logger.info("SEMANTIC POST-PROCESSING")
    logger.info("=" * 80)
    
    # Load existing results
    logger.info(f"Loading existing results from {index_path}")
    with open(index_path, 'r') as f:
        data = json.load(f)
    
    records = data['records']
    logger.info(f"Loaded {len(records)} records")
    
    # Filter records if requested
    if filter_low_confidence:
        original_count = len(records)
        records = [r for r in records if r['metadata'].get('average_confidence', 0) < 0.75]
        logger.info(f"Filtered to {len(records)} low-confidence records (from {original_count})")
    
    # Limit if requested
    if max_documents and len(records) > max_documents:
        records = records[:max_documents]
        logger.info(f"Limited to first {max_documents} documents")
    
    # Initialize semantic analyzer
    logger.info("Initializing semantic analyzer...")
    analyzer = SemanticAnalyzer(logger, api_key)
    
    # Build text cache
    # NOTE: For now, we'll extract text on-demand per document
    # In production, this should be cached during initial extraction
    text_cache = {}
    
    logger.info(f"Starting semantic analysis on {len(records)} documents...")
    start_time = time.time()
    
    # Analyze each record
    semantic_results = {}
    analyzed = 0
    skipped = 0
    errors = 0
    
    for idx, record in enumerate(records, 1):
        record_id = record['record_id']
        source_file = record['source_file']
        file_type = record['file_type']
        avg_confidence = record['metadata'].get('average_confidence', 0.0)
        
        logger.info(f"[{idx}/{len(records)}] Processing {record_id}")
        
        try:
            # Get text for this document
            # For now, we'll use a placeholder
            # In production, extract text from source file or cache
            text = _get_document_text(source_file, file_type, logger)
            
            if not text:
                logger.warning(f"No text available for {record_id}, skipping")
                skipped += 1
                continue
            
            # Check if should analyze
            if not analyzer.should_analyze(text, avg_confidence):
                skipped += 1
                continue
            
            # Run semantic analysis
            result = analyzer.analyze_document(
                text=text,
                filename=Path(source_file).name,
                file_type=file_type,
                existing_fields=record['extracted_fields']
            )
            
            semantic_results[record_id] = result
            analyzed += 1
            
        except Exception as e:
            logger.error(f"Error analyzing {record_id}: {e}", exc_info=True)
            errors += 1
    
    processing_time = time.time() - start_time
    
    # Save results
    logger.info(f"Saving semantic analysis results to {output_path}")
    output_data = {
        'metadata': {
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source_index': index_path,
            'total_records': len(records),
            'analyzed': analyzed,
            'skipped': skipped,
            'errors': errors,
            'processing_time_seconds': processing_time
        },
        'semantic_analysis': semantic_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info("=" * 80)
    logger.info("SEMANTIC ANALYSIS COMPLETE")
    logger.info("=" * 80)
    logger.info(f"  Total documents: {len(records)}")
    logger.info(f"  Analyzed: {analyzed}")
    logger.info(f"  Skipped: {skipped}")
    logger.info(f"  Errors: {errors}")
    logger.info(f"  Processing time: {processing_time:.1f} seconds")
    logger.info(f"  Output: {output_path}")
    logger.info("=" * 80)


def _get_document_text(source_file: str, file_type: str, logger) -> str:
    """
    Extract text from source file.
    This is a lightweight re-extraction (not full pipeline).
    """
    try:
        if file_type == 'pdf':
            # Quick PDF text extraction
            import PyPDF2
            with open(source_file, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
                return text
        
        elif file_type == 'csv':
            # Read CSV as text
            with open(source_file, 'r', encoding='utf-8-sig') as f:
                return f.read()
        
        elif file_type == 'image':
            # Would need OCR - skip for now unless cached
            logger.debug(f"Skipping image {source_file} - OCR text not cached")
            return ''
        
        else:
            return ''
    
    except Exception as e:
        logger.error(f"Error extracting text from {source_file}: {e}")
        return ''


def main():
    parser = argparse.ArgumentParser(
        description="Semantic post-processing for email attachments"
    )
    parser.add_argument(
        '--index',
        default='output/index.json',
        help="Path to index.json from initial processing"
    )
    parser.add_argument(
        '--output',
        default='output/semantic_analysis.json',
        help="Path to save semantic analysis results"
    )
    parser.add_argument(
        '--gemini-api-key',
        default=None,
        help="Google Gemini API key (or set GOOGLE_API_KEY env var)"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help="Analyze all documents (not just low-confidence)"
    )
    parser.add_argument(
        '--max-documents',
        type=int,
        default=None,
        help="Maximum number of documents to analyze"
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Load feature flags - exit early if AI is disabled
    feature_flags_path = Path(__file__) / 'config' / 'feature_flags.json'
    try:
        with open(feature_flags_path, 'r') as f:
            feature_flags = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Feature flags file not found at {feature_flags_path}")
        return 1
    
    enable_ai = feature_flags.get('ENABLE_AI', False)
    
    if not enable_ai:
        print("=" * 80)
        print("SEMANTIC ANALYSIS DISABLED")
        print("=" * 80)
        print("AI/LLM functionality is currently disabled (ENABLE_AI=false).")
        print("Semantic post-processing requires AI to be enabled.")
        print("")
        print("To enable:")
        print("  1. Edit config/feature_flags.json")
        print("  2. Set 'ENABLE_AI': true")
        print("  3. Re-run this script")
        print("=" * 80)
        return 0
    
    # Get API key (only needed when AI is enabled)
    api_key = args.gemini_api_key or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: Google Gemini API key required when ENABLE_AI=true.")
        print("Set --gemini-api-key or GOOGLE_API_KEY environment variable.")
        return 1
    
    # Initialize logger
    logger = create_logger(log_dir="logs", log_level=args.log_level)
    
    # Import AI modules (only after confirming AI is enabled)
    logger.info("AI enabled - importing semantic analyzer...")
    from extractors.semantic_analyzer import SemanticAnalyzer
    logger.info("Semantic analyzer module loaded")
    
    # Run semantic analysis
    try:
        run_semantic_analysis(
            index_path=args.index,
            output_path=args.output,
            api_key=api_key,
            logger=logger,
            filter_low_confidence=not args.all,
            max_documents=args.max_documents
        )
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
