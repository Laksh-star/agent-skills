<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/mbox-knowledge-pack/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `mbox-knowledge-pack`

*Convert local `.mbox` exports into private analysis packs, wiki packets, and optional fine-tune prep.*

</div>

---

## Origin

Created to mine an old sent-mail archive for writing material and wiki sources without ever uploading or mutating the raw export.

- **Imported from:** `codex-skills@7090b13`

## What It Does

- Parses messages, threads, links, and attachments into reports plus SQLite.
- Stages wiki imports as `raw/` compile packets (pairs with `wiki-maintainer`).
- Writing outlines from evidence-tagged messages.
- Fine-tuning prep only as an explicit opt-in, with redaction and audit steps.

## What Was Tested

A realistic local mbox export.

## Known Limits

Python 3 standard library only. Raw mailbox content is private; never commit generated packs.

## Status

- **Last verified:** 2026-08-22
- **Verified against:** a real local mbox export
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
