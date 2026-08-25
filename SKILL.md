---
name: english-reading-material-search
description: 为高中英语教师开放检索、逐URL核验并交付可离线审阅的 English Reading Material Pack。教师交付包含带逐篇一键复制原文的自包含HTML、集中呈现来源与教学分析的DOCX，以及每篇一个、只含完整未改写英文原文的规范命名UTF-8 TXT；已校验JSON仅作内部数据源，不进入交付目录。每个最终材料必须含公开原始页的完整原文、HTTP(S)原始URL、来源metadata、入选理由、词数与教学适配分析、风险和教师决定，并在正文硬筛和基础校验后调用默认自有线上API取得真实且经过合同验证的课标词汇覆盖；任一篇分析失败即阻断生产交付。适用于阅读理解、完形、概要写作、命题选材、来源比较和已有选材审查。
metadata:
  version: "1.4.1"
---

# 高中英语阅读材料检索与交付

Material Pack内部数据合同版本：**1.2**。生成教师交付物前，内部包必须使用1.2且每篇覆盖状态均为 `analyzed`；校验器继续读取/校验旧1.0/1.1包，但它们不能用于当前生产交付。

## 目标与主产物

正常交付3–5个非重复 `Material` 的 **English Reading Material Pack**。教师可见交付目录固定包含：

1. **展示页：`material-pack.html`**——自包含、可离线打开；按编号切换材料，每篇顶部可一键复制完整原文，分析信息按需展开，打印时显示全部材料及详情。
2. **分析报告：`material-analysis.docx`**——集中呈现来源、教学适配、课标词汇覆盖、入选理由、风险、不确定性和教师决定；不重复收录英文原文正文。
3. **纯文本目录：`reading-texts/`**——每篇一个UTF-8 TXT，命名为 `01_<清理后的原始标题>.txt`、`02_...txt`；文件只含完整 `original_text.blocks[].text`，供后续分析。

内部 `material-pack.json` 仍是唯一内容数据源，必须先写、先校验，再由固定渲染器生成上述产物；它是工作文件，不得放入教师交付目录。每个最终单元的核心仍是从原始公开网页完整提取的未改写英文正文。候选卡、摘要、reasoning、链接清单或漂亮界面都不能替代原文。

## 先读规则

- 外部检索前读取 [source-policy.md](references/source-policy.md)，落实完整访问、正文边界、来源关系和访问控制边界。
- 每次任务读取 [search-and-screening-method.md](references/search-and-screening-method.md)，按需求设计查询、逐URL核验并做完整性筛选。
- 写内部JSON及生成教师产物前读取 [output-contract.md](references/output-contract.md)，严格遵守字段、枚举、原文 block、TXT纯净边界、DOCX内容边界和交付顺序。
- 遇到聚合站、全文请求、零结果、文化负荷、元数据冲突或多站转载时，读取 [eval-pressure-cases.md](references/eval-pressure-cases.md) 的对应案例。

## 正常工作流

### 1. 建立 search brief

提取目标年级、题型/用途、主题、目标原文或改编后词数、文体、语言难度、时效、地域/文化偏好、敏感内容与再使用要求。信息不足时最多问两个高价值问题；不宜中断时采用保守假设并写入 `search_brief`。默认最终来源必须无需登录或付费即可完整打开并确认正文边界。

### 2. 规划并迭代检索

围绕核心概念、自然英语近义词、目标人群、文体、证据角度和时间设计3–5个查询族。先发现来源生态，再用准确标题、独特短语、署名或被引机构追到原始发布页。通常做2–3轮质量驱动调整；不要锁死网站清单。将实际查询、发现面、调整及打开过的URL写入 `search_log`。

### 3. 逐URL核验完整性与来源

搜索摘要只用于发现。对候选URL实际 `webfetch` 或用普通浏览器打开，核验标题、作者、机构、日期、规范URL、来源关系、许可、首段、末段、小标题、正文边界和访问控制。正文无法完整打开、登录/付费墙截断、动态失败后仍无法确认、只有摘要/节选，或需跨页补齐的项目必须进入 `discard_log`。

### 4. 提取完整 main body

只对通过硬筛的页面提取一次完整正文。按网页顺序将原始标题、副标题、小标题、段落和必要列表写入 `original_text.blocks`，分别使用 `title`、`subtitle`、`heading`、`paragraph`、`list_item`。不翻译、不改写、不纠错、不重排；只移除导航、广告、cookie提示、分享控件、推荐链接等网页 chrome。第一块必须是 `title`，并与 `source_metadata.title` 完全一致。不得把网页UI说明、入选理由、注释或模型文字混进原文 blocks。

### 5. 筛选与教学评估

记录提取文本的精确英文词数（标题、小标题和正文均计入），并相对 brief 判断主题、genre、语言负荷、背景负荷、适龄性和改编负荷。每个判断提供可检查依据。记录风险、不确定性和教师决定；高改编负荷、贯穿性背景障碍、来源不可追溯、实质重复或明显不适龄的材料通常淘汰。

### 6. 写内部 `material-pack.json`

严格按 [output-contract.md](references/output-contract.md) 构造内部JSON，正常含3–5篇。`source_metadata` 与 `original_text` 保存网页核验事实，教学负荷及入选理由保存评估，风险项用 `basis: fact|estimate` 明示性质，最终取舍写入 `teacher_decision`。生产包使用 `pack_type: production` 和 `extraction_status: complete_main_body`；不得把 fixture 标记用于真实交付。覆盖前初稿暂用兼容的 `schema_version: "1.1"` 通过基础结构校验，它只是不可交付的中间文件；adapter全部成功后原子写出可用于渲染的1.2内部包。把JSON放在工作区而非教师交付目录。

