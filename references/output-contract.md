# English Reading Material Pack 输出合同

## 1. 交付模式

教师交付目录固定包含三类产物，不含JSON：

- **展示页**：`material-pack.html`。它必须由已校验内部JSON经固定Python渲染器生成，可离线打开；每篇提供“复制原文”，不得让模型自由手写或直接修补最终HTML。
- **分析报告**：`material-analysis.docx`。它集中呈现来源、教学适配、词汇覆盖状态、入选理由、风险、不确定性、教师决定及检索记录，不重复收录英文原文正文。
- **纯文本目录**：`reading-texts/`。每个Material独立生成一个UTF-8 TXT，只含完整未改写 `original_text.blocks[].text`，用于后续程序分析。
- 正常包含3–5个非重复 `Material`。每个单元都必须有完整未改写 `Original text` 和已实际核验的HTTP(S)原始URL，不存在 link-only Material。
- **完整交付**：1.1中间JSON通过基础校验后调用兼容词汇服务；3–5篇全部分析成功后原子生成schema 1.2，再渲染HTML、DOCX和逐篇TXT。
- **基础交付**：词汇服务不可用且用户明确同意后，使用 `prepare_basic_delivery.py` 从原始schema 1.1工作文件生成新的schema 1.1基础包。每篇覆盖状态统一为 `unavailable`，教师产物明确显示词汇覆盖尚未完成；来源、原文和教学分析照常交付。
- 不能确认完整正文的页面只能进入 `discard_log`。不足3篇时报告缺口，不以不完整、合成或低质来源凑包。

## 2. 内部 JSON 顶层合同

JSON必须是UTF-8对象，字段名固定且不得添加注释；它是三个固定渲染器的唯一内容数据源和机器可读工作记录，但不得进入教师交付目录。生产包的最小形状如下：

```jsonc
{
  "schema_version": "1.2",
  "pack_type": "production",
  "pack_title": "...",
  "retrieval_topic": "...",
  "target_grade": "...",
  "intended_use": "...",
  "material_count": 3,
  "generated_date": "YYYY-MM-DD",
  "search_brief": {
    "length_target": "...",
    "genre_preference": "...",
    "freshness": "...",
    "access_reuse_requirements": "...",
    "assumptions": "..."
  },
  "materials": [],
  "search_log": [],
  "discard_log": []
}
```

约束：

- 完整包使用 `schema_version: "1.2"`，并要求每篇 `curriculum_vocabulary_coverage.status` 都是 `analyzed`。基础包保留 `schema_version: "1.1"`，要求每篇都显式使用 `status: unavailable`；它只能由固定脚本在服务失败且用户同意后生成。1.0包和缺少显式覆盖状态的旧1.1包只用于兼容读取。
- 真实交付只能使用 `pack_type: production`。`synthetic_fixture` 仅供本地UI/校验测试，并必须有醒目的 `fixture_notice`。
- `material_count` 为整数，必须与 `materials` 实际长度一致，且范围为3–5。
- `generated_date` 使用 `YYYY-MM-DD`。
- 页面极窄顶部所需的Pack标题、检索主题、目标年级、数量和日期必须来自上述顶层字段，不能只藏在自由文本中；`intended_use` 仍是必填数据字段，但不要求在极窄顶部重复展示。

## 3. Material 固定结构

每个 `materials[]` 对象必须包含以下字段：

```jsonc
{
  "id": "M1",
  "source_metadata": {
    "title": "Exact original title",
    "author": "Exact byline | not stated",
    "publishing_institution": "...",
    "original_url": "https://...",
    "publication_date": {
      "status": "verified | not_stated | uncertain",
      "published": "YYYY-MM-DD | null",
      "updated": "YYYY-MM-DD | null",
      "note": "What the page states or why status is uncertain"
    },
    "access_status": "complete body publicly accessible without login/paywall; checked ...",
    "source_relationship": "original publisher page | authorized reprint | agency carrier — details",
    "license_reuse_status": "exact stated license | not stated"
  },
  "original_text": {
    "extraction_status": "complete_main_body",
    "extraction_note": "complete public-page body; only webpage chrome removed",
    "checked_date": "YYYY-MM-DD",
    "blocks": [
      {"type": "title", "text": "Exact original title"},
      {"type": "subtitle", "text": "Exact subtitle, if present"},
      {"type": "paragraph", "text": "Exact first paragraph..."},
      {"type": "heading", "text": "Exact subheading, if present"},
      {"type": "paragraph", "text": "All remaining paragraphs in source order..."},
      {"type": "list_item", "text": "Exact list item, when part of the body"}
    ]
  },
  "selection_reason": "Why this complete source fits the brief and adds value",
  "teaching_fit": {
    "topic": "...",
    "genre": "...",
    "word_count": 000,
    "language_load": {"level": "low | medium | high", "evidence": "..."},
    "background_load": {"level": "low | medium | high", "evidence": "..."},
    "age_appropriateness": {"level": "suitable | conditional", "evidence": "..."},
    "adaptation_load": {"level": "low | medium | high", "evidence": "..."}
  },
  "curriculum_vocabulary_coverage": {"status": "analyzed", "...": "see section 4"},
  "risks_uncertainties": {
    "risks": [{"basis": "fact | estimate", "text": "..."}],
    "uncertainties": [{"basis": "fact | estimate", "text": "none found | explicit uncertainty"}],
    "teacher_decision": "Final task, edits, notes, sensitivity and reuse/printing decision"
  }
}
```

