# Methodology: AI-Assisted Literature Review Extraction

This document describes the methodology for using the Gemini LitReview pipeline to support systematic literature reviews. It explains the extraction process, output interpretation, and how researchers can integrate these outputs into their review workflow.

## Overview

This pipeline uses Google's Gemini 3 large language model to extract structured evidence from academic PDFs against predefined research questions. The tool is designed to **assist** researchers—not replace critical analysis—by automating the initial evidence extraction phase of systematic reviews.

### Key Principle: Human-in-the-Loop

The pipeline operates on a human-in-the-loop model:
- AI extracts candidate evidence and quotes from source documents
- Researchers verify extractions against original PDFs
- Final synthesis and interpretation remain human responsibilities

This approach combines AI efficiency with human expertise and judgement.

---

## Extraction Process

### Phase 1: Source Preparation

**Input requirements:**
- Research questions (1-5 RQs with keywords)
- Source citations with corresponding PDF files
- Context description (population, constructs, theoretical frameworks)

**Process:**
1. Citations are parsed and matched to PDF filenames using author name and year
2. PDFs are renamed to a standardised numbered format (e.g., `01_Kong_2023.pdf`)
3. Project configuration is generated with all metadata

### Phase 2: Context Framing

**Purpose:** Translate the researcher's plain-language context into a structured framing that guides extraction without biasing results.

**Process:**
1. Raw context (description, population, constructs) is submitted to Gemini 3 Flash
2. The model generates a neutral framing statement
3. Researcher reviews and approves the framing before extraction proceeds

**Quality check:** The framing should capture research intent without suggesting expected findings.

### Phase 3: Evidence Extraction

**Model:** Gemini 3 Pro (multimodal, capable of processing PDF documents directly)

**For each source PDF, the model extracts:**

