<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/fork-product-development/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `fork-product-development`

*Run an open-source fork as a product while keeping upstream PRs clean.*

</div>

---

## Origin

Shaped on a local Dayflow fork with a long-lived dev branch, a clean upstream PR branch, local app identity, and an install script.

- **Imported from:** `codex-skills@7090b13`

## What It Does

- Classifies every change as upstream candidate, fork-only, or maybe-later.
- Branch model for a downstream product line plus short-lived `pr/<feature>` branches.
- Upstream PR hygiene and fork-only hygiene checklists.
- Detailed playbook in `references/fork-product-playbook.md`.

## What Was Tested

Realistic workspace: a forked desktop app with private build identity, project report, and fork/upstream policy note.

## Known Limits

For pulling upstream into the fork, use `fork-sync-rebase`.

## Status

- **Last verified:** 2026-07-13
- **Verified against:** a forked desktop app with a clean upstream PR branch
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
