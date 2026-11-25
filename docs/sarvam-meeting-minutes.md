<div align="center">

<p>
  <a href="../README.md"><strong>← Back to Agent Skills</strong></a> &nbsp;·&nbsp;
  <a href="../skills/sarvam-meeting-minutes/SKILL.md"><strong>View SKILL.md</strong></a>
</p>

# `sarvam-meeting-minutes`

*Transcribe Indian-language and code-mixed meetings with Sarvam AI and draft evidence-backed minutes.*

</div>

---

## Origin

Built for real meeting recordings that mix Indian languages and English, where generic transcription failed.

- **Imported from:** `codex-skills@7090b13`

## What It Does

- Batch transcription with language auto-detection, `codemix` mode, and diarization.
- Minutes template that ties decisions and actions to transcript evidence.
- API key read from an environment variable and never printed.

## What Was Tested

Live Sarvam batch transcription of two `.m4a` meeting recordings with diarization; minutes generated from the transcript.

## Known Limits

Requires `pip install sarvamai` and `SARVAM_API_KEY`. Audio is sent to Sarvam's API, so get consent for sensitive recordings.

## Status

- **Last verified:** 2026-08-04
- **Verified against:** live Sarvam batch transcription
- **Hosts:** agent-agnostic

## Use This Skill

```bash
npx skills add Laksh-star/agent-skills
```
