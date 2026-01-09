# Claude Code Orchestration Guide

This document describes how Claude Code should run the literature review pipeline.

## Prerequisites

Before starting, verify:
1. `input/form_response.xlsx` exists (Microsoft Forms export)
2. `input/pdfs/` contains all source PDFs (downloaded from shared folder)
3. `.env` file has `GEMINI_API_KEY` set

## Orchestration Flow

### Phase 0: Prepare Input Files

Before running any scripts, verify input files are ready:

```bash
# Check Excel export exists
ls input/form_response.xlsx

# Check PDFs folder
ls input/pdfs/
```

**If Excel exists but `input/pdfs/` is empty or missing:**

1. Parse the Excel file to get the PDF folder link:
```bash
python -c "import pandas as pd; df = pd.read_excel('input/form_response.xlsx'); print('PDF Folder Link:', df.iloc[-1].get('pdf_folder_link', 'Not provided'))"
```

2. Inform the operator:
```
The input/pdfs/ folder is empty.

Please download PDFs from the shared folder link:
  [FOLDER_LINK]

Then place them in input/pdfs/ before proceeding.

PDF filenames should contain author name and year for automatic matching.
Examples: 'Kong_2023_meta_analysis.pdf', 'Smith et al 2024.pdf'
```

3. Wait for operator to confirm PDFs are downloaded before proceeding.

**Decision:**
- If both Excel and PDFs exist -> proceed to Phase 1
- If PDFs missing -> inform operator, wait for download

---

### Phase 1: Ingest

```bash
python scripts/01_ingest.py input/form_response.xlsx input/pdfs/
```

**What it does:**
- Parses Excel file for project metadata, research questions, and citations
- Displays the PDF folder link from the form (for reference)
- Matches PDFs to citations by author name and year
- Copies and renames PDFs to numbered format (01_Author_2023.pdf)
- Generates `config/project.yaml`

**Review checklist:**
1. Check exit code (0 = success, 1 = errors)
2. View `config/project.yaml`:
   - Are research questions parsed correctly?
   - Are all sources listed?
3. Check `pdfs/` folder has the expected number of files
4. If matching errors reported:
   - Show which sources couldn't be matched
   - Suggest renaming PDFs to include author_year

**Decision:**
- If no errors -> proceed to Phase 2
- If matching errors -> report to user, suggest fixes

---

### Phase 2: Translate Framing

```bash
python scripts/02_translate_framing.py config/project.yaml
```

**What it does:**
- Reads raw context from config
- Calls Gemini 3 Flash to create structured framing
- Updates config with `context_translated` field

**Review checklist:**
1. Read the translated framing output
2. Compare to original context
3. Check it's neutral (not biasing toward specific findings)
4. Verify it captures the research intent

**Decision:**
- If framing looks good -> proceed to Phase 3
- If problematic -> edit `config/project.yaml` directly, or re-run with `--skip`

---

### Phase 3a: Spot-Check Extraction

```bash
python scripts/03_extract.py config/project.yaml --sources 1-3
```

**What it does:**
- Uploads first 3 PDFs to Gemini
- Extracts evidence for each research question
- Saves JSON files to `extractions/`

**Review checklist:**
1. View `extractions/01_*.json`, `02_*.json`, `03_*.json`
2. For each, check:
   - `citation` and `title` are correct
   - `supporting_quotes` contain actual text from the paper
   - `has_evidence` flags are reasonable
   - Effect sizes are properly formatted
3. **Critical:** Do quotes look genuine (not fabricated)?

**Decision:**
- If quality is good -> proceed to Phase 3b
- If quotes seem fabricated -> STOP, report to user
- If minor issues -> note them, proceed with caution

---

### Phase 3b: Full Extraction

```bash
python scripts/03_extract.py config/project.yaml --sources 4-N
```

(Replace N with total source count)

**What it does:**
- Processes remaining PDFs
- Each takes 30-60 seconds

**Monitor for:**
- Multiple consecutive failures
- API errors