字段责任：

- `source_metadata` 和逐字 `original_text` 是网页核验事实；不猜作者、日期、来源关系或许可。
- `selection_reason` 与四类教学负荷是相对 search brief 的评估，必须给可检查依据。
- `risks` 和 `uncertainties` 至少各一项；用 `basis` 区分网页事实与评估。若未发现不确定性，仍显式记录 `none found` 及检查范围。
- `teacher_decision` 专门保留教师对题型、删改、注释、敏感性和印刷/分发的最终取舍。
- `id` 使用 `M1`、`M2`……且唯一；原始URL也必须在包内唯一，防止重复收录同文。

## 4. 课标词汇覆盖合同

完整schema 1.2包的每个Material都必须且只能有一个 `curriculum_vocabulary_coverage`，并且status必须为 `analyzed`。它是兼容课标索引API返回的真实、经合同验证的紧凑结果，不是CEFR、阅读等级或绝对难度判断。基础schema 1.1包统一使用 `status: unavailable`，不含任何估算统计。`analyzed` 形状固定为：

```jsonc
"curriculum_vocabulary_coverage": {
  "status": "analyzed",
  "engine_version": "coverage-engine/semver-or-build",
  "index_hash": "sha256:64-hex-digits",
  "analyzed_at": "RFC3339 timestamp with timezone",
  "summary": {
    "total_tokens": 000,
    "covered_tokens": 000,
    "token_coverage_rate": 0.0000,
    "total_types": 000,
    "covered_types": 000,
    "type_coverage_rate": 0.0000,
    "level_counts": {
      "foundation": 000,
      "high_school_required": 000,
      "high_school_selective": 000,
      "not_directly_listed": 000
    },
    "level_rates": {
      "foundation": 0.0000,
      "high_school_required": 0.0000,
      "high_school_selective": 0.0000,
      "not_directly_listed": 0.0000
    }
  },
  "focus_vocabulary": {
    "high_school_required": ["compact display string"],
    "high_school_selective": ["compact display string"],
    "not_directly_listed": ["compact display string"]
  }
}
```

- `total_tokens` / `total_types` 对应canonical denominator，`covered_tokens` / `covered_types` 对应matched；excluded词不写入紧凑统计。coverage rate均为0–1；covered不得超过total；type总数不得超过token总数。四个level count按token计，和为 `total_tokens`；`foundation`、`high_school_required`、`high_school_selective` 三项之和为 `covered_tokens`；各rate必须与对应分数一致（允许四位小数舍入）。这里的后两层分别表示“高中必修新增”和“选择性必修新增”，不包含基础层，避免把累计覆盖误当层级新增。
- `focus_vocabulary` 只含 `high_school_required`、`high_school_selective`、`not_directly_listed` 三个数组；基础词不逐项铺开。每组最多100个非空、去重、至多80字符的展示字符串。Material Pack只保存这些紧凑列表，不保存API返回的 `tokens`、完整token审计、逐token命中记录或其他大字段。
- 非 `analyzed` 状态的 `engine_version`、`index_hash`、`analyzed_at`、`summary`、`focus_vocabulary` 必须存在且为 `null`。基础包的3–5篇必须全部使用 `unavailable`，不能与 `analyzed`、`not_requested` 或字段缺失混用。API adapter不会生成 `unavailable`；只有 `prepare_basic_delivery.py` 可以在用户授权后写入。
- `analyzed` 的版本、索引hash、时间和统计都来自API响应并逐篇经过校验；执行者或模型不得自行推断、补写或把语言负荷判断转换为覆盖率。

