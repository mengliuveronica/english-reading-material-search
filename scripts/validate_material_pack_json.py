#!/usr/bin/env python3
"""Validate machine-readable Material Pack JSON without network access."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from material_pack_validation import load_pack, validate_pack


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path, help="material-pack.json to validate")
    parser.add_argument("--json", action="store_true", help="emit validation result as JSON")
    args = parser.parse_args()
    pack, errors = load_pack(args.pack)
    if not errors:
        errors = validate_pack(pack)
    result = {"valid": not errors, "error_count": len(errors), "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print("PASS: JSON has 3-5 complete Material units and required logs")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
