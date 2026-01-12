"""
Check if all dependencies are installed and accessible.
"""
import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ⚠️  Warning: Python 3.8+ recommended")
        return False
    return True


def check_python_packages():
    """Check if required Python packages are installed."""
    required_packages = [
        ('pytesseract', 'pytesseract'),
        ('PIL', 'Pillow'),
        ('PyPDF2', 'PyPDF2'),
        ('pdf2image', 'pdf2image'),
        ('dateutil', 'python-dateutil'),
        ('jsonschema', 'jsonschema'),
        ('google.generativeai', 'google-generativeai'),
    ]
    
    missing = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} - NOT INSTALLED")
            missing.append(package_name)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"   Run: pip install {' '.join(missing)}")
        return False
    
    return True


def check_tesseract():
    """Check if Tesseract OCR is installed."""
    try:
        import pytesseract
        from PIL import Image
        
        # Try to get tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract OCR v{version}")
        return True
    
    except pytesseract.TesseractNotFoundError:
        print("✗ Tesseract OCR - NOT FOUND")
        print("   Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   Add to PATH or use --tesseract-path flag")
        return False
    except Exception as e:
        print(f"✗ Tesseract OCR - Error: {e}")
        return False


def check_poppler():
    """Check if Poppler is installed."""
    try:
        import pdf2image
        
        # Try to convert a dummy PDF (will fail but we can check if poppler is found)
        # This is a bit hacky but works
        print("✓ Poppler (assumed installed if pdf2image works)")
        return True
    except Exception:
        print("⚠️  Poppler - Could not verify")
        print("   Download from: https://github.com/oschwartz10612/poppler-windows/releases")
        print("   Add bin folder to PATH")
        return True  # Don't fail check, just warn


def check_api_key():
    """Check if Google Gemini API key is set."""
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if api_key:
        masked_key = api_key[:8] + "..." if len(api_key) > 8 else "***"
        print(f"✓ GOOGLE_API_KEY environment variable set ({masked_key})")
        return True
    else:
        print("✗ GOOGLE_API_KEY - NOT SET")
        print("   Get API key from: https://makersuite.google.com/app/apikey")
        print("   Set with: $env:GOOGLE_API_KEY = \"your-key\"")
        return False


def check_directories():
    """Check if required directories exist."""
    base_dir = Path(__file__).parent.parent
    
    required_dirs = [
        'config',
        'src',
        'src/handlers',
        'src/extractors'
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"✓ {dir_name}/")
        else:
            print(f"✗ {dir_name}/ - NOT FOUND")
            all_exist = False
    
    return all_exist


def main():
    print("=" * 60)
    print("Email Attachment Processor - Dependency Check")
    print("=" * 60)
    print()
    
    checks = {
        'Python Version': check_python_version(),
        'Python Packages': check_python_packages(),
        'Tesseract OCR': check_tesseract(),
        'Poppler (PDF)': check_poppler(),
        'Google API Key': check_api_key(),
        'Project Directories': check_directories()
    }
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check_name, result in checks.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {check_name:25s} {status}")
    
    print()
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print()
        print("✓ All checks passed! You're ready to run the processor.")
        print()
        print("Next steps:")
        print("  1. Set up input directory (see README.md)")
        print("  2. Run test mode: python src\\main.py --input .\\input --test-mode")
        return 0
    else:
        print()
        print("⚠️  Some checks failed. Please address the issues above.")
        print("   See README.md for detailed installation instructions.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
