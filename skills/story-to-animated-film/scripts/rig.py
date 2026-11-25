"""Storybook character rig: expressive front-facing people built on core.py.

person(c, x, y, s, spec, pose='stand'|'sit'|'kneel', ...) draws a whole figure with
its feet at (x, y). A spec is a dict, e.g.
    dict(skin='#d09a6c', low='#f1e6cf', sash='#e8a23a', thread=True, hair='shikha', hairc='#1b1012', tilak=True)
    dict(skin='#c98d5e', low='#c2413a', top='#2f7a6a', fem=True, hair='bun', hairc='#1b1012', bindi=True)
hair: shikha | short | bun.  Optional: beard, mous, band, thread, sash, tilak, bindi, hairc.
Arms: L/R=dict(p=(x, y) wrist target in body space, a=hand angle, pose=open|flat|grip|pinch, ts=thumb side, held=fn).
"""
import math, skia
from core import *
pi = math.pi

def head(c, cx, cy, sp, m, gaze, t, fx=0, blind=False, talk=0.0, seed=0.0):
    skin = sp['skin']; R = 50; hc = sp.get('hairc', '#1b1012'); st = sp['hair']
    if st == 'bun': ink(c, oval(cx - fx * 34, cy - 40, 27, 25), hc, w=3)
    if st == 'shikha': ink(c, oval(cx - fx * 20, cy - 58, 13, 15), hc, w=3)
    for sx in (-1, 1): ink(c, oval(cx + sx * 49 - fx * 5, cy + 6, 9, 14), mixh(skin, '#7a3a20', .15), w=3)
    hd = smooth([(cx - 48, cy - 8), (cx - 36, cy - 44), (cx, cy - 56), (cx + 36, cy - 44), (cx + 48, cy - 8), (cx + 38, cy + 34), (cx + fx * 4, cy + 54), (cx - 38, cy + 34)])
    if sp.get('beard'):
        ink(c, smooth([(cx - 46, cy + 4), (cx - 40, cy + 50), (cx + fx * 4, cy + 82), (cx + 40, cy + 50), (cx + 46, cy + 4), (cx, cy + 20)]), sp['beard'], w=3)
    ink(c, hd, skin, w=3.6)
    c.drawCircle(cx - 26 + fx * 6, cy + 24, 13, P('#e2603a', .16, blur=6)); c.drawCircle(cx + 26 + fx * 6, cy + 24, 13, P('#e2603a', .16, blur=6))
    # hair cap
    lowy = {'shikha': cy - 30, 'short': cy - 24, 'bun': cy - 22}[st]
    cap = skia.Op(hd, smooth([(cx - 70, cy - 90), (cx + 70, cy - 90), (cx + 70, lowy - 2), (cx + 30, lowy - 8), (cx + fx * 10, lowy + (10 if st == 'bun' else -2)), (cx - 30, lowy - 8), (cx - 70, lowy - 2)]), skia.PathOp.kIntersect_PathOp)
    ink(c, cap, hc, w=2.5, a=.55 if st == 'shikha' else 1)
    if sp.get('band'):
        c.save(); c.clipPath(hd, skia.ClipOp.kIntersect, True); c.drawRect(skia.Rect.MakeLTRB(cx - 60, cy - 36, cx + 60, cy - 22), P(sp['band'])); c.restore()
    ox = fx * 9
    exs = (cx - 21 + ox, cx + 21 + ox); ey = cy + 2
    for i, ex in enumerate(exs):
        inner = 1 if i == 0 else -1
        rx = 11.5 * (1 - .12 * (fx * inner > 0) * abs(fx)); ry = 13
        if blind:
            p = skia.Path(); p.moveTo(ex - rx, ey - 1); p.quadTo(ex, ey + 8, ex + rx, ey - 1); c.drawPath(p, P(LINE, .9, stroke=4))
        else:
            eye3(c, ex, ey, rx, ry, m, blink(t, seed + .0), gaze, inner, skin, lash=4.5)
        brow3(c, ex, ey, rx, ry, m, inner, w=8, h=hc if not sp.get('beard') and st != 'bun' or hc[1] < 'a' else '#b9b4ac')
    if sp.get('tilak'): c.drawPath(capsule(cx + ox * .6, cy - 30, cx + ox * .6, cy - 18, 3, 2.4), P('#c7362b'))
    if sp.get('bindi'): c.drawCircle(cx + ox * .6, cy - 20, 4.2, P('#c7362b'))
    nx = cx + ox * 1.5
    n = skia.Path(); n.moveTo(nx - 2, cy + 8); n.quadTo(nx + 7 * (fx if fx else .6), cy + 20, nx - 4, cy + 22); c.drawPath(n, P(LINE, .6, stroke=2.6))
    mx, my = cx + ox * .9, cy + 34; cv = m['curve']; op = clamp(m['open_'] * .5 + talk * (.35 + .65 * abs(math.sin(t * 8.3 + seed))))
    if sp.get('beard'): my += 2
    if op > .08:
        mo = oval(mx, my + 2, 10 + 2 * abs(cv), 3 + 7 * op); c.drawPath(mo, P('#5a1c1c')); c.drawPath(mo, P(LINE, .8, stroke=2.4))
    else:
        p = skia.Path(); p.moveTo(mx - 14, my - cv * 4); p.quadTo(mx, my + cv * 10, mx + 14, my - cv * 4); c.drawPath(p, P(LINE, .9, stroke=3.2))
    if sp.get('mous'):
        for sx in (-1, 1):
            p = skia.Path(); p.moveTo(mx, my - 8); p.quadTo(mx + sx * 12, my - 12, mx + sx * 22, my - 3); c.drawPath(p, P(hc, 1, stroke=5.5))


