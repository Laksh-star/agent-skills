<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/wiki-maintainer/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `wiki-maintainer`

*An agent-maintained personal knowledge wiki, based on Karpathy's LLM Wiki pattern.*

</div>

---

## Origin

Built to keep a personal research vault compiled and interlinked without manual editing. It existed in two diverging copies (a Claude Code plugin and a Codex skill); this is the merged, agent-neutral version.

- **Imported from:** `codex-skills@7090b13 (skill body) + claude-llm-wiki@a82de76 (index/log conventions, guardrails)`

## What It Does

- Sets up a vault with `raw/`, `wiki/`, `outputs/`, and `agent_exports/` layers.
- Compiles new sources into existing articles, with bidirectional `[[wikilinks]]` and bridge articles across domains.
- Answers questions with citations, runs gap analysis, and generates publishable outputs.
- Ships stdlib-only scripts for linting, backlink repair, and article scaffolding.

## What Was Tested

Used on a real personal vault; bundled scripts compile and respond to `--help`. The Claude Code `/wiki:*` slash commands remain in the claude-llm-wiki plugin repo.

## Known Limits

Python 3 for the helper scripts. `pdftotext` optional for PDF sources. Contradictions and stale claims are flagged, never auto-resolved.

## Status

- **Last verified:** 2026-11-25
- **Verified against:** merged copy reviewed line by line; scripts smoke-tested with `--help`
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
