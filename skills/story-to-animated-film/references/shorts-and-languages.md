# Vertical Shorts and Language Versions

## Vertical shorts (9:16)

1. **Split at natural story breaks** into 3–5 parts of 25–55 s. Each must make sense alone.
2. **Recompose, don't crop.** Reuse the scene functions; render at 1080×1920 with a camera per scene:
   ```python
   CAMS = {'forest': cam_keys([(0, 1.5, 800, 640), (12, 1.5, 800, 640), (14.5, 1.62, 790, 640)]), ...}
   # inside render: c.translate(VW/2, VH/2); c.scale(z, z); c.translate(-cx, -cy); scene_fn(c, t)
   ```
   Zoom 1.3–1.6, centred on the speaker; pan between speakers who can't fit in the frame together. Keep the ground line inside the frame: a figure's feet cut off at the bottom edge looks wrong.
3. **Captions in the top third**, clear of the platform buttons at the bottom. Wrap by measured pixel width with the real font, not by character count:
   ```python
   f = ImageFont.truetype(font_path, size, layout_engine=ImageFont.Layout.RAQM)
   # add words to a line while f.getlength(line) <= max_width
   ```
4. **Cards.** A 2.5 s title card ("Part N of M"), a small header after it, and a 4.5 s closing card with a one-line takeaway and "Next: <next part's title>". The last part ends on the source credit instead.
5. **Audio.** Cut each part's audio from the master score at the same times (`ffmpeg -ss <t0> -t <dur> -i score.wav`), with a short fade in and out, then loudness-normalise.

## Language versions

- Read the language once at import (`LANG = os.environ.get('FILM_LANG', 'en')`) and keep a caption table and card strings per language. Render one file per language.
- Verses go in the target script (for example Sanskrit in Telugu script for a Telugu version).
- Long lines in Indic scripts run wider than English; wrap by measured width.
- Say that the translation is yours and unproofread, list the word choices a native reader should check, and recommend a proofread before publishing.
