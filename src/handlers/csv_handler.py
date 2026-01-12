"""
CSV file handler with column mapping and row-by-row extraction.
"""
import csv
import json
from pathlib import Path
from typing import Optional, Dict, Any, List


class CSVHandler:
    """Handler for CSV files with intelligent column mapping."""
    
    def __init__(self, logger, config_path: str = "config/field_patterns.json"):
        """
        Initialize CSV handler.
        
        Args:
            logger: Logger instance
            config_path: Path to field patterns configuration
        """
        self.logger = logger
        
        with open(config_path, 'r') as f:
            patterns = json.load(f)
        
        # Build synonym mappings from patterns
        self.field_synonyms = {
            'pickup_number': ['pickup', 'pkg', 'package', 'pickup_id', 'pkg_number', 
                              'package_number', 'pickup_no', 'pkg_no'],
            'scheduled_date': ['scheduled', 'date', 'pickup_date', 'collection_date',
                               'scheduled_on', 'pickup_time'],
            'material': ['material', 'type', 'waste_type', 'material_type', 'item',
                        'waste', 'recyclable'],
            'weight': ['weight', 'wt', 'mass', 'quantity', 'amount'],
            'weight_unit': ['unit', 'weight_unit', 'wt_unit', 'uom'],
            'reference_number': ['reference', 'ref', 'reference_no', 'ref_no',
                                 'order_number', 'order', 'order_id']
        }
    
    def map_columns_to_fields(self, headers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Map CSV column headers to field names.
        
        Args:
            headers: List of column headers from CSV
            
        Returns:
            Dict mapping field names to {column_index, mapping_type, confidence}
        """
        mappings = {}
        normalized_headers = [h.lower().strip().replace(' ', '_') for h in headers]
        
        for field_name, synonyms in self.field_synonyms.items():
            best_match = None
            best_confidence = 0.0
            best_type = 'none'
            
            for col_idx, header in enumerate(normalized_headers):
                # Check for exact match
                if header == field_name:
                    best_match = col_idx
                    best_confidence = 1.0
                    best_type = 'exact'
                    break
                
                # Check for synonym match
                for synonym in synonyms:
                    if synonym in header or header in synonym:
                        confidence = 0.85 if synonym == header else 0.75
                        if confidence > best_confidence:
                            best_match = col_idx
                            best_confidence = confidence
                            best_type = 'synonym'
            
            if best_match is not None:
                mappings[field_name] = {
                    'column_index': best_match,
                    'column_name': headers[best_match],
                    'mapping_type': best_type,
                    'confidence': best_confidence
                }
        
        return mappings
    
    def process(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Process CSV file and extract records row-by-row.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of extracted records (one per row), or empty list if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                # Try to detect dialect
                sample = f.read(4096)
                f.seek(0)
                
                try:
                    dialect = csv.Sniffer().sniff(sample)
                except csv.Error:
                    dialect = csv.excel
                
                reader = csv.reader(f, dialect=dialect)
                
                # Read headers
                try:
                    headers = next(reader)
                except StopIteration:
                    self.logger.error(f"CSV file {file_path.name} is empty")
                    return []
                
                # Map column headers to fields
                column_mappings = self.map_columns_to_fields(headers)
                
                self.logger.info(
                    f"CSV {file_path.name}: mapped {len(column_mappings)} of "
                    f"{len(self.field_synonyms)} fields"
                )
                
                # Process each row
                records = []
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    if not row or all(cell.strip() == '' for cell in row):
                        continue  # Skip empty rows
                    
                    record = {
                        'source_row': row_num,
                        'mapped_fields': {},
                        'raw_row': row
                    }
                    
                    # Extract fields based on mappings
                    for field_name, mapping in column_mappings.items():
                        col_idx = mapping['column_index']
                        
                        if col_idx < len(row):
                            value = row[col_idx].strip()
                            
                            record['mapped_fields'][field_name] = {
                                'value': value if value else None,
                                'confidence': mapping['confidence'] if value else 0.0,
                                'mapping_type': mapping['mapping_type'],
                                'source_column': mapping['column_name']
                            }
                        else:
                            record['mapped_fields'][field_name] = {
                                'value': None,
                                'confidence': 0.0,
                                'mapping_type': 'none',
                                'source_column': None
                            }
                    
                    # Add unmapped fields with null values
                    for field_name in self.field_synonyms.keys():
                        if field_name not in record['mapped_fields']:
                            record['mapped_fields'][field_name] = {
                                'value': None,
                                'confidence': 0.0,
                                'mapping_type': 'none',
                                'source_column': None
                            }
                    
                    records.append(record)
                
                self.logger.info(f"CSV {file_path.name}: extracted {len(records)} rows")
                return records
        
        except Exception as e:
            self.logger.error(
                f"Failed to process CSV {file_path.name}: {e}",
                exc_info=True
            )
            return []
