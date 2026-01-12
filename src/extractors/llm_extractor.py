"""
LLM-based semantic extraction using Google Gemini.
"""
import json
import google.generativeai as genai
from typing import Dict, Any, Optional


class LLMExtractor:
    """LLM-based semantic field extraction using Google Gemini."""
    
    def __init__(self, logger, api_key: Optional[str] = None):
        """
        Initialize LLM extractor.
        
        Args:
            logger: Logger instance
            api_key: Google Gemini API key (or set GOOGLE_API_KEY env var)
        """
        self.logger = logger
        
        if api_key:
            genai.configure(api_key=api_key)
        
        # Use Gemini 1.5 Flash for fast, cost-effective extraction
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def create_extraction_prompt(self, text: str) -> str:
        """
        Create structured prompt for field extraction.
        
        Args:
            text: Raw text to extract fields from
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a data extraction specialist. Extract the following fields from the text below. Return ONLY valid JSON.

Required fields to extract:
- pickup_number: Unique identifier for the pickup (e.g., PKG-2024-001, ORDER-123, etc.)
- scheduled_date: Date scheduled for pickup or collection (format as YYYY-MM-DD)
- weight: Numeric weight value only (e.g., 450 for "450 kg")
- weight_unit: Unit of measurement (kg, lbs, or tons)
- material: Type of material or waste (e.g., "Mixed Recyclables", "Paper", "Metal")
- reference_number: Reference or order number (e.g., REF-ABC-123)

For each field, provide:
1. value: The extracted value (or null if not found)
2. certainty: Your confidence level (high, medium, or low)

Return ONLY this JSON structure, nothing else:
{{
  "pickup_number": {{"value": "...", "certainty": "high/medium/low"}},
  "scheduled_date": {{"value": "YYYY-MM-DD or null", "certainty": "high/medium/low"}},
  "weight": {{"value": number or null, "certainty": "high/medium/low"}},
  "weight_unit": {{"value": "kg/lbs/tons or null", "certainty": "high/medium/low"}},
  "material": {{"value": "...", "certainty": "high/medium/low"}},
  "reference_number": {{"value": "...", "certainty": "high/medium/low"}}
}}

Text to extract from:
{text[:3000]}

Return only the JSON, no explanation."""
        
        return prompt
    
    def extract_fields(self, text: str) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Extract fields from text using LLM.
        
        Args:
            text: Raw text to extract fields from
            
        Returns:
            Dict mapping field names to {value, certainty}, or None if failed
        """
        try:
            self.logger.debug("Sending text to LLM for semantic extraction")
            
            prompt = self.create_extraction_prompt(text)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent extraction
                    top_p=0.95,
                    max_output_tokens=1024,
                )
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            
            result = json.loads(response_text)
            
            self.logger.debug(f"LLM extraction successful: {len(result)} fields")
            return result
        
        except json.JSONDecodeError as e:
            self.logger.error(f"LLM returned invalid JSON: {e}")
            self.logger.debug(f"LLM response: {response_text}")
            return None
        
        except Exception as e:
            self.logger.error(f"LLM extraction failed: {e}", exc_info=True)
            return None
    
    def validate_and_normalize(self, llm_output: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Validate and normalize LLM output.
        
        Args:
            llm_output: Raw LLM extraction output
            
        Returns:
            Validated and normalized field dictionary
        """
        normalized = {}
        
        expected_fields = [
            'pickup_number', 'scheduled_date', 'weight',
            'weight_unit', 'material', 'reference_number'
        ]
        
        for field_name in expected_fields:
            field_data = llm_output.get(field_name, {})
            
            value = field_data.get('value')
            certainty = field_data.get('certainty', 'low')
            
            # Normalize certainty to lowercase
            certainty = certainty.lower() if isinstance(certainty, str) else 'low'
            
            # Ensure certainty is valid
            if certainty not in ['high', 'medium', 'low']:
                certainty = 'low'
            
            # Special handling for weight (ensure numeric)
            if field_name == 'weight' and value is not None:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = None
                    certainty = 'low'
            
            # Special handling for weight_unit (normalize)
            if field_name == 'weight_unit' and value is not None:
                value = value.lower()
                if value not in ['kg', 'lbs', 'tons']:
                    # Try to normalize common variations
                    if 'kg' in value or 'kilo' in value:
                        value = 'kg'
                    elif 'lb' in value or 'pound' in value:
                        value = 'lbs'
                    elif 'ton' in value:
                        value = 'tons'
                    else:
                        certainty = 'low'
            
            normalized[field_name] = {
                'value': value,
                'certainty': certainty
            }
        
        return normalized
