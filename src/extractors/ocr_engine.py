"""
OCR engine wrapper for Tesseract.
"""
import pytesseract
from PIL import Image
from pathlib import Path
from typing import Optional, Dict, Any
import pdf2image
import tempfile


class OCREngine:
    """Wrapper for Tesseract OCR with fast and full modes."""
    
    def __init__(self, logger, tesseract_path: Optional[str] = None):
        """
        Initialize OCR engine.
        
        Args:
            logger: Logger instance
            tesseract_path: Optional path to tesseract executable
        """
        self.logger = logger
        
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Could add more preprocessing here:
        # - Contrast adjustment
        # - Noise reduction
        # - Deskewing
        
        return image
    
    def extract_text(self, image_path: Path, mode: str = 'full') -> Optional[Dict[str, Any]]:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
            mode: 'fast' for quick extraction, 'full' for better quality
            
        Returns:
            Dict with 'text' and 'confidence', or None if failed
        """
        try:
            # Load image
            image = Image.open(image_path)
            image = self.preprocess_image(image)
            
            # Set OCR configuration based on mode
            if mode == 'fast':
                # PSM 6 = Assume uniform block of text
                # OEM 1 = LSTM only (faster)
                config = '--psm 6 --oem 1'
            else:  # full
                # PSM 3 = Fully automatic page segmentation
                # OEM 3 = Default (LSTM + legacy, better accuracy)
                config = '--psm 3 --oem 3'
            
            # Extract text
            text = pytesseract.image_to_string(image, config=config)
            
            # Get confidence data
            try:
                data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if conf != '-1']
                avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.5
            except:
                avg_confidence = 0.7  # Default if confidence extraction fails
            
            return {
                'text': text,
                'confidence': avg_confidence
            }
        
        except Exception as e:
            self.logger.error(f"OCR failed for {image_path.name}: {e}", exc_info=True)
            return None
    
    def extract_text_from_pdf(self, pdf_path: Path, dpi: int = 300) -> Optional[Dict[str, Any]]:
        """
        Convert PDF pages to images and extract text via OCR.
        
        Args:
            pdf_path: Path to PDF file
            dpi: DPI for PDF to image conversion (higher = better quality, slower)
            
        Returns:
            Dict with combined 'text' and 'confidence', or None if failed
        """
        try:
            # Convert PDF to images
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                self.logger.debug(f"Converting PDF {pdf_path.name} to images at {dpi} DPI")
                
                images = pdf2image.convert_from_path(
                    pdf_path,
                    dpi=dpi,
                    output_folder=temp_dir,
                    fmt='png'
                )
                
                all_text = []
                all_confidences = []
                
                for page_num, image in enumerate(images, start=1):
                    self.logger.debug(f"OCR processing page {page_num} of {pdf_path.name}")
                    
                    # Preprocess and extract
                    image = self.preprocess_image(image)
                    
                    text = pytesseract.image_to_string(image, config='--psm 3 --oem 3')
                    all_text.append(text)
                    
                    # Get confidence
                    try:
                        data = pytesseract.image_to_data(
                            image,
                            config='--psm 3 --oem 3',
                            output_type=pytesseract.Output.DICT
                        )
                        confidences = [int(conf) for conf in data['conf'] if conf != '-1']
                        if confidences:
                            all_confidences.extend(confidences)
                    except:
                        pass
                
                combined_text = "\n\n".join(all_text)
                avg_confidence = (
                    sum(all_confidences) / len(all_confidences) / 100.0
                    if all_confidences else 0.5
                )
                
                return {
                    'text': combined_text,
                    'confidence': avg_confidence
                }
        
        except Exception as e:
            self.logger.error(
                f"PDF OCR failed for {pdf_path.name}: {e}",
                exc_info=True
            )
            return None
