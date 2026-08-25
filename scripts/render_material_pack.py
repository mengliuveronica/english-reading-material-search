#!/usr/bin/env python3
"""Render validated Material Pack JSON as the fixed offline reading UI."""

from __future__ import annotations

import argparse
import sys
from html import escape
from pathlib import Path
from string import Template
from typing import Any

from material_pack_validation import load_pack, validate_pack
from render_reading_texts import render_reading_text

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = ROOT / "assets" / "material-pack-template.html"
LOAD_LABELS = {"low": "低", "medium": "中", "high": "高", "suitable": "适合", "conditional": "有条件"}
BASIS_LABELS = {"fact": "事实", "estimate": "估计"}
LEVEL_LABELS = (("基础", "foundation"), ("必修新增", "high_school_required"), ("选择性必修新增", "high_school_selective"), ("未直接收录", "not_directly_listed"))
VOCAB_PROFILER_URL = "https://vocabprofiler.netlify.app/"
def e(value: Any) -> str:
    return escape(str(value), quote=True)
def publication_label(publication: dict[str, Any], compact: bool = False) -> str:
    if publication["status"] == "verified":
        value = str(publication["published"])
        if publication.get("updated"):
            value += f"；更新 {publication['updated']}"
        return value
    if compact:
        return "日期未注明" if publication["status"] == "not_stated" else "日期存疑"
    prefix = "日期未注明" if publication["status"] == "not_stated" else "日期存疑"
    return f"{prefix}；{publication['note']}"
def render_header(pack: dict[str, Any]) -> str:
    facts = (("主题", pack["retrieval_topic"]), ("年级", pack["target_grade"]),
             ("数量", f'{pack["material_count"]} 篇'), ("日期", pack["generated_date"]))
    fact_html = "".join(f"<div><dt>{e(label)}</dt><dd>{e(value)}</dd></div>" for label, value in facts)
    notice = ""
    if pack["pack_type"] == "synthetic_fixture":
        notice = f'<div class="notice-wrap"><p class="fixture-notice" role="note">{e(pack["fixture_notice"])}</p></div>'
    return (
        '<header class="pack-head"><div class="pack-head__inner">'
        f'<p class="pack-title">{e(pack["pack_title"])}</p><dl class="pack-facts">{fact_html}</dl>'
        f'</div></header>{notice}'
    )
def render_navigation(materials: list[dict[str, Any]]) -> str:
    items = []
    for index, material in enumerate(materials):
        item_id = e(material["id"])
        active = index == 0
        current = ' aria-current="page"' if active else ""
        items.append(
            f'<li role="presentation"><button id="tab-{item_id}" type="button" role="tab" aria-controls="material-{item_id}" '
            f'aria-selected="{str(active).lower()}"{current} tabindex="{0 if active else -1}" '
            f'aria-label="第 {index + 1:02d} 篇：{e(material["source_metadata"]["title"])}">'
            f'{index + 1:02d}</button></li>'
        )
    return '<nav class="rail" aria-label="材料切换"><ol role="tablist" aria-orientation="vertical">' + "".join(items) + "</ol></nav>"
def render_blocks(blocks: list[dict[str, str]]) -> str:
    output: list[str] = []
    list_open = False
    for block in blocks:
        block_type, text = block["type"], e(block["text"])
        if block_type == "list_item":
            if not list_open:
                output.append("<ul>")
                list_open = True
            output.append(f"<li>{text}</li>")
            continue
        if list_open:
            output.append("</ul>")
            list_open = False
        if block_type in {"title", "heading"}:
            output.append(f"<h2>{text}</h2>")
        elif block_type == "subtitle":
            output.append(f'<p class="original-subtitle">{text}</p>')
        else:
            output.append(f"<p>{text}</p>")
    if list_open:
        output.append("</ul>")
    return "".join(output)
def coverage_message(coverage: dict[str, Any] | None) -> str:
    return {"unavailable": "本次未完成覆盖分析", "not_requested": "本次未请求覆盖分析"}.get(coverage["status"], "") if coverage else ""

def render_coverage_metrics(material: dict[str, Any]) -> str:
    coverage = material.get("curriculum_vocabulary_coverage")
    if not coverage or coverage["status"] != "analyzed":
        message = coverage_message(coverage)
        return f'<p class="coverage-status">{e(message)}</p>' if message else ""
    summary = coverage["summary"]
    values = [("课标总覆盖", summary["token_coverage_rate"], f'{summary["covered_tokens"]}/{summary["total_tokens"]}')]
    values.extend((label, summary["level_rates"][key], summary["level_counts"][key]) for label, key in LEVEL_LABELS)
    metrics = "".join(
        f'<div><dt>{e(label)}</dt><dd>{e(format(rate, ".1%"))}<span>{e(count)}</span></dd></div>'
        for label, rate, count in values
    )
    return f'<dl class="coverage-metrics" aria-label="课标词汇覆盖指标">{metrics}</dl>'

def info_dl(values: tuple[tuple[str, Any], ...]) -> str:
    return '<dl class="info-list">' + "".join(
        f'<dt>{e(label)}</dt><dd>{e(value)}</dd>' for label, value in values
    ) + "</dl>"

def render_risks(entries: list[dict[str, str]]) -> str:
    return '<ul class="plain-list">' + "".join(
        f'<li><span class="basis">{e(BASIS_LABELS[entry["basis"]])}</span>　{e(entry["text"])}</li>'
        for entry in entries
    ) + "</ul>"