def person(c, x, y, s, sp, pose='stand', lean=0.0, L=None, R=None, mood='serene', gaze=(0, 0), t=0, fx=0, flip=False,
           blind=False, talk=0.0, seed=0.0, tilt=0.0, bob=0.0, a=1.0, skipL=False):
    m = MOODS[mood] if isinstance(mood, str) else mood
    skin = sp['skin']; fem = sp.get('fem'); lowc = sp['low']
    c.save(); c.translate(x, y); c.scale(-s if flip else s, s)
    c.drawPath(oval(0, 2, 120 if pose != 'stand' else 70, 12), P('#000000', .22, blur=8))
    if pose == 'stand':
        hip = (0, -205)
        for fxx in (-26, 26): ink(c, oval(fxx + 6, -8, 25, 10), skin, w=3)
        if fem: ink(c, smooth([(-48, -215), (48, -215), (64, -110), (74, -16), (0, -8), (-74, -16), (-64, -110)]), lowc)
        else:
            ink(c, smooth([(-50, -215), (50, -215), (58, -110), (56, -28), (0, -22), (-56, -28), (-58, -110)]), lowc)
            c.drawPath(poly([(0, -190), (4, -30)], False), P(LINE, .35, stroke=3))
    elif pose == 'sit':
        hip = (0, -54)
        ink(c, smooth([(-142, -28), (-92, -64), (0, -74), (92, -64), (142, -28), (96, -2), (0, 2), (-96, -2)]), lowc)
        p = skia.Path(); p.moveTo(-100, -20); p.quadTo(0, -52, 100, -20); c.drawPath(p, P(LINE, .35, stroke=3))
        ink(c, oval(-34, -10, 24, 10), skin, w=3); ink(c, oval(40, -8, 24, 10), skin, w=3)
    else:  # kneel
        hip = (0, -84)
        ink(c, oval(124, -10, 24, 10), skin, w=3)
        ink(c, smooth([(-50, -100), (44, -104), (120, -46), (130, -12), (20, 0), (-52, -8)]), lowc)
    c.translate(hip[0], hip[1] + bob); c.rotate(math.degrees(lean))
    tor = smooth([(-52, -120), (-30, -132), (30, -132), (52, -120), (48, -40), (48, 10), (-48, 10), (-48, -40)])
    ink(c, tor, sp['top'] if fem else skin)
    c.save(); c.clipPath(tor, skia.ClipOp.kIntersect, True)
    if fem:
        c.drawPath(poly([(-70, -140), (-18, -140), (64, 14), (10, 14)]), P(mixh(lowc, '#ffffff', .12))); c.drawPath(poly([(-18, -140), (64, 14)], False), P(LINE, .4, stroke=3))
        c.drawRect(skia.Rect.MakeLTRB(-60, -8, 60, 14), P(lowc))
    else:
        if sp.get('thread'): c.drawPath(poly([(-36, -130), (42, 8)], False), P('#fffdf2', 1, stroke=3.2))
        if sp.get('sash'):
            c.drawPath(poly([(70, -140), (24, -140), (-62, 14), (-14, 14)]), P(sp['sash'])); c.drawPath(poly([(24, -140), (-62, 14)], False), P(LINE, .35, stroke=3))
        c.drawRect(skia.Rect.MakeLTRB(-60, -6, 60, 14), P(mixh(lowc, '#000000', .08)))
    c.restore(); c.drawPath(tor, P(LINE, .85, stroke=4))
    ink(c, capsule(0, -126, 0, -152, 16, 15), skin, w=3)
    c.save(); c.translate(fx * 6, -198); c.rotate(math.degrees(tilt)); head(c, 0, 0, sp, m, gaze, t, fx, blind, talk, seed); c.restore()
    if pose == 'stand': dl, dr = dict(p=(-60, -8), a=pi / 2), dict(p=(60, -8), a=pi / 2)
    elif pose == 'sit': dl, dr = dict(p=(-76, 0), a=pi * .62, pose='flat'), dict(p=(76, 0), a=pi * .38, pose='flat')
    else: dl, dr = dict(p=(-40, 6), a=pi * .45, pose='flat'), dict(p=(46, 6), a=pi * .4, pose='flat')
    for side, spec, dflt in ((-1, L, dl), (1, R, dr)):
        if side == -1 and skipL: continue
        q = dict(dflt); q.update(spec or {})
        S = (side * 50, -114)
        E, Wr, ang = arm(c, S, q['p'], skin, 68, 64, bend=q.get('bend', -side), r=(17, 14, 11))
        hand(c, Wr[0], Wr[1], q.get('a', ang), q.get('pose', 'open'), ts=q.get('ts', -side), hs=.78, skin=skin, w=3, held=q.get('held'))
    c.restore()


def anjali(dy=0):
    return dict(p=(-8, -66 + dy), a=-pi / 2 + .12, pose='flat', ts=1), dict(p=(8, -66 + dy), a=-pi / 2 - .12, pose='flat', ts=-1)


def cam(a, b, z0=1.0, z1=1.06, c0=(960, 540), c1=(960, 540)):
    def f(t):
        k = ss(ramp(t, a, b)); return lerp(z0, z1, k), lerp(c0[0], c1[0], k), lerp(c0[1], c1[1], k)
    return f
def cam_keys(keys):  # [(t, z, cx, cy)]
    def f(t):
        if t <= keys[0][0]: return keys[0][1:]
        for (a, *A), (b, *B) in zip(keys, keys[1:]):
            if t <= b: k = ss((t - a) / (b - a)); return tuple(lerp(x, y, k) for x, y in zip(A, B))
        return keys[-1][1:]
    return f
