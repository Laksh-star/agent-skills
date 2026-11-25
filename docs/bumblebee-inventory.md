<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/bumblebee-inventory/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `bumblebee-inventory`

*Run Bumblebee supply-chain inventory scans and produce raw, public-safe, and agent-ready reports.*

</div>

---

## Origin

Captured while auditing package and MCP config exposure across several local repos.

- **Imported from:** `codex-skills@7090b13`

## What It Does

- Scans package metadata and MCP JSON configs across explicit repo roots.
- Preserves raw NDJSON for audit while generating sanitized public summaries.
- Produces handoff notes for coding agents.
- Read-only by default; never auto-installs tools.

## What Was Tested

Local scans across multiple real repositories.

## Known Limits

Requires the [Bumblebee](https://github.com/perplexityai/bumblebee) CLI. Keep personal root lists outside the repo.

## Status

- **Last verified:** 2026-05-24
- **Verified against:** local multi-repo scans
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