def render_coverage_details(material: dict[str, Any]) -> str:
    coverage = material.get("curriculum_vocabulary_coverage")
    if not coverage:
        return ""
    if coverage["status"] != "analyzed":
        return f'<section class="info-section coverage-detail"><h2>课标词汇重点</h2><p>{e(coverage_message(coverage))}</p></section>'
    summary, focus = coverage["summary"], coverage["focus_vocabulary"]
    rows = [("词项覆盖", f'{summary["type_coverage_rate"]:.1%} · {summary["covered_types"]}/{summary["total_types"]}')]
    rows.extend((label, "、".join(e(word) for word in focus[key]) or "—") for label, key in
                (("必修关注词", "high_school_required"), ("选择性必修关注词", "high_school_selective"),
                 ("未直接收录词", "not_directly_listed")))
    stats = '<dl class="info-list">' + "".join(f'<dt>{e(label)}</dt><dd>{value}</dd>' for label, value in rows) + "</dl>"
    tool = (f'<p class="coverage-tool">分析工具：<a href="{e(VOCAB_PROFILER_URL)}" target="_blank" '
            f'rel="noopener noreferrer">VocabProfiler</a></p>')
    return f'<section class="info-section coverage-detail"><h2>课标词汇重点</h2>{stats}{tool}</section>'

def render_more(material: dict[str, Any]) -> str:
    metadata, original, fit = material["source_metadata"], material["original_text"], material["teaching_fit"]
    source = info_dl((("作者", metadata["author"]), ("发布机构", metadata["publishing_institution"]),
        ("原始网址", metadata["original_url"]), ("发布日期", publication_label(metadata["publication_date"])),
        ("访问状态", metadata["access_status"]), ("来源关系", metadata["source_relationship"]),
        ("复用许可", metadata["license_reuse_status"]), ("核验日期", original["checked_date"]),
        ("提取状态", original["extraction_status"]), ("提取说明", original["extraction_note"])))
    fit_rows = (("主题", fit["topic"]), ("文体", fit["genre"]),
        ("语言负荷", f'{LOAD_LABELS[fit["language_load"]["level"]]}；{fit["language_load"]["evidence"]}'),
        ("背景负荷", f'{LOAD_LABELS[fit["background_load"]["level"]]}；{fit["background_load"]["evidence"]}'),
        ("适龄性", f'{LOAD_LABELS[fit["age_appropriateness"]["level"]]}；{fit["age_appropriateness"]["evidence"]}'),
        ("改编负荷", f'{LOAD_LABELS[fit["adaptation_load"]["level"]]}；{fit["adaptation_load"]["evidence"]}'))
    risk = material["risks_uncertainties"]
    sections = [f'<section class="info-section"><h2>来源详情</h2>{source}</section>',
        f'<section class="info-section"><h2>教学适配</h2>{info_dl(fit_rows)}</section>',
        f'<section class="info-section"><h2>入选理由</h2><p>{e(material["selection_reason"])}</p></section>',
        f'<section class="info-section"><h2>风险</h2>{render_risks(risk["risks"])}</section>',
        f'<section class="info-section"><h2>不确定性</h2>{render_risks(risk["uncertainties"])}</section>',
        f'<section class="info-section"><h2>教师决定</h2><p class="teacher-decision">{e(risk["teacher_decision"])}</p></section>',
        render_coverage_details(material)]
    return '<details class="more"><summary>更多信息</summary><div class="more-content">' + "".join(sections) + "</div></details>"

def render_material(material: dict[str, Any], index: int) -> str:
    metadata, original, fit = material["source_metadata"], material["original_text"], material["teaching_fit"]
    item_id = e(material["id"])
    hidden = "" if index == 0 else " hidden"
    source_line = (f'{e(metadata["publishing_institution"])} · {e(metadata["author"])} · '
                   f'{e(publication_label(metadata["publication_date"], compact=True))} · {e(fit["word_count"])} 词')
    copy_text = e(render_reading_text(material).rstrip("\n"))
    copy_action = (f'<div class="article-actions"><button class="copy-reading" type="button" '
                   f'data-copy-target="copy-source-{item_id}">复制原文</button>'
                   f'<span class="copy-status" role="status" aria-live="polite"></span></div>'
                   f'<pre class="copy-source" id="copy-source-{item_id}" hidden>{copy_text}</pre>')
    return (
        f'<article class="material" id="material-{item_id}" role="tabpanel" aria-labelledby="tab-{item_id}"{hidden}>'
        f'<header class="article-head"><h1>{e(metadata["title"])}</h1><p class="source-line">{source_line}'
        f'<a href="{e(metadata["original_url"])}" target="_blank" rel="noopener noreferrer">打开原始网页</a></p>'
        f'{copy_action}</header>{render_coverage_metrics(material)}'
        f'<div class="original-content" lang="en">{render_blocks(original["blocks"][1:])}</div>{render_more(material)}</article>'
    )

def render_document(pack: dict[str, Any], template_path: Path = DEFAULT_TEMPLATE) -> str:
    errors = validate_pack(pack)
    if errors:
        raise ValueError("invalid Material Pack: " + "; ".join(errors))
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.substitute(PAGE_TITLE=e(pack["pack_title"]), HEADER=render_header(pack),
        NAVIGATION=render_navigation(pack["materials"]),
        MATERIALS="".join(render_material(item, index) for index, item in enumerate(pack["materials"])))

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="validated material-pack.json")
    parser.add_argument("output", type=Path, help="destination material-pack.html")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    args = parser.parse_args()
    pack, errors = load_pack(args.input)
    if not errors:
        errors = validate_pack(pack)
    if errors:
        print("FAIL: HTML was not rendered", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    try:
        args.output.write_text(render_document(pack, args.template), encoding="utf-8")
    except (OSError, UnicodeError, KeyError, ValueError) as exc:
        print(f"FAIL: cannot render HTML: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: rendered offline HTML to {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
