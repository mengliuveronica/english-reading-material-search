#!/usr/bin/env python3
"""Render one clean UTF-8 reading-text file per validated Material."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from material_pack_validation import load_pack, validate_pack


def material_filename(index: int, title: str) -> str:
    normalized = unicodedata.normalize("NFKC", title).replace("'", "").replace("’", "")
    slug = re.sub(r"[^\w\s-]", " ", normalized, flags=re.UNICODE)
    slug = re.sub(r"[-\s]+", "-", slug).strip("-_")[:80].rstrip("-_") or "reading"
    return f"{index:02d}_{slug}.txt"


def render_reading_text(material: dict[str, Any]) -> str:
    return "\n\n".join(block["text"] for block in material["original_text"]["blocks"]) + "\n"


def write_reading_texts(pack: dict[str, Any], output_dir: Path) -> list[Path]:
    errors = validate_pack(pack)
    if errors:
        raise ValueError("invalid Material Pack: " + "; ".join(errors))
    filenames = [material_filename(index, material["source_metadata"]["title"])
                 for index, material in enumerate(pack["materials"], start=1)]
    if output_dir.is_dir():
        unexpected = sorted(path.name for path in output_dir.glob("*.txt") if path.name not in filenames)
        if unexpected:
            raise ValueError("output directory contains unexpected TXT files: " + ", ".join(unexpected))
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for material, filename in zip(pack["materials"], filenames, strict=True):
        output = output_dir / filename
        temporary = output.with_name(f".{output.name}.tmp")
        try:
            temporary.write_text(render_reading_text(material), encoding="utf-8", newline="\n")
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
        outputs.append(output)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="validated internal material-pack.json")
    parser.add_argument("output_dir", type=Path, help="delivery directory for numbered TXT files")
    args = parser.parse_args()
    pack, errors = load_pack(args.input)
    if not errors:
        errors = validate_pack(pack)
    if errors:
        print("FAIL: reading TXT files were not rendered", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    try:
        outputs = write_reading_texts(pack, args.output_dir)
    except (OSError, UnicodeError, KeyError, ValueError) as exc:
        print(f"FAIL: cannot render reading TXT files: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: rendered {len(outputs)} clean reading TXT files to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
