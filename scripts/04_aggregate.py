#!/usr/bin/env python3
"""
Phase 4: Aggregate extractions into final outputs.

Usage:
    python scripts/04_aggregate.py config/project.yaml

Outputs:
    - output/review_by_rq.md
    - output/extraction_matrix.xlsx

Exit codes:
    0 = Success
    1 = Error (no extractions found, etc.)
"""

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.aggregation import (
    load_extractions,
    generate_markdown_review,
    generate_excel_matrix,
    calculate_coverage_stats
)


def main():
    parser = argparse.ArgumentParser(description="Aggregate extractions into outputs")
    parser.add_argument("config_path", type=Path, help="Path to project.yaml")
    parser.add_argument("--extractions-dir", type=Path, default=Path("extractions"))
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()

    # Load config
    if not args.config_path.exists():
        print(f"ERROR: Config not found: {args.config_path}")
        return 1

    with open(args.config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Load extractions
    print(f"Loading extractions from {args.extractions_dir}/...")
    extractions = load_extractions(args.extractions_dir)

    if not extractions:
        print("ERROR: No extractions found.")
        print("Run 03_extract.py first.")
        return 1

    total = len(extractions)
    errors = sum(1 for e in extractions if "error" in e)
    print(f"Found {total} extractions ({total - errors} successful, {errors} with errors)")

    # Generate outputs
    args.output_dir.mkdir(parents=True, exist_ok=True)

    md_path = args.output_dir / "review_by_rq.md"
    xlsx_path = args.output_dir / "extraction_matrix.xlsx"

    print(f"\nGenerating {md_path}...")
    generate_markdown_review(
        extractions=extractions,
        research_questions=config["research_questions"],
        project=config["project"],
        output_path=md_path
    )

    print(f"Generating {xlsx_path}...")
    generate_excel_matrix(
        extractions=extractions,
        research_questions=config["research_questions"],
        output_path=xlsx_path
    )

    # Coverage stats
    stats = calculate_coverage_stats(extractions, config["research_questions"])

    print("\n" + "=" * 60)
    print("EVIDENCE COVERAGE BY RESEARCH QUESTION")
    print("=" * 60)

    successful = total - errors
    for rq in config["research_questions"]:
        rq_id = rq["id"]
        s = stats[rq_id]
        pct = s["percentage"]
        bar = "#" * int(pct / 4) + "-" * (25 - int(pct / 4))
        print(f"  {rq_id}: [{bar}] {s['with_evidence']}/{successful} ({pct:.0f}%)")

    print("\n" + "=" * 60)
    print("PHASE 4 COMPLETE")
    print("=" * 60)
    print(f"Outputs:")
    print(f"  - {md_path}")
    print(f"  - {xlsx_path}")
    print("\nREVIEW:")
    print("1. Check output/review_by_rq.md structure")
    print("2. Verify coverage percentages are reasonable")
    print("3. If approved, proceed to Phase 5: archive")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
