---
name: story-to-animated-film
description: >-
  Turn source material (a written brief, a PDF of a text, or a video) into an original
  code-drawn 2D animated story film in a style the user picks, with captions and a
  generated score, plus optional vertical shorts, language versions and a prompt pack
  for image/video models. Use when the user asks to make an animated video, animated
  story, explainer or short film from a document, brief, book, scripture or video.
---

# Story → Animated Film

Tell a story from a brief, a PDF or a video as an original animated film, drawn entirely in code (Python + skia) and encoded with ffmpeg. No image or video model is needed; everything runs locally.

The film is a story retold, not footage reused: from a video, take the story, never the pictures. For one verse set to a song, a lighter verse-to-short workflow fits better.

Deep detail lives in references: [styles](./references/styles.md) · [story.md format](./references/story-format.md) · [intake](./references/intake.md) · [shorts and languages](./references/shorts-and-languages.md) · [prompt pack](./references/prompt-pack.md) · [gotchas](./references/gotchas.md).

---

## Core Rules

1. **Ask the style first.** Before building, ask two questions in one message: which animation style (from [styles.md](./references/styles.md), with your recommendation for this source listed first), and which deliverables. Read the source only far enough to recommend. If no one can answer, use the recommended style and the master film, and say so at the top of your reply.
2. **One still before the film.** Render one frame of the opening scene in the chosen style and show it. A wrong style caught at one frame costs a minute.
3. **Original look only.** Never draw a known character, mascot or logo, and never name a studio or a living artist. "Disney style" means a look: warm, rounded, expressive 2D.
4. **Tied to the source.** Every beat carries its source reference (chapter, page, verse, timestamp) and a flag for whether it is from the source or invented. Paraphrase; never paste a modern copyrighted translation.
5. **Dignity for sacred and traditional subjects.** No caricature, nothing a tradition does not depict, and research any living art form before borrowing its look.
6. **Say what you did not check.** Translations you wrote are unproofread; music you generated is synthetic; say whether you watched the whole film or only checked stills.

---

## Craft Rules

| Rule | Number | Checked by |
|---|---|---|
| Hook: the opening poses the story's question, readable with the sound off | by 3 s | `qa/opening.jpg`, eval.md |
| The ending answers the opening question | the `Hook:` header | eval.md |
| Captions are readable | ≤ 2 lines, < 21 characters a second | story.py |
| The picture stays alive: an entrance, gesture, push or cut | every 2–3 s; never still ≥ 4 s outside title and end cards | qa.py |
| Voiced versions keep a natural pace | about 2.5 spoken words a second; retime to the recording | eval.md |
| Delivery loudness | −16 LUFS ±1, true peak ≤ −1 dBTP | qa.py |

---

## Deliverables

| Deliverable | Spec |
|---|---|
| Master film (default) | 16:9, 1920×1080, 24 fps, 2–3 min, captions, generated score, title and end card with the source reference |
| Vertical shorts | 3–5 standalone 9:16 parts (1080×1920), recomposed per scene, each with a title card and closing takeaway |
| Language versions | Same film with captions, cards and verses in another language and script |
| Prompt pack | Style bible, character and location sheets, shot list, per-shot prompts |

At the end, offer (don't build unasked): an illustrated storybook from stills of the same scenes, an interactive choice game, a knowledge graph of the source, a voice-over script.

---

## Workflow

### 1. Intake
Brief, PDF or video: see [intake.md](./references/intake.md). Quick version: `pdftotext -layout` for text PDFs, OCR for scans, a transcript plus scene-change frames for video (`ffmpeg -vf "select='gt(scene,0.35)'"`). The user must own or license any video.

### 2. Story bible: `story.md`
Write the story as [story.md](./scripts/story.md), the single project file ([format](./references/story-format.md)): headers (style, aspect, languages, max duration, the hook, intended holds), a scene table with a source reference and source/invented flag per beat, and timed captions per language. 8–11 beats in story order; one caption of at most two lines per beat; verses stay in their original script with a rendering beneath. Block every entrance (who walks in, from which side) in the beat column. Validate with `python3 scripts/story.py story.md`.

### 3. Setup
```bash
python3 -m pip install skia-python fonttools brotli scipy   # PIL must report features.check('raqm') True
python3 scripts/setup_fonts.py fonts la te dev    # Latin with IAST diacritics, Telugu, Devanagari
```
Render one test line per script at full size and look at it before building scenes.

### 4. Build the film
Copy [scripts/template_film.py](./scripts/template_film.py): a runnable two-scene film with captions in two languages. It shows the whole structure:
- `T*` scene starts, `DUR` and `CAPS` are read from story.md (`STORY=path` picks the file).
- `SEGS = [(start, end + 1.2, scene_fn, camera_fn)]` (the 1.2 s overlap crossfades scenes).
- Scene functions use local time `u = t - T*` and ease between poses with `eio(u, a, b)`; idle life (blinks, sway, mouth flaps) runs on `t` so holds never freeze.
- `cam_keys([(t, zoom, cx, cy), ...])` pushes in on whoever speaks.
- The caption language is chosen by `FILM_LANG`.

Characters come from [scripts/rig.py](./scripts/rig.py) (`person()` with stand/sit/kneel, arm targets, moods, `anjali()` for joined hands) on the drawing library [scripts/core.py](./scripts/core.py). Other styles: see [styles.md](./references/styles.md).

### 5. Check before rendering
- Contact sheet at every beat: `python3 film.py sheet.jpg 3 9 13 ...`.
- **Full-resolution close-ups of every contact**: a hand on a head, joined hands, a held object, a bow. Contact bugs only show at full size.
- Full-resolution crop of one caption per script and the end card.

### 6. Score and render
```bash
python3 scripts/score.py --duration 146 --out score.wav --bells 25,47,55 --dark 15-25 --hits 17.9
python3 scripts/render_chunks.py plan film.py        # prints chunk commands (~1300 frames each)
python3 scripts/render_chunks.py chunk film.py 0 1300 part_00.mp4
python3 scripts/render_chunks.py join final.mp4 score.wav part_00.mp4 part_01.mp4 ...
```
Render chunks in the foreground; many sandboxes stop background jobs soon after a turn ends. About 0.35 s per frame on 2 cores.

### 7. QA
```bash
python3 scripts/qa.py final.mp4 --story story.md --out qa
```
It checks size, frame rate, audio, length, loudness, black frames, stillness and story.md, and writes `qa/report.md`, `qa/contact.jpg` and `qa/opening.jpg`. Look at both sheets and at the frames either side of each join, then answer [eval.md](./eval.md) yes or no. Fix or name every "no".

### 8. Shorts, languages, prompt pack
See [shorts-and-languages.md](./references/shorts-and-languages.md) and [prompt-pack.md](./references/prompt-pack.md).

---

## Deliver

Send files as they finish, with `qa/report.md`. In the reply: the style and why; what each scene shows against the source, with references; what was invented; translation and fidelity caveats; whether you watched the full film or checked stills; the one or two weakest spots.
