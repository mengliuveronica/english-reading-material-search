---
name: english-reading-material-search
description: 为高中英语教师检索并核验3–5篇公开可访问的英文阅读材料，生成可离线浏览的HTML、教师分析报告DOCX和逐篇纯文本TXT。适用于阅读理解、完形填空、概要写作、命题选材和已有材料审查，流程包括来源核验、教学适配判断与课标词汇覆盖分析。
---

# 高中英语阅读材料检索与交付

## 功能概述

这个 Skill 根据教师给出的年级、主题、题型和篇幅要求，检索3–5篇公开可完整访问的英文材料。每篇材料都要经过原始网页核验、完整正文提取、教学适配判断和课标词汇覆盖分析。

当前版本为1.6.0。它把教师阅读、后续文本分析和内部校验分开处理，最终交付HTML、DOCX和逐篇TXT。词汇服务暂时不可用时，教师也可以确认先生成基础材料包，稍后补充词汇覆盖分析。

## 交付内容

| 文件 | 用途 |
|---|---|
| `material-pack.html` | 离线浏览全部材料。页面按编号切换文章，并提供一键复制原文、词汇覆盖概览和可展开的教学分析。 |
| `material-analysis.docx` | 汇总来源信息、教学适配、词汇覆盖、入选理由、风险和教师决定，供教师阅读和存档。 |
| `reading-texts/` | 每篇文章一个UTF-8 TXT。文件只保存标题和完整英文正文，便于继续做命题或文本分析。 |

教师交付目录采用下面的结构：

```text
delivery/
├── material-pack.html
├── material-analysis.docx
└── reading-texts/
    ├── 01_Original-Title.txt
    ├── 02_Original-Title.txt
    └── 03_Original-Title.txt
```

处理过程中使用 `material-pack.json` 保存来源、原文和分析数据。把这个文件放在工作目录，用固定脚本校验并生成教师产物。

## 工作步骤

### 查找和筛选

开始检索前先检查词汇服务：

```bash
python3 scripts/check_vocabulary_service.py
```

这个检查只发送内置短文本。服务不可用时，说明备用地址配置方式，并请用户选择稍后重试、使用兼容服务或在检索完成后生成基础材料包。

1. 先确认年级、题型或用途、主题、篇幅、文体、难度、时效、文化背景和复用要求。信息不足时，最多补问两个会明显影响检索结果的问题；也可以采用保守假设并写入 `search_brief`。
2. 围绕主题设计3–5组查询。先了解有哪些来源，再用准确标题、独特短语、作者或发布机构追到原始网页。把实际查询和调整过程写入 `search_log`。
3. 打开每个候选URL，核对标题、作者、机构、日期、正文首尾、小标题、来源关系、访问状态和许可说明。只有正文能够公开完整打开的页面才进入下一步；其余候选写入 `discard_log`。
4. 按网页顺序提取标题、副标题、小标题、段落和正文列表。保留原始措辞、拼写、大小写和标点，只清理导航、广告、Cookie提示和推荐链接等网页界面元素。
5. 计算准确词数，并判断主题匹配、文体、语言负荷、背景负荷、适龄性和改编量。最终选择3–5篇内容不同、来源清楚、适合教学的材料。

### 生成交付物

6. 按 [output-contract.md](references/output-contract.md) 建立内部JSON。覆盖分析前使用schema 1.1完成基础校验：

```bash
python3 scripts/validate_material_pack_json.py path/to/work/material-pack.json
```

7. 调用VocabProfiler完成课标词汇覆盖分析：

```bash
python3 scripts/add_vocabulary_coverage.py path/to/work/material-pack.json \
  --output path/to/work/material-pack.covered.json
```

脚本默认调用 `https://vocabprofiler.netlify.app/api/analyze`，逐篇分析完整正文。所有材料通过API合同校验后，内部包升级为schema 1.2。默认地址不可用时，可以通过 `VOCAB_PROFILE_API_URL` 或 `--api-url` 指定兼容服务。

如果所有服务都不可用，先征得用户同意，再从原始schema 1.1工作文件生成基础包：

```bash
python3 scripts/prepare_basic_delivery.py path/to/work/material-pack.json \
  --output path/to/work/material-pack.basic.json
```

基础包保留来源核验、完整原文和教学分析，并把每篇词汇覆盖状态标为 `unavailable`。它不会替换原始工作文件，也不会生成估算数据。

8. 准备DOCX依赖。先运行 `node -e "require('docx')"`；如果本机还没有依赖，在 Skill 根目录执行：

```bash
npm ci --ignore-scripts
```

随后生成三类教师产物：

```bash
python3 scripts/validate_material_pack_json.py path/to/work/material-pack.covered.json
python3 scripts/render_material_pack.py path/to/work/material-pack.covered.json path/to/delivery/material-pack.html
node scripts/render_material_analysis.js path/to/work/material-pack.covered.json path/to/delivery/material-analysis.docx
python3 scripts/render_reading_texts.py path/to/work/material-pack.covered.json path/to/delivery/reading-texts
```

生成基础包时，把三条渲染命令中的 `material-pack.covered.json` 换成 `material-pack.basic.json`。HTML和DOCX会明确显示词汇覆盖尚未完成。

9. 打开HTML和DOCX，抽查复制按钮、原始链接、词汇覆盖、教学分析和打印效果。逐个比对TXT与 `original_text.blocks`，确认材料数量、标题和正文一致。内容需要调整时，修改内部JSON并重新运行渲染脚本。

## 交付前检查

- 最终有3–5篇不重复的材料，每篇都有经过核验的原始URL和完整正文。
- 完整包中每篇词汇覆盖状态都是 `analyzed`；用户确认的基础包中每篇状态统一为 `unavailable`。
- HTML可以离线打开；复制按钮会复制标题和全文；页面与打印预览都能显示全部材料。基础包会显示词汇覆盖尚未完成。
- DOCX包含来源、教学适配、词汇覆盖状态、风险和教师决定，英文全文留在HTML与TXT中。
- `reading-texts/` 中的TXT数量与材料数量一致，文件按两位序号排列，只含原文。
- 教师交付目录只放HTML、DOCX和TXT；内部JSON保留在工作目录。

严格筛选后少于3篇时，报告缺口和可放宽的条件，让教师决定下一轮检索方向。

## 来源和文本原则

- 使用无需登录或付费即可完整阅读的页面，并尊重网站的访问控制。
- 以原始网页可见信息记录作者、机构、日期、来源关系和许可；页面未注明的字段写 `not stated`。
- 按原网页顺序保存正文。转载版本可以帮助判断来源关系，但每组重复文本只选一个规范来源。
- 把“公开可读”和“允许印刷或再发布”分开记录，由教师或所在机构作最终使用决定。
- 词汇覆盖以兼容服务返回的真实结果为准。服务失败时保留现有工作文件，并由用户决定重试、切换服务或先生成基础包。

## 参考文件

| 什么时候读 | 文件 |
|---|---|
| 第一次安装或遇到运行问题时 | [FAQ.md](FAQ.md) |
| 想看一份完整教师请求时 | [teacher-request.md](examples/teacher-request.md) |
| 开始外部检索前 | [source-policy.md](references/source-policy.md) |
| 每次规划查询和筛选时 | [search-and-screening-method.md](references/search-and-screening-method.md) |
| 建立内部JSON和生成交付物前 | [output-contract.md](references/output-contract.md) |
| 遇到聚合站、付费来源、零结果、文化负荷、元数据冲突或多站转载时 | [eval-pressure-cases.md](references/eval-pressure-cases.md) |
