# Gotchas & Fixes

Real failure modes hit while making a 2.5-minute film, four vertical shorts and a second-language version from a 50-page scripture PDF.

---

## 1. Hand slices through another character's head
- **Symptom:** A blessing hand meant to rest on a bowed head cuts across the face instead. Invisible on a 640-pixel contact sheet; obvious at full size.
- **Cause:** The hand was placed at fixed coordinates while the other figure's bow moved the head; and the arm was drawn before the head, so the head painted over half of it.
- **Fix:** Compute the target from the other figure's actual pose each frame (the crown of a bowed head is `x + r*sin(lean), y − r*cos(lean)`). Draw the touching arm last: `person(..., skipL=True)`, then `arm()` and `hand()` after the other figure. Check every contact moment with a full-resolution crop.

## 2. Background render killed partway
- **Symptom:** A 20-minute render started in the background stopped at frame 1800 of 3840; no error.
- **Cause:** The agent sandbox stopped background processes a few minutes after the turn ended.
- **Fix:** Render in foreground chunks of ~1300 frames (under 10 minutes each) and join losslessly: `scripts/render_chunks.py plan | chunk | join`. Check frames either side of each join for a hitch.

## 3. Rendering twice as slow as it should be
- **Symptom:** 0.7 s per frame instead of 0.35.
- **Cause:** `canvas.saveLayer(None, paint)` allocates a full-frame layer for every cut-out.
- **Fix:** Always pass a bounding rectangle: `c.saveLayer(skia.Rect.MakeLTRB(x0, y0, x1, y1), paint)`.

## 4. Diacritics render as boxes
- **Symptom:** "Vyādha Gītā" shows boxes for ā and ī.
- **Cause:** Font packages split Latin into `latin` and `latin-ext` subsets; the base file lacks the extended letters.
- **Fix:** Merge the two subsets with `fontTools.merge.Merger` (`scripts/setup_fonts.py la` does this).

## 5. Front-facing characters can't bow
- **Symptom:** A deep `lean` reads as tipping sideways, and bowing figures run into whoever they bow to.
- **Fix:** Keep bows small, or switch the pose to a kneel with a modest lean. Leave about 300 px between the bowing figure and the one bowed to.

## 6. Prologue music shifts the story score
- **Symptom:** After adding an opening sequence, the story music drifted 0.6 s early against the picture.
- **Cause:** `acrossfade` overlaps the two files, shortening the total by the crossfade length.
- **Fix:** Make the prologue audio longer than the prologue picture by the crossfade duration.

## 7. Characters enter from nowhere
- **Symptom:** A character is simply present when the scene fades in, which reads as a cut rather than a story beat.
- **Fix:** Block entrances in the story bible (who walks in, from which side) and animate them in the first 2–3 s of the scene.

## 8. Long held props read as sticks across the screen
- **Symptom:** A musical instrument held at the hand extended far beyond the figure.
- **Fix:** Angle long props down into the figure's silhouette and keep the holding arm close to the body.

## 9. Instant percussion attacks become peaks over 0 dB
- **Symptom:** The mixed score measures fine as WAV, but the delivered MP4 shows a true peak near or above 0 dBTP.
- **Cause:** Strokes and bells that start at full level are clicks; the AAC encoder overshoots on them.
- **Fix:** Give every percussion sound a 4 ms attack, target −2 dBTP in the join, and measure the delivered file with `qa.py`, not the WAV.

## 10. Long still stretches nobody notices
- **Symptom:** A seated dialogue held in one wide shot for 15 s or more; on a contact sheet it looks fine.
- **Fix:** `qa.py` flags anything still for 4 s outside the `Holds:` ranges. Cut to a closer shot, push the camera in on the speaker, or bring in a gesture every 2–3 s.

## 11. Splayed elbows and arms that look stuck on
- **Symptom:** Seated figures prop themselves on the floor with elbows out in a "W"; a standing figure meant to look stunned stands with hands on hips; a raised hand crosses the face; arms look bolted to the side of the chest.
- **Cause:** The old rig always bent the elbow outward, its resting hand targets were too close for a straight arm, seated rest put the hands on the floor, and the shoulder had no shape.
- **Fix:** `rig.py` now hangs the upper arm and brings the forearm toward the viewer for near hands, takes the lower elbow for far ones, rests seated hands on the knees, rounds the shoulder into the torso and limits the wrist. Use `gesture()` names, then check with `pose_sheet.py` and `pose_check.py`.

