"""
Image file handler with lightweight OCR check and signal detection.
"""
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any


class ImageHandler:
    """Handler for image files with OCR and signal detection."""
    
    def __init__(self, logger, ocr_engine, config_path: str = "config/thresholds.json"):
        """
        Initialize image handler.
        
        Args:
            logger: Logger instance
            ocr_engine: OCR engine instance
            config_path: Path to thresholds configuration
        """
        self.logger = logger
        self.ocr_engine = ocr_engine
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.min_chars = config['image_text_minimum_chars']
        self.signal_keywords = config['image_signal_keywords']
    
    def has_numeric_signals(self, text: str) -> bool:
        """
        Check if text contains numeric signals (dates, numbers, units).
        
        Args:
            text: Extracted text to check
            
        Returns:
            True if signals found, False otherwise
        """
        text_lower = text.lower()
        
        # Check for signal keywords
        for keyword in self.signal_keywords:
            if keyword in text_lower:
                return True
        
        # Check for date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',  # DD Month
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check for numeric values (numbers with 2+ digits)
        if re.search(r'\d{2,}', text):
            return True
        
        return False
    
    def process(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Process image file with lightweight OCR check.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dict with extracted text and OCR quality, or None if skipped
        """
        # Step 1: Run lightweight OCR
        self.logger.debug(f"Running lightweight OCR on {file_path.name}")
        quick_result = self.ocr_engine.extract_text(file_path, mode='fast')
        
        if quick_result is None:
            self.logger.log_skipped_file(
                str(file_path),
                "Image processing failed - unable to read image"
            )
            return None
        
        text = quick_result['text']
        char_count = len(text.strip())
        
        # Step 2 & 3: Check character count and signals
        has_signals = self.has_numeric_signals(text)
        
        self.logger.debug(
            f"Image {file_path.name}: {char_count} chars, "
            f"signals={'yes' if has_signals else 'no'}"
        )
        
        # Step 4: Decide whether to skip
        if char_count < self.min_chars and not has_signals:
            self.logger.log_skipped_file(
                str(file_path),
                f"Low-content image (logo/signature): {char_count} chars, no numeric signals"
            )
            return None
        
        # Step 5: Run full OCR if passed checks
        if char_count >= self.min_chars:
            # Already have good text from fast mode, but could run full for better quality
            self.logger.debug(f"Using fast OCR result for {file_path.name} ({char_count} chars)")
            full_result = quick_result
        else:
            # Has signals but low char count - run full OCR for better accuracy
            self.logger.debug(f"Running full OCR on {file_path.name} (has signals)")
            full_result = self.ocr_engine.extract_text(file_path, mode='full')
        
        return {
            'text': full_result['text'],
            'ocr_quality': full_result['confidence'],
            'extraction_method': 'ocr',
            'char_count': len(full_result['text'].strip()),
            'had_signals': has_signals
        }
