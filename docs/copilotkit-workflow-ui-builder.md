<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/copilotkit-workflow-ui-builder/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `copilotkit-workflow-ui-builder`

*Wrap an existing workflow or backend in a CopilotKit UI that operates real app state.*

</div>

---

## Origin

Distilled from adding CopilotKit to working products where the copilot had to read and drive real workflow state instead of being a detached chat widget.

- **Imported from:** `codex-skills@7090b13`

## What It Does

- Maps workflow state into copilot context and registers narrow frontend tools.
- Puts the workflow surface first, with visible human approval gates.
- Supports a local no-key fallback and a hosted runtime path, stated honestly.
- Validates with builds, smoke tests, and browser checks.

## What Was Tested

Real workflow apps with CopilotKit integrations validated through build and browser checks.

## Known Limits

Node.js project with CopilotKit packages. Hosted copilot mode needs an LLM API key. CopilotKit APIs evolve; re-check imports against current docs.

## Status

- **Last verified:** 2026-05-21
- **Verified against:** real CopilotKit workflow integrations
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
