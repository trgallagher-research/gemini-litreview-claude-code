"""
Aggregate extraction results into MD and Excel outputs.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime


def load_extractions(extractions_folder: Path) -> list:
    """Load all extraction JSONs from folder."""
    extractions = []
    for json_file in sorted(extractions_folder.glob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            extractions.append(json.load(f))
    return extractions


def generate_markdown_review(
    extractions: list,
    research_questions: list,
    project: dict,
    output_path: Path
) -> None:
    """Generate narrative review organised by RQ."""
    lines = []

    lines.append(f"# Literature Review: {project.get('name', 'Untitled')}")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Requester:** {project.get('requester', 'Unknown')}")
    lines.append(f"**Sources analysed:** {len(extractions)}")
    lines.append(f"**Research questions:** {len(research_questions)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for rq in research_questions:
        rq_id = rq["id"]
        rq_text = rq["text"].strip()

        lines.append(f"## {rq_id}: {_get_rq_short_title(rq_text)}")
        lines.append("")
        lines.append(f"> {rq_text}")
        lines.append("")

        sources_with_evidence = []
        sources_without_evidence = []

        for ext in extractions:
            if "error" in ext:
                continue
            rq_data = ext.get("extractions", {}).get(rq_id, {})
            if rq_data.get("has_evidence", False):
                sources_with_evidence.append((ext, rq_data))
            else:
                sources_without_evidence.append(ext)

        total = len([e for e in extractions if "error" not in e])
        with_ev = len(sources_with_evidence)
        pct = (with_ev / total * 100) if total > 0 else 0
        lines.append(f"**Evidence found in {with_ev}/{total} sources ({pct:.0f}%)**")
        lines.append("")

        if sources_with_evidence:
            lines.append("### Summary of Findings")
            lines.append("")

            for ext, rq_data in sources_with_evidence:
                source_num = ext.get("source_number", "?")
                citation = ext.get("citation", "Unknown")
                answer = rq_data.get("answer", "")
                effect_size = rq_data.get("effect_size")
                quotes = rq_data.get("supporting_quotes", [])

                lines.append(f"**{citation} [Source {source_num}]**")
                lines.append("")
                lines.append(answer)

                if effect_size:
                    lines.append(f"*Effect size: {effect_size}*")

                if quotes and len(quotes) > 0:
                    quote_text = quotes[0].get("quote", "")
                    if quote_text:
                        lines.append("")
                        if len(quote_text) > 300:
                            quote_text = quote_text[:297] + "..."
                        lines.append(f"> {quote_text}")
                        if quotes[0].get("location"):
                            lines.append(f"> - {quotes[0]['location']}")

                lines.append("")

        if sources_without_evidence:
            lines.append("### Sources Without Evidence for This RQ")
            lines.append("")
            for ext in sources_without_evidence:
                source_num = ext.get("source_number", "?")
                citation = ext.get("citation", "Unknown")
                lines.append(f"- Source {source_num}: {citation}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Error section
    error_extractions = [e for e in extractions if "error" in e]
    if error_extractions:
        lines.append("## Extraction Errors")
        lines.append("")
        for ext in error_extractions:
            source_num = ext.get("source_number", "?")
            filename = ext.get("filename", "Unknown")
            error = ext.get("error", "Unknown error")
            lines.append(f"- Source {source_num} ({filename}): {error}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # References
    lines.append("## References")
    lines.append("")
    for ext in sorted(extractions, key=lambda x: x.get("source_number", 0)):
        if "error" not in ext:
            source_num = ext.get("source_number", "?")
            citation = ext.get("citation", "Unknown")
            title = ext.get("title", "")
            lines.append(f"{source_num}. {citation}. {title}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_excel_matrix(
    extractions: list,
    research_questions: list,
    output_path: Path
) -> None:
    """Generate Excel matrix with one row per source."""
    rows = []

    for ext in extractions:
        if "error" in ext:
            row = {
                "Source #": ext.get("source_number"),
                "Filename": ext.get("filename"),
                "Status": "Error",
                "Error": ext.get("error")
            }
        else:
            sample = ext.get("sample", {}) or {}
            row = {
                "Source #": ext.get("source_number"),
                "Citation": ext.get("citation"),
                "Title": ext.get("title"),
                "Study Type": ext.get("study_type"),
                "Sample N": sample.get("n"),
                "Age Range": sample.get("age_range"),
                "Population": sample.get("population"),
                "Status": "Success"
            }

            for rq in research_questions:
                rq_id = rq["id"]
                rq_data = ext.get("extractions", {}).get(rq_id, {})

                row[f"{rq_id} Evidence"] = "Y" if rq_data.get("has_evidence") else "N"
                finding = rq_data.get("answer", "")
                if len(finding) > 500:
                    finding = finding[:497] + "..."
                row[f"{rq_id} Finding"] = finding
                row[f"{rq_id} Effect Size"] = rq_data.get("effect_size")
                row[f"{rq_id} Direction"] = rq_data.get("direction")

        rows.append(row)

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False, engine="openpyxl")


def calculate_coverage_stats(extractions: list, research_questions: list) -> dict:
    """Calculate evidence coverage statistics by RQ."""
    stats = {}
    total_sources = len([e for e in extractions if "error" not in e])

    for rq in research_questions:
        rq_id = rq["id"]
        with_evidence = sum(
            1 for ext in extractions
            if "error" not in ext
            and ext.get("extractions", {}).get(rq_id, {}).get("has_evidence", False)
        )
        stats[rq_id] = {
            "with_evidence": with_evidence,
            "total": total_sources,
            "percentage": (with_evidence / total_sources * 100) if total_sources > 0 else 0
        }

    return stats


def _get_rq_short_title(rq_text: str) -> str:
    """Extract short title from RQ text."""
    text = rq_text.strip()
    for delimiter in ["?", "impact", "affect", "influence", "relationship"]:
        if delimiter in text.lower():
            idx = text.lower().find(delimiter)
            if idx > 20:
                text = text[:idx]
                break

    text = text.strip().rstrip(",.:;")
    if len(text) > 60:
        text = text[:57] + "..."

    return text
