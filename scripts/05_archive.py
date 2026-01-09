#!/usr/bin/env python3
"""
Phase 5: Archive the completed run.

Usage:
    python scripts/05_archive.py config/project.yaml

Outputs:
    - runs/{timestamp}/ containing config, extractions, and outputs

Exit codes:
    0 = Success
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description="Archive completed run")
    parser.add_argument("config_path", type=Path, help="Path to project.yaml")
    parser.add_argument("--extractions-dir", type=Path, default=Path("extractions"))
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    args = parser.parse_args()

    # Load config
    if not args.config_path.exists():
        print(f"ERROR: Config not found: {args.config_path}")
        return 1

    with open(args.config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Create timestamped archive folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    project_slug = "".join(c if c.isalnum() else "_" for c in config["project"]["name"].lower())[:30]
    archive_name = f"{timestamp}_{project_slug}"
    archive_path = args.runs_dir / archive_name

    archive_path.mkdir(parents=True, exist_ok=True)

    print(f"Archiving to {archive_path}/...")

    # Copy files
    shutil.copy2(args.config_path, archive_path / "project.yaml")
    print(f"  - Copied project.yaml")

    if args.extractions_dir.exists() and list(args.extractions_dir.glob("*.json")):
        shutil.copytree(args.extractions_dir, archive_path / "extractions")
        print(f"  - Copied extractions/")

    if args.output_dir.exists() and list(args.output_dir.iterdir()):
        shutil.copytree(args.output_dir, archive_path / "output")
        print(f"  - Copied output/")

    # Summary file
    summary = {
        "project": config["project"]["name"],
        "requester": config["project"]["requester"],
        "archived_at": datetime.now().isoformat(),
        "sources_count": len(config["sources"]),
        "rq_count": len(config["research_questions"])
    }

    with open(archive_path / "run_summary.yaml", "w", encoding="utf-8") as f:
        yaml.dump(summary, f)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\nArchive: {archive_path}/")
    print(f"\nDeliverables for requester:")
    print(f"  - {args.output_dir}/review_by_rq.md")
    print(f"  - {args.output_dir}/extraction_matrix.xlsx")
    print("\nSummary:")
    print(f"  - Project: {config['project']['name']}")
    print(f"  - Sources: {len(config['sources'])}")
    print(f"  - Research Questions: {len(config['research_questions'])}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
