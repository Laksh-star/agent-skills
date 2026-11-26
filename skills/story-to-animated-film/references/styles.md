# Animation Styles

Offer these when asking the style question, each with its one-line description, and list the one you recommend for this source first.

| Style | Looks like | Best for | Built with |
|---|---|---|---|
| **Storybook 2D** | Warm, rounded characters with expressive faces, painted backgrounds | Children's tales, parables, explainers | `scripts/rig.py` on `scripts/core.py` |
| **Tholu Bommalata shadow play** | Translucent jewel-coloured leather puppets on a lamp-lit cloth, profile faces, visible rods | Indian epics, Puranic and folk stories, Telugu audiences | the `tholu-bommalata-shadow-play` skill in this repo (invocation, fidelity check, list of departures); this skill still runs intake, story bible, shorts and languages |
| **Silhouette theatre** | Flat dark figures against skies that change colour with the mood | Short, solemn or dramatic pieces; flashbacks inside another style | the rig's poses drawn as single-colour shapes; less tested, so show a still early |
| **Another folk-art style** (Kalamkari, Pattachitra, Madhubani, Warli…) | Flat painted panels in that tradition's line and palette | Stories tied to that region or tradition | a new build: read two sources on the tradition's conventions first, ask for reference images, warn that it takes longer |
| **Prompt pack only** | Whatever an image + video model can do, at higher polish | Client or brand films where finish matters more than control | no film rendered; the prompt pack, plus a code-drawn animatic if wanted |

## Choosing the recommendation

- Sacred, epic or Indian folk material, especially for a Telugu audience → shadow play.
- Children, or a general explainer → storybook.
- A very short, solemn piece → silhouette.
- A commercial brief with a budget for generative tools → prompt pack.

## Storybook rig: quick reference

`person(c, x, y, s, spec, pose, L=..., R=..., mood=..., gaze=..., t=t, fx=..., flip=..., talk=..., bob=..., lean=..., skipL=...)`

- `spec`: `dict(skin, low, top?, sash?, thread?, hair='shikha'|'short'|'bun', hairc, beard?, mous?, band?, tilak?, bindi?, fem?)`
- Arms: start from a named gesture, then adjust: `L, R = gesture('chest', 'speak')`, or one arm `R = gesture('bless', side=1)`. Gestures: rest (pose-aware: hanging, hands on knees, hands on thighs), chest, speak, offer, raise, bless, point, akimbo, lap, knee. Animate by easing the target: `R = dict(gesture('speak', side=1), p=(96, -50 + 10*sin(t*2.4)))`.
- How the arm is solved: the upper arm hangs at the side and the forearm comes toward the viewer whenever the hand is near; for far or high hands the elbow takes the lower side and never folds in across the body. Elbows go out only on request (`elbow='out'`, as in akimbo). The wrist follows the forearm and bends at most 70 degrees. `behind=True` draws an arm behind the body.
- Check arms with `scripts/pose_sheet.py` (every pose × gesture at full size) and `scripts/pose_check.py film.py` (every 0.5 s: reach, elbow fold, wrist).
- Joined hands: `L, R = anjali()`.
- Walking: move `x` while `bob = sin(t*9)*5`.
- Moods: serene, warm, smile, frown, shock, sad, smug, joy; switch with `mood_at(u, [(0, 'serene'), (4.5, 'frown')])`.
- `skipL=True` leaves the left arm out so you can draw it after another figure (a hand resting on someone's head).

## Silhouette theatre

Use the same poses but fill every shape in one dark colour (no faces, no outlines) against a sky gradient that shifts with the story: indigo night, red for conflict, gold for resolution. Add a vignette. It reads best for short sequences and flashbacks.
