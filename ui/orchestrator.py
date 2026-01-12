"""
Orchestrator - Bridge between Streamlit UI and backend extraction system.
Handles subprocess execution of extraction pipeline.
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple


def run_extraction(folder_path: str, output_dir: str = "output") -> Tuple[bool, str, str]:
    """
    Run Phase 1 extraction pipeline.
    
    Executes src/main.py as a subprocess to avoid blocking the UI.
    
    Args:
        folder_path: Path to folder containing files to process
        output_dir: Output directory path (default: 'output')
    
    Returns:
        Tuple of (success: bool, message: str, output_path: str)
    """
    # Validate folder exists
    if not os.path.exists(folder_path):
        return False, f"Folder not found: {folder_path}", None
    
    if not os.path.isdir(folder_path):
        return False, f"Path is not a directory: {folder_path}", None
    
    # Get absolute paths
    folder_path = os.path.abspath(folder_path)
    output_dir = os.path.abspath(output_dir)
    
    # Path to main.py
    project_root = Path(__file__).parent.parent
    main_script = project_root / "src" / "main.py"
    
    if not main_script.exists():
        return False, f"Extraction script not found at {main_script}", None
    
    # Get API key from environment
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return False, "GOOGLE_API_KEY environment variable not set", None
    
    # Build command
    command = [
        sys.executable,  # Use same Python interpreter
        str(main_script),
        "--input", folder_path,
        "--output", output_dir,
        "--log-level", "INFO"
    ]
    
    try:
        # Run extraction as subprocess
        # Note: This blocks, but in a production version you'd want async execution
        # For Phase 1, we'll accept this limitation
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            cwd=str(project_root)
        )
        
        if result.returncode == 0:
            # Check if output was created
            index_file = Path(output_dir) / "index.json"
            if index_file.exists():
                return True, "Extraction completed successfully!", output_dir
            else:
                return False, "Extraction ran but no output found", None
        else:
            error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
            return False, f"Extraction failed: {error_msg}", None
    
    except subprocess.TimeoutExpired:
        return False, "Extraction timed out after 1 hour", None
    
    except Exception as e:
        return False, f"Error running extraction: {str(e)}", None


def check_dependencies() -> Tuple[bool, str]:
    """
    Check if all dependencies are available.
    
    Returns:
        Tuple of (all_ok: bool, message: str)
    """
    issues = []
    
    # Check Python
    if sys.version_info < (3, 8):
        issues.append(f"Python 3.8+ required (found {sys.version_info.major}.{sys.version_info.minor})")
    
    # Check API key
    if not os.getenv('GOOGLE_API_KEY'):
        issues.append("GOOGLE_API_KEY environment variable not set")
    
    # Check src/main.py exists
    project_root = Path(__file__).parent.parent
    main_script = project_root / "src" / "main.py"
    if not main_script.exists():
        issues.append(f"Extraction script not found at {main_script}")
    
    if issues:
        return False, "Issues found:\n" + "\n".join(f"• {issue}" for issue in issues)
    else:
        return True, "All dependencies OK"


# Phase 2A: API Key Validation and Semantic Analysis

def validate_api_key(api_key: str, max_retries: int = 2) -> Tuple[bool, str]:
    """
    Validate Google Gemini API key with a lightweight test call.
    
    Args:
        api_key: Google Gemini API key to validate
        max_retries: Number of retry attempts
    
    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    import time
    
    for attempt in range(max_retries):
        try:
            import google.generativeai as genai
            
            # Configure with provided key
            genai.configure(api_key=api_key)
            
            # Make a minimal test call - use stable model version
            model = genai.GenerativeModel('gemini-1.0-pro')
            response = model.generate_content(
                "Reply with only the word 'OK'",
                generation_config={
                    'temperature': 0,
                    'max_output_tokens': 10,
                }
            )
            
            # Check if we got a response
            if response and response.text:
                return True, "API key validated successfully"
            else:
                return False, "API key validation failed: No response from API"
        
        except Exception as e:
            error_msg = str(e)
            
            # Don't retry on clear auth failures
            if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                return False, "Invalid API key"
            elif "quota" in error_msg.lower():
                return False, "API quota exceeded"
            elif "permission" in error_msg.lower():
                return False, "API key lacks required permissions"
            
            # Retry on network/timeout errors
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                return False, f"Validation error: {error_msg[:100]}"
    
    return False, "Validation failed after retries"


