"""
Field extractor orchestrator - combines pattern and LLM extraction.
"""
import json
from typing import Dict, Any, Optional


class FieldExtractor:
    """Main field extraction orchestrator combining pattern and LLM methods."""
    
    def __init__(self, logger, text_parser, llm_extractor, confidence_scorer,
                 config_path: str = "config/thresholds.json"):
        """
        Initialize field extractor.
        
        Args:
            logger: Logger instance
            text_parser: TextParser instance
            llm_extractor: LLMExtractor instance or None (when AI disabled)
            confidence_scorer: ConfidenceScorer instance
            config_path: Path to thresholds configuration
        """
        self.logger = logger
        self.text_parser = text_parser
        self.llm_extractor = llm_extractor  # Can be None when ENABLE_AI=false
        self.confidence_scorer = confidence_scorer
        self.ai_enabled = llm_extractor is not None
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.llm_fallback_threshold = config['llm_fallback_trigger_threshold']
        self.llm_fallback_min_fields = config['llm_fallback_min_fields']
    
    def should_trigger_llm_fallback(self, pattern_results: Dict[str, Dict[str, Any]]) -> bool:
        """
        Determine if LLM fallback should be triggered.
        
        Args:
            pattern_results: Results from pattern extraction
            
        Returns:
            True if LLM fallback should be used
        """
        # Count fields with confidence >= threshold
        good_fields = 0
        
        for field_name, field_data in pattern_results.items():
            match_type = field_data.get('match_type', 'none')
            value = field_data.get('value')
            
            if value is not None:
                confidence = self.confidence_scorer.score_pattern_match(match_type)
                if confidence >= self.llm_fallback_threshold:
                    good_fields += 1
        
        # Trigger LLM if we don't have enough good fields
        return good_fields < self.llm_fallback_min_fields
    
    def merge_pattern_and_llm_results(
        self,
        pattern_results: Dict[str, Dict[str, Any]],
        llm_results: Optional[Dict[str, Dict[str, Any]]],
        ocr_quality: float = 1.0
    ) -> Dict[str, Dict[str, Any]]:
        """
        Merge pattern and LLM extraction results, taking higher confidence.
        
        Args:
            pattern_results: Results from pattern extraction
            llm_results: Optional results from LLM extraction
            ocr_quality: OCR quality multiplier
            
        Returns:
            Merged field dictionary with values and confidences
        """
        merged = {}
        
        for field_name, pattern_data in pattern_results.items():
            # Get pattern-based value and confidence
            pattern_value = pattern_data.get('value')
            match_type = pattern_data.get('match_type', 'none')
            pattern_confidence = self.confidence_scorer.score_pattern_match(
                match_type,
                ocr_quality
            )
            
            # Check if we have LLM result for this field
            llm_data = llm_results.get(field_name, {}) if llm_results else {}
            llm_value = llm_data.get('value')
            llm_certainty = llm_data.get('certainty', 'low')
            llm_confidence = self.confidence_scorer.score_llm_extraction(llm_certainty)
            
            # Choose higher confidence result
            if llm_value is not None and llm_confidence > pattern_confidence:
                final_value = llm_value
                final_confidence = llm_confidence
                extraction_method = 'llm'
            elif pattern_value is not None:
                final_value = pattern_value
                final_confidence = pattern_confidence
                extraction_method = 'pattern'
            elif llm_value is not None:
                # LLM found something even if confidence is lower
                final_value = llm_value
                final_confidence = llm_confidence
                extraction_method = 'llm'
            else:
                final_value = None
                final_confidence = 0.0
                extraction_method = 'none'
            
            merged[field_name] = {
                'value': final_value,
                'confidence': final_confidence,
                'extraction_method': extraction_method
            }
        
        return merged
    
    def extract(self, text: str, ocr_quality: float = 1.0) -> Dict[str, Any]:
        """
        Extract fields from text using hybrid pattern + LLM approach.
        
        Args:
            text: Raw text to extract from
            ocr_quality: OCR quality multiplier (0.0-1.0)
            
        Returns:
            Dictionary with extracted fields, metadata, and notes
        """
        # Step 1: Apply pattern matchers
        self.logger.debug("Applying pattern-based extraction")
        pattern_results = self.text_parser.extract_all_fields(text)
        
        # Step 2: Evaluate pattern results and check if AI is enabled
        should_use_llm = False
        
        if self.ai_enabled:
            should_use_llm = self.should_trigger_llm_fallback(pattern_results)
        
        # Step 3: Apply LLM fallback if enabled and triggered
        llm_results = None
        
        if should_use_llm:
            self.logger.debug("Pattern extraction insufficient, triggering LLM fallback")
            llm_results = self.llm_extractor.extract_fields(text)
            
            if llm_results:
                # Validate and normalize LLM output
                llm_results = self.llm_extractor.validate_and_normalize(llm_results)
        else:
            if not self.ai_enabled:
                self.logger.debug("AI disabled - LLM extraction skipped")
            else:
                self.logger.debug("Pattern extraction sufficient - LLM not needed")
        
        # Step 4: Merge results
        extracted_fields = self.merge_pattern_and_llm_results(
            pattern_results,
            llm_results,
            ocr_quality
        )
        
        # Step 5: Calculate metadata
        extraction_methods = set(
            field['extraction_method'] 
            for field in extracted_fields.values()
        )
        
        if 'llm' in extraction_methods and 'pattern' in extraction_methods:
            overall_method = 'hybrid'
        elif 'llm' in extraction_methods:
            overall_method = 'llm'
        elif 'pattern' in extraction_methods:
            overall_method = 'pattern'
        else:
            overall_method = 'none'
        
        avg_confidence = self.confidence_scorer.calculate_average_confidence(extracted_fields)
        
        # Generate notes
        notes_parts = []
        
        if overall_method == 'hybrid':
            notes_parts.append("Used hybrid extraction (pattern + LLM)")
        elif overall_method == 'llm':
            notes_parts.append("Used LLM semantic extraction")
        elif overall_method == 'pattern':
            notes_parts.append("Used pattern-based extraction")
        
        field_counts = {
            'found': sum(1 for f in extracted_fields.values() if f['value'] is not None),
            'total': len(extracted_fields)
        }
        notes_parts.append(f"Extracted {field_counts['found']}/{field_counts['total']} fields")
        
        notes = "; ".join(notes_parts)
        
        return {
            'extracted_fields': extracted_fields,
            'extraction_method': overall_method,
            'average_confidence': avg_confidence,
            'notes': notes
        }
