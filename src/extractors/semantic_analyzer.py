"""
Semantic document interpretation layer - Post-processing analysis.
Intelligently understands document content beyond predefined fields.
"""
import json
from typing import Dict, Any, Optional, List
import google.generativeai as genai


class SemanticAnalyzer:
    """
    Post-processing semantic analyzer for documents.
    Identifies document types and extracts operationally relevant information.
    """
    
    def __init__(self, logger, api_key: str, model_name: str = "gemini-1.0-pro"):
        """
        Initialize semantic analyzer.
        
        Args:
            logger: Logger instance
            api_key: Google Gemini API key
            model_name: Model to use for analysis (default: gemini-1.0-pro)
        """
        self.logger = logger
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Minimum text length to trigger semantic analysis
        self.min_text_length = 50
        
        # Document type categories
        self.document_types = [
            "logistics/pickup/delivery",
            "invoice",
            "confirmation",
            "report/summary",
            "label",
            "contract",
            "internal_note",
            "unknown"
        ]
        
        # Observation categories
        self.observation_categories = [
            "identifier",
            "date",
            "quantity",
            "amount",
            "entity",
            "location",
            "note",
            "other"
        ]
    
    def should_analyze(self, text: str, pattern_confidence: float) -> bool:
        """
        Determine if semantic analysis should run.
        
        Args:
            text: Extracted text from document
            pattern_confidence: Average confidence from pattern extraction
            
        Returns:
            True if semantic analysis should be performed
        """
        # Skip if no text
        if not text or len(text.strip()) < self.min_text_length:
            self.logger.debug("Semantic analysis skipped: insufficient text")
            return False
        
        # Skip if pattern extraction was highly successful
        if pattern_confidence >= 0.75:
            self.logger.debug(f"Semantic analysis skipped: pattern confidence {pattern_confidence:.2f} is sufficient")
            return False
        
        # Skip obvious noise (check for boilerplate indicators)
        lowercase_text = text.lower()
        boilerplate_indicators = [
            "unsubscribe",
            "privacy policy",
            "terms and conditions",
            "copyright",
            "all rights reserved"
        ]
        boilerplate_count = sum(1 for indicator in boilerplate_indicators if indicator in lowercase_text)
        
        if boilerplate_count >= 2 and len(text) < 500:
            self.logger.debug("Semantic analysis skipped: appears to be boilerplate")
            return False
        
        return True
    
    def analyze_document(
        self,
        text: str,
        filename: str,
        file_type: str,
        existing_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic analysis on a document.
        
        Args:
            text: Extracted text from document
            filename: Source filename
            file_type: Type of file (pdf, image, csv)
            existing_fields: Previously extracted fields from pattern matching
            
        Returns:
            Semantic analysis results
        """
        try:
            # Build context summary
            context = self._build_context_summary(existing_fields, filename, file_type)
            
            # Create semantic analysis prompt
            prompt = self._create_analysis_prompt(text, context)
            
            # Call LLM
            self.logger.debug(f"Running semantic analysis on {filename}")
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'top_p': 0.95,
                    'max_output_tokens': 2048,
                }
            )
            
            # Parse response
            result = self._parse_llm_response(response.text)
            
            if result:
                self.logger.info(f"Semantic analysis completed: {result['document_type']}")
                return result
            else:
                self.logger.warning("Failed to parse semantic analysis response")
                return self._empty_result("Failed to parse LLM response")
        
        except Exception as e:
            self.logger.error(f"Semantic analysis failed: {e}")
            return self._empty_result(f"Error: {str(e)}")
    
    def _build_context_summary(
        self,
        existing_fields: Optional[Dict[str, Any]],
        filename: str,
        file_type: str
    ) -> str:
        """Build context summary from existing data."""
        context_parts = [f"Filename: {filename}", f"File type: {file_type}"]
        
        if existing_fields:
            found_fields = []
            for field_name, field_data in existing_fields.items():
                if field_data.get('value') is not None:
                    found_fields.append(f"{field_name}={field_data['value']}")
            
            if found_fields:
                context_parts.append(f"Previously extracted: {', '.join(found_fields)}")
        
        return " | ".join(context_parts)
    
    def _create_analysis_prompt(self, text: str, context: str) -> str:
        """Create the semantic analysis prompt."""
        # Truncate text if too long
        max_text_length = 3000
        if len(text) > max_text_length:
            text = text[:max_text_length] + "...[truncated]"
        
        prompt = f"""You are analyzing a business document to extract operationally relevant information.

CONTEXT:
{context}

DOCUMENT TEXT:
{text}

TASK:
Analyze this document and identify:
1. Document type (logistics/pickup/delivery, invoice, confirmation, report/summary, label, contract, internal_note, unknown)
2. Key observations - ANY information that appears operationally important
3. Why each observation matters

IMPORTANT RULES:
- Do NOT limit yourself to predefined fields
- Look for ANY identifiers, dates, quantities, amounts, locations, entities, schedules, or notes
- Skip headers, footers, legal boilerplate, and noise
- If a value is clearly important but doesn't fit a category, include it as "other"
- Do NOT make up information that isn't in the text
- Provide confidence (0.0-1.0) for each observation
- Explain WHY each value matters operationally

OUTPUT FORMAT (valid JSON ONLY):
{{
  "document_type": "one of the categories listed",
  "key_observations": [
    {{
      "label": "human-readable label",
      "value": "extracted value",
      "category": "identifier|date|quantity|amount|entity|location|note|other",
      "confidence": 0.85,
      "reasoning": "why this matters operationally"
    }}
  ],
  "actionability_hint": "natural language summary of what this document could impact"
}}

Return ONLY valid JSON. No explanations before or after."""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse and validate LLM JSON response."""
        try:
            # Try to extract JSON from response
            # Sometimes LLM wraps it in markdown code blocks
            response_text = response_text.strip()
            
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate structure
            if 'document_type' not in result:
                self.logger.warning("Missing document_type in semantic analysis")
                return None
            
            if 'key_observations' not in result:
                result['key_observations'] = []
            
            if 'actionability_hint' not in result:
                result['actionability_hint'] = ""
            
            return result
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse semantic analysis JSON: {e}")
            self.logger.debug(f"Response text: {response_text[:500]}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing semantic analysis: {e}")
            return None
    
    def _empty_result(self, reason: str) -> Dict[str, Any]:
        """Return empty semantic analysis result."""
        return {
            'document_type': 'unknown',
            'key_observations': [],
            'actionability_hint': f"No meaningful information extracted. {reason}"
        }
    
    def analyze_batch(
        self,
        records: List[Dict[str, Any]],
        text_cache: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze a batch of records.
        
        Args:
            records: List of extraction records
            text_cache: Dictionary mapping record_id to extracted text
            
        Returns:
            Dictionary mapping record_id to semantic analysis results
        """
        results = {}
        analyzed_count = 0
        skipped_count = 0
        
        for record in records:
            record_id = record['record_id']
            text = text_cache.get(record_id, '')
            
            # Check if should analyze
            avg_confidence = record['metadata'].get('average_confidence', 0.0)
            
            if not self.should_analyze(text, avg_confidence):
                skipped_count += 1
                continue
            
            # Perform analysis
            result = self.analyze_document(
                text=text,
                filename=record['source_file'].split('\\')[-1],
                file_type=record['file_type'],
                existing_fields=record['extracted_fields']
            )
            
            results[record_id] = result
            analyzed_count += 1
            
            # Log progress every 10 documents
            if analyzed_count % 10 == 0:
                self.logger.info(f"Semantic analysis progress: {analyzed_count} analyzed, {skipped_count} skipped")
        
        self.logger.info(f"Semantic analysis complete: {analyzed_count} analyzed, {skipped_count} skipped")
        return results