def analyze_with_intent(
    index_path: str,
    api_key: str,
    intent: str,
    output_dir: str = "output"
) -> Tuple[bool, str, str]:
    """
    Run semantic analysis with custom user intent.
    
    Args:
        index_path: Path to index.json from Phase 1 extraction
        api_key: Google Gemini API key
        intent: Natural language intent from user
        output_dir: Output directory for results
    
    Returns:
        Tuple of (success: bool, message: str, output_path: str)
    """
    try:
        import json
        from datetime import datetime
        
        # Add src to path for imports
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root / "src"))
        
        from logger import create_logger
        from extractors.semantic_analyzer import SemanticAnalyzer
        
        # Load index
        if not os.path.exists(index_path):
            return False, f"Index file not found: {index_path}", None
        
        with open(index_path, 'r') as f:
            data = json.load(f)
        
        records = data.get('records', [])
        if not records:
            return False, "No records found in index", None
        
        # Create timestamped output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"semantic_analysis_{timestamp}.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Initialize logger (to temp location for UI)
        logger = create_logger(log_dir="logs", log_level="INFO")
        
        # Initialize semantic analyzer with custom intent
        analyzer = SemanticAnalyzer(logger, api_key)
        
        # Build text cache from source files
        text_cache = {}
        for record in records:
            record_id = record['record_id']
            source_file = record['source_file']
            file_type = record['file_type']
            
            # Extract text based on file type
            text = _extract_text_for_semantic(source_file, file_type, logger)
            if text:
                text_cache[record_id] = text
        
        # Run analysis with intent-modified prompts
        # Note: For Phase 2A, we'll add intent context to each analysis
        results = {}
        analyzed = 0
        skipped = 0
        
        for record in records:
            record_id = record['record_id']
            text = text_cache.get(record_id, '')
            
            if not text:
                skipped += 1
                continue
            
            avg_confidence = record['metadata'].get('average_confidence', 0.0)
            
            # For intent-driven analysis, we're more aggressive
            # We want to analyze even if pattern extraction was good
            if not text or len(text.strip()) < 50:
                skipped += 1
                continue
            
            # Wrap each document analysis in try/except to prevent total failure
            try:
                # Modify the analyzer's prompt creation to include intent
                # We'll do this by temporarily modifying the analyze_document method
                original_create_prompt = analyzer._create_analysis_prompt
                
                def intent_aware_prompt(text_arg, context_arg):
                    base_prompt = original_create_prompt(text_arg, context_arg)
                    # Insert intent before TASK section
                    intent_section = f"\n\nUSER INTENT:\n{intent}\n\nFocus your analysis on information relevant to this intent.\n"
                    return base_prompt.replace("TASK:", intent_section + "TASK:")
                
                analyzer._create_analysis_prompt = intent_aware_prompt
                
                # Analyze document
                result = analyzer.analyze_document(
                    text=text,
                    filename=Path(record['source_file']).name,
                    file_type=record['file_type'],
                    existing_fields=record['extracted_fields']
                )
                
                # Restore original method
                analyzer._create_analysis_prompt = original_create_prompt
                
                results[record_id] = result
                analyzed += 1
            
            except Exception as e:
                # Log error but continue processing
                logger.error(f"Failed to analyze {record_id}: {str(e)}")
                # Add error result instead of skipping
                results[record_id] = {
                    'document_type': 'unknown',
                    'key_observations': [],
                    'actionability_hint': f'Analysis failed: {str(e)[:100]}'
                }
                analyzed += 1  # Count as analyzed (with error)
        
        # Save results
        output_data = {
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source_index': index_path,
                'intent': intent,
                'total_records': len(records),
                'analyzed': analyzed,
                'skipped': skipped,
                'timestamp': timestamp
            },
            'semantic_analysis': results
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        return True, f"Analyzed {analyzed} documents (skipped {skipped})", output_path
    
    except Exception as e:
        return False, f"Analysis failed: {str(e)}", None


def _extract_text_for_semantic(source_file: str, file_type: str, logger) -> str:
    """
    Lightweight text extraction for semantic analysis.
    Reuses extraction logic without running full pipeline.
    """
    try:
        if file_type == 'pdf':
            import PyPDF2
            with open(source_file, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
                return text
        
        elif file_type == 'csv':
            with open(source_file, 'r', encoding='utf-8-sig') as f:
                return f.read()
        
        elif file_type == 'image':
            # Skip images for now (would need OCR)
            logger.debug(f"Skipping image {source_file} - OCR not cached")
            return ''
        
        else:
            return ''
    
    except Exception as e:
        logger.error(f"Error extracting text from {source_file}: {e}")
        return ''