## 5. Original text 合同

- `blocks` 是完整 main-body extraction，不是摘要、改编稿、OCR猜测或界面文案。
- 第一项必须是 `type: title`，其 `text` 与 `source_metadata.title` 逐字符一致。
- 其余块按原网页顺序保存；允许类型仅为 `title`、`subtitle`、`heading`、`paragraph`、`list_item`。
- 保留原始措辞、拼写、大小写、标点、段落、小标题和必要列表；不翻译、不纠错、不静默合并或重排。
- 只删除导航、广告、cookie提示、推荐链接、分享/打印控件等网页 chrome。不得把“入选理由”“风险”“教学提示”“打开原网页”等UI内容放进 blocks。
- 页面若缺首段、末段、折叠内容或动态内容，不能使用 `complete_main_body`；它应进入 `discard_log`。
- 每篇至少80个英文词元。`word_count` 必须等于所有 blocks 中英文词元总数；规则为 `A–Z/a–z` 单词及内部连字符/撇号，标题、副标题和小标题计入。

## 6. Metadata 与教学判断

- **Title / Author / Publishing institution**：只记录原始页直接可见事实；无作者写 `not stated`。
- **Publication date**：`verified` 必须有 `published` 日期；页面未标明则 `not_stated`；明确冲突且无法消解用 `uncertain` 并在 `note` 和风险中解释。
- **Original URL**：只能是实际核验页面的完整 `http://` 或 `https://` URL；去掉无关跟踪参数。禁止 `javascript:`、`data:`、相对地址、用户信息和含空白/控制字符的URL。
- **Access status**：明确全文无需登录/付费且已确认完整，并写核验日期。
- **Source relationship / License**：说明原始发布、授权转载或通讯社关系；没有许可声明写 `not stated`，不能把公开访问写成开放许可。
- **Language / Background / Age / Adaptation**：相对 brief 判断低/中/高或适龄结论，并紧跟词汇、句法、文化制度、敏感性或删改需求证据。
- **Risks**：至少检查地域/样本偏差、因果夸张、敏感内容、商业/倡议立场、时效、删改失真和再使用状态。

## 7. Search log 与 Discard log

`search_log` 至少一项，固定形状：

```jsonc
{
  "id": "L1",
  "accessed_at": "YYYY-MM-DD HH:MM TZ",
  "query": "...",
  "discovery_surface": "web search | named database/search surface",
  "adjustment_decision": "What result quality/completeness showed and what changed",
  "verified_urls": ["https://..."]
}
```

只有实际打开的HTTP(S)地址才能进入 `verified_urls`；只看过摘要时留空数组。日志用于追溯，不能替代原文。

`discard_log` 是对象数组，每项含 `id`、`title_or_source`、`url`（实际打开的HTTP(S) URL或 `null`）和 `reason`。登录/付费墙、正文不完整、动态加载后仍无法确认、摘要/预览、来源关系不明、过时、不适龄、高背景/改编负荷、重复或元数据冲突均在此记录。

## 8. API adapter 与固定分层渲染合同

完整交付默认包含覆盖分析。外部检索前先运行 `python3 scripts/check_vocabulary_service.py`；预检使用内置短文本，不发送教师材料。完整正文写入且1.1中间JSON通过基础校验后，adapter对3–5篇材料按 `original_text.blocks` 原顺序以两个换行拼接全部 `text`，标题取 `source_metadata.title`，向选定HTTP(S)端点逐篇独立POST且只发送：

```jsonc
{"text":"complete ordered English text","title":"Exact original title","mode":"compact"}
```

API响应envelope必须在根对象提供 `schema_version: "1.0"`、`mode: "compact"`、`engine_version`、`index_hash`、`analyzed_at`、`summary`、`tokens` 和 `focus_vocabulary`。每篇响应都必须提供canonical `summary.tokens`、`summary.types`、`summary.levels`：adapter用token/type denominator、matched、coverage_rate形成紧凑总览，用levels的三个新增层及 `denominator - matched` 形成四项level统计，并交叉校验canonical status counts、层级token/type counts/rates和总数；不再接受扁平summary。

