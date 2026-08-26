#!/usr/bin/env python3
"""Prepare an explicit schema 1.1 basic delivery after user authorization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from add_vocabulary_coverage import AdapterError, write_json_atomic
from material_pack_validation import load_pack, validate_pack
from vocabulary_coverage_contract import unavailable_coverage


def prepare_basic_pack(pack: dict[str, Any]) -> int:
    errors = validate_pack(pack)
    if errors:
        raise AdapterError("input validation failed:\n- " + "\n- ".join(errors))
    if pack.get("schema_version") != "1.1" or pack.get("pack_type") != "production":
        raise AdapterError("basic delivery requires a production schema 1.1 input")
    for material in pack["materials"]:
        coverage = material.get("curriculum_vocabulary_coverage")
        if isinstance(coverage, dict) and coverage.get("status") == "analyzed":
            raise AdapterError("refusing to replace an existing analyzed coverage result")
    for material in pack["materials"]:
        material["curriculum_vocabulary_coverage"] = unavailable_coverage()
    final_errors = validate_pack(pack)
    if final_errors:
        raise AdapterError("basic output validation failed:\n- " + "\n- ".join(final_errors))
    return len(pack["materials"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="validated production schema 1.1 JSON")
    parser.add_argument("--output", required=True, type=Path, help="new basic-delivery JSON")
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise AdapterError("basic delivery output must use a new file path")
        pack, read_errors = load_pack(args.input)
        if read_errors:
            raise AdapterError("input validation failed:\n- " + "\n- ".join(read_errors))
        material_count = prepare_basic_pack(pack)
        write_json_atomic(args.output, pack)
    except AdapterError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: wrote schema 1.1 basic delivery to {args.output} ({material_count} materials)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
