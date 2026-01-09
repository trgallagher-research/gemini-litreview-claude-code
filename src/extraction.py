"""
Extract evidence from PDFs using Gemini 3 Pro.
"""

from google import genai
from google.genai import types
import json
import time
from pathlib import Path
from typing import Optional


class GeminiExtractor:
    """PDF evidence extractor using Gemini 3 Pro."""

    def __init__(self, api_key: str, model_name: str = "gemini-3-pro-preview"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def upload_pdf(self, pdf_path: Path):
        """Upload PDF to Gemini File API."""
        return self.client.files.upload(file=str(pdf_path))

    def delete_file(self, file) -> None:
        """Clean up uploaded file."""
        if file is None:
            return
        try:
            self.client.files.delete(name=file.name)
        except Exception:
            pass


def extract_single_pdf(
    extractor: GeminiExtractor,
    pdf_path: Path,
    source_number: int,
    research_questions: list,
    context: str,
    output_path: Path,
    retry_attempts: int = 3
) -> dict:
    """
    Extract evidence from a single PDF and save to JSON.

    Returns:
        Extraction result dict
    """
    # Upload PDF
    uploaded_file = None
    try:
        uploaded_file = extractor.upload_pdf(pdf_path)
    except Exception as e:
        result = {
            "source_number": source_number,
            "filename": pdf_path.name,
            "error": f"Failed to upload PDF: {str(e)}",
            "extractions": {}
        }
        _save_result(result, output_path)
        return result

    # Build prompt
    prompt = _build_extraction_prompt(
        source_number=source_number,
        filename=pdf_path.name,
        research_questions=research_questions,
        context=context
    )

    # Attempt extraction with retries
    last_error = None
    for attempt in range(retry_attempts):
        try:
            response = extractor.client.models.generate_content(
                model=extractor.model_name,
                contents=[
                    types.Part.from_uri(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )

            result = json.loads(response.text)
            extractor.delete_file(uploaded_file)
            _save_result(result, output_path)
            return result

        except json.JSONDecodeError as e:
            last_error = f"JSON parse error: {e}"
            if hasattr(response, 'text'):
                extracted = _extract_json_from_text(response.text)
                if extracted:
                    extractor.delete_file(uploaded_file)
                    _save_result(extracted, output_path)
                    return extracted
        except Exception as e:
            last_error = str(e)

        wait_time = (2 ** attempt) * 2
        if attempt < retry_attempts - 1:
            time.sleep(wait_time)

    extractor.delete_file(uploaded_file)

    result = {
        "source_number": source_number,
        "filename": pdf_path.name,
        "error": str(last_error),
        "extractions": {}
    }
    _save_result(result, output_path)
    return result


def _save_result(result: dict, output_path: Path) -> None:
    """Save extraction result to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def _extract_json_from_text(text: str) -> Optional[dict]:
    """Try to extract JSON from text that may be wrapped in markdown."""
    import re
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _build_extraction_prompt(
    source_number: int,
    filename: str,
    research_questions: list,
    context: str
) -> str:
    """Build the extraction prompt dynamically based on RQs."""
    rq_sections = []
    for rq in research_questions:
        keywords_str = ", ".join(rq.get("keywords", []))
        section = f"### {rq['id']}\n{rq['text'].strip()}"
        if keywords_str:
            section += f"\nRelevant keywords: {keywords_str}"
        rq_sections.append(section)

    rq_text = "\n\n".join(rq_sections)

    extraction_entries = []
    for rq in research_questions:
        extraction_entries.append(f'''    "{rq['id']}": {{
      "has_evidence": <true/false>,
      "answer": "<summary of findings OR 'No relevant evidence in this article'>",
      "supporting_quotes": [
        {{"quote": "<exact quote from article>", "location": "<page number or section>"}}
      ],
      "effect_size": "<as reported in article, or null>",
      "direction": "<positive/negative/mixed/null>"
    }}''')

    extractions_schema = ",\n".join(extraction_entries)

    return f"""You are a research assistant extracting evidence from academic articles for a systematic literature review.

## Context
{context}

## Your Task
Read this article carefully and answer each research question below based ONLY on evidence explicitly stated in the article.

Source Number: {source_number}
Filename: {filename}

## Research Questions

{rq_text}

## Required Output Format

Return a JSON object with exactly this structure:

{{
  "source_number": {source_number},
  "filename": "{filename}",
  "citation": "<Author (Year) format - use 'et al.' for 3+ authors>",
  "title": "<Full article title as it appears>",
  "study_type": "<meta-analysis / systematic review / RCT / quasi-experimental / longitudinal / cross-sectional / qualitative / theoretical / other>",
  "sample": {{
    "n": <number or null if not applicable>,
    "age_range": "<age range string or null>",
    "population": "<description of participants>",
    "notes": "<any relevant notes about the sample>"
  }},
  "extractions": {{
{extractions_schema}
  }}
}}

## Critical Instructions

1. **Evidence-based only**: Report ONLY findings explicitly stated in the article.
2. **Exact quotes required**: For each RQ with evidence, provide at least one exact quote with location.
3. **No evidence is valid**: If no evidence, set has_evidence to false.
4. **Effect sizes**: Report exactly as stated (e.g., "r = 0.35", "d = 0.42"). Set to null if not reported.
5. **Direction**: positive/negative/mixed/null based on findings.

Return ONLY valid JSON. No markdown formatting, no explanatory text."""