| Field | Description |
|-------|-------------|
| `study_type` | Design classification (e.g., longitudinal, meta-analysis, RCT) |
| `sample.n` | Sample size |
| `sample.age_range` | Participant age range |
| `sample.population` | Population description |
| `has_evidence` | Boolean indicating whether the source addresses the RQ |
| `answer` | Summary of findings relevant to the RQ |
| `supporting_quotes` | Direct quotations with page/section locations |
| `effect_size` | Reported effect sizes (Cohen's d, β, r, OR, etc.) |
| `direction` | Effect direction (positive, negative, mixed, null) |

**Extraction prompt structure:**
1. Framing context is provided to situate the review
2. Each research question is presented with keywords
3. The model is instructed to extract only information explicitly stated in the document
4. Direct quotations are required to support each finding

**Quality controls:**
- Spot-check extraction: First 3 sources are extracted and manually verified before proceeding
- Quote verification: Supporting quotes include page locations for researcher validation
- Conservative flagging: Sources without clear evidence are marked `has_evidence: false`

### Phase 4: Aggregation

**Outputs generated:**

1. **Narrative Review (`review_by_rq.md`):**
   - Organised by research question
   - Each source's findings summarised with effect sizes
   - Supporting quotes included
   - Coverage statistics (% of sources with evidence per RQ)

2. **Evidence Matrix (`extraction_matrix.xlsx`):**
   - One row per source
   - Columns for each RQ (evidence yes/no, summary, effect size)
   - Study characteristics (design, sample size, population)
   - Suitable for import into systematic review software

### Phase 5: Archival

All outputs, configurations, and extraction JSONs are archived with timestamps for reproducibility and audit trails.

---

## Using the Outputs

### For Systematic Reviews

#### Step 1: Verify Extractions

**Critical:** AI extractions must be verified against original sources.

1. Open `extraction_matrix.xlsx` alongside your PDFs
2. For each extraction, verify:
   - Quotes exist in the source at the stated location
   - Effect sizes are accurately reported
   - The `has_evidence` flag is appropriate
3. Correct any errors directly in the spreadsheet
4. Document verification in your review protocol

#### Step 2: Synthesise Findings

The `review_by_rq.md` provides a starting point for narrative synthesis:

1. **Group findings by theme** within each RQ
2. **Assess consistency** of effect directions across studies
3. **Note heterogeneity** in effect sizes and populations
4. **Identify gaps** using the "Sources Without Evidence" lists

#### Step 3: Quality Assessment

The pipeline does **not** perform quality/risk-of-bias assessment. Researchers must:

1. Apply appropriate quality assessment tools (e.g., GRADE, Newcastle-Ottawa, Cochrane RoB)
2. Weight findings by study quality in synthesis
3. Report quality assessment separately

#### Step 4: Integrate into Review Manuscript

**Methods section template:**

> Evidence extraction was supported by an AI-assisted pipeline using Google Gemini 3 Pro. For each included source (N=X), the model extracted study characteristics, findings relevant to each research question, supporting quotations with page locations, and reported effect sizes. All AI extractions were independently verified against original sources by [researcher names]. The AI-generated extractions served as a first pass; final interpretations and synthesis were conducted by the research team.

**Reporting checklist:**
- [ ] State the AI model used (Gemini 3 Pro)
- [ ] Describe verification process
- [ ] Clarify human responsibilities (synthesis, quality assessment, interpretation)
- [ ] Provide access to extraction data (supplementary materials or repository)

### For Scoping Reviews

The outputs are well-suited for scoping reviews where the goal is mapping available evidence:

1. Use `extraction_matrix.xlsx` to chart study characteristics
2. Use coverage statistics to identify evidence gaps
3. The narrative summaries support rapid evidence mapping

### For Meta-Analyses

If conducting meta-analysis:

1. Use extracted effect sizes as a starting point
2. **Always verify** effect sizes against original sources
3. Extract additional statistical information (SE, CI, N per group) manually
4. The pipeline extracts reported effect sizes but does not calculate or convert them

---

## Limitations and Considerations

### What the Pipeline Does Well

- Rapid initial extraction across many sources
- Consistent application of extraction criteria
- Identification of relevant passages with page locations
- Structured output suitable for further analysis

### What Requires Human Judgement

| Task | Why Human Judgement is Needed |
|------|------------------------------|
| Quality assessment | Requires methodological expertise |
| Evidence synthesis | Requires domain knowledge and critical analysis |
| Handling contradictions | Requires interpretation of study differences |
| Contextualisation | Requires understanding of broader literature |
| Final conclusions | Requires weighing evidence and acknowledging uncertainty |

### Known Limitations

1. **PDF quality dependency:** Extraction quality depends on PDF text extraction; scanned documents or complex layouts may reduce accuracy

2. **Quotation accuracy:** While quotes are generally accurate, page numbers may occasionally be approximate; always verify

3. **Effect size extraction:** The model extracts reported effect sizes but may miss unreported effects or those requiring calculation

4. **Language:** Currently optimised for English-language sources

5. **Recency:** The model's training data has a cutoff date; very recent methodological developments may not be reflected

---

## Transparency and Reproducibility

### What to Archive

For reproducibility, archive:

```
project_archive/
├── project.yaml           # Full configuration with RQs and context
├── extractions/           # Raw JSON extractions per source
│   ├── 01_Author_2023.json
│   └── ...
├── review_by_rq.md        # Generated narrative review
├── extraction_matrix.xlsx # Evidence matrix
└── verification_log.xlsx  # Your verification notes (researcher-created)
```

### Recommended Reporting

When publishing research using this pipeline:

1. **Cite the tool** with version/date
2. **Provide extraction data** as supplementary material
3. **Describe verification process** in methods
4. **Acknowledge AI assistance** transparently

### PRISMA Considerations

For PRISMA-compliant reviews:
- Report AI-assisted extraction in the "Data extraction" section
- Include verification procedures
- The pipeline does not affect study selection (that remains manual)

---

## Ethical Considerations

### Appropriate Use

This tool is appropriate for:
- Accelerating systematic review workflows
- Supporting researchers with large numbers of sources
- Ensuring consistent extraction across sources
- Educational purposes (learning systematic review methods)

### Inappropriate Use

This tool should **not** be used to:
- Fully automate reviews without human verification
- Replace critical reading of sources
- Generate reviews without researcher expertise in the domain
- Bypass quality assessment procedures

### Transparency

Researchers using this tool should:
- Disclose AI assistance in publications
- Provide access to raw extractions for verification
- Maintain ultimate responsibility for review conclusions

---

## Quick Reference: Output Files

| File | Contents | Primary Use |
|------|----------|-------------|
| `review_by_rq.md` | Narrative summaries organised by RQ with quotes | Starting point for synthesis writing |
| `extraction_matrix.xlsx` | Tabular data with one row per source | Data charting, evidence tables, export to other tools |
| `extractions/*.json` | Raw extraction data per source | Verification, custom analysis, audit trail |
| `project.yaml` | Project configuration | Reproducibility, documentation |

---

## Citation

If using this pipeline in published research, please cite:

> Gallagher, T. (2025). Gemini LitReview: AI-Assisted Literature Review Extraction Pipeline. https://github.com/trgallagher-research/gemini-litreview-claude-code

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-09 | Initial release with Gemini 3 Pro extraction |
