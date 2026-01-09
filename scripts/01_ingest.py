#!/usr/bin/env python3
"""
Phase 1: Ingest Microsoft Forms Excel export and prepare project.

PREREQUISITES:
  - Download PDFs from the shared folder link to input/pdfs/
  - PDFs should contain author name and year in filename for matching

Usage:
    python scripts/01_ingest.py input/form_response.xlsx input/pdfs/

Outputs:
    - config/project.yaml
    - pdfs/*.pdf (renamed to numbered format)

Exit codes:
    0 = Success
    1 = Validation errors (missing files, parse errors)
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import (
    parse_form_response,
    match_pdfs_to_sources,
    rename_pdfs,
    generate_yaml_config,
    validate_setup,
    create_sample_excel
)


def main():
    parser = argparse.ArgumentParser(description="Ingest Forms export and PDFs")
    parser.add_argument("excel_path", type=Path, nargs="?", help="Path to Forms Excel export")
    parser.add_argument("pdf_folder", type=Path, nargs="?", help="Path to folder with downloaded PDFs")
    parser.add_argument("--config-out", type=Path, default=Path("config/project.yaml"))
    parser.add_argument("--pdfs-out", type=Path, default=Path("pdfs"))
    parser.add_argument("--create-sample", action="store_true", help="Create sample Excel and exit")
    args = parser.parse_args()

    # Handle sample creation
    if args.create_sample:
        sample_path = Path("input/sample_form_response.xlsx")
        create_sample_excel(sample_path)
        print(f"Sample Excel file created at: {sample_path}")
        return 0

    # Validate arguments
    if not args.excel_path or not args.pdf_folder:
        parser.print_help()
        print("\nError: excel_path and pdf_folder are required")
        return 1

    if not args.excel_path.exists():
        print(f"ERROR: Excel file not found: {args.excel_path}")
        return 1

    # Parse Excel
    print(f"Parsing {args.excel_path}...")
    parsed_data = parse_form_response(args.excel_path)

    # Display folder link for reference
    folder_link = parsed_data.get("pdf_folder_link", "")
    if folder_link:
        print(f"\n" + "-" * 60)
        print("PDF FOLDER LINK FROM FORM:")
        print("-" * 60)
        print(f"  {folder_link}")
        print("-" * 60)

    # Check PDFs exist in input folder
    if not args.pdf_folder.exists():
        args.pdf_folder.mkdir(parents=True, exist_ok=True)

    pdf_files = list(args.pdf_folder.glob("*.pdf"))
    expected_count = len(parsed_data["sources"])

    print(f"\nExpected sources from citations: {expected_count}")
    print(f"PDFs found in {args.pdf_folder}: {len(pdf_files)}")

    # Pre-flight check: No PDFs found
    if len(pdf_files) == 0:
        print("\n" + "=" * 60)
        print("ERROR: No PDFs found in input folder!")
        print("=" * 60)
        if folder_link:
            print(f"\nPlease download PDFs from the shared folder:")
            print(f"  {folder_link}")
        else:
            print(f"\nNo PDF folder link was provided in the form.")
            print(f"Please obtain the PDFs from the requester.")
        print(f"\nThen place them in: {args.pdf_folder.absolute()}/")
        print("\nEnsure each PDF filename contains author name and year.")
        print("Examples: 'Kong_2023_meta_analysis.pdf', 'Kong et al 2023.pdf'")
        print("=" * 60)
        return 1

    if len(pdf_files) < expected_count:
        print(f"\nWARNING: Found fewer PDFs ({len(pdf_files)}) than expected ({expected_count})")

    # Match PDFs to citations
    print(f"\nMatching PDFs to citations...")
    parsed_data["sources"], unmatched = match_pdfs_to_sources(
        parsed_data["sources"], args.pdf_folder
    )

    # Count matches
    matched = sum(1 for s in parsed_data["sources"].values() if s.get("original_filename"))

    # Show matching results
    print(f"\n" + "-" * 60)
    print("SOURCE MATCHING RESULTS:")
    print("-" * 60)
    for num, source in parsed_data["sources"].items():
        if source.get("original_filename"):
            print(f"  {num:2d}. {source['citation'][:50]}")
            print(f"      -> {source['original_filename']}")
        else:
            print(f"  {num:2d}. {source['citation'][:50]}")
            print(f"      -> [NOT FOUND] No matching PDF")
    print("-" * 60)
    print(f"Matched: {matched}/{expected_count}")

    if unmatched:
        print(f"\nPDFs in folder not matched to any citation:")
        for pdf in unmatched:
            print(f"  - {pdf}")

    # Validate
    errors = validate_setup(parsed_data["sources"], args.pdf_folder)

    if errors:
        print("\n" + "=" * 60)
        print("VALIDATION ERRORS:")
        print("=" * 60)
        for err in errors:
            print(f"  - {err}")

    if matched < expected_count:
        print("\n" + "=" * 60)
        print("ACTION REQUIRED:")
        print("=" * 60)
        print("Some citations could not be matched to PDFs.")
        print("Please ensure PDF filenames contain author name and year.")
        print("Examples: 'Kong_2023_meta_analysis.pdf' or 'Kong et al 2023.pdf'")
        print("=" * 60)

    # Rename PDFs
    print(f"\nRenaming matched PDFs to {args.pdfs_out}/...")
    args.pdfs_out.mkdir(parents=True, exist_ok=True)
    rename_pdfs(parsed_data["sources"], args.pdf_folder, args.pdfs_out)

    # Update sources with renamed filenames
    for num, source in parsed_data["sources"].items():
        if source.get("original_filename"):
            source["filename"] = source["renamed_filename"]

    # Generate config (without translated framing yet)
    parsed_data["context_translated"] = None
    generate_yaml_config(parsed_data, args.config_out)

    print(f"\n" + "=" * 60)
    print("PHASE 1 COMPLETE")
    print("=" * 60)
    print(f"Config saved: {args.config_out}")
    print(f"PDFs folder:  {args.pdfs_out}/")
    print(f"\nProject:      {parsed_data['project']['name']}")
    print(f"Requester:    {parsed_data['project']['requester']}")
    print(f"RQs:          {len(parsed_data['research_questions'])}")
    print(f"Sources:      {matched}/{expected_count} matched")

    # Summary for Claude Code
    print("\n" + "=" * 60)
    print("REVIEW CHECKLIST:")
    print("=" * 60)
    print(f"1. View {args.config_out} to verify RQs parsed correctly")
    print(f"2. Check {args.pdfs_out}/ has {matched} renamed files")
    if errors or matched < expected_count:
        print(f"3. RESOLVE matching issues before proceeding")
        print(f"   (Some sources have no matching PDF)")
    else:
        print("3. No errors - ready for Phase 2")
    print("=" * 60)

    return 1 if (errors or matched < expected_count) else 0


if __name__ == "__main__":
    sys.exit(main())
