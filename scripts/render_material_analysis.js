#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const {
  AlignmentType, BorderStyle, Document, ExternalHyperlink, Footer, HeadingLevel,
  LevelFormat, PageNumber, Packer, Paragraph, ShadingType, Table, TableCell,
  TableRow, TextRun, VerticalAlign, WidthType,
} = require("docx");

const LOAD = { low: "低", medium: "中", high: "高", suitable: "适合", conditional: "有条件" };
const LEVELS = [["基础", "foundation"], ["必修新增", "high_school_required"], ["选择性必修新增", "high_school_selective"], ["未直接收录", "not_directly_listed"]];
const VOCAB_PROFILER_URL = "https://vocabprofiler.netlify.app/";
const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "D9D9D9" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };

function paragraph(text, options = {}) {
  return new Paragraph({ spacing: { after: 120 }, ...options, children: [new TextRun(String(text))] });
}

function heading(text, level, pageBreakBefore = false) {
  return new Paragraph({ heading: level, pageBreakBefore, children: [new TextRun(String(text))] });
}

function publicationLabel(value) {
  if (value.status === "verified") return value.updated ? `${value.published}；更新 ${value.updated}` : value.published;
  return `${value.status === "not_stated" ? "日期未注明" : "日期存疑"}；${value.note}`;
}

function valueParagraph(value, link = false) {
  if (!link) return paragraph(value, { spacing: { after: 0 } });
  return new Paragraph({ spacing: { after: 0 }, children: [new ExternalHyperlink({
    link: String(value), children: [new TextRun({ text: String(value), style: "Hyperlink" })],
  })] });
}

function infoTable(rows) {
  return new Table({
    columnWidths: [2160, 6840],
    margins: { top: 100, bottom: 100, left: 140, right: 140 },
    rows: rows.map(([label, value, link = false]) => new TableRow({ children: [
      new TableCell({ borders: BORDERS, width: { size: 2160, type: WidthType.DXA }, shading: { fill: "F3F1EC", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: String(label), bold: true })] })] }),
      new TableCell({ borders: BORDERS, width: { size: 6840, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
        children: [valueParagraph(value, link)] }),
    ] })),
  });
}

function bullet(text) {
  return new Paragraph({ numbering: { reference: "analysis-bullets", level: 0 }, spacing: { after: 90 }, children: [new TextRun(String(text))] });
}

function coverageChildren(coverage) {
  if (!coverage || coverage.status !== "analyzed") return [paragraph("课标词汇覆盖尚未完成；来源核验和教学分析可正常使用。")];
  const summary = coverage.summary;
  const focus = coverage.focus_vocabulary;
  const distribution = LEVELS.map(([label, key]) => `${label} ${(summary.level_rates[key] * 100).toFixed(1)}%`).join("｜");
  return [infoTable([
    ["课标总覆盖", `${(summary.token_coverage_rate * 100).toFixed(1)}% · ${summary.covered_tokens}/${summary.total_tokens}`],
    ["词项覆盖", `${(summary.type_coverage_rate * 100).toFixed(1)}% · ${summary.covered_types}/${summary.total_types}`],
    ["四层分布", distribution],
    ["必修关注词", focus.high_school_required.join("、") || "—"],
    ["选择性必修关注词", focus.high_school_selective.join("、") || "—"],
    ["未直接收录词", focus.not_directly_listed.join("、") || "—"],
    ["分析工具", VOCAB_PROFILER_URL, true],
  ])];
}

