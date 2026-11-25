"""Core 2D drawing library for code-drawn animation (skia-python).

Shapes, gradients, glow, articulated hands and arms, expressive eyes and brows,
moods, multi-script shaped text (Indic and Arabic via PIL+raqm), and a scene
renderer with crossfades. Fill FONTS before drawing text; see setup_fonts.py.
"""

import math, random, os, unicodedata, numpy as np, skia
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1920, 1080, 24
LINE = '#2a1530'
# FONTS = {'te': '.../ramabhadra-telugu-400-normal.ttf', 'dev': '.../tiro-devanagari-hindi-devanagari-400-normal.ttf',
#          'ar': '.../vazirmatn-arabic-600-normal.ttf', 'la': '.../noto-serif-telugu-latin-600-normal.ttf'}
FONTS = {}
SCRIPTS = {'te': [(0x0C00, 0x0C7F)], 'kn': [(0x0C80, 0x0CFF)], 'ta': [(0x0B80, 0x0BFF)], 'dev': [(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
           'gur': [(0x0A00, 0x0A7F)], 'bn': [(0x0980, 0x09FF)],
           'ar': [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)]}
RTL = {'ar'}

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ramp(t, a, b): return clamp((t - a) / (b - a)) if b != a else float(t >= a)
def ss(x): x = clamp(x); return x * x * (3 - 2 * x)
def eio(t, a, b): return ss(ramp(t, a, b))
def lerp(a, b, k): return a + (b - a) * k
def hx(h): h = h.lstrip('#'); return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
def mixh(h1, h2, k):
    a, b = hx(h1), hx(h2); k = clamp(k); return '#%02x%02x%02x' % tuple(int(round(lerp(x, y, k))) for x, y in zip(a, b))
def col(h, a=1.0): r, g, b = hx(h); return skia.ColorSetARGB(int(clamp(a) * 255), r, g, b)
def P(h='#000000', a=1.0, stroke=0, blur=0, shader=None, blend=None):
    p = skia.Paint(AntiAlias=True); p.setColor(col(h, a))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke); p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        p.setShader(shader)
        if a < 1: p.setAlphaf(a)
    if blend is not None: p.setBlendMode(blend)
    return p
def lin(x0, y0, x1, y1, stops): return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], [col(h, a) for _, h, a in stops], [s for s, _, _ in stops])
def rad(cx, cy, r, stops): return skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(r, .1), [col(h, a) for _, h, a in stops], [s for s, _, _ in stops])
def oval(cx, cy, rx, ry): p = skia.Path(); p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)); return p
def rrect(l, t, r, b, rr): p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(l, t, r, b), rr, rr)); return p
def poly(pts, close=True):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    if close: p.close()
    return p
def smooth(pts, close=True):  # Catmull-Rom -> cubic
    p = skia.Path(); n = len(pts); p.moveTo(*pts[0])
    for i in (range(n) if close else range(n - 1)):
        p0 = pts[(i - 1) % n] if (close or i > 0) else pts[i]; p1 = pts[i]; p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (close or i + 2 < n) else p2
        p.cubicTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1])
    if close: p.close()
    return p
def ink(c, path, fill, line=LINE, w=4.0, a=1.0, shader=None):
    c.drawPath(path, P(fill, a, shader=shader))
    if w > 0: c.drawPath(path, P(line, 0.85 * a, stroke=w))
def glow(c, x, y, r, h, a):
    if a > 0.002: c.drawCircle(x, y, r, P(blend=skia.BlendMode.kScreen, shader=rad(x, y, r, [(0, h, a), (0.35, h, a * 0.45), (1, h, 0)])))
def ik(sx, sy, tx, ty, l1, l2, bend=1):
    dx, dy = tx - sx, ty - sy; d = max(1e-3, min(math.hypot(dx, dy), l1 + l2 - 0.5)); base = math.atan2(dy, dx)
    a = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    return (sx + l1 * math.cos(base + bend * a), sy + l1 * math.sin(base + bend * a)), (sx + d * math.cos(base), sy + d * math.sin(base))
