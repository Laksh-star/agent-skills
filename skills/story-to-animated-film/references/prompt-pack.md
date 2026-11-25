# Prompt Pack

A model-agnostic pack for regenerating the film with an image model and a video model. Clips are 5–10 s; split longer shots. Write it as `<Title>_prompt_pack.md`.

1. **Style bible.** The look in words (never a studio or artist name), the palette as hex values taken from the code, lighting rules, camera language, aspect ratio, 24 fps, and **no text in frame** (captions are added in the edit).
2. **Character sheets.** Age, build, proportions in head-heights, costume with hex colours, hair and marks, expression range. A turnaround prompt (front / three-quarter / profile on a plain background) to generate first and attach as the reference image for every shot. A negative prompt: extra fingers, fused hands, off-model faces, text, logos, photorealism. For a saint or deity, the attributes that must appear.
3. **Environment sheets.** Each location as an empty-plate prompt.
4. **Shot list** table: shot id, film start–end, caption, action, camera, transition.
5. **Per shot.** Keyframe image prompt, motion prompt, end-state description, negative prompt, which reference images to attach.
6. **Assembly.** Cut to the caption timings; burn captions and cards from the code (generated text in video is unreliable, especially in Indic and Arabic scripts); loudness-normalise to −16 LUFS.

Tell the user that character consistency across shots is the main risk with generative video, and that the code-drawn film works as the animatic to cut against.
