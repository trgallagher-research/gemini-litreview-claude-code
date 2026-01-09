# Gemini LitReview with Claude Code

AI-assisted literature review extraction using Google Gemini 3, designed to be orchestrated by Claude Code.

## Overview

This pipeline extracts evidence from academic PDFs against research questions using Gemini 3 Pro. Unlike traditional interactive scripts, this version is designed for **Claude Code orchestration** - each phase is a separate script that Claude Code runs, reviews the output, and decides whether to proceed.

## How It Works

```
Claude Code orchestrates 5 phases:

┌─────────────────────────────────────────────────────────────┐
│  Phase 1: 01_ingest.py                                      │
│  Parse Excel → Match PDFs → Generate config                 │
│  Claude Code reviews: config/project.yaml                   │
├─────────────────────────────────────────────────────────────┤
│  Phase 2: 02_translate_framing.py                           │
│  Plain context → Structured framing (Gemini 3 Flash)        │
│  Claude Code reviews: translated framing output             │
├─────────────────────────────────────────────────────────────┤
│  Phase 3a: 03_extract.py --sources 1-3                      │
│  Spot-check first 3 PDFs (Gemini 3 Pro)                     │
│  Claude Code reviews: extractions/*.json quality            │
├─────────────────────────────────────────────────────────────┤
│  Phase 3b: 03_extract.py --sources 4-N                      │
│  Extract remaining PDFs                                     │
├─────────────────────────────────────────────────────────────┤
│  Phase 4: 04_aggregate.py                                   │
│  Generate markdown review + Excel matrix                    │
│  Claude Code reviews: coverage stats, output quality        │
├─────────────────────────────────────────────────────────────┤
│  Phase 5: 05_archive.py                                     │
│  Archive run with timestamp                                 │
│  Pipeline complete!                                         │
└─────────────────────────────────────────────────────────────┘
```

## Setup

```bash
# Clone the repository
git clone https://github.com/trgallagher-research/gemini-litreview-claude-code.git
cd gemini-litreview-claude-code

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

Get your Gemini API key at: https://aistudio.google.com/apikey

## Usage with Claude Code

1. **Place your input files:**
   - `input/form_response.xlsx` - Microsoft Forms export with project details
   - `input/pdfs/` - Your source PDF files

2. **Ask Claude Code to run the pipeline:**
   ```
   Run the literature review extraction pipeline step by step.
   Review outputs at each phase and confirm before proceeding.
   ```

3. **Claude Code will:**
   - Run each phase script
   - Review outputs and show you summaries
   - Ask for confirmation before proceeding
   - Handle any errors or issues

See [ORCHESTRATION.md](ORCHESTRATION.md) for detailed Claude Code instructions.

## Manual Usage

You can also run each phase manually:

```bash
# Phase 1: Ingest Excel and PDFs
python scripts/01_ingest.py input/form_response.xlsx input/pdfs/

# Phase 2: Translate framing context
python scripts/02_translate_framing.py config/project.yaml

# Phase 3: Extract evidence (spot-check first)
python scripts/03_extract.py config/project.yaml --sources 1-3
# Review extractions/, then continue:
python scripts/03_extract.py config/project.yaml --sources 4-23

# Phase 4: Generate outputs
python scripts/04_aggregate.py config/project.yaml

# Phase 5: Archive
python scripts/05_archive.py config/project.yaml
```

## Project Structure

```
gemini-litreview-claude-code/
├── scripts/                    # Phase scripts (run by Claude Code)
│   ├── 01_ingest.py
│   ├── 02_translate_framing.py
│   ├── 03_extract.py
│   ├── 04_aggregate.py
│   └── 05_archive.py
├── src/                        # Core modules
│   ├── ingest.py
│   ├── framing.py
│   ├── extraction.py
│   └── aggregation.py
├── input/                      # Your input files go here
│   ├── form_response.xlsx
│   └── pdfs/
├── config/                     # Generated project config
├── pdfs/                       # Renamed PDFs
├── extractions/                # JSON extraction results
├── output/                     # Final deliverables
│   ├── review_by_rq.md
│   └── extraction_matrix.xlsx
└── runs/                       # Archived runs
```

## Outputs

| File | Description |
|------|-------------|
| `output/review_by_rq.md` | Narrative review organized by research question |
| `output/extraction_matrix.xlsx` | Spreadsheet with one row per source |
| `extractions/*.json` | Individual extraction results per PDF |
| `runs/{timestamp}/` | Archived run for reproducibility |

## Excel Input Format

The pipeline expects an Excel file with these columns:

| Column | Description |
|--------|-------------|
| `project_name` | Name of your literature review |
| `requester_name` | Your name |
| `rq_count` | Number of research questions (1-5) |
| `rq1_id`, `rq1_text`, `rq1_keywords` | Research question 1 |
| `rq2_id`, `rq2_text`, `rq2_keywords` | Research question 2 |
| `source_citations` | Newline-separated citations |
| `context_description` | What the review is about |
| `context_population` | Target population |
| `context_constructs` | Key constructs |

Run `python scripts/01_ingest.py --create-sample` to generate a template.

## Requirements

- Python 3.10+
- Gemini API key (free tier available)

## License

MIT