def blink(t, seed=0.0, period=3.7): ph = (t + seed) % period; return 1 - 0.95 * math.exp(-((ph - 0.08) / 0.05) ** 2)

def capsule(x0, y0, x1, y1, r0, r1=None):
    r1 = r0 if r1 is None else r1
    a = skia.Path(); a.addCircle(x0, y0, r0); b = skia.Path(); b.addCircle(x1, y1, r1)
    u = skia.Op(a, b, skia.PathOp.kUnion_PathOp); dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy)
    if L > 1e-3:
        nx, ny = -dy / L, dx / L
        u = skia.Op(u, poly([(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1), (x1 - nx * r1, y1 - ny * r1), (x0 - nx * r0, y0 - ny * r0)]), skia.PathOp.kUnion_PathOp)
    return u
def union(paths):
    u = paths[0]
    for p in paths[1:]: u = skia.Op(u, p, skia.PathOp.kUnion_PathOp)
    return u
def rot(x, y, a): return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)

FINGERS = {'open': [(10, .24, 25, 5.8), (3.5, .07, 30, 6), (-3.5, -.07, 29, 5.8), (-10, -.24, 22, 5.2)],
           'flat': [(9, .03, 26, 5.4), (3, 0, 30, 5.6), (-3, 0, 29, 5.5), (-9, -.03, 24, 5)],
           'grip': [(10, .35, 10, 6.6), (3.5, .3, 11, 6.8), (-3.5, .25, 11, 6.6), (-10, .2, 9, 6)],
           'pinch': [(10, .2, 22, 5.8), (3.5, .75, 11, 6.4), (-3.5, .7, 10, 6.2), (-10, .65, 9, 5.8)]}
THUMB = {'open': (1.0, 23), 'flat': (.42, 20), 'grip': (.15, 22), 'pinch': (.62, 31)}
PINCH_OFF = (50, 25)   # held object's centre in hand space for 'pinch'
def hand(c, wx, wy, ang, pose='open', ts=1, hs=1.0, skin='#c88a5c', w=3.6, held=None):
    """Wrist at (wx,wy); fingers point along ang (radians); thumb on local +y when ts=1. held(c,x,y) draws a pinched object."""
    c.save(); c.translate(wx, wy); c.rotate(math.degrees(ang)); c.scale(hs, hs * ts)
    parts = [capsule(-10, 0, 8, 0, 11, 13), rrect(2, -17, 38, 17, 14)]; fs = FINGERS[pose]
    for by, a, L, r in fs: parts.append(capsule(31, by, 31 + L * math.cos(a), by + L * math.sin(a), r, r * .92))
    ink(c, union(parts), skin, w=w)
    for i in range(3):
        b1, a1, L1, _ = fs[i]; b2, a2, L2, _ = fs[i + 1]; mb, ma = (b1 + b2) / 2, (a1 + a2) / 2; ml = min(L1, L2) * (.75 if pose in ('open', 'flat') else .9)
        c.drawPath(poly([(30, mb), (30 + ml * math.cos(ma), mb + ml * math.sin(ma))], close=False), P(LINE, .7, stroke=2.2))
    if held: held(c, *PINCH_OFF)
    ta, tl = THUMB[pose]; ink(c, capsule(12, 12, 12 + tl * math.cos(ta), 12 + tl * math.sin(ta), 7.2, 6.2), skin, w=w)
    c.restore()
def wrist_for(px, py, ang, ts=1, hs=1.0, off=PINCH_OFF):  # where the wrist goes so a pinched object lands on (px,py)
    dx, dy = rot(off[0] * hs, off[1] * hs * ts, ang); return px - dx, py - dy
