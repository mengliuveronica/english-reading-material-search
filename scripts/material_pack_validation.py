#!/usr/bin/env python3
"""Shared validation rules for deterministic Material Pack JSON."""

from __future__ import annotations

import re
from typing import Any

from material_pack_validation_helpers import (
    BLOCK_TYPES,
    DATE_RE,
    count_original_words,
    is_http_url,
    load_pack,
    list_value as _list,
    object_value as _object,
    text_value as _text,
    validate_date as _date,
    validate_load as _load,
    validate_risk_entries as _risk_entries,
)
from vocabulary_coverage_contract import validate_coverage

ID_RE = re.compile(r"^M[1-9]\d*$")


def _validate_metadata(material: dict[str, Any], path: str, errors: list[str]) -> tuple[str, str]:
    meta_path = f"{path}.source_metadata"
    metadata = _object(material, "source_metadata", path, errors)
    title = _text(metadata, "title", meta_path, errors)
    fields = ("author", "publishing_institution", "access_status", "source_relationship", "license_reuse_status")
    for field in fields:
        _text(metadata, field, meta_path, errors)
    source_url = _text(metadata, "original_url", meta_path, errors)
    if source_url and not is_http_url(source_url):
        errors.append(f"{meta_path}.original_url: only valid http/https URLs are allowed")
    publication = _object(metadata, "publication_date", meta_path, errors)
    date_path = f"{meta_path}.publication_date"
    status = _text(publication, "status", date_path, errors)
    _text(publication, "note", date_path, errors)
    if status and status not in {"verified", "not_stated", "uncertain"}:
        errors.append(f"{date_path}.status: invalid status")
    for key in ("published", "updated"):
        if key not in publication:
            errors.append(f"{date_path}.{key}: required field")
        value = publication.get(key)
        if value is not None and (not isinstance(value, str) or not DATE_RE.fullmatch(value)):
            errors.append(f"{date_path}.{key}: expected YYYY-MM-DD or null")
    published = publication.get("published")
    if status == "verified" and (not isinstance(published, str) or not DATE_RE.fullmatch(published)):
        errors.append(f"{date_path}.published: verified dates require YYYY-MM-DD")
    return title, source_url


def _validate_original(material: dict[str, Any], path: str, title: str, pack_type: str, errors: list[str]) -> int:
    original_path = f"{path}.original_text"
    original = _object(material, "original_text", path, errors)
    extraction_status = _text(original, "extraction_status", original_path, errors)
    expected = "synthetic_fixture" if pack_type == "synthetic_fixture" else "complete_main_body"
    if extraction_status and extraction_status != expected:
        errors.append(f"{original_path}.extraction_status: expected {expected}")
    _text(original, "extraction_note", original_path, errors)
    checked_date = _text(original, "checked_date", original_path, errors)
    _date(checked_date, f"{original_path}.checked_date", errors)
    blocks = _list(original, "blocks", original_path, errors)
    for index, block in enumerate(blocks):
        block_path = f"{original_path}.blocks[{index}]"
        if not isinstance(block, dict):
            errors.append(f"{block_path}: required object")
            continue
        block_type = _text(block, "type", block_path, errors)
        _text(block, "text", block_path, errors)
        if block_type and block_type not in BLOCK_TYPES:
            errors.append(f"{block_path}.type: unsupported block type")
    if not blocks or not isinstance(blocks[0], dict) or blocks[0].get("type") != "title":
        errors.append(f"{original_path}.blocks: first block must be title")
    elif blocks[0].get("text") != title:
        errors.append(f"{path}: first original-text block must exactly match source_metadata.title")
    count = count_original_words([block for block in blocks if isinstance(block, dict)])
    if count < 80:
        errors.append(f"{original_path}: at least 80 English words required; found {count}")
    return count


def _validate_fit_and_risks(material: dict[str, Any], path: str, count: int, errors: list[str]) -> None:
    _text(material, "selection_reason", path, errors)
    fit = _object(material, "teaching_fit", path, errors)
    for field in ("topic", "genre"):
        _text(fit, field, f"{path}.teaching_fit", errors)
    stated_count = fit.get("word_count")
    if isinstance(stated_count, bool) or not isinstance(stated_count, int):
        errors.append(f"{path}.teaching_fit.word_count: required integer")
    elif stated_count != count:
        errors.append(f"{path}.teaching_fit.word_count: stated {stated_count}, counted {count}")
    for field in ("language_load", "background_load", "adaptation_load"):
        _load(fit.get(field), f"{path}.teaching_fit.{field}", errors)
    _load(fit.get("age_appropriateness"), f"{path}.teaching_fit.age_appropriateness", errors, {"suitable", "conditional"})
    risk = _object(material, "risks_uncertainties", path, errors)
    _risk_entries(risk.get("risks"), f"{path}.risks_uncertainties.risks", errors)
    _risk_entries(risk.get("uncertainties"), f"{path}.risks_uncertainties.uncertainties", errors)
    _text(risk, "teacher_decision", f"{path}.risks_uncertainties", errors)


