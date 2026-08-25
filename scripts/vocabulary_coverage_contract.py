#!/usr/bin/env python3
"""Contract validation for compact curriculum-vocabulary coverage data."""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any

API_SCHEMA_VERSION = "1.0"
PACK_SCHEMA_VERSION = "1.2"
LEVEL_KEYS = ("foundation", "high_school_required", "high_school_selective", "not_directly_listed")
FOCUS_KEYS = ("high_school_required", "high_school_selective", "not_directly_listed")
COVERAGE_KEYS = {
    "status", "engine_version", "index_hash", "analyzed_at", "summary", "focus_vocabulary"
}
SUMMARY_KEYS = {
    "total_tokens", "covered_tokens", "token_coverage_rate", "total_types",
    "covered_types", "type_coverage_rate", "level_counts", "level_rates",
}
RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
INDEX_HASH_RE = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$")
ENGINE_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+:-]{0,127}$")
MAX_FOCUS_ITEMS = 100


def unavailable_coverage(status: str = "unavailable") -> dict[str, Any]:
    if status not in {"unavailable", "not_requested"}:
        raise ValueError("status must be unavailable or not_requested")
    return {
        "status": status,
        "engine_version": None,
        "index_hash": None,
        "analyzed_at": None,
        "summary": None,
        "focus_vocabulary": None,
    }


def _exact_keys(value: dict[str, Any], expected: set[str], path: str, errors: list[str]) -> None:
    missing = sorted(expected - value.keys())
    extra = sorted(value.keys() - expected)
    if missing:
        errors.append(f"{path}: missing fields {missing}")
    if extra:
        errors.append(f"{path}: unsupported fields {extra}")


