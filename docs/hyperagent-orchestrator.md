<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/hyperagent-orchestrator/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `hyperagent-orchestrator`

*Drive Hyperagent agents over its hosted MCP server: dispatch, chain, fan out, and monitor.*

</div>

---

## Origin

Captured while orchestrating pre-built Hyperagent agents from an MCP client: sequential research → deck chains, parallel fan-out, and a fleet dashboard.

- **Imported from:** `hyperagent-orchestrator@c33f301`

## What It Does

- Explains the mental model: MCP is a remote control for agents that already exist; every run is asynchronous.
- Core dispatch loop plus recipes for sequential chains, fan-out, and human-in-the-loop refinement.
- Compares server-side agent delegation with client-side MCP orchestration.
- Dashboard pattern with a snapshot-first fallback (`references/dashboard.md`).

## What Was Tested

Live runs against the Hyperagent MCP server (`https://hyperagent.com/api/mcp`) in June 2026.

## Known Limits

Requires a Hyperagent account and an MCP host connected to its server. Scores, costs, and run counts are not exposed over MCP. The tool list should be re-checked against the live server before relying on response shapes.

## Status

- **Last verified:** 2026-06-26
- **Verified against:** live Hyperagent MCP server (six tools)
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
