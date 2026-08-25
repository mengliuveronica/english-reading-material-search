#!/usr/bin/env python3
"""Small shared helpers for Material Pack validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

WORD_RE = re.compile(r"\b[A-Za-z]+(?:[’'-][A-Za-z]+)*\b")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BLOCK_TYPES = {"title", "subtitle", "heading", "paragraph", "list_item"}
LOAD_LEVELS = {"low", "medium", "high"}


def is_http_url(value: str) -> bool:
    if not isinstance(value, str) or value != value.strip() or re.search(r"[\s\x00-\x1f]", value):
        return False
    try:
        parsed = urlparse(value)
        _ = parsed.port
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and parsed.username is None


def count_original_words(blocks: list[dict[str, Any]]) -> int:
    text = "\n\n".join(str(block.get("text", "")) for block in blocks)
    return len(WORD_RE.findall(text))


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON field: {key}")
        value[key] = item
    return value


def load_pack(path: Path) -> tuple[Any, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text, object_pairs_hook=_unique_object), []
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return None, [f"cannot read JSON: {exc}"]


def object_value(parent: dict[str, Any], key: str, path: str, errors: list[str]) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f"{path}.{key}: required object")
        return {}
    return value


def list_value(parent: dict[str, Any], key: str, path: str, errors: list[str]) -> list[Any]:
    value = parent.get(key)
    if not isinstance(value, list):
        errors.append(f"{path}.{key}: required array")
        return []
    return value


def text_value(parent: dict[str, Any], key: str, path: str, errors: list[str]) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}.{key}: required non-empty string")
        return ""
    return value


def validate_date(value: str, path: str, errors: list[str]) -> None:
    if value and not DATE_RE.fullmatch(value):
        errors.append(f"{path}: expected YYYY-MM-DD")


def validate_load(value: Any, path: str, errors: list[str], levels: set[str] = LOAD_LEVELS) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: required object")
        return
    level = text_value(value, "level", path, errors)
    text_value(value, "evidence", path, errors)
    if level and level not in levels:
        errors.append(f"{path}.level: expected one of {sorted(levels)}")


def validate_risk_entries(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path}: required non-empty array")
        return
    for index, entry in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{item_path}: required object")
            continue
        basis = text_value(entry, "basis", item_path, errors)
        text_value(entry, "text", item_path, errors)
        if basis and basis not in {"fact", "estimate"}:
            errors.append(f"{item_path}.basis: expected fact or estimate")
