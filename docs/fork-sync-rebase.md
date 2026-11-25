<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/fork-sync-rebase/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `fork-sync-rebase`

*Review and safely integrate upstream changes into a long-lived fork.*

</div>

---

## Origin

Distilled from repeatedly syncing a long-lived desktop-app fork whose local identity, storage, and integrations had to survive upstream changes.

- **Imported from:** `codex-skills@7090b13`

## What It Does

- Defaults to review mode: fetch, compare, assess risk, and stop.
- Integration mode uses a dated upstream reference branch and a disposable integration branch.
- Safety invariants: never push upstream, never rebase the active branch first, preserve fork-only boundaries.
- Ends with a completion report covering adopted, deferred, and excluded upstream areas.

## What Was Tested

Used on a real long-lived fork with local app identity and upstream drift.

## Known Limits

Git only. Pairs with `fork-product-development`, which handles feature classification and upstream PR prep.

## Status

- **Last verified:** 2026-09-06
- **Verified against:** a real long-lived product fork
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
