#!/usr/bin/env python3
"""
Phase 1: Ingest Microsoft Forms Excel export and prepare project.

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
    parser.add_argument("pdf_folder", type=Path, nargs="?", help="Path to folder with PDFs")
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

    print(f"Parsing {args.excel_path}...")
    parsed_data = parse_form_response(args.excel_path)

    print(f"Matching PDFs in {args.pdf_folder}...")
    if not args.pdf_folder.exists():
        print(f"WARNING: PDF folder not found, creating: {args.pdf_folder}")
        args.pdf_folder.mkdir(parents=True, exist_ok=True)

    parsed_data["sources"], unmatched = match_pdfs_to_sources(
        parsed_data["sources"], args.pdf_folder
    )

    # Validate
    errors = validate_setup(parsed_data["sources"], args.pdf_folder)

    if errors:
        print("\n" + "=" * 60)
        print("VALIDATION ERRORS:")
        print("=" * 60)
        for err in errors:
            print(f"  - {err}")
        print(f"\nFound {len(errors)} errors.")

    if unmatched:
        print(f"\nUnmatched PDFs in folder: {', '.join(unmatched)}")

    # Rename PDFs
    print(f"\nRenaming PDFs to {args.pdfs_out}/...")
    args.pdfs_out.mkdir(parents=True, exist_ok=True)
    rename_pdfs(parsed_data["sources"], args.pdf_folder, args.pdfs_out)

    # Update sources with renamed filenames
    for num, source in parsed_data["sources"].items():
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
    print(f"RQs:          {len(parsed_data['research_questions'])}")
    print(f"Sources:      {len(parsed_data['sources'])}")

    # Summary for Claude Code
    print("\n" + "=" * 60)
    print("REVIEW CHECKLIST:")
    print("=" * 60)
    print(f"1. View {args.config_out} to verify RQs parsed correctly")
    print(f"2. Check {args.pdfs_out}/ has {len(parsed_data['sources'])} renamed files")
    if errors:
        print(f"3. FIX {len(errors)} ERRORS before proceeding")
    else:
        print("3. No errors - ready for Phase 2")
    print("=" * 60)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