function materialChildren(material, index) {
  const source = material.source_metadata;
  const fit = material.teaching_fit;
  const risk = material.risks_uncertainties;
  return [
    heading(`材料 ${String(index + 1).padStart(2, "0")} · ${source.title}`, HeadingLevel.HEADING_1, index > 0),
    heading("来源信息", HeadingLevel.HEADING_2),
    infoTable([["作者", source.author], ["发布机构", source.publishing_institution], ["发布日期", publicationLabel(source.publication_date)],
      ["原始网址", source.original_url, true], ["访问状态", source.access_status], ["来源关系", source.source_relationship],
      ["复用许可", source.license_reuse_status], ["核验日期", material.original_text.checked_date], ["提取说明", material.original_text.extraction_note]]),
    heading("入选理由", HeadingLevel.HEADING_2), paragraph(material.selection_reason),
    heading("教学适配", HeadingLevel.HEADING_2),
    infoTable([["主题", fit.topic], ["文体", fit.genre], ["原文词数", fit.word_count],
      ["语言负荷", `${LOAD[fit.language_load.level]}；${fit.language_load.evidence}`],
      ["背景负荷", `${LOAD[fit.background_load.level]}；${fit.background_load.evidence}`],
      ["适龄性", `${LOAD[fit.age_appropriateness.level]}；${fit.age_appropriateness.evidence}`],
      ["改编负荷", `${LOAD[fit.adaptation_load.level]}；${fit.adaptation_load.evidence}`]]),
    heading("课标词汇覆盖", HeadingLevel.HEADING_2), ...coverageChildren(material.curriculum_vocabulary_coverage),
    heading("风险", HeadingLevel.HEADING_2), ...risk.risks.map((item) => bullet(`${item.basis === "fact" ? "事实" : "估计"}：${item.text}`)),
    heading("不确定性", HeadingLevel.HEADING_2), ...risk.uncertainties.map((item) => bullet(`${item.basis === "fact" ? "事实" : "估计"}：${item.text}`)),
    heading("教师决定", HeadingLevel.HEADING_2), paragraph(risk.teacher_decision),
  ];
}

function buildDocument(pack) {
  const children = [heading(pack.pack_title, HeadingLevel.TITLE), paragraph("English Reading Material Pack · 分析报告", { alignment: AlignmentType.CENTER }),
    infoTable([["检索主题", pack.retrieval_topic], ["目标年级", pack.target_grade], ["预期用途", pack.intended_use], ["材料数量", `${pack.material_count} 篇`], ["生成日期", pack.generated_date]]),
    ...(pack.fixture_notice ? [paragraph(pack.fixture_notice)] : []),
    ...pack.materials.flatMap(materialChildren),
    heading("检索记录", HeadingLevel.HEADING_1, true),
    ...pack.search_log.flatMap((item) => [heading(item.id, HeadingLevel.HEADING_2), infoTable([["访问时间", item.accessed_at], ["查询", item.query], ["发现渠道", item.discovery_surface], ["调整决定", item.adjustment_decision], ["已核验网址", item.verified_urls.join("；") || "无"]])]),
    heading("淘汰记录", HeadingLevel.HEADING_1),
    ...(pack.discard_log.length ? pack.discard_log.flatMap((item) => [heading(item.id, HeadingLevel.HEADING_2), infoTable([["标题或来源", item.title_or_source], ["网址", item.url || "无"], ["原因", item.reason]])]) : [paragraph("无。")]),
  ];
  return new Document({
    styles: { default: { document: { run: { font: "Arial", size: 22, color: "111111" }, paragraph: { spacing: { line: 320 } } } }, paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: "Arial", size: 44, bold: true }, paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 240, after: 180 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Arial", size: 32, bold: true }, paragraph: { spacing: { before: 300, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Arial", size: 25, bold: true, color: "C43B25" }, paragraph: { spacing: { before: 220, after: 100 }, outlineLevel: 1 } },
    ] },
    numbering: { config: [{ reference: "analysis-bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 260 } } } }] }] },
    sections: [{ properties: { page: { margin: { top: 1100, right: 1100, bottom: 1100, left: 1100 } } }, footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun("第 "), new TextRun({ children: [PageNumber.CURRENT] }), new TextRun(" 页") ] })] }) }, children }],
  });
}

async function main() {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) throw new Error("usage: render_material_analysis.js INPUT.json OUTPUT.docx");
  const validator = path.join(__dirname, "validate_material_pack_json.py");
  const result = spawnSync(process.env.PYTHON || "python3", [validator, input], { encoding: "utf8" });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout || "Material Pack validation failed");
  const pack = JSON.parse(fs.readFileSync(input, "utf8"));
  const target = path.resolve(output);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const temporary = path.join(path.dirname(target), `.${path.basename(target)}.tmp`);
  try {
    fs.writeFileSync(temporary, await Packer.toBuffer(buildDocument(pack)));
    fs.renameSync(temporary, target);
  } finally {
    if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
  }
  console.log(`PASS: rendered analysis DOCX to ${target}`);
}

main().catch((error) => { console.error(`FAIL: ${error.message}`); process.exitCode = 1; });
