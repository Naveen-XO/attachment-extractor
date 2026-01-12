"""
Pattern-based text parser for field extraction.
"""
import json
import re
from datetime import datetime
from dateutil import parser as date_parser
from typing import Dict, Any, Optional, Tuple


class TextParser:
    """Pattern-based text parsing for field extraction."""
    
    def __init__(self, logger, config_path: str = "config/field_patterns.json"):
        """
        Initialize text parser.
        
        Args:
            logger: Logger instance
            config_path: Path to field patterns configuration
        """
        self.logger = logger
        
        with open(config_path, 'r') as f:
            self.patterns = json.load(f)
    
    def extract_field_with_pattern(self, text: str, field_name: str) -> Tuple[Optional[str], str]:
        """
        Extract a single field using regex patterns.
        
        Args:
            text: Text to extract from
            field_name: Name of field to extract
            
        Returns:
            Tuple of (value, match_type)
        """
        field_config = self.patterns.get(field_name, {})
        patterns_list = field_config.get('patterns', [])
        keywords = field_config.get('keywords', [])
        
        # Try exact pattern matches first
        for pattern in patterns_list:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip() if match.groups() else match.group(0).strip()
                    if value:
                        return value, 'exact'
            except Exception as e:
                self.logger.debug(f"Pattern match error for {field_name}: {e}")
                continue
        
        # Try keyword proximity matching
        for keyword in keywords:
            # Find keyword in text
            keyword_pattern = re.escape(keyword)
            match = re.search(f"{keyword_pattern}[:\\s-]*([A-Za-z0-9-]+)", text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value:
                    return value, 'keyword'
        
        return None, 'none'
    
    def normalize_date(self, date_str: str) -> Optional[str]:
        """
        Parse and normalize date to YYYY-MM-DD format.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Normalized date string or None if parsing failed
        """
        try:
            parsed_date = date_parser.parse(date_str, fuzzy=True)
            return parsed_date.strftime('%Y-%m-%d')
        except:
            return None
    
    def normalize_weight_unit(self, unit_str: str) -> Optional[str]:
        """
        Normalize weight unit to standard format.
        
        Args:
            unit_str: Weight unit string
            
        Returns:
            Normalized unit (kg, lbs, tons) or None
        """
        unit_lower = unit_str.lower().strip()
        
        normalization = self.patterns.get('weight_unit', {}).get('normalization', {})
        
        for standard_unit, variations in normalization.items():
            if unit_lower in [v.lower() for v in variations]:
                return standard_unit
        
        return unit_lower if unit_lower in ['kg', 'lbs', 'tons'] else None
    
    def extract_all_fields(self, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract all fields from text using patterns.
        
        Args:
            text: Text to extract from
            
        Returns:
            Dict mapping field names to {value, match_type}
        """
        extracted = {}
        
        field_names = [
            'pickup_number', 'scheduled_date', 'material',
            'weight', 'weight_unit', 'reference_number'
        ]
        
        for field_name in field_names:
            value, match_type = self.extract_field_with_pattern(text, field_name)
            
            # Post-process specific fields
            if field_name == 'scheduled_date' and value:
                value = self.normalize_date(value)
                if not value:
                    match_type = 'none'
            
            elif field_name == 'weight_unit' and value:
                value = self.normalize_weight_unit(value)
                if not value:
                    match_type = 'none'
            
            elif field_name == 'weight' and value:
                # Extract numeric part and clean
                try:
                    # Remove non-numeric characters except decimal point
                    numeric_value = re.sub(r'[^\d.]', '', value)
                    value = float(numeric_value)
                except (ValueError, TypeError):
                    value = None
                    match_type = 'none'
            
            extracted[field_name] = {
                'value': value,
                'match_type': match_type
            }
        
        return extracted