def _count(value: Any, path: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        errors.append(f"{path}: expected non-negative integer")
        return None
    return value


def _rate(value: Any, path: str, errors: list[str]) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        errors.append(f"{path}: expected finite number from 0 to 1")
        return None
    number = float(value)
    if not 0 <= number <= 1:
        errors.append(f"{path}: expected finite number from 0 to 1")
        return None
    return number


def _ratio_matches(count: int | None, total: int | None, rate: float | None) -> bool:
    if count is None or total is None or rate is None:
        return True
    expected = count / total if total else 0.0
    return math.isclose(rate, expected, abs_tol=1e-4)


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not RFC3339_RE.fullmatch(value):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def _validate_summary(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: required object")
        return
    _exact_keys(value, SUMMARY_KEYS, path, errors)
    total_tokens = _count(value.get("total_tokens"), f"{path}.total_tokens", errors)
    covered_tokens = _count(value.get("covered_tokens"), f"{path}.covered_tokens", errors)
    total_types = _count(value.get("total_types"), f"{path}.total_types", errors)
    covered_types = _count(value.get("covered_types"), f"{path}.covered_types", errors)
    token_rate = _rate(value.get("token_coverage_rate"), f"{path}.token_coverage_rate", errors)
    type_rate = _rate(value.get("type_coverage_rate"), f"{path}.type_coverage_rate", errors)
    if total_tokens == 0:
        errors.append(f"{path}.total_tokens: must be positive for complete English text")
    if total_types == 0:
        errors.append(f"{path}.total_types: must be positive for complete English text")
    if covered_tokens is not None and total_tokens is not None and covered_tokens > total_tokens:
        errors.append(f"{path}.covered_tokens: cannot exceed total_tokens")
    if covered_types is not None and total_types is not None and covered_types > total_types:
        errors.append(f"{path}.covered_types: cannot exceed total_types")
    if total_types is not None and total_tokens is not None and total_types > total_tokens:
        errors.append(f"{path}.total_types: cannot exceed total_tokens")
    if not _ratio_matches(covered_tokens, total_tokens, token_rate):
        errors.append(f"{path}.token_coverage_rate: inconsistent with covered_tokens/total_tokens")
    if not _ratio_matches(covered_types, total_types, type_rate):
        errors.append(f"{path}.type_coverage_rate: inconsistent with covered_types/total_types")
    _validate_levels(value, path, total_tokens, covered_tokens, errors)


def _validate_levels(
    summary: dict[str, Any], path: str, total: int | None, covered: int | None, errors: list[str]
) -> None:
    counts, rates = summary.get("level_counts"), summary.get("level_rates")
    if not isinstance(counts, dict) or set(counts) != set(LEVEL_KEYS):
        errors.append(f"{path}.level_counts: expected exactly {list(LEVEL_KEYS)}")
        counts = {}
    if not isinstance(rates, dict) or set(rates) != set(LEVEL_KEYS):
        errors.append(f"{path}.level_rates: expected exactly {list(LEVEL_KEYS)}")
        rates = {}
    checked_counts = {key: _count(counts.get(key), f"{path}.level_counts.{key}", errors) for key in LEVEL_KEYS}
    checked_rates = {key: _rate(rates.get(key), f"{path}.level_rates.{key}", errors) for key in LEVEL_KEYS}
    if total is not None and all(value is not None for value in checked_counts.values()):
        if sum(checked_counts.values()) != total:
            errors.append(f"{path}.level_counts: counts must sum to total_tokens")
        listed = sum(checked_counts[key] for key in LEVEL_KEYS[:3])
        if covered is not None and listed != covered:
            errors.append(f"{path}.level_counts: first three curriculum levels must sum to covered_tokens")
    for key in LEVEL_KEYS:
        if not _ratio_matches(checked_counts[key], total, checked_rates[key]):
            errors.append(f"{path}.level_rates.{key}: inconsistent with count/total_tokens")


def _validate_focus(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, dict) or set(value) != set(FOCUS_KEYS):
        errors.append(f"{path}: expected exactly {list(FOCUS_KEYS)} arrays")
        return
    for key in FOCUS_KEYS:
        entries = value[key]
        item_path = f"{path}.{key}"
        if not isinstance(entries, list) or len(entries) > MAX_FOCUS_ITEMS:
            errors.append(f"{item_path}: expected compact array of at most {MAX_FOCUS_ITEMS} strings")
            continue
        seen: set[str] = set()
        for index, entry in enumerate(entries):
            if not isinstance(entry, str) or not entry.strip() or len(entry) > 80:
                errors.append(f"{item_path}[{index}]: expected non-empty string of at most 80 characters")
            elif entry.casefold() in seen:
                errors.append(f"{item_path}[{index}]: duplicate focus item")
            else:
                seen.add(entry.casefold())


def validate_coverage(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{path}: required object"]
    _exact_keys(value, COVERAGE_KEYS, path, errors)
    status = value.get("status")
    if status not in {"analyzed", "unavailable", "not_requested"}:
        errors.append(f"{path}.status: expected analyzed, unavailable, or not_requested")
        return errors
    if status != "analyzed":
        for key in ("engine_version", "index_hash", "analyzed_at", "summary", "focus_vocabulary"):
            if value.get(key) is not None:
                errors.append(f"{path}.{key}: must be null when status is {status}")
        return errors
    engine, index_hash, analyzed_at = value.get("engine_version"), value.get("index_hash"), value.get("analyzed_at")
    if not isinstance(engine, str) or not ENGINE_VERSION_RE.fullmatch(engine):
        errors.append(f"{path}.engine_version: expected a compact version/build identifier")
    if not isinstance(index_hash, str) or not INDEX_HASH_RE.fullmatch(index_hash):
        errors.append(f"{path}.index_hash: expected a SHA-256 hash")
    if not _valid_timestamp(analyzed_at):
        errors.append(f"{path}.analyzed_at: expected valid RFC 3339 timestamp with timezone")
    _validate_summary(value.get("summary"), f"{path}.summary", errors)
    _validate_focus(value.get("focus_vocabulary"), f"{path}.focus_vocabulary", errors)
    return errors
