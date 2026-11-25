<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/expert-judgment-distillation/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `expert-judgment-distillation`

*Turn domain expert judgment into datasets, evals, repair loops, and case studies.*

</div>

---

## Origin

Built while modeling an editorial judgment workflow after the Thinking Machines / Bridgewater Tinker write-up.

- **Imported from:** `codex-skills@7090b13`

## What It Does

- Label taxonomies, seed datasets, prompt baselines, and contested-example review.
- Fine-tuning or Tinker-style experiment loops with failure taxonomies and repair sets.
- Held-out evals and two-stage rubric models.
- Dataset validator script and case-study templates.

## What Was Tested

A realistic editorial/Tinker experiment workspace.

## Known Limits

Python 3 for the validator. Fine-tuning itself needs whatever training stack the user chooses. Cites the source article conceptually without implying endorsement.

## Status

- **Last verified:** 2026-07-02
- **Verified against:** an editorial judgment experiment workspace
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
