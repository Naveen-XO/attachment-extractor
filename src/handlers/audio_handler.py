"""
Audio file handler - skips processing and logs.
"""
from pathlib import Path
from typing import Optional, Dict, Any


class AudioHandler:
    """Handler for audio files - skips without processing."""
    
    def __init__(self, logger):
        """Initialize audio handler."""
        self.logger = logger
    
    def should_skip(self, file_path: Path) -> bool:
        """Audio files are always skipped."""
        return True
    
    def process(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Process audio file (actually just logs and skips).
        
        Args:
            file_path: Path to audio file
            
        Returns:
            None (file is skipped)
        """
        self.logger.log_skipped_file(
            str(file_path),
            "Audio file - no transcription extraction per requirements"
        )
        return None
