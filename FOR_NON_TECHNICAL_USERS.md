# 📋 SIMPLE GUIDE: Extract Data from Documents
## For Non-Technical Users

---

## 🎯 What This Does

**You have documents (PDFs, images, Excel files) with information in them.**  
**This tool reads them and puts the data into organized files you can use.**

**Think of it like a robot that:**
- Opens each document
- Finds important information (numbers, dates, names)
- Writes it down in neat organized lists
- You get a file with all the data ready to use

---

## ⚡ Quick Version (If You're In A Hurry)

1. Put your documents in a folder
2. Double-click `EXTRACT.bat`
3. Type your folder path when asked
4. Wait for it to finish
5. Open the `output` folder to see results

**That's it!**

---

## 📚 Detailed Steps

### PART 1: First Time Setup (Only Do This Once)

#### Step 1: Open PowerShell

1. Click the Windows Start button (bottom left)
2. Type: `PowerShell`
3. Click on **Windows PowerShell** (the blue icon)
4. A black window will open

#### Step 2: Go to the Right Folder

In the PowerShell window, type this and press Enter:
```
cd C:\Users\Navee\OneDrive\Desktop\attachment-extractor
```

✅ **You should see the folder path change**

#### Step 3: Install Required Programs

**Part A: Install Python Packages**

Type this and press Enter:
```
pip install -r requirements.txt
```

⏱️ **Wait 2-3 minutes** while it downloads and installs.  
✅ **You'll see "Successfully installed..." messages**

**Part B: Install Tesseract (OCR Reader)**

1. Open your web browser
2. Go to: https://github.com/UB-Mannheim/tesseract/wiki
3. Click the download link for Windows
4. Run the installer file
5. Click "Next" → "Next" → "Install"
6. Leave the default location: `C:\Program Files\Tesseract-OCR`

**Part C: Install Poppler (PDF Reader)**

1. Go to: https://github.com/oschwartz10612/poppler-windows/releases
2. Download the latest ZIP file
3. Extract it to: `C:\poppler\`
4. Find the folder: `C:\poppler\Library\bin`

**Add Poppler to PATH:**
1. Press Windows + R
2. Type: `sysdm.cpl` and press Enter
3. Click "Environment Variables"
4. Under "System variables", find "Path"
5. Click "Edit"
6. Click "New"
7. Type: `C:\poppler\Library\bin`
8. Click OK on all windows

#### Step 4: Test That Everything Works

In PowerShell, type:
```
python verify_extraction_mode.py
```

✅ **You should see: `[SUCCESS] ALL VERIFICATIONS PASSED!`**

❌ **If you see errors, ask for help before continuing**

---

### PART 2: Every Time You Want to Extract Data

#### Step 1: Organize Your Documents

Put all the documents you want to process in **one folder**.

For example:
```
C:\MyDocuments\
├── invoice1.pdf
├── receipt.jpg
├── data.csv
├── contract.pdf
└── ...
```

✅ **The tool will read all files in this folder and all subfolders**

#### Step 2: Run the Extraction

**Option A: Using the Command (Recommended)**

1. Open PowerShell (if not already open)
2. Make sure you're in the right folder:
   ```
   cd C:\Users\Navee\OneDrive\Desktop\attachment-extractor
   ```
3. Type this command (replace the path with YOUR folder):
   ```
   python src\main.py --input "C:\MyDocuments"
   ```
4. Press Enter

**Option B: Using the Automatic Script (Easier)**

1. Find the file: `EXTRACT.bat` (if it exists)
2. Double-click it
3. When asked, type your folder path
4. Press Enter

#### Step 3: Watch It Work

You'll see messages like:
```
Processing 127 files...
[1/127] Processing invoice1.pdf
[2/127] Processing receipt.jpg
...
```

⏱️ **Wait until you see: "Processing Complete!"**

**Time estimate:**
- 10 files = ~30 seconds
- 100 files = ~2-3 minutes
- 1000 files = ~20-30 minutes

☕ **For large batches, go get coffee!**

#### Step 4: Find Your Results

After it finishes, go to the folder:
```
C:\Users\Navee\OneDrive\Desktop\attachment-extractor\output\
```

You'll see these files:

📄 **summary.txt** - Quick overview (open with Notepad)
- How many files processed
- How many records created
- Success statistics

📄 **index.json** - All your data (open with Excel or Notepad)
- Complete list of everything extracted
- Can be imported into databases

📁 **records/** folder - Individual files
- One file for each record
- Easier to look at one at a time

---

### PART 3: Understanding Your Results

#### What's in the Results?

For each document, the tool tried to find:

| Field | What It Means | Example |
|-------|--------------|---------|
| **pickup_number** | Unique ID number | PKG-2026-00123 |
| **scheduled_date** | Date something happens | 2026-01-15 |
| **weight** | How much it weighs | 450 |
| **weight_unit** | Pounds, kg, etc. | kg |
| **material** | What type of stuff | Mixed Recyclables |
| **reference_number** | Another tracking number | REF-ABC-789 |

#### How to Read summary.txt

Open `output\summary.txt` in Notepad.

You'll see something like:
```
Total Files: 127
Processed: 125
Skipped: 2
Records Created: 348

