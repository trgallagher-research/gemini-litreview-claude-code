#!/usr/bin/env python3
"""
Phase 3: Extract evidence from PDFs using Gemini 3 Pro.

Usage:
    python scripts/03_extract.py config/project.yaml
    python scripts/03_extract.py config/project.yaml --sources 1-3
    python scripts/03_extract.py config/project.yaml --sources 4-23
    python scripts/03_extract.py config/project.yaml --source 5

Outputs:
    - extractions/{source_num}_{author_year}.json for each processed PDF

Exit codes:
    0 = All extractions successful
    1 = Some extractions failed
"""

import argparse
import os
import sys
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction import GeminiExtractor, extract_single_pdf


def parse_source_range(range_str: str, max_source: int) -> list:
    """Parse source range string like '1-3' or '4-23' into list of ints."""
    if "-" in range_str:
        start, end = range_str.split("-")
        return list(range(int(start), min(int(end), max_source) + 1))
    else:
        return [int(range_str)]


def main():
    parser = argparse.ArgumentParser(description="Extract evidence from PDFs")
    parser.add_argument("config_path", type=Path, help="Path to project.yaml")
    parser.add_argument("--sources", type=str, help="Source range (e.g., '1-3' or '4-23')")
    parser.add_argument("--source", type=int, help="Single source number")
    parser.add_argument("--force", action="store_true", help="Re-extract even if JSON exists")
    parser.add_argument("--extractions-dir", type=Path, default=Path("extractions"))
    parser.add_argument("--pdfs-dir", type=Path, default=Path("pdfs"))
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        return 1

    # Load config
    if not args.config_path.exists():
        print(f"ERROR: Config not found: {args.config_path}")
        return 1

    with open(args.config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config.get("context_translated"):
        print("ERROR: No translated framing in config.")
        print("Run 02_translate_framing.py first.")
        return 1

    sources = config["sources"]
    max_source = max(int(k) for k in sources.keys())

    # Determine which sources to process
    if args.source:
        source_nums = [args.source]
    elif args.sources:
        source_nums = parse_source_range(args.sources, max_source)
    else:
        source_nums = list(range(1, max_source + 1))

    print("=" * 60)
    print(f"EXTRACTING SOURCES {source_nums[0]}-{source_nums[-1]} ({len(source_nums)} total)")
    print("=" * 60)

    args.extractions_dir.mkdir(parents=True, exist_ok=True)

    # Initialize extractor
    extractor = GeminiExtractor(api_key)

    successes = 0
    failures = 0
    skipped = 0

    for source_num in source_nums:
        source = sources.get(str(source_num)) or sources.get(source_num)
        if not source:
            print(f"  [{source_num}] WARNING: Source not found in config, skipping")
            continue

        pdf_path = args.pdfs_dir / source["filename"]
        json_path = args.extractions_dir / f"{pdf_path.stem}.json"

        # Skip if exists and not forcing
        if json_path.exists() and not args.force:
            print(f"  [{source_num}/{max_source}] {source['filename']} (skipped - exists)")
            skipped += 1
            continue

        print(f"  [{source_num}/{max_source}] {source['filename']}...", end=" ", flush=True)

        result = extract_single_pdf(
            extractor=extractor,
            pdf_path=pdf_path,
            source_number=source_num,
            research_questions=config["research_questions"],
            context=config["context_translated"],
            output_path=json_path
        )

        if "error" in result:
            print(f"ERROR: {result['error'][:50]}")
            failures += 1
        else:
            # Quick summary
            evidence = []
            for rq in config["research_questions"]:
                rq_id = rq["id"]
                has_ev = result.get("extractions", {}).get(rq_id, {}).get("has_evidence", False)
                evidence.append(f"{rq_id}:{'Y' if has_ev else 'N'}")
            print(f"OK ({' '.join(evidence)})")
            successes += 1

        # Small delay between extractions
        time.sleep(1)

    # Summary
    print("\n" + "=" * 60)
    print("PHASE 3 RESULTS")
    print("=" * 60)
    print(f"Successful: {successes}")
    print(f"Failed:     {failures}")
    print(f"Skipped:    {skipped}")

    # Guidance for Claude Code
    is_spot_check = (source_nums == list(range(1, min(4, max_source + 1))))

    print("\n" + "=" * 60)
    if is_spot_check:
        print("SPOT-CHECK REVIEW:")
        print("=" * 60)
        print("1. View extractions/*.json files")
        print("2. Check supporting_quotes are actual quotes from papers")
        print("3. Verify has_evidence flags make sense")
        print(f"4. If OK, run: python scripts/03_extract.py {args.config_path} --sources 4-{max_source}")
    else:
        print("EXTRACTION REVIEW:")
        print("=" * 60)
        if failures > 0:
            print(f"WARNING: {failures} extractions failed")
            print("Check extractions/ for error details")
        else:
            print("All extractions successful")
        print("Ready for Phase 4: aggregation")
    print("=" * 60)

    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
