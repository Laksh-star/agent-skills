#!/usr/bin/env python3
"""A minimal, runnable shadow play: the invocation, then two scenes and captions.
Copy it, keep the structure, replace the cast and scenes. Timings and captions come from story.md
(pass another with STORY=path).

    FONTS_DIR=/path/from/setup_fonts FILM_LANG=en python3 template_shadow.py sheet.jpg 1 4 10 16 22 30
writes a contact sheet. Render the whole play with render_chunks.py in this folder.

Blocking rules from the tradition: divinities enter from the audience's right (screen right),
other characters from the audience's left; the lamps dip at every scene change.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from shadow import *
from story import load

FD = os.environ.get('FONTS_DIR', 'fonts')
core.FONTS.update({k: os.path.join(FD, f'{k}.ttf') for k in ('la', 'te', 'dev') if os.path.exists(os.path.join(FD, f'{k}.ttf'))})
LANG = os.environ.get('FILM_LANG', 'en')
STORY = load(os.environ.get('STORY', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'story.md')))
PRO = STORY.header('Prologue')                                  # invocation length
S1, S2 = (STORY.scene_starts[k] for k in ('forest', 'hut'))     # story time: begins when the prologue ends
DUR = STORY.header('Duration'); SD = DUR - PRO

SAGE = dict(skin='#d99a5a', low='#e8731e', border='#7a2a14', sash='#e8731e', hair='jata', beard='#3a2418', gold='#8a4a22')
PRINCE = dict(skin='#3f6fc4', low='#e8b21e', border='#b3200f', sash='#fff3d6', thread=True, hair='shikha', crown=True, gold=G)   # Rama/Krishna-type heroes are blue
WOMAN = dict(skin='#e2975a', low='#b3200f', border='#1f6b4a', top='#1f6b4a', fem=True, hair='bun', bindi=True, gold=G)
CAST_L, CAST_R = (PRINCE, WOMAN, SAGE), (SAGE, WOMAN, PRINCE)

def sc_forest(c, t):
    u = t - S1
    tree(c, 420, t, .9, False)
    ent = eio(u, .5, 2.6); greet = eio(u, 3.0, 3.8)
    puppet(c, lerp(-260, 700, ent), PRINCE, near=mixa((12, 14), ANJ[0], greet), far=mixa((-14, 10), ANJ[1], greet),
           lean=12 * greet, nod=10 * greet, bob=hop(t, ent < 1))
    puppet(c, 1460, SAGE, 'sit', face=-1, near=mixa((50, 80), (124, 26), eio(u, 4.2, 5.0)), far=(24, 60), nod=3 * sin(t * 2.6) * (5 < u < 8))

def sc_hut(c, t):
    u = t - S2
    hut(c, 1100); lampstand(c, 960, t)
    ent = eio(u, .4, 2.4); speak = 2.8 < u < 7.5
    puppet(c, lerp(-240, 440, ent), WOMAN, near=(72, 52 + (24 * sin(t * 2.6) if speak else 0)), far=(-14, 10), bob=hop(t, ent < 1))

SCENES = [(S1, sc_forest), (S2, sc_hut)]
CAPS = {lang: STORY.captions(lang) for lang in STORY.languages()}
PCAPS = {lang: STORY.captions(lang, 'prologue') for lang in STORY.languages()}

def caption(c, t, table):
    for a, b, lines in table:
        if a - .2 <= t <= b + .3:
            al = eio(t, a - .1, a + .35) * (1 - eio(t, b - .25, b + .15))
            for i, ln in enumerate(lines):
                verse = '।' in ln or '॥' in ln
                draw_text(c, ln, 46 if verse else 44, W / 2, 962 + i * 62, '#ffd98a' if verse else '#fff1d6', al)

def render(T):
    surf = skia.Surface(W, H); c = surf.getCanvas()
    if T < PRO:
        screen(c, T); sc_invoc(c, T, CAST_L, CAST_R); frame(c, T)
        lamp_dip(c, T, [0, PRO], width=1.0)
        caption(c, T, PCAPS[LANG])
    else:
        t = T - PRO
        screen(c, t)
        [f for s, f in SCENES if s <= t][-1](c, t)
        if t < 4: draw_ink(c, {'en': 'A Shadow Play', 'te': 'తోలుబొమ్మలాట'}[LANG], 120, 1460, 330, eio(t, .6, 1.4) * (1 - eio(t, 3.0, 3.8)))
        frame(c, t)
        lamp_dip(c, t, [s for s, _ in SCENES] + [SD])
        caption(c, t, CAPS[LANG])
    k = 1 - eio(T, 0, .8) + eio(T, DUR - 1.0, DUR - .1)
    if k > 0: c.drawRect(skia.Rect.MakeWH(W, H), P('#000000', k))
    return surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)

if __name__ == '__main__':
    from PIL import Image
    ts = [float(x) for x in sys.argv[2:]]
    ims = [Image.fromarray(render(t)[..., :3]).resize((640, 360)) for t in ts]
    sheet = Image.new('RGB', (4 * 640, ((len(ims) + 3) // 4) * 360))
    for i, im in enumerate(ims): sheet.paste(im, ((i % 4) * 640, (i // 4) * 360))
    sheet.save(sys.argv[1])
