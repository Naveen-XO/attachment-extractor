"""
File scanner for discovering and cataloging email attachments.
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple


class FileScanner:
    """Scans directory and catalogs files by type."""
    
    def __init__(self, config_path: str = "config/file_extensions.json"):
        """Initialize scanner with file type mappings."""
        with open(config_path, 'r') as f:
            self.extensions = json.load(f)
        
        # Create reverse mapping: extension -> type
        self.ext_to_type = {}
        for file_type, exts in self.extensions.items():
            for ext in exts:
                self.ext_to_type[ext.lower()] = file_type
    
    def scan_directory(self, directory: str) -> Dict[str, List[Path]]:
        """
        Recursively scan directory and catalog files by type.
        
        Args:
            directory: Path to directory to scan
            
        Returns:
            Dictionary mapping file type to list of file paths
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Initialize catalog
        catalog = {
            'audio': [],
            'image': [],
            'pdf': [],
            'csv': [],
            'document': [],
            'unknown': []
        }
        
        # Recursively find all files
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                file_type = self.ext_to_type.get(ext, 'unknown')
                catalog[file_type].append(file_path)
        
        return catalog
    
    def create_processing_manifest(self, catalog: Dict[str, List[Path]]) -> List[Tuple[Path, str]]:
        """
        Create ordered list of files to process.
        
        Args:
            catalog: File catalog from scan_directory
            
        Returns:
            List of (file_path, file_type) tuples
        """
        manifest = []
        
        # Process in order: CSV first (fastest), then PDF, images, documents
        # Audio files are not included  in manifest (will be skipped)
        for file_type in ['csv', 'pdf', 'image', 'document']:
            for file_path in catalog.get(file_type, []):
                manifest.append((file_path, file_type))
        
        return manifest
    
    def get_statistics(self, catalog: Dict[str, List[Path]]) -> Dict[str, int]:
        """
        Get file count statistics.
        
        Args:
            catalog: File catalog from scan_directory
            
        Returns:
            Dictionary with counts by type and total
        """
        stats = {file_type: len(files) for file_type, files in catalog.items()}
        stats['total'] = sum(stats.values())
        return stats
