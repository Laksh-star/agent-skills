# Gotchas & Fixes

Real failure modes hit while making a 2.5-minute shadow play, in English and Telugu.

---

## 1. Drawn from memory, audited afterwards
- **Symptom:** The first version had no invocation, no head rods and characters entering from any side. The person who commissioned it asked, rightly, what had been done to be true to the form: the answer was "nothing beyond general knowledge".
- **Fix:** Read sources before designing (Rule 1 in SKILL.md), and keep the departures list as you go. The invocation, head rod and entrance rules all came from one source read afterwards.

## 2. Bows bring puppets into each other
- **Symptom:** A bow rotates the whole puppet about its feet, so the head travels far forward and lands on the figure being bowed to.
- **Fix:** Keep `lean` at 26° or less, add `nod` for the rest, and leave about 300 px between the bowing puppet and whoever it bows to.

## 3. Rendering twice as slow as it should be
- **Symptom:** 0.7 s per frame.
- **Cause:** Unbounded `saveLayer(None, paint)` for every cut-out.
- **Fix:** Every `puppet()`, `layer()` and prop passes a bounding rectangle (already done in `shadow.py`; keep it so in new props).

## 4. Overlapping cut-outs change colour
- **Symptom:** A puppet behind a tree turns muddy green.
- **Cause:** Multiply blending, as with real translucent leather.
- **Fix:** True to the medium, so keep it, but don't park a puppet behind scenery for a whole scene.

## 5. Long held props read as sticks across the screen
- **Symptom:** Saraswati's veena stuck out horizontally beyond her body like a pole.
- **Fix:** Angle long props down (−30°) into the silhouette and keep the holding arm close to the body.

## 6. Background render stopped partway
- **Symptom:** The Telugu render stopped at frame 1800 of 3840 with no error.
- **Fix:** Render in foreground chunks of about 1300 frames and join them losslessly (`scripts/render_chunks.py`).

## 7. Invocation music pushes the story score out of sync
- **Fix:** `score_shadow.py` makes the prologue audio 0.6 s longer than the prologue picture and crossfades over that 0.6 s, so the story music starts exactly at the cut.
