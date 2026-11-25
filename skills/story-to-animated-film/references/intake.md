# Intake: Brief, PDF or Video

## Brief

Confirm characters, setting, period, audience (children or adults), length and caption language. Write the story yourself. If the brief is thin, show the beat sheet before building.

## PDF

```bash
pdfinfo source.pdf
pdftotext -layout source.pdf source.txt
grep -n -i -E "chapter|canto|<character names>|<place names>" source.txt | head -100
```

Then read the narrative passages in full; don't build from grep hits alone. Note the chapter, page or verse number for every beat you will show.

- **Scanned PDF** (pdftotext returns little or nothing): OCR it first (for example `ocrmypdf` or `tesseract` on rasterised pages), then proceed.
- **Mixed scripts**: PDFs of scripture often hold romanised transliteration rather than native script. If you transliterate into the native script yourself, say so in the reply so a reader can check it.
- **Long texts**: the story may be a frame around teaching chapters. Decide with the user whether the film tells only the frame story or also touches the teachings; a 2–3 minute film usually carries the frame.

## Video

- **Rights first.** Only the user's own or licensed footage. The film retells the story; it never reuses frames.
- **Getting the file.** Many sandboxes cannot download from video sites. Ask the user to attach the file, or use a video-understanding or transcription tool if your environment has one.
- **Transcript.** Use the video's captions if it has them, or a speech-to-text tool. Read it like a text source; timestamps are your source references.
- **Reference frames** for setting and props:
  ```bash
  ffmpeg -i in.mp4 -vf "select='gt(scene,0.35)',scale=640:-1" -vsync vfr ref_%03d.jpg
  ```
  Look at them; don't trace them.
- **Real people** in the video are redrawn as generic characters, never as recognisable likenesses. Ask first if a public figure is central to the story.

## Story bible format

```text
| # | Beat | On screen | Source ref | Source / invented | Caption (≤ 2 lines) |
```

Keep it beside the film code; the reply's scene-by-scene summary comes from it.
