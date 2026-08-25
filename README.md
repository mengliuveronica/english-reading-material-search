# English Reading Material Search

A reusable agent skill for finding, verifying, screening, and packaging complete English reading materials for Chinese senior-high-school teaching.

## What it delivers

- A self-contained offline HTML review page with one-click copying for each complete original text.
- A teacher-facing DOCX report containing source information, teaching fit, compact curriculum-vocabulary coverage, risks, and decisions.
- One clean UTF-8 TXT file per reading, containing only the complete original text for downstream analysis.
- Internal validated JSON used only during processing; it is not included in teacher deliverables.

## Install

```bash
npx skills add mengliuveronica/english-reading-material-search --skill english-reading-material-search
```

While the repository is private, installation requires GitHub access to the repository. After a future public release, the same repository can be indexed by [skills.sh](https://skills.sh/).

## Runtime requirements

- Python 3.10+
- Node.js 18+
- The pinned DOCX renderer dependency:

```bash
npm ci --ignore-scripts
```

No Python packages are required. The production workflow calls the versioned VocabProfiler API documented in `SKILL.md`; API failures block final delivery rather than producing estimated coverage.

## Repository layout

```text
SKILL.md
assets/
references/
scripts/
package.json
package-lock.json
```

Run `npx skills add . --list` from this directory to validate local skill discovery.