def arm(c, S, Wt, sleeve, L1, L2, bend=1, elbow=None, r=(25, 21, 16), cuff=None):
    E, Wr = (elbow, Wt) if elbow else ik(S[0], S[1], Wt[0], Wt[1], L1, L2, bend)
    ink(c, union([capsule(*S, *E, r[0], r[1]), capsule(*E, *Wr, r[1], r[2])]), sleeve)
    dx, dy = Wr[0] - E[0], Wr[1] - E[1]; L = math.hypot(dx, dy) or 1; ux, uy = dx / L, dy / L
    if cuff: ink(c, capsule(Wr[0] - ux * 12, Wr[1] - uy * 12, Wr[0] - ux * 2, Wr[1] - uy * 2, r[2] + 3, r[2] + 3), cuff, w=3)
    return E, Wr, math.atan2(uy, ux)

# moods: eye = openness, tilt = +anger/-sadness, low = lower lid, happy = closed ^ eyes, pup = pupil scale
MOODS = {'smile': dict(tilt=0, raise_=0, curve=.8, open_=0, eye=1, happy=0, pup=1, low=.12),
         'frown': dict(tilt=1, raise_=-4, curve=-.8, open_=0, eye=.85, happy=0, pup=1, low=.12),
         'smug': dict(tilt=.35, raise_=0, curve=.7, open_=0, eye=.45, happy=0, pup=1, low=.32),
         'shock': dict(tilt=-.6, raise_=14, curve=0, open_=1, eye=1.15, happy=0, pup=.65, low=0),
         'sad': dict(tilt=-.9, raise_=6, curve=-.6, open_=0, eye=.7, happy=0, pup=1, low=0),
         'warm': dict(tilt=-.35, raise_=4, curve=1, open_=.6, eye=.9, happy=0, pup=1, low=.28),
         'serene': dict(tilt=-.05, raise_=4, curve=.6, open_=0, eye=.78, happy=0, pup=1, low=.18),
         'joy': dict(tilt=-.3, raise_=5, curve=1, open_=.5, eye=0, happy=1, pup=1, low=0)}
def mood_at(t, keys, dur=0.45):  # keys: [(time, mood_name), ...]
    cur = MOODS[keys[0][1]]
    for tk, mname in keys[1:]:
        if t < tk: break
        k = ss((t - tk) / dur); cur = {kk: lerp(cur[kk], MOODS[mname][kk], k) for kk in cur}
    return cur
def eye3(c, ex, ey, rx, ry, m, bl=1.0, gaze=(0, 0), inner=1, skin='#c88a5c', iris='#4a2a18', lash=6.0):
    """inner = x-direction of the inner corner; gaze in [-1,1]^2."""
    op = clamp(m['eye'] * bl, 0, 1.2)
    if m['happy'] > .5:
        p = skia.Path(); p.moveTo(ex - rx, ey + 4); p.quadTo(ex, ey - ry * 1.2, ex + rx, ey + 4); c.drawPath(p, P(LINE, 1, stroke=lash)); return
    big = 1 + .15 * max(0, op - 1); erx, ery = rx * big, ry * big; shape = oval(ex, ey, erx, ery)
    c.drawPath(shape, P('#fffaf2')); c.save(); c.clipPath(shape, skia.ClipOp.kIntersect, True)
    ix, iy = ex + gaze[0] * erx * .42, ey + gaze[1] * ery * .36; ir = erx * .66
    c.drawCircle(ix, iy, ir, P(iris)); c.drawCircle(ix, iy, ir * .5 * m['pup'], P('#120808')); c.drawCircle(ix - ir * .32, iy - ir * .36, ir * .24, P('#ffffff', .95))
    lid = clamp(1 - op); k = m['tilt'] * .32 * inner; ly = ey - ery * 1.02 + lid * 2.05 * ery; lidc = mixh(skin, '#000000', .12)
    X0, X1 = ex - erx * 1.6, ex + erx * 1.6
    edge = skia.Path(); edge.moveTo(X0, ly + (X0 - ex) * k); edge.quadTo(ex, ly - ery * .35 * (1 - lid), X1, ly + (X1 - ex) * k)
    reg = skia.Path(edge); reg.lineTo(X1, ey - ery * 3); reg.lineTo(X0, ey - ery * 3); reg.close(); c.drawPath(reg, P(lidc))
    if m.get('low', 0) > .01:
        yl = ey + ery * (1.05 - m['low'] * 1.1); lp = skia.Path(); lp.moveTo(X0, ey + ery * 3); lp.lineTo(X0, yl + ery * .2)
        lp.quadTo(ex, yl - ery * .25, X1, yl + ery * .2); lp.lineTo(X1, ey + ery * 3); lp.close(); c.drawPath(lp, P(lidc))
    c.restore(); c.drawPath(shape, P(LINE, .75, stroke=2.4))
    c.save(); c.clipPath(oval(ex, ey, erx + 2.5, ery + 2.5), skia.ClipOp.kIntersect, True); c.drawPath(edge, P(LINE, 1, stroke=lash)); c.restore()