Actionable Records: 142 / 348 (40.8%)
```

**What this means:**
- Started with 127 files
- Successfully read 125 of them
- Skipped 2 (maybe audio files or corrupted)
- Created 348 individual records
- 142 of those have all the important information ("actionable")

#### How to Use the Data

**For Excel:**
1. Open Excel
2. Click File → Open
3. Browse to: `output\index.json`
4. Excel will show you the data in a table
5. You can now sort, filter, and use it

**For Analysis:**
1. Give `output\index.json` to your data analyst
2. They can import it into any database or tool
3. All fields are already organized

---

## 🔧 Common Problems & Solutions

### Problem: "Python is not recognized"

**Solution:** Python isn't installed.
1. Go to: https://www.python.org/downloads/
2. Download Python
3. Install it
4. **Important:** Check "Add Python to PATH" during installation

### Problem: "Tesseract not found"

**Solution:** Tesseract isn't installed or not in PATH.
1. Make sure you installed Tesseract (see Part 1, Step 3B)
2. Check it's at: `C:\Program Files\Tesseract-OCR`
3. Restart PowerShell and try again

### Problem: "No records created"

**Possible reasons:**
- Folder path is wrong (check spelling)
- Files are in unsupported format (only PDFs, images, CSV work)
- Files are corrupted

**What to do:**
1. Open `logs\errors.log` in Notepad
2. Look for error messages
3. Share them with technical support

### Problem: "Processing is very slow"

**Normal speeds:**
- 1-2 seconds per simple PDF
- 3-5 seconds per scanned document
- 1-3 seconds per image

**If slower:**
- You might have very large files
- Just wait, it will finish
- Or try with fewer files first (use --test-mode)

### Problem: "Low confidence" in logs

**This is normal!**
- Means the tool isn't 100% sure about some data
- Check `logs\low_confidence.log` to see which records
- Manually verify those specific records

---

## 📋 Checklist for Each Batch

Before you start:
- [ ] All documents are in one folder
- [ ] You know the folder path (e.g., C:\MyDocuments)
- [ ] PowerShell is open
- [ ] You're in the right directory

Run extraction:
- [ ] Type the command with your folder path
- [ ] Press Enter
- [ ] Wait for "Processing Complete!"

After it finishes:
- [ ] Open output\summary.txt
- [ ] Check how many records were created
- [ ] Verify a few records look correct
- [ ] Use the data in Excel or your system

---

## 🎓 Quick Training Script

**If someone is showing you how to use this, ask them to:**

1. Show you where PowerShell is
2. Show you the command to run
3. Show you where to find the results
4. Show you what the output looks like
5. Let you try it once with them watching

**Practice on 5-10 test files first before doing a big batch!**

---

## 💾 Backup & Safety

**Important files to keep:**
- The whole `attachment-extractor` folder (this contains the program)
- Your `output\` folder (this contains your results)

**Safe to delete:**
- Files in `logs\` (these are just processing logs)
- Files in `output\` if you've already copied the data elsewhere

**Never delete:**
- `src\` folder (this is the program)
- `config\` folder (this has the settings)

---

## 📞 When to Ask for Help

Ask a technical person if:
- ❌ Verification test fails
- ❌ You see error messages you don't understand
- ❌ No records are created after processing
- ❌ Results look wrong or incomplete
- ❌ You need to extract different types of information

**What to tell them:**
1. What you were trying to do
2. What command you ran
3. What error message you saw (copy the exact text)
4. Share the file: `logs\errors.log`

---

## 🚀 Your Workflow in 3 Steps

### Every day/week when you have documents to process:

```
1. Put documents in a folder
   └─ Example: C:\TodaysInvoices\

2. Run extraction command
   └─ python src\main.py --input "C:\TodaysInvoices"

3. Get results from output folder
   └─ Open output\summary.txt to see what you got
```

**That's literally it!**

---

## 🎯 Success Tips

✅ **Start small** - Test with 10 files before doing 1000  
✅ **Check results** - Look at summary.txt after each batch  
✅ **Keep backups** - Copy output folder somewhere safe  
✅ **Be patient** - Large batches take time, that's normal  
✅ **Ask questions** - Better to ask than guess  

---

## 📝 Your Personal Notes Section

**Write down your specific settings here:**

My document folder location:
```
_________________________________________________
```

The exact command I use:
```
_________________________________________________
```

Who to contact if I have problems:
```
Name: _________________________________________
Email: ________________________________________
Phone: ________________________________________
```

Last successful run:
```
Date: _________________________________________
Files processed: _______________________________
Records created: _______________________________
```

---

## ✨ Remember

**You don't need to understand how it works.**  
**You just need to:**
1. Put files in a folder
2. Run the command
3. Get organized data out

**If something seems wrong, ask for help. That's completely normal!**

---

**Ready to try? Start with PART 2, Step 1!**
