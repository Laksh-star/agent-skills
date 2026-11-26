#!/usr/bin/env python3
"""A minimal, runnable story film: two scenes, two characters, captions, a title and an end card.
Copy it, keep the structure, replace the scenes.

    FONTS_DIR=/path/from/setup_fonts FILM_LANG=en python3 template_film.py sheet.jpg 2 6 10 14 18
writes a contact sheet of those times. Render the whole film with render_chunks.py.

Structure (timings and captions come from story.md; pass another with STORY=path):
  T*      scene start times (film seconds)
  SEGS    (start, end, scene_fn, camera_fn); overlapping by 1.2 s crossfades the scenes
  CAPS    {lang: [(start, end, [line1, line2]), ...]}
  render(t) -> RGBA numpy frame
Scene functions work in local time u = t - T*; poses ease with eio(u, a, b);
idle life (blinks, sway, mouth flaps) runs on t so holds never freeze.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from core import *
from rig import person, anjali, cam, cam_keys, pi
from story import load

FD = os.environ.get('FONTS_DIR', 'fonts')
core.FONTS.update({k: os.path.join(FD, f'{k}.ttf') for k in ('la', 'te', 'dev') if os.path.exists(os.path.join(FD, f'{k}.ttf'))})
LANG = os.environ.get('FILM_LANG', 'en')
STORY = load(os.environ.get('STORY', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'story.md')))
W, H, FPS = 1920, 1080, 24
T1, T2, T3 = (STORY.scene_starts[k] for k in ('meet', 'lesson', 'end'))   # timings live in story.md
DUR = STORY.header('Duration')

SAGE = dict(skin='#c2936c', low='#faf6ec', sash='#e8a23a', thread=True, hair='short', hairc='#e9e6e0', beard='#efece6')
GIRL = dict(skin='#c98d5e', low='#c2413a', top='#2f7a6a', fem=True, hair='bun', hairc='#1b1012', bindi=True)

def sky(c, top, mid, bot, hy=700):
    c.drawRect(skia.Rect.MakeLTRB(-200, -200, W + 200, H + 200), P(shader=lin(0, 0, 0, hy, [(0, top, 1), (.6, mid, 1), (1, bot, 1)])))

def ground(c, y, c1, c2):
    c.drawRect(skia.Rect.MakeLTRB(-200, y, W + 200, H + 200), P(shader=lin(0, y, 0, H, [(0, c1, 1), (1, c2, 1)])))

def sc_meet(c, t):
    u = t - T1
    sky(c, '#f6c98a', '#f9e2b4', '#e9f0c8', 760); glow(c, 1480, 260, 420, '#ffe2a0', .5); ground(c, 800, '#7fae62', '#5d8e4c')
    walk = eio(u, 1.0, 4.5)
    person(c, lerp(-150, 640, walk), lerp(980, 960, walk), 1.0, GIRL, 'stand', mood='serene', gaze=(.9, 0), t=t, fx=.8,
           bob=math.sin(t * 9) * 5 * (0 < walk < 1), seed=2.1)
    greet = eio(u, 5.0, 5.8); Lh, Rh = anjali()
    person(c, 1260, 960, 1.0, SAGE, 'sit', mood=mood_at(u, [(0, 'serene'), (5.2, 'warm')]), gaze=(-.9, 0), t=t, fx=-.7, flip=True,
           L=Lh if greet > .5 else None, R=Rh if greet > .5 else None, talk=.8 * (6 < u < 9.5), seed=.4)

def sc_lesson(c, t):
    u = t - T2
    sky(c, '#2a1c3a', '#5a2f3a', '#b9713c', 1080); glow(c, 960, 1180, 900, '#ffb44a', .5); ground(c, 860, '#5a3420', '#3a2014')
    point = eio(u, 2.0, 2.8)
    person(c, 1260, 960, 1.0, SAGE, 'sit', mood='warm', gaze=(-.9, 0), t=t, fx=-.7, flip=True, talk=.8 * (1 < u < 8), seed=.4,
           R=dict(p=(lerp(76, 120, point), lerp(0, -150, point)), a=lerp(pi * .38, -pi * .2, point), pose='open', ts=-1))
    person(c, 640, 980, 1.0, GIRL, 'stand', mood=mood_at(u, [(0, 'serene'), (5, 'joy')]), gaze=(.9, -.1), t=t, fx=.8, seed=2.1)

def sc_end(c, t):
    u = t - T3; sky(c, '#2a1c3a', '#5a2f3a', '#b9713c', 1080)
    a = eio(u, .6, 1.8)
    draw_text(c, END[LANG][0], 64, 960, 430, '#ffe9a8', a)
    draw_text(c, END[LANG][1], 40, 960, 530, '#fff4dc', eio(u, 1.6, 2.6))

SEGS = [
    (T1, T2 + 1.2, sc_meet, cam_keys([(0, 1.0, 960, 540), (5, 1.0, 960, 540), (9, 1.12, 960, 600)])),
    (T2, T3 + 1.2, sc_lesson, cam(T2, T3 + 1.2, 1.0, 1.08, (960, 540), (900, 600))),
    (T3, DUR + 1, sc_end, cam(T3, DUR, 1.0, 1.0)),
]
TITLE = {'en': ['The Quiet Teacher', 'a template story'], 'te': ['మౌన గురువు', 'ఒక నమూనా కథ']}
END = {'en': ['Listening is the first lesson.', 'Source: your text, chapter and verse'], 'te': ['వినడమే మొదటి పాఠం.', 'మూలం: మీ గ్రంథం, అధ్యాయం']}
CAPS = {lang: STORY.captions(lang) for lang in STORY.languages()}

def captions(c, t):
    for a, b, lines in CAPS[LANG]:
        if a - .2 <= t <= b + .3:
            al = eio(t, a - .1, a + .35) * (1 - eio(t, b - .25, b + .15))
            if al <= 0: continue
            c.drawRect(skia.Rect.MakeLTRB(0, H - 250, W, H), P(shader=lin(0, H - 250, 0, H, [(0, '#140a10', 0), (.45, '#140a10', .62 * al), (1, '#140a10', .82 * al)])))
            y0 = H - 100 - (len(lines) - 1) * 32
            for i, ln in enumerate(lines): draw_text(c, ln, 50, W / 2, y0 + i * 64, '#fff4dc', al)

def title(c, t):
    a = eio(t, .4, 1.2) * (1 - eio(t, 3.8, 4.8))
    if a <= 0: return
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), P('#1a0f14', .45 * a))
    draw_text(c, TITLE[LANG][0], 120, 960, 470, '#ffe9a8', a); draw_text(c, TITLE[LANG][1], 44, 960, 590, '#fff4dc', a)

def fades(c, t):
    k = 1 - eio(t, 0, .8) + eio(t, DUR - 1.2, DUR - .1)
    if k > 0: c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), P('#000000', k))

def render(t):
    return core.render(t, SEGS, overlays=(captions, title, fades))

if __name__ == '__main__':
    from PIL import Image
    ts = [float(x) for x in sys.argv[2:]]
    ims = [Image.fromarray(render(t)[..., :3]).resize((640, 360)) for t in ts]
    sheet = Image.new('RGB', (4 * 640, ((len(ims) + 3) // 4) * 360))
    for i, im in enumerate(ims): sheet.paste(im, ((i % 4) * 640, (i // 4) * 360))
    sheet.save(sys.argv[1])