def brow3(c, ex, ey, rx, ry, m, inner=1, w=11, h='#1b1012'):
    y = ey - ry - 9 - m['raise_']; tilt = m['tilt'] * 9; xi, xo = ex + inner * rx * 1.05, ex - inner * rx * 1.15
    yi, yo = y + tilt, y - tilt * .35; mx, my = (xi + xo) / 2, (yi + yo) / 2 - 5
    c.drawPath(union([capsule(xi, yi, mx, my, w * .55, w * .47), capsule(mx, my, xo, yo, w * .47, w * .26)]), P(h))

def moon(c, x, y, r, phase=1.0, side=1, sky_h='#141c4c', glow_a=1.0):  # side=1 waning (shadow from right), -1 waxing
    g = glow_a * (.25 + .75 * phase ** .8); glow(c, x, y, r * 4.2, '#8fa2e8', .32 * g); glow(c, x, y, r * 2, '#f6efd2', .45 * g)
    c.drawCircle(x, y, r, P(shader=rad(x - r * .3, y - r * .3, r * 1.4, [(0, '#fffbea', 1), (.7, '#f5e8bd', 1), (1, '#e3cf98', 1)])))
    for dx, dy, cr in [(-.35, -.2, .18), (.25, .3, .22), (.1, -.45, .1), (-.2, .42, .12)]: c.drawCircle(x + dx * r, y + dy * r, cr * r, P('#c9b47e', .22))
    if phase < .999:
        c.save(); c.clipPath(oval(x, y, r + .5, r + .5), skia.ClipOp.kIntersect, True)
        c.drawCircle(x + 2.05 * r * phase * side, y, r * 1.02, P(mixh(sky_h, '#0a0f2e', .4), .94)); c.restore()

# ---- multi-script text: script runs, one font per script, two-level bidi for RTL lines (tested: Telugu, Devanagari, Persian, mixed credits)
def script_of(ch):
    o = ord(ch)
    for name, ranges in SCRIPTS.items():
        if any(a <= o <= b for a, b in ranges): return name
    if ch in '': return None                      # joiners stay inside the current run
    if unicodedata.category(ch)[0] in 'PSZ': return 'neu'     # punctuation, symbols, spaces
    return 'la'
