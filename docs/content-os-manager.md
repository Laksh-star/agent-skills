<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/content-os-manager/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `content-os-manager`

*Set up a markdown Content OS for ideas, drafts, feedback, published posts, and themes.*

</div>

---

## Origin

Built to run a personal writing pipeline as durable markdown plus a few narrowly scoped agent threads.

- **Imported from:** `codex-skills@7090b13`

## What It Does

- Creates the folder and template structure with a bundled script.
- Defines three starter threads: ideas, drafts, and weekly review.
- Optional Teams, Slack, email, and analytics integrations, review-first.
- Never overwrites existing content without confirmation.

## What Was Tested

A real content workspace set up and used across idea, draft, and review threads.

## Known Limits

Python 3 for the setup script. Thread creation depends on what the agent host supports (sessions, chats, scheduled tasks); otherwise the prompts are written to files.

## Status

- **Last verified:** 2026-05-30
- **Verified against:** a real personal content workspace
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
