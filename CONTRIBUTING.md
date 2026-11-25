# Contributing to Agent Skills

Every skill in this repo must be **portable, self-contained, and verified on a real workflow**. The quality gate below is enforced by [`scripts/validate-skills.py`](./scripts/validate-skills.py) locally and in CI.

```bash
python3 scripts/validate-skills.py           # must pass before every commit
python3 scripts/validate-skills.py --strict  # recommended before a release
```

## Adding a Skill

1. Create `skills/<name>/SKILL.md` (kebab-case `name` that matches the folder).
2. Put deep detail in `references/`, repeatable mechanics in `scripts/`, templates and fixtures in `assets/`.
3. Copy [`docs/_template.md`](./docs/_template.md) to `docs/<name>.md` and fill it in.
4. Add a row to the matching category table in [`README.md`](./README.md).
5. Run the validator, then complete the release checklist below.

## The Quality Gate

| # | Gate | Rule | Enforced |
|---|---|---|---|
| 1 | **Spec** | Frontmatter with `name` (== folder, kebab-case, ≤ 64 chars) and `description` (≤ 1024 chars) that includes a "Use when …" trigger. Allowed keys: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. | ✅ script |
| 2 | **Size** | `SKILL.md` ≤ 500 lines. Push detail into `references/`. | ✅ script |
| 3 | **Links** | Every relative link and every referenced `references/`, `scripts/`, `assets/` file exists. | ✅ script |
| 4 | **Scripts** | Bundled `.py`, `.js`, `.mjs`, `.sh` pass syntax checks. Each script should support `--help` or a sample fixture for a cheap smoke run. | ✅ syntax · 👤 smoke |
| 5 | **Secrets** | No API keys, tokens, private keys, or credentialed URLs. Read credentials from env vars and name them in the docs. | ✅ script + gitleaks in CI |
| 6 | **Privacy** | No personal home paths (`/Users/<name>`), email addresses, account IDs, client names, or real customer data. Fixtures must be synthetic. | ✅ paths/emails · 👤 the rest |
| 7 | **Portability** | Write for "the agent", not a specific product. Host-specific paths and variables (`~/.codex`, `CODEX_HOME`, `~/.claude`, `${CLAUDE_PLUGIN_ROOT}`, `mcp__…__` tool names) are rejected unless the skill declares `metadata.hosts`. Host UI metadata belongs in `agents/<host>.yaml`. | ✅ script |
| 8 | **Dependencies** | Every companion repo, CLI, or API is publicly linked, and required env vars are listed in `docs/<name>.md`. A skill that only works with an unpublished repo does not ship. | 👤 review |
| 9 | **Freshness** | `docs/<name>.md` has `Last verified: YYYY-MM-DD`. Re-verify third-party API facts before bumping it. | ✅ script |
| 10 | **No overlap** | Two skills must not compete for the same request. The validator warns when descriptions overlap heavily. | ⚠️ script warns |
| 11 | **Hygiene** | No `__pycache__`, `.pyc`, `.DS_Store`, `.env*`, `dist/`, or `.skill`/`.zip` archives inside `skills/`. | ✅ script |
| 12 | **Catalog** | README links the skill, and `docs/<name>.md` exists. | ✅ script |

### Declaring a host-specific skill

Most skills should be agent-agnostic. If a skill only makes sense inside one host (for example, it reads Codex task history), declare it:

```yaml
---
name: example-skill
description: … Use when …
metadata:
  hosts: codex
---
```

Then label it **Codex-only** in the README and in `docs/<name>.md`.

## Release Checklist

Copy this into the PR description:

```markdown
- [ ] `python3 scripts/validate-skills.py --strict` passes
- [ ] Manual read-through: instructions are concise and written for "the agent"
- [ ] Tested against a realistic workspace or fixture (described in docs/<name>.md)
- [ ] Prerequisites, env vars, and companion repos are documented with public links
- [ ] Known limits documented
- [ ] Installed from a fresh clone (`npx skills add …`) and triggered once in at least one agent
- [ ] `Last verified` date updated
```

## Importing a Skill From Another Repo

- Copy the skill in fresh (no history import), and record `Imported from: <repo>@<sha>` in `docs/<name>.md`.
- Scan the **source repo's full git history** for secrets before archiving it (`gitleaks detect --source <repo>`).
- Neutralize host-specific wording, remove generated files, then run the validator.
