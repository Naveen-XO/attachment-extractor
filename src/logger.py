"""
Logging system for email attachment processor.
Handles multi-file logging with timestamps and context.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class ProcessorLogger:
    """Multi-file logger for processing pipeline."""
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """
        Initialize logger with multiple output files.
        
        Args:
            log_dir: Directory to store log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log files
        self.processing_log = self.log_dir / "processing.log"
        self.skipped_log = self.log_dir / "skipped_files.log"
        self.low_confidence_log = self.log_dir / "low_confidence.log"
        self.errors_log = self.log_dir / "errors.log"
        
        # Set up main logger
        self.logger = logging.getLogger("AttachmentProcessor")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter('%(asctime)s | %(message)s')
        
        # Main processing log handler
        processing_handler = logging.FileHandler(self.processing_log, encoding='utf-8')
        processing_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(processing_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(console_handler)
        
        # Write run separator
        self._write_run_separator()
    
    def _write_run_separator(self):
        """Write separator for new run."""
        separator = f"\n{'='*80}\n=== RUN STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n{'='*80}\n"
        
        for log_file in [self.processing_log, self.skipped_log, 
                         self.low_confidence_log, self.errors_log]:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(separator)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message."""
        self.logger.error(message, exc_info=exc_info, **kwargs)
        
        # Also write to errors log
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.errors_log, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} | {message}\n")
            if exc_info:
                import traceback
                f.write(traceback.format_exc() + "\n")
    
    def log_skipped_file(self, file_path: str, reason: str):
        """Log skipped file with reason."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"{timestamp} | {file_path} | REASON: {reason}"
        
        with open(self.skipped_log, 'a', encoding='utf-8') as f:
            f.write(message + "\n")
        
        self.info(f"Skipped: {file_path} - {reason}")
    
    def log_low_confidence(self, record_id: str, source_file: str, 
                          low_confidence_fields: dict):
        """Log record with low confidence fields."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.low_confidence_log, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} | Record: {record_id} | Source: {source_file}\n")
            for field, confidence in low_confidence_fields.items():
                f.write(f"  - {field}: {confidence:.2f}\n")
            f.write("\n")
        
        self.warning(f"Low confidence in {record_id}: {list(low_confidence_fields.keys())}")
    
    def log_file_processed(self, file_path: str, file_type: str, 
                          extraction_method: str, processing_time_ms: float,
                          success: bool = True):
        """Log successful file processing."""
        status = "SUCCESS" if success else "FAILED"
        self.info(
            f"Processed: {file_path} | Type: {file_type} | "
            f"Method: {extraction_method} | Time: {processing_time_ms:.0f}ms | "
            f"Status: {status}"
        )


def create_logger(log_dir: str = "logs", log_level: str = "INFO") -> ProcessorLogger:
    """Create and return processor logger instance."""
    return ProcessorLogger(log_dir, log_level)
