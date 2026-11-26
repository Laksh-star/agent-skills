# story.md: the single project file

One file holds what the film says and when: headers, a scene table tied to the source, and timed captions per language. The film script reads its timings and captions from it, `qa.py` reads its limits and holds from it, and the prompt pack's shot list can be written from it. Change a caption or a timing here, not in code.

Run `python3 scripts/story.py story.md` after every edit. It exits 1 and lists the problems.

## Headers

| Header | Meaning | Example |
|---|---|---|
| Style | The style the user chose (see styles.md) | `storybook`, `tholu-bommalata` |
| Aspect | `16:9` or `9:16`; qa.py checks the size against it | `16:9` |
| Audience | Who it is for; shapes pace and vocabulary | `children`, `family`, `general` |
| Languages | Caption languages, comma-separated; each needs a `## Captions: <lang>` block | `en, te` |
| Duration | The film's length in seconds (the template uses it as DUR) | `146` |
| Max duration | qa.py fails anything longer (+2 s grace) | `150` |
| Prologue | Shadow play only: invocation length; story time starts after it | `14` |
| Source | The source, with edition | `Mahābhārata, Vana Parva, ed. …` |
| Hook | The question or tension the opening poses, in one line; the ending must answer it | `Can a butcher teach a sage?` |
| Holds | Ranges in film seconds (prologue included) where a still frame is intended, such as title and end cards; qa.py does not fail stillness there | `0-2, 140-146` |

Unknown headers are kept and readable with `S.header('Name')`, so add what your film needs.

## Scenes

```markdown
## Scenes

| id | start | source | origin | beat |
|---|---|---|---|---|
| crane | 0 | Vana Parva 196.1–8 | source | The crane's droppings; Kauśika's angry glance kills it |
| woman | 25 | 196.9–20 | mixed | He begs at a house; the woman makes him wait, then rebukes him |
```

- `id` is how the film script finds the scene (`S.scene_starts['crane']`).
- `start` is in film seconds (in story seconds after the prologue for a shadow play).
- `source` is a chapter, page, verse or timestamp; `origin` is `source`, `invented` or `mixed`. story.py refuses anything else.

## Timed blocks

```markdown
## Captions: en

- 7.3-12.0 | Kauśika, a young Brahmin, sat beneath a tree / reciting the Vedas.
```

- `start-end | line one / line two` (seconds, then up to two lines split by ` / `).
- Any `## <Kind>: <lang>` block is read the same way; the shadow play uses `## Prologue: te` for the invocation's captions (`S.captions('te', 'prologue')`).

story.py checks each block for order, overlaps, more than two lines, and reading speed: over 21 characters a second (vowel signs and other combining marks not counted) is too fast to read.

## Reading it in a film script

```python
from story import load
STORY = load(os.environ.get('STORY', 'story.md'))
T1, T2 = (STORY.scene_starts[k] for k in ('crane', 'woman'))
DUR = STORY.header('Duration')
CAPS = {lang: STORY.captions(lang) for lang in STORY.languages()}
```

Both templates do exactly this; run them with `STORY=path/to/story.md`.
