# Development Environment Setup
## For Developers Working on This Project

---

## Branch Structure

```
main (production)     ← Stable, AI disabled by default
  |
  └─ dev (development) ← Active development, AI enabled for testing
```

---

## Quick Setup for Developers

### 1. Clone and Switch to Dev Branch

```bash
# Clone repository
git clone https://github.com/Naveen-XO/attachment-extractor.git
cd attachment-extractor

# Switch to dev branch
git checkout dev

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Development Environment

```bash
# Copy dev config to active config
cp config/feature_flags.dev.json config/feature_flags.json

# Set API key for development
# Windows PowerShell:
$env:GOOGLE_API_KEY = "your-dev-api-key"

# Linux/Mac:
export GOOGLE_API_KEY="your-dev-api-key"
```

### 3. Verify Setup

```bash
python verify_extraction_mode.py
python check_flags.py
```

**Expected output:**
```
ENABLE_AI = True
Mode: ENABLED (Full AI)
```

---

## Environment Configurations

### Development (`config/feature_flags.dev.json`)
```json
{
  "ENABLE_AI": true,
  "debug_mode": true,
  "verbose_logging": true,
  "test_mode_default": true
}
```

**Use when:**
- Testing new features
- Debugging AI extraction
- Developing new extractors
- Running full test suite

### Production (`config/feature_flags.prod.json`)
```json
{
  "ENABLE_AI": false,
  "debug_mode": false,
  "verbose_logging": false,
  "test_mode_default": false
}
```

**Use when:**
- Deploying to users
- Processing large batches
- Need maximum speed
- Want zero API costs

---

## Development Workflow

### Working on New Features

```bash
# 1. Make sure you're on dev branch
git checkout dev
git pull origin dev

# 2. Use dev config
cp config/feature_flags.dev.json config/feature_flags.json

# 3. Make your changes
# Edit code...

# 4. Test your changes
python verify_extraction_mode.py
python src/main.py --input "test_data" --test-mode

# 5. Commit and push to dev
git add .
git commit -m "feat: your feature description"
git push origin dev
```

### Publishing to Production

```bash
# 1. Test thoroughly on dev branch
python verify_extraction_mode.py

# 2. Switch to main
git checkout main

# 3. Merge dev into main
git merge dev

# 4. Ensure production config is active
cp config/feature_flags.prod.json config/feature_flags.json
git add config/feature_flags.json
git commit -m "chore: production config"

# 5. Push to main
git push origin main
```

---

## Testing Guide

### Run All Tests

```bash
# Verify implementation
python verify_extraction_mode.py

# Test with AI disabled
cp config/feature_flags.prod.json config/feature_flags.json
python src/main.py --input "test_data" --test-mode

# Test with AI enabled
cp config/feature_flags.dev.json config/feature_flags.json
python src/main.py --input "test_data" --test-mode

# Compare results
```

### Test Extraction Modes

**Extraction-Only Mode:**
```bash
# feature_flags.json: ENABLE_AI = false
python src/main.py --input "test_docs" --test-mode --log-level DEBUG
# Should see: "AI disabled - LLM modules will not be imported"
```

**AI-Enabled Mode:**
```bash
# feature_flags.json: ENABLE_AI = true
python src/main.py --input "test_docs" --test-mode --log-level DEBUG
# Should see: "AI enabled - importing LLM modules..."
```

---

## Development vs Production

| Aspect | Development (dev) | Production (main) |
|--------|------------------|-------------------|
| **Branch** | `dev` | `main` |
| **Config** | `feature_flags.dev.json` | `feature_flags.prod.json` |
| **AI Mode** | Enabled | Disabled |
| **API Key** | Required | Not required |
| **Logging** | Verbose (DEBUG) | Standard (INFO) |
| **Speed** | Slower (testing accuracy) | Fast (production speed) |
| **Use Case** | Testing, debugging | End users, production |

---

## Project Structure

```
attachment-extractor/
│
├── config/
│   ├── feature_flags.json       ← Active config (gitignored in dev)
│   ├── feature_flags.dev.json   ← Dev template
│   ├── feature_flags.prod.json  ← Prod template
│   └── ...
│
├── src/
│   ├── main.py                  ← Loads feature_flags.json
│   ├── extractors/
│   │   ├── llm_extractor.py     ← Only imported if ENABLE_AI=true
│   │   └── semantic_analyzer.py ← Only imported if ENABLE_AI=true
│   └── ...
│
├── tests/                       ← (Create test suite here)
│
├── docs/
│   ├── DEV_SETUP.md             ← This file
│   ├── USER_JOURNEY.md
│   └── ...
│
└── ...
```

---

## Git Workflow

### Branching Strategy

```
main (stable, production-ready)
  └─ dev (active development)
      └─ feature/your-feature (optional feature branches)