def _validate_material(
    material: Any, index: int, schema_version: str, pack_type: str, errors: list[str]
) -> tuple[str, str]:
    path = f"materials[{index}]"
    if not isinstance(material, dict):
        errors.append(f"{path}: required object")
        return "", ""
    material_id = _text(material, "id", path, errors)
    if material_id and not ID_RE.fullmatch(material_id):
        errors.append(f"{path}.id: expected M followed by a positive integer")
    title, source_url = _validate_metadata(material, path, errors)
    count = _validate_original(material, path, title, pack_type, errors)
    _validate_fit_and_risks(material, path, count, errors)
    coverage_path = f"{path}.curriculum_vocabulary_coverage"
    coverage = material.get("curriculum_vocabulary_coverage")
    if "curriculum_vocabulary_coverage" in material:
        errors.extend(validate_coverage(coverage, coverage_path))
    if schema_version == "1.2" and pack_type == "production":
        if "curriculum_vocabulary_coverage" not in material:
            errors.append(f"{coverage_path}: required for production schema 1.2")
        elif not isinstance(coverage, dict) or coverage.get("status") != "analyzed":
            errors.append(f"{coverage_path}.status: must be analyzed for production schema 1.2")
    return material_id, source_url


def _validate_logs(pack: dict[str, Any], errors: list[str]) -> None:
    logs = _list(pack, "search_log", "root", errors)
    if not logs:
        errors.append("root.search_log: at least one entry required")
    for index, entry in enumerate(logs):
        path = f"root.search_log[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{path}: required object")
            continue
        for field in ("id", "accessed_at", "query", "discovery_surface", "adjustment_decision"):
            _text(entry, field, path, errors)
        for url_index, url in enumerate(_list(entry, "verified_urls", path, errors)):
            if not is_http_url(url):
                errors.append(f"{path}.verified_urls[{url_index}]: only valid http/https URLs are allowed")
    for index, entry in enumerate(_list(pack, "discard_log", "root", errors)):
        path = f"root.discard_log[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{path}: required object")
            continue
        for field in ("id", "title_or_source", "reason"):
            _text(entry, field, path, errors)
        if "url" not in entry:
            errors.append(f"{path}.url: required field")
        elif entry["url"] is not None and not is_http_url(entry["url"]):
            errors.append(f"{path}.url: expected null or valid http/https URL")


def _validate_top(pack: dict[str, Any], errors: list[str]) -> tuple[str, str]:
    version = _text(pack, "schema_version", "root", errors)
    if version and version not in {"1.0", "1.1", "1.2"}:
        errors.append("root.schema_version: expected 1.0, 1.1, or 1.2")
    pack_type = _text(pack, "pack_type", "root", errors)
    if pack_type and pack_type not in {"production", "synthetic_fixture"}:
        errors.append("root.pack_type: expected production or synthetic_fixture")
    for field in ("pack_title", "retrieval_topic", "target_grade", "intended_use"):
        _text(pack, field, "root", errors)
    generated = _text(pack, "generated_date", "root", errors)
    _date(generated, "root.generated_date", errors)
    if pack_type == "synthetic_fixture":
        _text(pack, "fixture_notice", "root", errors)
    brief = _object(pack, "search_brief", "root", errors)
    for field in ("length_target", "genre_preference", "freshness", "access_reuse_requirements", "assumptions"):
        _text(brief, field, "root.search_brief", errors)
    return version, pack_type


def validate_pack(pack: Any) -> list[str]:
    if not isinstance(pack, dict):
        return ["root: required JSON object"]
    errors: list[str] = []
    schema_version, pack_type = _validate_top(pack, errors)
    materials = _list(pack, "materials", "root", errors)
    if not 3 <= len(materials) <= 5:
        errors.append(f"root.materials: material count must be 3-5; found {len(materials)}")
    declared = pack.get("material_count")
    if isinstance(declared, bool) or not isinstance(declared, int) or declared != len(materials):
        errors.append(f"root.material_count: must equal materials length {len(materials)}")
    identities = [
        _validate_material(item, index, schema_version, pack_type, errors) for index, item in enumerate(materials)
    ]
    ids = [item[0] for item in identities if item[0]]
    urls = [item[1] for item in identities if item[1]]
    if len(ids) != len(set(ids)):
        errors.append("root.materials: material IDs must be unique")
    if len(urls) != len(set(urls)):
        errors.append("root.materials: original URLs must be unique")
    _validate_logs(pack, errors)
    return errors
