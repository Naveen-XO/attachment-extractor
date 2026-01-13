# QUICK START: User Journey at a Glance

## The Simple Path (Most Users)

```
┌────────────────────────────────────────────────────────────┐
│  STEP 1: ONE-TIME SETUP (5 minutes)                       │
├────────────────────────────────────────────────────────────┤
│  → pip install -r requirements.txt                         │
│  → Install Tesseract OCR                                   │
│  → Install Poppler                                         │
│  → python verify_extraction_mode.py  ✓                     │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 2: EVERY TIME YOU NEED EXTRACTION                   │
├────────────────────────────────────────────────────────────┤
│  → python src\main.py --input "C:\YourFolder"             │
│                                                            │
│  [Processing happens automatically...]                     │
│  • Scans all files recursively                            │
│  • OCR on images/scanned PDFs                             │
│  • Pattern matching for field extraction                  │
│  • No AI calls, no delays                                 │
│                                                            │
│  [Done in 1-2 seconds per file!]                          │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│  STEP 3: REVIEW YOUR RESULTS                              │
├────────────────────────────────────────────────────────────┤
│  Files created in output/ folder:                         │
│  • index.json        ← All your data                      │
│  • summary.txt       ← Stats & overview                    │
│  • records/*.json    ← Individual records                  │
│  • logs/*            ← Processing details                  │
└────────────────────────────────────────────────────────────┘
```

---

## AI Mode (When You Need It)

```
┌────────────────────────────────────────────────────────────┐
│  WHEN: Pattern extraction isn't enough                    │
├────────────────────────────────────────────────────────────┤
│  1. Edit config/feature_flags.json                        │
│     Change: "ENABLE_AI": false → true                     │
│                                                            │
│  2. Set API key:                                          │
│     $env:GOOGLE_API_KEY = "your-key"                      │
│                                                            │
│  3. Run extraction:                                       │
│     python src\main.py --input "C:\YourFolder"            │
│                                                            │
│  Now: Pattern extraction + LLM fallback                   │
│  Slower but more accurate on complex documents            │
└────────────────────────────────────────────────────────────┘
```

---

## Daily Workflow

### Morning: 100 PDFs to process

```powershell
# Put files in folder
# └─ C:\TodaysDocuments\

# Run extraction (AI disabled, fast)
python src\main.py --input "C:\TodaysDocuments"

# Wait ~2 minutes (100 files × ~1.2 sec each)

# Check results
cat output\summary.txt
# Shows: 100 files → 243 records → 85 actionable

# Open in Excel/JSON viewer
start output\index.json
```

**Total time:** 2-3 minutes  
**Cost:** $0  
**Effort:** One command

---

## Key Concepts

### What Happens During Extraction?

```
Your File → ┌─────────────┐ → ┌─────────────┐ → ┌─────────────┐ → JSON
            │   Read      │   │   Extract   │   │   Pattern   │
            │   (OCR if   │   │   Text      │   │   Match     │
            │   needed)   │   │             │   │   Fields    │
            └─────────────┘   └─────────────┘   └─────────────┘
                                                       │
                                            [AI disabled by default]
                                                       │
                                            (Optional: LLM if enabled)
```

### What Fields Are Extracted?

From each document, the system tries to find:

| Field | Example | Used For |
|-------|---------|----------|
| **pickup_number** | PKG-2026-00123 | Unique identifier |
| **scheduled_date** | 2026-01-15 | When it happens |
| **weight** | 450.0 | Amount |
| **weight_unit** | kg | Unit of measure |
| **material** | Mixed Recyclables | What it is |
| **reference_number** | REF-ABC-789 | External tracking |

### How Is Confidence Calculated?

| Match Type | Confidence | What It Means |
|------------|-----------|---------------|
| **Exact pattern** | 0.90-1.00 | Perfect match, very reliable |
| **Fuzzy pattern** | 0.60-0.80 | Close match, probably right |
| **Inferred** | 0.40-0.60 | Guessed, needs review |
| **LLM high** | 0.85-0.95 | AI very confident |
| **LLM medium** | 0.70-0.85 | AI somewhat confident |
| **LLM low** | 0.50-0.70 | AI uncertain |

---

## Decision Guide

### Should I Enable AI?

```
Check your results first (AI disabled):

├─ ✓ Good confidence (>0.75) on most records?
│  └─ Keep AI disabled → You're done!
│
├─ ✗ Low confidence on many records?
│  └─ Check logs/low_confidence.log
│     ├─ Same patterns repeating?
│     │  └─ Add to config/field_patterns.json
│     │
│     └─ Very different formats?
│        └─ Enable AI for those batches
│
└─ ? Mixed results?
   └─ Process in two batches:
      • High-confidence files → AI disabled (fast)
      • Low-confidence files → AI enabled (accurate)
```

---

## What Success Looks Like

### After Running Extraction

```
✓ Output folder created with:
  • index.json (your data)
  • summary.txt (stats)
  • 100+ individual JSON records

✓ Summary shows:
  • 95%+ files processed
  • 40-60% marked as "actionable"
  • Average confidence >0.75

✓ Logs show:
  • No errors (or very few)
  • Clear processing messages
  • "AI disabled" confirmation

✓ You can now:
  • Import to Excel/database
  • Filter actionable records
  • Process next batch
```

---

## Common Questions

**Q: Do I need an API key?**  
A: No! Not when AI is disabled (default mode).

**Q: How long does it take?**  
A: ~1-2 seconds per file (extraction-only), ~3-5 seconds with AI.

**Q: What if I have 10,000 files?**  
A: Process in batches using --test-mode, or let it run overnight (3-6 hours).

**Q: Can I customize what fields to extract?**  
A: Yes, edit `config/field_patterns.json` to add your patterns.

**Q: What if extraction quality is poor?**  
A: Try enabling AI, OR improve your patterns, OR re-scan at higher DPI.

**Q: Is my data sent to the cloud?**  
A: Only when AI is enabled (sends text to Gemini). Disabled by default.

**Q: Can I undo / re-run?**  
A: Yes! Output folder can be deleted and regenerated anytime.

---

## The Bottom Line

### Your Simplest Workflow:

```powershell
# Drop files in folder
# └─ C:\Documents\

# Run this one command
python src\main.py --input "C:\Documents"

# Wait (1-2 min per 100 files)

# Get results in output/
```

**That's it!**

---

**Now you're ready to extract. Just provide your folder path.**