```

### Typical Development Cycle

```bash
# Day 1: Start new feature
git checkout dev
git pull origin dev
git checkout -b feature/new-extraction-method

# Work on feature...
git add .
git commit -m "feat: add new extraction method"

# Day 2: Continue work
git add .
git commit -m "test: add tests for new method"

# Day 3: Ready to merge
git checkout dev
git merge feature/new-extraction-method
git push origin dev

# When stable: merge to main
git checkout main
git merge dev
git push origin main
```

---

## Environment Variables

### Required for Development

```bash
# Google Gemini API Key (for AI testing)
GOOGLE_API_KEY=your-key-here
```

### Optional

```bash
# Override default log level
LOG_LEVEL=DEBUG

# Override default output directory
OUTPUT_DIR=dev_output

# Tesseract path (if not in PATH)
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

## Common Development Tasks

### Switch to Development Mode

```bash
cp config/feature_flags.dev.json config/feature_flags.json
python check_flags.py
# Should show: ENABLE_AI = True
```

### Switch to Production Mode

```bash
cp config/feature_flags.prod.json config/feature_flags.json
python check_flags.py
# Should show: ENABLE_AI = False
```

### Test Both Modes

```bash
# Test extraction-only
cp config/feature_flags.prod.json config/feature_flags.json
python src/main.py --input test_data --test-mode

# Test AI-enabled
cp config/feature_flags.dev.json config/feature_flags.json
python src/main.py --input test_data --test-mode

# Compare outputs
```

### Debug AI Extraction

```bash
# Enable AI and verbose logging
cp config/feature_flags.dev.json config/feature_flags.json
python src/main.py --input "problem_file.pdf" --log-level DEBUG

# Check logs
cat logs/processing.log
```

---

## Code Guidelines

### When Adding New Features

1. **Work on dev branch**
2. **Test with both AI modes** (enabled/disabled)
3. **Update documentation**
4. **Add to verify_extraction_mode.py if needed**
5. **Keep AI modules optional** (conditional imports)

### When Modifying AI Code

- ✅ Keep imports conditional (`if enable_ai:`)
- ✅ Test with `ENABLE_AI=false` to ensure no breakage
- ✅ Document any new AI features
- ✅ Update feature flag descriptions

### When Modifying Extraction Code

- ✅ Test on both text-based and scanned PDFs
- ✅ Run with `--log-level DEBUG`
- ✅ Check confidence scores are reasonable
- ✅ Verify output format unchanged

---

## Troubleshooting Development Issues

### "LLM modules not found"

**Cause:** `ENABLE_AI=true` but dependencies not installed  
**Fix:** `pip install google-generativeai`

### "API key required"

**Cause:** `ENABLE_AI=true` but no API key set  
**Fix:** `export GOOGLE_API_KEY="your-key"`

### "Verification fails"

**Cause:** Code structure doesn't match verification expectations  
**Fix:** Check conditional imports are properly implemented

### "Tests pass locally but fail on main"

**Cause:** Probably using dev config on main branch  
**Fix:** Always use production config on main

---

## Release Checklist

Before merging dev to main:

- [ ] All tests pass on dev branch
- [ ] `verify_extraction_mode.py` passes
- [ ] Test with `ENABLE_AI=false` (extraction-only)
- [ ] Test with `ENABLE_AI=true` (full AI mode)
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Production config is set (`feature_flags.prod.json`)
- [ ] No sensitive data in commits
- [ ] README updated if needed

---

## Best Practices

✅ **Always work on dev branch** for new features  
✅ **Test both AI modes** before merging  
✅ **Keep feature flags in sync** with documentation  
✅ **Use meaningful commit messages**  
✅ **Document breaking changes**  
✅ **Keep main branch stable** at all times  

---

## Quick Reference Commands

```bash
# Setup
git checkout dev
pip install -r requirements.txt
cp config/feature_flags.dev.json config/feature_flags.json

# Development
python src/main.py --input test_data --test-mode --log-level DEBUG

# Testing
python verify_extraction_mode.py
python check_flags.py

# Switch modes
cp config/feature_flags.dev.json config/feature_flags.json    # Dev mode
cp config/feature_flags.prod.json config/feature_flags.json   # Prod mode

# Deploy to main
git checkout main
git merge dev
git push origin main
```

---

**Happy coding! 🚀**