API的canonical focus必须恰含三个数组：高中层级使用 `{headword, forms, ...}`，未直接收录使用 `{surface, count}`。adapter逐项校验后压成去重且不超过80字符的展示字符串，只保留后三类focus，不展开foundation。adapter会限制响应大小、设置逐请求timeout，并逐篇校验schema、engine version、SHA-256 index hash、canonical summary、focus及统计一致性；根 `tokens` 仅用于确认compact envelope且不会写入Material Pack。服务仅为本次请求分析正文，不保存正文；Material Pack也不保存根 `tokens` 或完整token审计。

```bash
python3 scripts/check_vocabulary_service.py
python3 scripts/validate_material_pack_json.py path/to/work/material-pack.json
python3 scripts/add_vocabulary_coverage.py path/to/work/material-pack.json \
  --output path/to/work/material-pack.covered.json
python3 scripts/validate_material_pack_json.py path/to/work/material-pack.covered.json
python3 scripts/render_material_pack.py path/to/work/material-pack.covered.json path/to/delivery/material-pack.html
node scripts/render_material_analysis.js path/to/work/material-pack.covered.json path/to/delivery/material-analysis.docx
python3 scripts/render_reading_texts.py path/to/work/material-pack.covered.json path/to/delivery/reading-texts
```

服务不可用且用户确认基础交付时运行：

```bash
python3 scripts/prepare_basic_delivery.py path/to/work/material-pack.json \
  --output path/to/work/material-pack.basic.json
```

随后用 `material-pack.basic.json` 运行同一验证器和三个渲染器。

- adapter默认调用稳定自有入口 `https://vocabprofiler.netlify.app/api/analyze`，正常命令无需填写URL；`VOCAB_PROFILE_API_URL` 可覆盖默认地址，显式 `--api-url` 的优先级最高；地址只接受无用户信息的 `http://` / `https://` URL。
- 保留 `--timeout`、`--max-response-bytes`、可重复的 `--header NAME=VALUE`；如服务需要凭据，用 `--api-key-env ENV_NAME` 和可选 `--api-key-header` 从环境变量取完整header值，不把secret写入脚本、JSON或文档。
- 任一材料发生网络、timeout、HTTP、响应过大、JSON或合同错误时，adapter整体退出非零，既不改输入，也不覆盖已存在的输出。adapter没有 `--allow-unavailable`，也不会估算覆盖率。失败会阻断完整交付，并把是否生成基础包交给用户决定。
- 只有3–5篇全部得到经验证的独立指标后，adapter才设置schema 1.2、执行最终合同校验，并使用输出目录内临时文件原子替换目标。`--output` 可以等于输入，但独立输出更便于审阅。
- `prepare_basic_delivery.py` 只接受production schema 1.1，要求新输出路径，并拒绝替换任何已有 `analyzed` 结果。它原子写出每篇均为 `unavailable` 的基础包，不修改原始工作文件。

HTML渲染器会再次执行同一验证，失败时不输出新HTML。固定模板为 `assets/material-pack-template.html`。生成页面必须：

- 自包含CSS/JavaScript，不依赖CDN、框架、网络字体或运行时网络请求；
- 采用Clean Swiss阅读版式：白底、黑字、仅用朱红作强调，统一 `system-ui, Arial, sans-serif`，无阴影、无圆角，屏幕可见UI字号不小于12px；
- 极窄顶部展示Pack标题、主题、年级、材料数和生成日期；桌面左侧固定72px的01/02/03……编号栏，移动端改为顶部横向编号栏；
- 编号控件按真实3–5篇动态生成，当前项使用朱红竖线和数字；点击或使用方向键、Home、End只显示对应文章，并正确维护tab/panel的ARIA状态与键盘焦点；
- 每篇使用独立语义化 `<article>`；当前篇标题为48–56px，来源、作者、日期、词数和经验证的原始网页链接同列展示；标题区另提供清晰的“复制原文”按钮和 `aria-live` 状态反馈；
- 复制内容必须由该Material全部 `original_text.blocks[].text` 按原顺序以空行连接，含标题、副标题、小标题、段落与列表项，不含URL、metadata、覆盖率、教学分析或界面文案；优先使用Clipboard API，权限或 `file://` 环境失败时回退到本地textarea复制，不发起网络请求；
- 完整包在每篇标题下固定显示课标总覆盖、基础、必修新增、选择性必修新增、未直接收录五项百分比和数量，中文标签不小于13px。基础包在同一位置显示“课标词汇覆盖尚未完成；来源核验和教学分析可正常使用”，不显示或推测任何指标；
- 完整未改写原文紧接五项指标持续显示，以18px、1.7行高和约72ch行长作为页面主体，不再把原文放入折叠区；
- 每篇只保留一个默认折叠的“更多信息” `<details>`，统一容纳来源详情、教学适配、入选理由、风险、不确定性、教师决定和“课标词汇重点”；词汇部分只显示词项覆盖、必修关注词、选择性必修关注词、未直接收录词及可点击的 `https://vocabprofiler.netlify.app/`，不重复顶部词次与四层指标；
- `engine_version`、`index_hash`、`analyzed_at` 继续保存在内部JSON并参与合同校验，但不得渲染到HTML或DOCX，也不得用其他引擎ID、hash或时间戳替代展示；
- 不提供全文搜索、负荷筛选、批量展开/收起、sticky工具栏、卡片墙、双栏callout、chips或无后端功能的保存按钮；屏幕交互只保留材料切换、逐篇复制原文和单篇“更多信息”展开；
- print CSS显示全部3–5篇、合理分页并强制呈现每篇“更多信息”内容；打印前后脚本可临时设置并恢复details状态；
- 使用语义化HTML、键盘原生控件、清晰focus样式、合理对比度，并尊重 `prefers-reduced-motion`；
- 对所有动态文本做HTML属性级转义；所有可点击URL在验证后才进入 `href`。

