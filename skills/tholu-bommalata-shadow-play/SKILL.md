---
name: tholu-bommalata-shadow-play
description: >-
  Tell a story as a code-drawn shadow-puppet film in the visual language of Tholu
  Bommalata, the leather shadow theatre of the Telugu-speaking region: translucent
  jewel-coloured profile puppets with rods on a lamp-lit cloth, opening with the
  traditional Ganesha and Saraswati invocation, with a fidelity check against published
  sources and an honest list of departures. Use when the user asks for a shadow play,
  shadow puppet video, tholu bommalata or tholubommalata version of a story, or an
  Indian epic or folk tale told as puppet theatre.
---

# Tholu Bommalata Shadow Play

Render a story as a shadow-puppet film in the visual language of Tholu Bommalata, drawn in code (Python + skia) and encoded with ffmpeg.

Tholu Bommalata is a living, hereditary and endangered tradition of Andhra Pradesh, Telangana and parts of Karnataka. This skill makes an **homage in its visual language, not a reproduction** of any troupe's puppets. Say so in the credits and in your reply.

Story intake, the story bible, vertical shorts and language versions follow the `story-to-animated-film` skill in this repo; this skill supplies the look.

References: [conventions and sources](./references/conventions.md) · [story.md format](../story-to-animated-film/references/story-format.md) · [eval](./eval.md) · [Telugu voice script](./references/voice-script.md) · [gotchas](./references/gotchas.md).

---

## Core Rules

1. **Fidelity before drawing.** Read at least two descriptive sources on the form before designing (see [conventions.md](./references/conventions.md)) and re-check the conventions against them. Keep a list of departures while you design, not after.
2. **Ask for references and people.** Ask for photographs of real puppets and a real screen (use them for iconography only; never trace a maker's puppet). Ask whether a practising troupe can voice, review or be credited; for anything published, recommend it.
3. **Open with the invocation.** The cast is pinned at both edges of the screen; Ganesha enters from the audience's right and dances, then Saraswati. About 14 seconds.
4. **Block entrances by the tradition.** Divinities enter from the audience's right (screen right), other characters from the left; demons drop from above.
5. **Faces never change.** Carry every beat with gesture: joined hands, a pointing arm, a whole-body bow, a hop for each step, a flip to turn.
6. **Never pass off synthetic sound as a troupe's.** The puppeteers' own voices and songs are the heart of the form; say plainly when the audio is synthesised.

---

## Craft Rules

| Rule | Number | Checked by |
|---|---|---|
| Hook: the first story scene poses its question, readable with the sound off | within 3 s of the invocation ending | `qa/contact.jpg`, eval.md |
| The ending answers the opening question | the `Hook:` header | eval.md |
| Captions sit in the black cloth band and are readable | ≤ 2 lines, < 21 characters a second | story.py |
| The show never stalls: a hop, gesture, entrance or lamp dip | every 2–3 s; never still ≥ 4 s outside title and end cards | qa.py |
| Voiced versions keep the narrator's pace | about 2.5 spoken words a second; retime to the recording | eval.md |
| Delivery loudness | −16 LUFS ±1, true peak ≤ −1 dBTP | qa.py |

---

## Workflow

### 1. Setup
```bash
python3 -m pip install skia-python fonttools brotli scipy   # PIL must have raqm
python3 scripts/setup_fonts.py fonts la te dev
```

### 2. Write story.md
Copy [scripts/story.md](./scripts/story.md): headers (including `Prologue:` for the invocation's length and `Hook:`), a scene table with source references and source/invented flags, entrances blocked by side in the beat column, and timed `## Prologue: <lang>` and `## Captions: <lang>` blocks. Scene and caption times are in story time, which starts when the invocation ends. Validate with `python3 scripts/story.py story.md`.

### 3. Build from the template
Copy [scripts/template_shadow.py](./scripts/template_shadow.py): a runnable play with the invocation, two scenes, entrances, a lamp dip at scene changes, and captions in English and Telugu, all timed from story.md (`STORY=path` picks the file). It draws with [scripts/shadow.py](./scripts/shadow.py):

| Function | What it draws |
|---|---|
| `screen(c, t, tint, ta)` | Lamp-lit cloth with a woven texture and a row of flickering oil lamps; optional coloured light |
| `frame(c, t)` | The black cloth band below (captions go here), side posts, top border |
| `puppet(c, x, spec, pose, face, near, far, lean, nod, bob, held, rods)` | A profile puppet with perforations, rivets, and body, head and hand rods |
| `ganesha(...)`, `SARA` + `veena`, `sc_invoc(c, t, left_cast, right_cast)` | The invocation |
| `tree`, `hut`, `lampstand`, `dais`, `bush` | Flat cut-out scenery |
| `lamp_dip(c, t, cuts)`, `draw_ink(...)` | Scene-change dip; title text inked onto the cloth |

Specs are dicts (`skin, low, border, gold, sash, thread, hair='shikha'|'bun'|'jata'|'crop', crown, divine, tilak, bindi, beard, mous, band, fem, top`). Heroes such as Rama and Krishna take blue skin; women tend to yellow or orange tones.

Poses, as (near arm, far arm) in degrees: hanging `(12,14) (-14,10)`; joined hands `ANJ`; pointing `(112,6)`; blessing `(124,26)`; hand to chest `(28,150)`; startled `(118,44) (108,56)`; speaking `(72, 52 + 24*sin(t*2.6))`. Walk with `bob=hop(t)`; ease between poses with `mixa(a, b, eio(u, t0, t1))`.

### 4. Check
Contact sheet at every beat including the invocation (1, 4, 6, 10.5, 13 s). Look for puppets colliding during bows, props crossing faces, and captions per script at full size.

### 5. Score and render
```bash
python3 scripts/score_shadow.py --prologue 14 --duration 146 --out score.wav --quiet 17.5-25 --cuts 25,47,55 --hits 17.9
```
```bash
python3 scripts/render_chunks.py plan my_play.py          # prints chunk commands (~1300 frames each)
python3 scripts/render_chunks.py chunk my_play.py 0 1300 part_00.mp4
python3 scripts/render_chunks.py join final.mp4 score.wav part_00.mp4 part_01.mp4 ...
```
Render chunks in the foreground; many sandboxes stop background jobs soon after a turn ends. About 0.35 s per frame on 2 cores.

### 6. QA
```bash
python3 scripts/qa.py final.mp4 --story story.md --out qa
```
Then look at `qa/contact.jpg` and `qa/opening.jpg` and answer [eval.md](./eval.md), which adds the fidelity checks. Fix or name every "no".

### 7. Voice version (optional)
For a Telugu voice version, write a recording script following [voice-script.md](./references/voice-script.md), ask for the recording first, then retime the film to the voice.

---

## Deliver

The film per language with `qa/report.md`, then a **fidelity note**: what follows the tradition, what departs from it, what was not verified, with links to the sources read. State that the audio is synthetic if it is, and recommend crediting the tradition and working with a practising troupe for anything published.