**Decision:**
- If mostly successful -> proceed to Phase 4
- If many failures -> report which sources failed, suggest re-running individual sources with `--source N`

---

### Phase 4: Aggregate

```bash
python scripts/04_aggregate.py config/project.yaml
```

**What it does:**
- Loads all extraction JSONs
- Generates `output/review_by_rq.md`
- Generates `output/extraction_matrix.xlsx`
- Calculates coverage statistics

**Review checklist:**
1. Check coverage percentages (output in terminal)
2. Flag any RQs with very low coverage (<20%)
3. View `output/review_by_rq.md`:
   - Structure looks correct?
   - Citations formatted properly?
4. Optionally preview Excel file

**Decision:**
- If outputs look good -> proceed to Phase 5
- If issues -> can re-run after fixing extractions

---

### Phase 5: Archive

```bash
python scripts/05_archive.py config/project.yaml
```

**What it does:**
- Creates timestamped folder in `runs/`
- Copies config, extractions, and outputs
- Creates run summary

**Final report to user:**
- Number of sources processed
- Evidence coverage by RQ
- Location of deliverables:
  - `output/review_by_rq.md`
  - `output/extraction_matrix.xlsx`
- Any warnings or issues noted

---

## Error Handling

| Error | Action |
|-------|--------|
| Missing GEMINI_API_KEY | Stop, tell user to configure `.env` |
| No PDFs in input folder | Display folder link, instruct operator to download |
| PDFs not matched | Show unmatched files, suggest renaming with author_year |
| API rate limit | Script handles retries; if persistent, wait 60s |
| Extraction failures | Note which sources failed, offer to retry |
| Low coverage RQ | Flag in final report (not a blocker) |

---

## Example Session

```
User: Run the literature review pipeline on my files.

Claude Code:
1. Checks input/ folder:
   "Found form_response.xlsx"
   "Checking input/pdfs/..."

2. If PDFs missing:
   "No PDFs found in input/pdfs/

   The form includes this folder link:
   https://sharepoint.com/sites/research/papers

   Please download PDFs from this link and place them in input/pdfs/
   Let me know when ready."

3. User: "Done, PDFs are downloaded"

4. Runs: python scripts/01_ingest.py input/form_response.xlsx input/pdfs/
5. Reviews output, reports:
   "Found 15 sources and 3 research questions.
   PDF folder link: https://sharepoint.com/sites/research/papers
   14/15 PDFs matched successfully.

   Source 7 (Chen et al. 2022) could not be matched.
   Please check if the PDF filename contains 'Chen' and '2022'."

6. User fixes filename or confirms to proceed with 14 sources

7. Runs: python scripts/02_translate_framing.py config/project.yaml
8. Shows translated framing, asks:
   "Does this framing look appropriate for your review?"

9. User confirms

10. Runs: python scripts/03_extract.py config/project.yaml --sources 1-3
11. Reviews extractions, reports:
    "Spot-check complete. Quotes verified against first 3 PDFs.
    Quality looks good. Proceeding with remaining 12 sources."

12. Runs: python scripts/03_extract.py config/project.yaml --sources 4-15

13. Runs: python scripts/04_aggregate.py config/project.yaml
14. Reports coverage stats:
    "RQ1: 80% coverage (12/15 sources)
     RQ2: 53% coverage (8/15 sources)
     RQ3: 67% coverage (10/15 sources)"

15. Runs: python scripts/05_archive.py config/project.yaml
16. Final report:
    "Pipeline complete!

    Deliverables ready:
    - output/review_by_rq.md
    - output/extraction_matrix.xlsx

    Archived to: runs/2024-01-15_143022_my_review/"
```

---

## Tips for Claude Code

1. **Always check exit codes** - non-zero means something went wrong
2. **Read the terminal output** - each script provides review guidance
3. **Trust but verify** - spot-check extractions before full run
4. **Be transparent** - show users coverage stats and any warnings
5. **Don't skip phases** - each builds on the previous one
6. **Handle missing PDFs gracefully** - display the folder link and guide the operator