DOCX分析报告必须由 `scripts/render_material_analysis.js` 生成，并满足：

- 文件名固定为 `material-analysis.docx`，面向人阅读，按材料编号组织；
- 包含Pack概况，以及每篇的来源信息、入选理由、教学适配、课标词汇覆盖、风险、不确定性和教师决定，末尾包含检索与淘汰记录；
- 完整包每篇词汇覆盖压缩为：课标总覆盖、词项覆盖、一行四层百分比分布、三组关注词及可点击的 `https://vocabprofiler.netlify.app/`；基础包只显示覆盖尚未完成。两种模式都不显示引擎版本、索引hash或分析时间；
- 不重复收录 `original_text.blocks` 的英文正文；正文只进入HTML与逐篇TXT；
- 使用标题层级、两列表格、真实项目符号、页边距和页码形成可导航的专业版式；URL使用可点击超链接；
- 生成前调用同一JSON校验器；失败时不生成可交付DOCX。

逐篇TXT必须由 `scripts/render_reading_texts.py` 生成，并满足：

- 输出目录固定为 `reading-texts/`，每个Material恰有一个UTF-8文件；
- 文件名使用 `NN_<清理后的原始标题>.txt`：`NN` 为从01开始的两位序号，删除英文直/弯撇号，以连字符替换其他标点和空白，标题部分最长80字符，空标题回退为 `reading`；
- 内容只由该Material全部 `original_text.blocks[].text` 按原顺序组成，块间一个空行，文件末尾一个换行；不得增加标题标签、URL、metadata、JSON字段名、分析、Markdown标记或界面文案；
- 新任务使用空的 `reading-texts/` 目录；若目录中存在本次不应生成的旧TXT，渲染器必须失败而不是静默保留或删除，避免旧材料污染交付；
- 生成前调用同一JSON校验器；材料数、标题或原文不合法时不输出交付TXT。

不得手改已生成HTML、DOCX或TXT来改变内容；任何内容修正都回到内部JSON，重新校验并运行三个渲染器。教师交付目录不得包含JSON。

## 9. 验证与边界

- 完整包逐篇确认 `status: analyzed`、合法且非空的内部 `engine_version` / `index_hash`、经canonical响应转换的 `summary` 和三个focus数组；同时确认HTML和DOCX显示精简指标。基础包确认schema为1.1、用户已同意、3–5篇状态全部为 `unavailable`，HTML和DOCX均显示覆盖尚未完成。两种模式都不在教师产物中显示内部技术字段。
- 离线实际点击每篇“复制原文”并粘贴抽查：必须从原始标题开始，覆盖全部原文块，且不含来源、分析或界面文案。
- 解压或抽取DOCX文本检查所有分析栏目齐全且没有英文原文正文；逐个读取TXT检查文件名、UTF-8编码、顺序、块间空行及纯文本边界，并确认TXT数量等于 `material_count`。
- 最终列出交付目录内容，确认只有HTML、DOCX和 `reading-texts/*.txt`，没有 `.json`、脚本、模板或测试文件。
- JSON校验器不联网，不能证明URL真实、页面完整、提取逐字、许可正确或材料真正适龄；执行者仍须逐URL核验，教师仍须作再使用决定。
