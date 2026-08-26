# English Reading Material Search

A reusable agent skill for finding, verifying, screening, and packaging complete English reading materials for Chinese senior-high-school teaching.

## What it delivers

- A self-contained offline HTML review page with one-click copying for each complete original text.
- A teacher-facing DOCX report containing source information, teaching fit, compact curriculum-vocabulary coverage, risks, and decisions.
- One clean UTF-8 TXT file per reading for downstream adaptation and analysis.
- Internal validated JSON used only during processing and kept outside teacher deliverables.

## Install

```bash
npx skills add mengliuveronica/english-reading-material-search --skill english-reading-material-search
```

The public repository is structured for discovery and installation through the open [skills.sh](https://skills.sh/) ecosystem.

## Quick start

A teacher can begin with a natural-language request such as:

> 请为高二英语阅读理解课寻找3篇关于“青少年参与社区问题解决”的英文材料。每篇500至800词，背景知识负担适中，并提供来源核验、教学适配和课标词汇覆盖分析。

See [the complete teacher-request example](examples/teacher-request.md) for the expected process and deliverables.

## Runtime requirements

- Python 3.10 or newer. See [`requirements.txt`](requirements.txt); the Python runtime uses only the standard library.
- Node.js 18 or newer for DOCX generation.
- Install the pinned DOCX dependency from the Skill root:

```bash
npm ci --ignore-scripts
```

## Check vocabulary-service access

Run this before a long search. It uses an internal sample sentence and does not send teacher material:

```bash
python3 scripts/check_vocabulary_service.py
```

A compatible alternate endpoint can be supplied through `VOCAB_PROFILE_API_URL` or `--api-url`. If no service is reachable, the user may authorize a basic delivery containing the verified sources, complete texts, and teaching analysis while clearly marking vocabulary coverage as unfinished.

```bash
python3 scripts/prepare_basic_delivery.py path/to/work/material-pack.json \
  --output path/to/work/material-pack.basic.json
```

The API adapter still fails closed and never estimates coverage. Read [FAQ.md](FAQ.md) for network, source-access, material-count, and delivery questions.

## Repository layout

```text
SKILL.md
README.md
FAQ.md
CHANGELOG.md
requirements.txt
assets/
examples/
references/
scripts/
package.json
package-lock.json
```

Run `npx skills add . --list` from this directory to validate local skill discovery.
