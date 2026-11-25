<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/cloudflare-remote-mcp-worker/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `cloudflare-remote-mcp-worker`

*Deploy an MCP-capable repo as a Cloudflare Worker with a verified remote `/mcp` endpoint.*

</div>

---

## Origin

Extracted from moving a local MCP server onto Cloudflare so browser users and MCP clients could share the same Worker logic.

- **Imported from:** `codex-skills@7090b13`

## What It Does

- Audits the repo for an existing MCP server or backend.
- Adds `wrangler.jsonc`, explicit scripts, and a `/mcp` + `/health` surface.
- Hands secret entry and `wrangler login` to the user instead of handling tokens.
- Verifies the remote endpoint and lands docs and screenshots on `main`.

## What Was Tested

A real MCP-capable repo deployed to a Cloudflare Worker and exercised through its remote `/mcp` URL.

## Known Limits

Requires a Cloudflare account and the `wrangler` CLI. Not for local-only stdio packaging.

## Status

- **Last verified:** 2026-05-21
- **Verified against:** a live Cloudflare Worker `/mcp` endpoint
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