_TXT = {}
def text_img(s, size, h='#fff4dc', shadow=.75):
    key = (s, size, h, shadow)
    if key in _TXT: return _TXT[key]
    runs = []
    for ch in s:
        kind = script_of(ch)
        if kind is None: kind = runs[-1][0] if runs else 'neu'
        if runs and runs[-1][0] == kind: runs[-1] = [kind, runs[-1][1] + ch]
        else: runs.append([kind, ch])
    sdir = lambda k: None if k == 'neu' else ('r' if k in RTL else 'l')
    strong = [sdir(k) for k, _ in runs if k != 'neu']; base_dir = strong[0] if strong else 'l'
    dirs = []
    for i, (k, _) in enumerate(runs):   # neutrals take the direction around them, else the line's direction
        if k != 'neu': dirs.append(sdir(k)); continue
        prv = next((sdir(q) for q, _ in reversed(runs[:i]) if q != 'neu'), None)
        nxt = next((sdir(q) for q, _ in runs[i + 1:] if q != 'neu'), None)
        dirs.append(prv if prv == nxt and prv else base_dir)
    main = next((k for k, _ in runs if k not in ('neu', 'la')), 'la')
    fk = lambda k: 'la' if k == 'neu' else k
    fonts = {f: ImageFont.truetype(FONTS[f], int(size * (.9 if (f == 'la' and main != 'la') else 1)), layout_engine=ImageFont.Layout.RAQM) for f in set(fk(k) for k, _ in runs)}
    items = [(fk(k), t_, d) for (k, t_), d in zip(runs, dirs)]
    other = 'l' if base_dir == 'r' else 'r'; seq = items[::-1] if base_dir == 'r' else items[:]; vis, blk = [], []
    for it in seq:
        if it[2] == other: blk.append(it)
        else: vis += blk[::-1]; blk = []; vis.append(it)
    vis += blk[::-1]
    widths = [fonts[f].getlength(t_, direction='rtl' if d == 'r' else 'ltr') for f, t_, d in vis]
    asc = max(f.getmetrics()[0] for f in fonts.values()); desc = max(f.getmetrics()[1] for f in fonts.values()); pad = int(size * .6)
    base = Image.new('L', (int(sum(widths)) + 2 * pad, asc + desc + 2 * pad), 0); d_ = ImageDraw.Draw(base); xx = pad
    for (f, t_, d), wd in zip(vis, widths):
        d_.text((xx, pad + asc), t_, font=fonts[f], fill=255, anchor='ls', direction='rtl' if d == 'r' else 'ltr'); xx += wd
    fa = np.asarray(base, np.float32) / 255
    sh = np.roll(np.asarray(base.filter(ImageFilter.GaussianBlur(size * .12)), np.float32) / 255 * shadow, (int(size * .05), int(size * .03)), (0, 1))
    a = fa + sh * (1 - fa); out = np.zeros(fa.shape + (4,), np.float32); cr = hx(h)
    for i in range(3): out[..., i] = cr[i] * fa / np.maximum(a, 1e-4)
    out[..., 3] = a * 255
    _TXT[key] = skia.Image.fromarray(np.ascontiguousarray(out.clip(0, 255).astype(np.uint8)), colorType=skia.kRGBA_8888_ColorType)
    return _TXT[key]
def draw_text(c, s, size, cx, cy, h='#fff4dc', a=1.0):
    if a <= .01: return
    img = text_img(s, size, h); p = skia.Paint(AntiAlias=True); p.setAlphaf(clamp(a))
    c.drawImage(img, cx - img.width() / 2, cy - img.height() / 2, skia.SamplingOptions(skia.FilterMode.kLinear), p)

def warp(t, knots):  # knots [(film_t, story_t), ...]; slope 1 outside
    if t <= knots[0][0]: return knots[0][1] - (knots[0][0] - t)
    for (a, oa), (b, ob) in zip(knots, knots[1:]):
        if t <= b: return lerp(oa, ob, (t - a) / (b - a))
    return knots[-1][1] + (t - knots[-1][0])

# SEGS = [(start, end, scene_fn, camera_fn(t)->(zoom,cx,cy)), ...]
def render(t, SEGS, overlays=()):
    surf = skia.Surface(W, H); c = surf.getCanvas(); c.clear(skia.ColorBLACK)
    active = [s for s in SEGS if s[0] <= t < s[1]]
    for i, (a, b, fn, cf) in enumerate(active):
        if i > 0: c.saveLayerAlpha(None, int(255 * eio(t, a, a + 1.0)))
        c.save(); z, cx, cy = cf(t); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-cx, -cy); fn(c, t); c.restore()
        if i > 0: c.restore()
    for ov in overlays: ov(c, t)
    return surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