### 7. 基础校验后必须调用课标词汇覆盖API

先运行基础校验：

```bash
python3 scripts/validate_material_pack_json.py path/to/material-pack.json
```

只有完整正文已通过来源硬筛、全部 `original_text.blocks` 已按序写入1.1中间JSON且基础校验通过，才调用自有版本化API；这是WorkBuddy生产流程的强制步骤：

```bash
python3 scripts/add_vocabulary_coverage.py path/to/material-pack.json \
  --output path/to/material-pack.covered.json
```

默认服务为 `https://vocabprofiler.netlify.app/api/analyze`，无需用户填写URL；该稳定自有入口代理底层分析服务，部署环境可用 `VOCAB_PROFILE_API_URL` 覆盖默认地址，调试时也可显式传 `--api-url`；timeout、响应大小及header/环境凭据参数仍可扩展。

adapter对3–5篇逐篇独立发送 `{text, title, mode:"compact"}`：text是完整按序英文正文，title取原始标题。它要求API 1.0 envelope及canonical `summary.tokens/types/levels` 和结构化focus，校验每篇schema、engine version、index hash、canonical统计、focus及统计一致性，再转换为基础、必修新增、选择性必修新增、未直接收录四层紧凑结果；不保存根 `tokens`、完整token审计或正文。只有全部材料成功且最终合同通过，才原子写出schema 1.2。任一篇API不可用、超时、响应过大或合同错误都会整体失败，不覆盖输入或既有输出，并阻断最终生产交付；不允许模型估计、补写、生成 `unavailable` 或静默降级。

### 8. 最终校验并生成分层交付物

只对adapter成功写出的schema 1.2 covered内部JSON运行；示例中 `delivery/` 是教师交付目录，内部JSON位于其外。DOCX渲染要求Node.js 18+及锁定的 `docx` 依赖：先运行 `node -e "require('docx')"`；若依赖不存在，从Skill根目录执行 `npm ci --ignore-scripts` 后再渲染。

```bash
python3 scripts/validate_material_pack_json.py path/to/work/final-material-pack.json
python3 scripts/render_material_pack.py path/to/work/final-material-pack.json path/to/delivery/material-pack.html
node scripts/render_material_analysis.js path/to/work/final-material-pack.json path/to/delivery/material-analysis.docx
python3 scripts/render_reading_texts.py path/to/work/final-material-pack.json path/to/delivery/reading-texts
```

校验失败时修正上游JSON并从覆盖步骤重跑；不得绕过校验或手改生成产物来掩盖数据问题。三个渲染器都必须成功。HTML渲染器再次校验并转义动态文本；每篇“复制原文”只复制全部原文blocks，不复制分析或界面文案，并在Clipboard API失败时使用离线回退。DOCX只呈现面向人的来源与分析。TXT渲染器为每篇生成规范命名的独立纯文本，按原顺序以空行连接全部blocks，不增加标签、metadata或分析；新任务使用空的 `reading-texts/`，若发现本次不应存在的旧TXT则失败，不静默保留或删除。

### 9. 交付与最终检查

教师交付目录只交付 `material-pack.html`、`material-analysis.docx` 和 `reading-texts/`；不得交付JSON。对3–5篇逐篇核对 `curriculum_vocabulary_coverage.status` 都是 `analyzed`，内部 `engine_version`、`index_hash`、canonical-derived `summary` 和 `focus_vocabulary` 均合法非空；其中引擎版本、索引hash和分析时间只用于内部校验，不得显示在HTML或DOCX。离线打开HTML，确认编号栏及键盘切换、每篇“复制原文”、原始网页链接、顶部五项覆盖指标、持续可见的完整原文、唯一默认折叠“更多信息”和打印全部材料均正常；“更多信息”中的词汇部分只保留词项覆盖、三组关注词及VocabProfiler链接，不重复顶部统计。实际点击复制并粘贴抽查，内容必须以原始标题开始且不含分析文字。

确认DOCX包含来源、教学适配、入选理由、精简词汇覆盖、风险、不确定性、教师决定及检索/淘汰记录；词汇覆盖只呈现总覆盖、词项覆盖、一行四层百分比分布、三组关注词及VocabProfiler链接，不显示技术字段，也不重复收录英文正文。确认 `reading-texts/` 恰有3–5个TXT，与材料一一对应；文件名按两位序号排序，文本逐块匹配内部JSON的 `original_text.blocks[].text`，且不含URL、字段名、覆盖率或教学分析。最后确认教师交付目录没有 `.json`、模板、脚本或测试文件。

严格筛选后不足3篇时停止，报告缺口与可放宽项；不要伪造一个可通过校验的包，也不要用不完整来源凑数。

## 不可越界

- 不绕过登录、订阅、付费墙、robots/技术限制或其他访问控制。
- 不把片段、搜索摘要、AI补写、多个页面拼接文本或合成fixture标作真实完整原文。
- 不从转载页补原始页缺失段落；同一文本的多站版本只计一次。
- 不编造标题、作者、机构、日期、许可、URL、完整性、词数、课标覆盖率、API版本或索引hash；API失败不得模型估计。
- 不声称“公开可读”等于可任意印刷/再发布；记录许可状态，把实际使用和分发决定交给教师/机构。
- 不自由手写或手改最终HTML、DOCX、TXT，不依赖CDN、网络字体或外部框架，不把网页界面文字写入 `original_text.blocks`，不把内部JSON放进教师交付目录。
