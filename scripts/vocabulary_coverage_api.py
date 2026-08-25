#!/usr/bin/env python3
"""Normalize the versioned Edge compact response into Material Pack coverage."""

from __future__ import annotations

import math
from typing import Any

from vocabulary_coverage_contract import (
    API_SCHEMA_VERSION,
    FOCUS_KEYS,
    LEVEL_KEYS,
    MAX_FOCUS_ITEMS,
    validate_coverage,
)


class CoverageContractError(ValueError):
    """Raised when an Edge response violates the pinned API contract."""


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CoverageContractError(f"{path} must be an object")
    return value


def _integer(parent: dict[str, Any], key: str, path: str) -> int:
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CoverageContractError(f"{path}.{key} must be a non-negative integer")
    return value


def _rate(parent: dict[str, Any], key: str, path: str) -> float:
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CoverageContractError(f"{path}.{key} must be a finite rate from 0 to 1")
    number = float(value)
    if not 0 <= number <= 1:
        raise CoverageContractError(f"{path}.{key} must be a finite rate from 0 to 1")
    return number


def _check_ratio(count: int, total: int, rate: float, path: str) -> None:
    expected = count / total if total else 0.0
    if not math.isclose(rate, expected, abs_tol=1e-4):
        raise CoverageContractError(f"{path} is inconsistent with count/denominator")


def _check_status_counts(
    value: Any, expected: dict[str, int], path: str, excluded: int | None = None
) -> None:
    counts = _object(value, path)
    for key, count in expected.items():
        actual = counts.get(key, 0)
        if isinstance(actual, bool) or not isinstance(actual, int) or actual != count:
            raise CoverageContractError(f"{path}.{key} is inconsistent with canonical summary")
    actual_excluded = counts.get("excluded", 0)
    if excluded is not None and (
        isinstance(actual_excluded, bool) or not isinstance(actual_excluded, int) or actual_excluded != excluded
    ):
        raise CoverageContractError(f"{path}.excluded is inconsistent with canonical summary")


def _canonical_summary(value: dict[str, Any]) -> dict[str, Any]:
    tokens = _object(value.get("tokens"), "response.summary.tokens")
    types = _object(value.get("types"), "response.summary.types")
    levels = _object(value.get("levels"), "response.summary.levels")
    total_tokens = _integer(tokens, "denominator", "response.summary.tokens")
    covered_tokens = _integer(tokens, "matched", "response.summary.tokens")
    token_rate = _rate(tokens, "coverage_rate", "response.summary.tokens")
    observed = _integer(tokens, "observed_lexical", "response.summary.tokens")
    excluded = _integer(tokens, "excluded", "response.summary.tokens")
    total_types = _integer(types, "denominator", "response.summary.types")
    covered_types = _integer(types, "matched", "response.summary.types")
    type_rate = _rate(types, "coverage_rate", "response.summary.types")
    if observed != total_tokens + excluded:
        raise CoverageContractError("response.summary.tokens observed_lexical must equal denominator + excluded")
    _check_ratio(covered_tokens, total_tokens, token_rate, "response.summary.tokens.coverage_rate")
    _check_ratio(covered_types, total_types, type_rate, "response.summary.types.coverage_rate")
    if set(levels) != set(LEVEL_KEYS[:3]):
        raise CoverageContractError(f"response.summary.levels must contain exactly {list(LEVEL_KEYS[:3])}")
    level_counts: dict[str, int] = {}
    level_rates: dict[str, float] = {}
    type_level_total = 0
    for key in LEVEL_KEYS[:3]:
        level = _object(levels[key], f"response.summary.levels.{key}")
        token_count = _integer(level, "token_count", f"response.summary.levels.{key}")
        token_level_rate = _rate(level, "token_rate", f"response.summary.levels.{key}")
        type_count = _integer(level, "type_count", f"response.summary.levels.{key}")
        type_level_rate = _rate(level, "type_rate", f"response.summary.levels.{key}")
        _check_ratio(token_count, total_tokens, token_level_rate, f"response.summary.levels.{key}.token_rate")
        _check_ratio(type_count, total_types, type_level_rate, f"response.summary.levels.{key}.type_rate")
        level_counts[key], level_rates[key] = token_count, token_level_rate
        type_level_total += type_count
    if sum(level_counts.values()) != covered_tokens or type_level_total != covered_types:
        raise CoverageContractError("response.summary.levels counts must sum to matched token/type counts")
    unlisted = total_tokens - covered_tokens
    if unlisted < 0:
        raise CoverageContractError("response.summary.tokens.matched cannot exceed denominator")
    level_counts["not_directly_listed"] = unlisted
    level_rates["not_directly_listed"] = unlisted / total_tokens if total_tokens else 0.0
    _check_status_counts(tokens.get("status_counts"), level_counts, "response.summary.tokens.status_counts", excluded)
    type_expected = {key: levels[key]["type_count"] for key in LEVEL_KEYS[:3]}
    type_expected["not_directly_listed"] = total_types - covered_types
    _check_status_counts(types.get("status_counts"), type_expected, "response.summary.types.status_counts")
    return {
        "total_tokens": total_tokens, "covered_tokens": covered_tokens, "token_coverage_rate": token_rate,
        "total_types": total_types, "covered_types": covered_types, "type_coverage_rate": type_rate,
        "level_counts": level_counts, "level_rates": level_rates,
    }


