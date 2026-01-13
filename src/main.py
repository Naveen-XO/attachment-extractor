"""
Main processing pipeline for email attachment extraction.
"""
import argparse
import sys
import time
import os
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from logger import create_logger
from file_scanner import FileScanner
from confidence import ConfidenceScorer
from output_writer import OutputWriter

# Handlers
from handlers.audio_handler import AudioHandler
from handlers.image_handler import ImageHandler
from handlers.pdf_handler import PDFHandler
from handlers.csv_handler import CSVHandler

# Extractors (OCR and parsing - always needed)
from extractors.ocr_engine import OCREngine
from extractors.text_parser import TextParser
from extractors.field_extractor import FieldExtractor
# Note: LLMExtractor imported conditionally based on ENABLE_AI flag


def process_file(file_path: Path, file_type: str, handlers: dict, field_extractor: FieldExtractor,
                 confidence_scorer: ConfidenceScorer, output_writer: OutputWriter, logger) -> int:
    """
    Process a single file.
    
    Returns:
        Number of records created (0 if skipped, 1+ for successful extraction)
    """
    start_time = time.time()
    
    try:
        # Route to appropriate handler
        if file_type == 'audio':
            handlers['audio'].process(file_path)
            return 0  # Skipped
        
        elif file_type == 'csv':
            # CSV produces multiple records
            csv_records = handlers['csv'].process(file_path)
            
            if not csv_records:
                logger.warning(f"No records extracted from CSV {file_path_name}")
                return 0
            
            # Process each CSV row as a record
            for csv_record in csv_records:
                # CSV handler already provides mapped fields with confidence
                extracted_fields = csv_record['mapped_fields']
                source_row = csv_record['source_row']
                
                # Determine actionable status
                actionable = confidence_scorer.determine_actionable(extracted_fields)
                avg_conf = confidence_scorer.calculate_average_confidence(extracted_fields)
                
                # Create and write record
                record = output_writer.create_record(
                    source_file=file_path,
                    file_type='csv',
                    extracted_fields=extracted_fields,
                    actionable=actionable,
                    notes=f"CSV row {source_row}",
                    metadata={
                        'extraction_method': 'csv_mapping',
                        'average_confidence': avg_conf,
                        'processing_time_ms': (time.time() - start_time) * 1000
                    },
                    source_row=source_row
                )
                
                output_writer.write_record(record)
                
                # Log low confidence fields
                low_conf = confidence_scorer.identify_low_confidence_fields(extracted_fields)
                if low_conf:
                    logger.log_low_confidence(record['record_id'], str(file_path), low_conf)
            
            processing_time = (time.time() - start_time) * 1000
            logger.log_file_processed(str(file_path), 'csv', 'csv_mapping', 
                                     processing_time, success=True)
            return len(csv_records)
        
        elif file_type in ['image', 'pdf']:
            # Get handler
            handler = handlers[file_type]
            
            # Process file to extract text
            result = handler.process(file_path)
            
            if result is None:
                return 0  # Skipped or failed
            
            # Extract fields from text
            extracted_text = result['text']
            ocr_quality = result.get('ocr_quality', 1.0)
            
            extraction = field_extractor.extract(extracted_text, ocr_quality)
            
            # Determine actionable status
            extracted_fields = extraction['extracted_fields']
            actionable = confidence_scorer.determine_actionable(extracted_fields)
            
            # Create and write record
            record = output_writer.create_record(
                source_file=file_path,
                file_type=file_type,
                extracted_fields=extracted_fields,
                actionable=actionable,
                notes=extraction['notes'],
                metadata={
                    'extraction_method': extraction['extraction_method'],
                    'average_confidence': extraction['average_confidence'],
                    'ocr_quality': ocr_quality,
                    'processing_time_ms': (time.time() - start_time) * 1000
                }
            )
            
            output_writer.write_record(record)
            
            # Log low confidence fields
            low_conf = confidence_scorer.identify_low_confidence_fields(extracted_fields)
            if low_conf:
                logger.log_low_confidence(record['record_id'], str(file_path), low_conf)
            
            processing_time = (time.time() - start_time) * 1000
            logger.log_file_processed(str(file_path), file_type, 
                                     extraction['extraction_method'],
                                     processing_time, success=True)
            return 1
        
        else:
            logger.warning(f"Unsupported file type: {file_type} for {file_path}")
            return 0
    
    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Email Attachment Processing System - Extract workflow fields from attachments"
    )
    parser.add_argument(
        '--input',
        required=True,
        help="Path to input directory containing email attachments"
    )
    parser.add_argument(
        '--output',
        default='output',
        help="Path to output directory (default: output)"
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help="Process only first 20 files for testing"
    )
    parser.add_argument(
        '--gemini-api-key',
        default=None,
        help="Google Gemini API key (or set GOOGLE_API_KEY env var)"
    )
    parser.add_argument(
        '--tesseract-path',
        default=None,
        help="Path to Tesseract executable (if not in PATH)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be processed without actually extracting (no LLM/OCR calls)"
    )
    args = parser.parse_args()
    
    # Load feature flags
    import json
    feature_flags_path = Path(__file__).parent.parent / 'config' / 'feature_flags.json'
    with open(feature_flags_path, 'r') as f:
        feature_flags = json.load(f)
    
    enable_ai = feature_flags.get('ENABLE_AI', False)
    
    # Get API key from args or environment (only required if AI is enabled)
    api_key = args.gemini_api_key or os.getenv('GOOGLE_API_KEY')
    
    if enable_ai and not api_key:
        print("ERROR: Google Gemini API key required when ENABLE_AI=true.")
        print("Set --gemini-api-key or GOOGLE_API_KEY environment variable.")
        return 1
    
    # Initialize logger
    logger = create_logger(log_dir="logs", log_level=args.log_level)
    logger.info("=" * 80)
    logger.info("Email Attachment Processing System - Starting")
    logger.info("=" * 80)
    logger.info(f"AI/LLM Mode: {'ENABLED' if enable_ai else 'DISABLED (extraction-only mode)'}")
    
    start_time = time.time()
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        
        scanner = FileScanner()
        confidence_scorer = ConfidenceScorer()
        output_writer = OutputWriter(logger, output_dir=args.output)
        
        # Initialize extractors
        ocr_engine = OCREngine(logger, tesseract_path=args.tesseract_path)
        text_parser = TextParser(logger)
        
        # Conditionally import and initialize LLM extractor
        llm_extractor = None
        if enable_ai:
            logger.info("AI enabled - importing LLM modules...")
            from extractors.llm_extractor import LLMExtractor
            llm_extractor = LLMExtractor(logger, api_key=api_key)
            logger.info("LLM extractor initialized")
        else:
            logger.info("AI disabled - LLM modules will not be imported")
        
        field_extractor = FieldExtractor(logger, text_parser, llm_extractor, confidence_scorer)
        
        # Initialize handlers
        handlers = {
            'audio': AudioHandler(logger),
            'image': ImageHandler(logger, ocr_engine),
            'pdf': PDFHandler(logger, ocr_engine),
            'csv': CSVHandler(logger)
        }
        
        # Scan input directory
        logger.info(f"Scanning input directory: {args.input}")
        catalog = scanner.scan_directory(args.input)
        stats = scanner.get_statistics(catalog)
        
        logger.info(f"Found {stats['total']} files:")
        for file_type, count in stats.items():
            if file_type != 'total':
                logger.info(f"  {file_type}: {count}")
        
        # Create processing manifest
        manifest = scanner.create_processing_manifest(catalog)
        
        # Test mode: limit files
        if args.test_mode:
            manifest = manifest[:20]
            logger.info(f"TEST MODE: Processing only first {len(manifest)} files")
        
        # Dry-run mode: show what would be processed
        if args.dry_run:
            logger.info("=" * 80)
            logger.info("DRY RUN MODE - No actual processing will occur")
            logger.info("=" * 80)
            logger.info(f"Would process {len(manifest)} files:")
            for idx, (file_path, file_type) in enumerate(manifest, 1):
                logger.info(f"  [{idx}] {file_type:8s} - {file_path.name}")
            logger.info("=" * 80)
            logger.info(f"Dry run complete. No files processed.")
            return 0
        
        # Process files
        logger.info(f"Processing {len(manifest)} files...")
        
        skipped_count = stats['audio']  # Audio files are always skipped
        processed_count = 0
        
        for idx, (file_path, file_type) in enumerate(manifest, 1):
            logger.info(f"[{idx}/{len(manifest)}] Processing {file_path.name}")
            
            records_created = process_file(
                file_path, file_type, handlers, field_extractor,
                confidence_scorer, output_writer, logger
            )
            
            if records_created > 0:
                processed_count += 1
        
        # Generate index and summary
        logger.info("Generating index and summary...")
        output_writer.write_index()
        
        processing_time = time.time() - start_time
        output_writer.generate_summary(stats, skipped_count, processing_time)
        
        # Final summary
        logger.info("=" * 80)
        logger.info("Processing Complete!")
        logger.info("=" * 80)
        logger.info(f"Total files: {stats['total']}")
        logger.info(f"Processed: {processed_count}")
        logger.info(f"Skipped: {skipped_count}")
        logger.info(f"Records created: {len(output_writer.all_records)}")
        logger.info(f"Total time: {processing_time:.1f} seconds")
        logger.info(f"Output directory: {args.output}")
        logger.info("=" * 80)
        
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
