"""
PDF file handler with text extraction and OCR fallback.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
import PyPDF2


class PDFHandler:
    """Handler for PDF files with text extraction and OCR fallback."""
    
    def __init__(self, logger, ocr_engine, config_path: str = "config/thresholds.json"):
        """
        Initialize PDF handler.
        
        Args:
            logger: Logger instance
            ocr_engine: OCR engine instance
            config_path: Path to thresholds configuration
        """
        self.logger = logger
        self.ocr_engine = ocr_engine
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.min_text_chars = config['pdf_text_minimum_chars']
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF using PyPDF2.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text string
        """
        try:
            text = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to extract text from page {page_num} of {file_path.name}: {e}"
                        )
                        continue
            
            return text.strip()
        
        except Exception as e:
            self.logger.error(
                f"Failed to read PDF {file_path.name}: {e}",
                exc_info=True
            )
            return ""
    
    def process(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Process PDF file with text extraction or OCR.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dict with extracted text and metadata, or None if failed
        """
        # Step 1: Attempt text extraction
        self.logger.debug(f"Extracting text from PDF {file_path.name}")
        extracted_text = self.extract_text_from_pdf(file_path)
        
        char_count = len(extracted_text.strip())
        self.logger.debug(f"PDF {file_path.name}: extracted {char_count} characters")
        
        # Step 2-3: Decide if we need OCR
        if char_count > self.min_text_chars:
            # Sufficient text extracted
            return {
                'text': extracted_text,
                'ocr_quality': 1.0,  # High quality from direct text extraction
                'extraction_method': 'text',
                'char_count': char_count
            }
        
        else:
            # Low/no text - treat as scanned PDF, run OCR
            self.logger.info(
                f"PDF {file_path.name} has insufficient text ({char_count} chars), "
                f"treating as scanned - running OCR"
            )
            
            try:
                ocr_result = self.ocr_engine.extract_text_from_pdf(file_path)
                
                if ocr_result is None:
                    self.logger.error(f"OCR failed for PDF {file_path.name}")
                    return None
                
                return {
                    'text': ocr_result['text'],
                    'ocr_quality': ocr_result['confidence'],
                    'extraction_method': 'ocr',
                    'char_count': len(ocr_result['text'].strip())
                }
            
            except Exception as e:
                self.logger.error(
                    f"OCR processing failed for PDF {file_path.name}: {e}",
                    exc_info=True
                )
                return None