def _summary(value: Any) -> dict[str, Any]:
    """Require and normalize the canonical tokens/types/levels summary."""
    return _canonical_summary(_object(value, "response.summary"))


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CoverageContractError(f"{path} must be a non-empty string")
    return " ".join(value.split())


def _truncate(value: str) -> str:
    return value if len(value) <= 80 else value[:79] + "…"


def _focus_display(value: Any, category: str, path: str) -> str:
    item = _object(value, path)
    if category in FOCUS_KEYS[:2]:
        headword = _text(item.get("headword"), f"{path}.headword")
        forms = item.get("forms")
        if not isinstance(forms, list):
            raise CoverageContractError(f"{path}.forms must be an array")
        visible: list[str] = []
        for index, form in enumerate(forms):
            cleaned = _text(form, f"{path}.forms[{index}]")
            if cleaned.casefold() != headword.casefold() and cleaned.casefold() not in {x.casefold() for x in visible}:
                visible.append(cleaned)
        return _truncate(f"{headword}（{', '.join(visible)}）" if visible else headword)
    surface = _text(item.get("surface"), f"{path}.surface")
    count = item.get("count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise CoverageContractError(f"{path}.count must be a positive integer")
    return _truncate(f"{surface} ×{count}" if count > 1 else surface)


def _focus(value: Any) -> dict[str, list[str]]:
    source = _object(value, "response.focus_vocabulary")
    if set(source) != set(FOCUS_KEYS):
        raise CoverageContractError(f"response.focus_vocabulary must contain exactly {list(FOCUS_KEYS)}")
    result: dict[str, list[str]] = {}
    for key in FOCUS_KEYS:
        entries = source[key]
        if not isinstance(entries, list):
            raise CoverageContractError(f"response.focus_vocabulary.{key} must be an array")
        if len(entries) > MAX_FOCUS_ITEMS:
            raise CoverageContractError(
                f"response.focus_vocabulary.{key} must contain at most {MAX_FOCUS_ITEMS} items"
            )
        compact: list[str] = []
        for index, entry in enumerate(entries):
            display = _focus_display(entry, key, f"response.focus_vocabulary.{key}[{index}]")
            if display.casefold() not in {item.casefold() for item in compact}:
                compact.append(display)
            if len(compact) == MAX_FOCUS_ITEMS:
                break
        result[key] = compact
    return result


def coverage_from_api(payload: Any) -> dict[str, Any]:
    response = _object(payload, "response")
    if response.get("schema_version") != API_SCHEMA_VERSION:
        raise CoverageContractError(f"response.schema_version must be {API_SCHEMA_VERSION}")
    if response.get("mode") != "compact":
        raise CoverageContractError("response.mode must be compact")
    if not isinstance(response.get("tokens"), list):
        raise CoverageContractError("response.tokens must be an array")
    coverage = {
        "status": "analyzed", "engine_version": response.get("engine_version"),
        "index_hash": response.get("index_hash"), "analyzed_at": response.get("analyzed_at"),
        "summary": _summary(response.get("summary")),
        "focus_vocabulary": _focus(response.get("focus_vocabulary")),
    }
    errors = validate_coverage(coverage, "response")
    if errors:
        raise CoverageContractError("; ".join(errors))
    return coverage
