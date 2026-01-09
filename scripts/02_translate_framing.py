#!/usr/bin/env python3
"""
Phase 2: Translate plain-language context into structured framing.

Usage:
    python scripts/02_translate_framing.py config/project.yaml
    python scripts/02_translate_framing.py config/project.yaml --skip

Outputs:
    - Updates config/project.yaml with context_translated field

Exit codes:
    0 = Success
    1 = API error
"""

import argparse
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.framing import translate_framing, create_fallback_framing


def main():
    parser = argparse.ArgumentParser(description="Translate framing context")
    parser.add_argument("config_path", type=Path, help="Path to project.yaml")
    parser.add_argument("--skip", action="store_true", help="Skip translation, use raw context")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key and not args.skip:
        print("ERROR: GEMINI_API_KEY not found in .env")
        print("Either set the API key or use --skip to use raw context")
        return 1

    # Load config
    if not args.config_path.exists():
        print(f"ERROR: Config not found: {args.config_path}")
        print("Run 01_ingest.py first")
        return 1

    with open(args.config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    context_raw = config["context_raw"]

    print("=" * 60)
    print("ORIGINAL CONTEXT:")
    print("=" * 60)
    print(f"Description: {context_raw.get('description', 'N/A')[:100]}...")
    print(f"Population:  {context_raw.get('population', 'N/A')}")
    print(f"Constructs:  {context_raw.get('constructs', 'N/A')[:80]}...")
    print(f"Focus:       {context_raw.get('focus', 'N/A')}")

    if args.skip:
        print("\nSkipping translation, using raw context...")
        context_translated = create_fallback_framing(context_raw)
    else:
        print("\nTranslating framing with Gemini 3 Flash...")
        try:
            context_translated = translate_framing(context_raw, api_key)
        except Exception as e:
            print(f"ERROR: Framing translation failed: {e}")
            return 1

    # Update config
    config["context_translated"] = context_translated

    with open(args.config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print("\n" + "=" * 60)
    print("TRANSLATED FRAMING:")
    print("=" * 60)
    print(context_translated)

    print("\n" + "=" * 60)
    print("PHASE 2 COMPLETE")
    print("=" * 60)
    print(f"Config updated: {args.config_path}")
    print("\nREVIEW:")
    print("- Does the framing capture the research intent?")
    print("- Is it neutral (not biasing toward specific findings)?")
    print(f"- If not OK, edit context_translated in {args.config_path}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
