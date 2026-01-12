"""
Confidence scoring and actionable determination for extracted fields.
"""
import json
from typing import Dict, Any, List


class ConfidenceScorer:
    """Calculates confidence scores and determines actionable status."""
    
    def __init__(self, config_path: str = "config/thresholds.json"):
        """Initialize scorer with threshold configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.field_threshold = self.config['field_confidence_threshold']
        self.required_fields = self.config['required_fields_for_actionable']
    
    def score_pattern_match(self, match_type: str, ocr_quality: float = 1.0) -> float:
        """
        Calculate confidence score for pattern-based extraction.
        
        Args:
            match_type: Type of match (exact, keyword, position, fuzzy, none)
            ocr_quality: OCR quality multiplier (0.0-1.0)
            
        Returns:
            Confidence score (0.0-1.0)
        """
        base_scores = {
            'exact': 0.95,          # Exact regex pattern match
            'keyword': 0.80,        # Keyword proximity match
            'position': 0.60,       # Position-based extraction
            'fuzzy': 0.40,          # Fuzzy/partial match
            'none': 0.0             # No match found
        }
        
        base_score = base_scores.get(match_type, 0.0)
        return base_score * ocr_quality
    
    def score_llm_extraction(self, llm_certainty: str) -> float:
        """
        Calculate confidence score for LLM-based extraction.
        
        Args:
            llm_certainty: LLM's certainty level (high, medium, low)
            
        Returns:
            Confidence score (0.0-1.0)
        """
        certainty_scores = {
            'high': 0.90,
            'medium': 0.65,
            'low': 0.40
        }
        
        return certainty_scores.get(llm_certainty, 0.0)
    
    def score_csv_mapping(self, mapping_type: str) -> float:
        """
        Calculate confidence score for CSV column mapping.
        
        Args:
            mapping_type: Type of mapping (exact, synonym, inferred, none)
            
        Returns:
            Confidence score (0.0-1.0)
        """
        mapping_scores = {
            'exact': 1.0,           # Column header matches field name exactly
            'synonym': 0.85,        # Column header is known synonym
            'inferred': 0.60,       # Inferred from position/pattern
            'none': 0.0             # Could not map column
        }
        
        return mapping_scores.get(mapping_type, 0.0)
    
    def merge_scores(self, pattern_score: float, llm_score: float = None) -> Dict[str, Any]:
        """
        Merge pattern and LLM scores, taking higher confidence.
        
        Args:
            pattern_score: Score from pattern matching
            llm_score: Optional score from LLM extraction
            
        Returns:
            Dict with final score and extraction method
        """
        if llm_score is None:
            return {
                'confidence': pattern_score,
                'extraction_method': 'pattern'
            }
        
        if llm_score > pattern_score:
            return {
                'confidence': llm_score,
                'extraction_method': 'llm'
            }
        else:
            return {
                'confidence': pattern_score,
                'extraction_method': 'pattern' if pattern_score > 0 else 'llm'
            }
    
    def determine_actionable(self, extracted_fields: Dict[str, Dict[str, Any]]) -> bool:
        """
        Determine if record is actionable based on required fields.
        
        Args:
            extracted_fields: Dictionary of field names to {value, confidence} dicts
            
        Returns:
            True if all required fields meet threshold, False otherwise
        """
        for field_name in self.required_fields:
            field_data = extracted_fields.get(field_name, {})
            confidence = field_data.get('confidence', 0.0)
            value = field_data.get('value')
            
            # Field must exist, have a value, and meet threshold
            if value is None or confidence < self.field_threshold:
                return False
        
        return True
    
    def calculate_average_confidence(self, extracted_fields: Dict[str, Dict[str, Any]]) -> float:
        """
        Calculate average confidence across all extracted fields.
        
        Args:
            extracted_fields: Dictionary of field names to {value, confidence} dicts
            
        Returns:
            Average confidence score
        """
        confidences = [
            field_data.get('confidence', 0.0) 
            for field_data in extracted_fields.values()
        ]
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    def identify_low_confidence_fields(self, extracted_fields: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        Identify fields with confidence below threshold.
        
        Args:
            extracted_fields: Dictionary of field names to {value, confidence} dicts
            
        Returns:
            Dictionary of low-confidence field names to confidence scores
        """
        low_confidence = {}
        
        for field_name, field_data in extracted_fields.items():
            confidence = field_data.get('confidence', 0.0)
            if confidence < self.field_threshold:
                low_confidence[field_name] = confidence
        
        return low_confidence
