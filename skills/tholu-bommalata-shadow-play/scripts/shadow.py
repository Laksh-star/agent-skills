"""Tholu Bommalata style shadow-puppet layer on core.py.

The lit cloth (screen, frame), perforation and rivets, profile puppets with body, head
and hand rods (puppet), divinity marks (umark), flat cut-out props, the Ganesha and
Saraswati puppets, and the opening invocation (sc_invoc).

Draw order per frame: screen() -> props and puppets -> title ink -> frame() -> lamp_dip() -> captions.
Angles are degrees: an arm is (shoulder from hanging, elbow bend); lean and nod are forward-positive.
"""
import math, random, numpy as np, skia
from core import *

W, H, FPS = 1920, 1080, 24
GY, BAND = 892, 906            # ground line for puppets; top of the black cloth under the screen
OUT, HOLE = '#1c0d08', '#fff3cc'
sin, cos, rad_ = math.sin, math.cos, math.radians

_rs = np.random.RandomState(4)
_w = _rs.rand(H // 2, W // 2).astype(np.float32)
_weave = (0.5 + 0.5 * np.sin(np.arange(W // 2)[None, :] * 2.1)) * .5 + (0.5 + 0.5 * np.sin(np.arange(H // 2)[:, None] * 2.1)) * .5
_tex = np.clip(232 + (_w - .5) * 26 + (_weave - .5) * 16, 0, 255).astype(np.uint8)
_tex = np.repeat(np.repeat(_tex, 2, 0), 2, 1)
TEX = skia.Image.fromarray(np.ascontiguousarray(np.dstack([_tex, _tex, _tex, np.full_like(_tex, 255)])), colorType=skia.kRGBA_8888_ColorType)

def screen(c, t, tint=None, ta=0.0):
    fl = 1 + .03 * sin(t * 9.1) + .02 * sin(t * 14.3 + 1) + .015 * sin(t * 23.7)
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(960, 760, 1250 * fl, [(0, '#fff0bd', 1), (.35, '#f8d98a', 1), (.7, '#dfa24a', 1), (1, '#8a4a16', 1)])))
    for i in range(5):  # the row of oil lamps behind the cloth
        lx = 320 + i * 320; f = 1 + .12 * sin(t * (10 + i) + i * 2)
        glow(c, lx, 900, 300 * f, '#fff6d0', .5)
    pm = skia.Paint(); pm.setBlendMode(skia.BlendMode.kMultiply); c.drawImage(TEX, 0, 0, skia.SamplingOptions(), pm)
    if tint and ta > 0: c.drawRect(skia.Rect.MakeWH(W, H), P(tint, ta, blend=skia.BlendMode.kMultiply))

def frame(c, t):
    c.drawRect(skia.Rect.MakeLTRB(0, BAND, W, H), P(shader=lin(0, BAND, 0, BAND + 40, [(0, '#2a1508', 1), (1, '#120805', 1)])))
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 46), P('#160b06')); c.drawRect(skia.Rect.MakeLTRB(0, 46, W, 54), P('#7a2a14'))
    for i in range(49):  # mango-leaf toranam along the top
        x = i * 40 + 20; sw = sin(t * 1.3 + i * .7) * 3
        c.drawPath(smooth([(x - 13, 52), (x + 13, 52), (x + sw, 104)]), P('#1f3a16' if i % 2 else '#16280f'))
    for x0 in (0, W - 38): c.drawRect(skia.Rect.MakeLTRB(x0, 0, x0 + 38, BAND), P('#160b06'))
    c.drawRect(skia.Rect.MakeWH(W, H), P(shader=rad(960, 520, 1300, [(0, '#000000', 0), (.72, '#000000', 0), (1, '#000000', .5)])))

# ------------------------------------------------------------------ puppet parts
def dots(c, pts, step=17, r=2.7, col_=HOLE):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0); n = max(1, int(L / step))
        for i in range(n + 1): k = i / n; c.drawCircle(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, r, P(col_))
def rivet(c, x, y): c.drawCircle(x, y, 7.5, P(OUT)); c.drawCircle(x, y, 3, P(HOLE))
def shp(c, path, fill, w=4.5): ink(c, path, fill, line=OUT, w=w)

def umark(c, x, y, s=1.0):   # the U-shaped mark with a dot at its base that signals divinity
    u = skia.Path(); u.moveTo(x - 8 * s, y - 16 * s); u.quadTo(x - 9 * s, y + 6 * s, x, y + 7 * s); u.quadTo(x + 9 * s, y + 6 * s, x + 8 * s, y - 16 * s)
    c.drawPath(u, P('#fffdf2', 1, stroke=4.5 * s)); c.drawPath(oval(x, y - 2 * s, 2.6 * s, 4.5 * s), P('#b3200f'))

def arm(c, sx, sy, a1, a2, sp, held=None):
    a1, a2 = rad_(a1), rad_(a2); ex, ey = sx + 104 * sin(a1), sy + 104 * cos(a1); b = a1 + a2
    hx, hy = ex + 96 * sin(b), ey + 96 * cos(b); dx, dy = sin(b), cos(b); nx, ny = dy, -dx
    shp(c, capsule(sx, sy, ex, ey, 21, 17), sp['skin']); shp(c, capsule(ex, ey, hx, hy, 17, 13), sp['skin'])
    ux, uy = sin(a1), cos(a1)
    shp(c, capsule(sx + ux * 34, sy + uy * 34, sx + ux * 46, sy + uy * 46, 22, 22), sp['gold'], w=3); dots(c, [(sx + ux * 40 - uy * 12, sy + uy * 40 + ux * 12), (sx + ux * 40 + uy * 12, sy + uy * 40 - ux * 12)], 8, 2.2)
    shp(c, capsule(hx - dx * 16, hy - dy * 16, hx - dx * 6, hy - dy * 6, 15, 15), sp['gold'], w=3)
    tip = (hx + dx * 50, hy + dy * 50)
    shp(c, smooth([(hx - nx * 12, hy - ny * 12), (hx + dx * 22 - nx * 17, hy + dy * 22 - ny * 17), tip, (hx + dx * 24 + nx * 13, hy + dy * 24 + ny * 13), (hx + nx * 12, hy + ny * 12)]), sp['skin'], w=3.5)
    shp(c, capsule(hx + dx * 8 - nx * 12, hy + dy * 8 - ny * 12, hx + dx * 22 - nx * 27, hy + dy * 22 - ny * 27, 5.5, 4.5), sp['skin'], w=3)
    rivet(c, sx, sy); rivet(c, ex, ey); rivet(c, hx, hy)
    if held: held(c, hx + dx * 24, hy + dy * 24, b)
    return hx + dx * 26, hy + dy * 26

def head(c, sp, nod=0.0, blind=False):
    c.save(); c.translate(4, -438); c.rotate(nod); c.translate(-4, 438)
    hs = sp['hair']; hc = sp.get('hairc', '#140a08')
    if hs == 'shikha': shp(c, oval(-40, -540, 17, 20), hc, w=3)
    if hs == 'bun': shp(c, oval(-52, -500, 30, 28), hc, w=3); dots(c, [(-70, -500), (-52, -520), (-34, -500)], 12, 2.4)
    if hs == 'jata': shp(c, smooth([(-30, -520), (-34, -590), (0, -612), (30, -585), (24, -520)]), hc, w=3); dots(c, [(-22, -560), (18, -560)], 10, 2.4)
    if sp.get('beard'):
        shp(c, smooth([(-6, -462), (10, -440), (30, -392), (58, -430), (56, -468), (30, -458)]), sp['beard'], w=3.5)
    face = smooth([(-36, -470), (-44, -505), (-28, -538), (8, -550), (40, -532), (50, -510), (72, -486), (54, -476), (60, -468), (52, -462), (58, -454), (44, -440), (14, -438), (-14, -446)])
    shp(c, face, sp['skin'])
    # hair cap
    cap = skia.Op(face, smooth([(-70, -580), (60, -580), (48, -524), (10, -534), (-18, -520), (-22, -486), (-40, -462), (-70, -462)]), skia.PathOp.kIntersect_PathOp)
    shp(c, cap, hc, w=3)
    if sp.get('band'):
        bd = skia.Op(face, poly([(-60, -536), (60, -536), (60, -518), (-60, -518)]), skia.PathOp.kIntersect_PathOp); shp(c, bd, sp['band'], w=3); dots(c, [(-34, -527), (40, -527)], 11, 2.2)
    # the big fish-shaped eye of the leather puppets
    ex, ey = 22, -500
    if blind: e = skia.Path(); e.moveTo(ex - 20, ey - 2); e.quadTo(ex, ey + 12, ex + 22, ey - 2); c.drawPath(e, P(OUT, 1, stroke=4.5))
    else:
        eye = smooth([(ex - 22, ey), (ex - 4, ey - 12), (ex + 24, ey - 2), (ex - 2, ey + 9)]); c.drawPath(eye, P('#fffdf2')); c.drawPath(eye, P(OUT, 1, stroke=3.2)); c.drawCircle(ex + 4, ey - 1, 6.5, P(OUT))
    br = skia.Path(); br.moveTo(ex - 22, ey - 18); br.quadTo(ex + 2, ey - 30, ex + 30, ey - 14); c.drawPath(br, P(OUT, 1, stroke=5))
    c.drawPath(poly([(50, -470), (60, -468), (50, -464)]), P('#9a1c12'))
    shp(c, oval(-16, -494, 9, 14), sp['skin'], w=3); c.drawCircle(-16, -474, 8, P(sp['gold'])); c.drawCircle(-16, -474, 8, P(OUT, 1, stroke=2.5)); c.drawCircle(-16, -474, 2.6, P(HOLE))
    if sp.get('crown'):
        shp(c, smooth([(-40, -534), (-30, -596), (-6, -604), (4, -650), (16, -604), (40, -592), (46, -530)]), sp['gold'], w=3.5); dots(c, [(-28, -548), (36, -546)], 11, 2.4); dots(c, [(-18, -580), (26, -578)], 11, 2.4); c.drawCircle(4, -618, 5, P('#b3200f'))
    if sp.get('tilak'): c.drawPath(capsule(34, -530, 40, -518, 3.4, 3), P('#b3200f'))
    if sp.get('bindi'): c.drawCircle(38, -522, 5, P('#b3200f'))
    if sp.get('mous'): m = skia.Path(); m.moveTo(56, -474); m.quadTo(40, -480, 30, -466); c.drawPath(m, P(hc, 1, stroke=5))
    c.restore()

def puppet(c, x, sp, pose='stand', face=1, s=1.0, lean=0.0, bob=0.0, nod=0.0, near=(12, 14), far=(-14, 10), y=GY, held=None, blind=False, rods=True, alpha=.93):
    """Profile puppet facing +x (face=-1 mirrors). Angles in degrees: arm (shoulder from hanging, elbow bend), lean and nod forward positive."""
    up = 170 if pose == 'sit' else 0
    pm = skia.Paint(); pm.setBlendMode(skia.BlendMode.kMultiply); pm.setAlphaf(alpha); pm.setImageFilter(skia.ImageFilters.Blur(1.1, 1.1))
    lr = rad_(lean)
    def world(lx, ly): return x + face * s * (lx * cos(lr) - ly * sin(lr)), y - bob + s * (lx * sin(lr) + ly * cos(lr))
    if rods:
        bx, by = world(0, -300 + up); c.drawPath(poly([(bx, by), (x + face * 14, H + 20)], False), P('#2a160c', .42, stroke=9, blur=2.5))
    c.saveLayer(skia.Rect.MakeLTRB(x - 440 * s, y - bob - 720 * s, x + 440 * s, y + 70), pm); c.translate(x, y - bob); c.scale(s * face, s); c.rotate(lean)
    fem = sp.get('fem'); low = sp['low']; brd = sp['border']
    if pose == 'sit':
        shp(c, smooth([(-96, 0), (-84, -66), (-20, -100), (70, -84), (150, -36), (160, -6), (120, 4)]), low)
        k = skia.Path(); k.moveTo(-60, -30); k.quadTo(40, -70, 140, -24); c.drawPath(k, P(OUT, .8, stroke=3.5)); dots(c, [(-70, -12), (130, -6)], 16)
        shp(c, smooth([(116, -22), (176, -14), (178, 0), (120, 2)]), sp['skin'], w=3.5)
    elif fem:
        shp(c, smooth([(-34, 2), (-96, 2), (-92, -14)]), sp['skin'], w=3.5); shp(c, smooth([(30, -16), (104, -10), (106, 4), (30, 4)]), sp['skin'], w=3.5)
        shp(c, smooth([(-48, -262), (48, -262), (78, -150), (104, -16), (0, -8), (-96, -16), (-74, -150)]), low)
        for i in range(5): c.drawPath(poly([(-20 + i * 12, -250), (-52 + i * 30, -52)], False), P(OUT, .55, stroke=3))
        shp(c, smooth([(-96, -16), (0, -8), (104, -16), (100, -50), (0, -42), (-92, -50)]), brd, w=3.5); dots(c, [(-84, -32), (0, -25), (92, -32)], 15)
    else:
        for (hx_, ax, fx_) in ((-14, -62, -66), (14, 54, 50)):
            shp(c, smooth([(fx_ - 8, -16), (fx_ + 62, -10), (fx_ + 64, 4), (fx_ - 10, 4)]), sp['skin'], w=3.5)
            shp(c, capsule(hx_, -250, ax, -34, 44, 25), low); c.drawPath(poly([(ax - 23, -46), (ax + 23, -42)], False), P(OUT, 1, stroke=19)); c.drawPath(poly([(ax - 22, -46), (ax + 22, -42)], False), P(brd, 1, stroke=12)); dots(c, [(ax - 16, -45), (ax + 16, -43)], 8, 2.2)
            c.drawPath(poly([(hx_, -240), (ax, -70)], False), P(OUT, .5, stroke=3))
        shp(c, poly([(-26, -256), (30, -256), (6, -70)]), mixh(low, '#ffffff', .25), w=3.5); dots(c, [(-8, -236), (5, -100)], 20); dots(c, [(14, -236), (8, -100)], 20)
    c.translate(0, up)
    fx_, fy_ = arm(c, -56, -408, far[0], far[1], dict(sp, skin=mixh(sp['skin'], '#000000', .16)))
    tor = smooth([(-66, -414), (-40, -432), (40, -432), (66, -414), (50, -330), (46, -258), (-46, -258), (-50, -330)])
    shp(c, tor, sp['top'] if fem else sp['skin'])
    c.save(); c.clipPath(tor, skia.ClipOp.kIntersect, True)
    if fem: c.drawPath(poly([(-80, -440), (-22, -440), (66, -250), (8, -250)]), P(low)); dots(c, [(-42, -420), (40, -262)], 16)
    elif sp.get('sash'): c.drawPath(poly([(80, -440), (30, -440), (-64, -250), (-14, -250)]), P(sp['sash'])); dots(c, [(48, -420), (-36, -262)], 16)
    if sp.get('thread'): c.drawPath(poly([(-40, -430), (44, -262)], False), P('#fffdf2', 1, stroke=4)); c.drawPath(poly([(-40, -430), (44, -262)], False), P(OUT, .5, stroke=1.2))
    c.restore(); c.drawPath(tor, P(OUT, .9, stroke=4.5))
    if sp.get('divine'): umark(c, -22, -318); umark(c, 22, -318)
    nk = skia.Path(); nk.moveTo(-34, -424); nk.quadTo(2, -372, 38, -424); c.drawPath(nk, P(sp['gold'], 1, stroke=9)); dots(c, [(-28, -412), (-12, -398), (2, -394), (16, -398), (30, -412)], 9, 2.3)
    shp(c, rrect(-52, -276, 52, -246, 9), sp['gold'], w=3.5); dots(c, [(-42, -261), (42, -261)], 12, 2.5)
    shp(c, capsule(2, -428, 6, -450, 17, 16), sp['skin'], w=3.5)
    head(c, sp, nod, blind)
    nx_, ny_ = arm(c, 56, -408, near[0], near[1], sp, held)
    c.restore()
    if rods:
        hl = (4 - 60 * sin(rad_(nod)), -500 + up); wx, wy = world(*hl); c.drawPath(poly([(wx, wy), (wx - face * 10, H + 20)], False), P('#2a160c', .26, stroke=5, blur=2))
        for (lx, ly) in ((nx_, ny_ + up), (fx_, fy_ + up)):
            wx, wy = world(lx, ly); c.drawPath(poly([(wx, wy), (wx + face * 6, H + 20)], False), P('#2a160c', .3, stroke=5, blur=2))
    return world(nx_, ny_ + up)

def layer(c, box=None, a=.93, blur=1.1):
    pm = skia.Paint(); pm.setBlendMode(skia.BlendMode.kMultiply); pm.setAlphaf(a); pm.setImageFilter(skia.ImageFilters.Blur(blur, blur)); c.saveLayer(skia.Rect.MakeLTRB(*box) if box else None, pm)

# ------------------------------------------------------------------ props (flat leather cut-outs)
def leaf(c, x, y, a, L, colr):
    c.save(); c.translate(x, y); c.rotate(a); shp(c, smooth([(0, 0), (L * .5, -L * .2), (L, 0), (L * .5, L * .2)]), colr, w=3.5); dots(c, [(L * .2, 0), (L * .8, 0)], 14, 2.4); c.restore()
def tree(c, x, t, sc=1.0, branch=True, y=GY):   # branch=True adds a long horizontal branch to the right
    layer(c, (x - 540 * sc, y - 920 * sc, x + 540 * sc, y + 40)); c.translate(x, y); c.scale(sc, sc)
    shp(c, smooth([(-52, 14), (-34, -230), (-44, -470), (38, -470), (34, -230), (62, 14)]), '#8a4a22'); dots(c, [(-4, -40), (-6, -440)], 26, 3)
    if branch:
        b = skia.Path(); b.moveTo(10, -400); b.cubicTo(160, -440, 300, -380, 470, -410); c.drawPath(b, P(OUT, 1, stroke=40)); c.drawPath(b, P('#8a4a22', 1, stroke=31))
    r = random.Random(3)
    for ring, (n, R, L) in enumerate(((16, 250, 150), (12, 160, 140), (7, 70, 120))):
        for i in range(n):
            a = 360 / n * i + ring * 11; sw = sin(t * .8 + i + ring) * 2.5
            leaf(c, cos(rad_(a)) * R * 1.25, -640 + sin(rad_(a)) * R * .62, a + sw, L, ('#2f6b2a', '#4f8f2f', '#1f5226')[(i + ring) % 3])
    c.restore()
def hut(c, x, y=GY):
    layer(c, (x - 100, y - 650, x + 770, y + 40)); c.translate(x, y)
    shp(c, smooth([(-60, -390), (330, -600), (720, -390), (700, -350), (-40, -350)], True), '#c98a2e')
    for i in range(15): c.drawPath(poly([(-30 + i * 52, -356), (lerp(-30 + i * 52, 330, .5), -470)], False), P(OUT, .6, stroke=3))
    dots(c, [(-30, -368), (690, -368)], 18, 3)
    wall = skia.Op(poly([(0, -350), (660, -350), (660, 14), (0, 14)]), smooth([(130, 30), (130, -200), (200, -290), (330, -320), (460, -290), (530, -200), (530, 30)]), skia.PathOp.kDifference_PathOp)
    shp(c, wall, '#b5552b'); dots(c, [(30, -330), (630, -330)], 20, 3); dots(c, [(60, -300), (60, -20)], 22, 3); dots(c, [(600, -300), (600, -20)], 22, 3)
    c.restore()
def lampstand(c, x, t, y=GY):
    f = 1 + .1 * sin(t * 11) + .06 * sin(t * 17.3); glow(c, x, y - 430, 260 * f, '#fff6d0', .7)
    layer(c, (x - 100, y - 540, x + 100, y + 40)); c.translate(x, y)
    shp(c, smooth([(-60, 14), (-18, -30), (-12, -330), (-64, -366), (0, -392), (64, -366), (12, -330), (18, -30), (60, 14)]), '#c98a2e'); dots(c, [(0, -60), (0, -320)], 24, 3)
    shp(c, smooth([(0, -392 - 78 * f), (19, -424), (0, -394), (-19, -424)]), '#e8731e', w=3)
    c.restore()
def dais(c, x0, x1, y=GY):
    layer(c, (x0 - 12, y - 80, x1 + 12, y + 30)); shp(c, rrect(x0, y - 60, x1, y + 14, 8), '#7a2a14'); dots(c, [(x0 + 20, y - 40), (x1 - 20, y - 40)], 20, 3); dots(c, [(x0 + 20, y - 16), (x1 - 20, y - 16)], 20, 3); c.restore()
def bush(c, x, y=GY):
    layer(c, (x - 290, y - 290, x + 290, y + 70)); c.translate(x, y)
    for i in range(9): leaf(c, 0, 0, -170 + i * 20, 250 - abs(i - 4) * 14, ('#2f6b2a', '#1f5226')[i % 2])
    c.restore()

def ganesha(c, x, t, face=-1, bob=0.0, lean=0.0, near=(80, 60), far=(100, 50), y=GY, alpha=.93):
    sp = dict(skin='#e8622a', gold='#e0a422'); lr = rad_(lean)
    def world(lx, ly): return x + face * (lx * cos(lr) - ly * sin(lr)), y - bob + (lx * sin(lr) + ly * cos(lr))
    for (lx, ly, a_, w_) in ((0, -260, .42, 9), (40, -470, .26, 5)):
        wx, wy = world(lx, ly); c.drawPath(poly([(wx, wy), (x + face * 12, H + 20)], False), P('#2a160c', a_, stroke=w_, blur=2.2))
    pm = skia.Paint(); pm.setBlendMode(skia.BlendMode.kMultiply); pm.setAlphaf(alpha); pm.setImageFilter(skia.ImageFilters.Blur(1.1, 1.1))
    c.saveLayer(skia.Rect.MakeLTRB(x - 420, y - bob - 720, x + 420, y + 70), pm); c.translate(x, y - bob); c.scale(face, 1); c.rotate(lean)
    for (hx_, ax, fx_) in ((-34, -66, -74), (34, 58, 50)):
        shp(c, smooth([(fx_ - 8, -16), (fx_ + 66, -10), (fx_ + 68, 4), (fx_ - 10, 4)]), sp['skin'], w=3.5)
        shp(c, capsule(hx_, -170, ax, -34, 50, 30), '#e8b21e'); c.drawPath(poly([(ax - 26, -46), (ax + 26, -42)], False), P(OUT, 1, stroke=19)); c.drawPath(poly([(ax - 25, -46), (ax + 25, -42)], False), P('#b3200f', 1, stroke=12)); dots(c, [(ax - 18, -45), (ax + 18, -43)], 9, 2.2)
    shp(c, poly([(-30, -176), (34, -176), (4, -60)]), '#f3d98a', w=3.5); dots(c, [(2, -160), (4, -86)], 18)
    arm(c, -74, -372, far[0], far[1], dict(sp, skin='#c9521f'))
    shp(c, oval(0, -262, 112, 118), sp['skin']); umark(c, -44, -262, 1.3); umark(c, 0, -246, 1.3); umark(c, 44, -262, 1.3)
    th = skia.Path(); th.moveTo(-70, -350); th.quadTo(20, -250, 84, -200); c.drawPath(th, P('#fffdf2', 1, stroke=5)); c.drawPath(th, P(OUT, .5, stroke=1.4))
    shp(c, rrect(-104, -196, 104, -166, 10), sp['gold'], w=3.5); dots(c, [(-92, -181), (92, -181)], 12, 2.5)
    shp(c, oval(0, -372, 92, 50), sp['skin']); nk = skia.Path(); nk.moveTo(-60, -384); nk.quadTo(4, -318, 66, -384); c.drawPath(nk, P(sp['gold'], 1, stroke=10)); dots(c, [(-48, -366), (-22, -348), (4, -342), (30, -348), (54, -366)], 9, 2.4)
    shp(c, smooth([(-80, -520), (-118, -470), (-104, -400), (-52, -392), (-30, -440), (-36, -510)]), '#f08a4a'); dots(c, [(-96, -468), (-84, -412), (-52, -410)], 13, 2.4)
    tr = skia.Path(); tr.moveTo(74, -470); tr.cubicTo(120, -440, 128, -350, 96, -312); tr.cubicTo(80, -292, 54, -306, 66, -330)
    c.drawPath(tr, P(OUT, 1, stroke=46)); c.drawPath(tr, P(sp['skin'], 1, stroke=37))
    shp(c, oval(22, -476, 72, 66), sp['skin']); shp(c, poly([(70, -440), (128, -420), (72, -420)]), '#fffdf2', w=3)
    eye = smooth([(26, -486), (42, -496), (66, -488), (44, -479)]); c.drawPath(eye, P('#fffdf2')); c.drawPath(eye, P(OUT, 1, stroke=3)); c.drawCircle(48, -487, 5.5, P(OUT)); umark(c, 30, -520, 1.1)
    shp(c, smooth([(-34, -520), (-26, -584), (0, -592), (12, -646), (26, -592), (56, -580), (62, -518)]), sp['gold'], w=3.5); dots(c, [(-20, -536), (50, -534)], 11, 2.4); dots(c, [(-10, -568), (40, -566)], 11, 2.4); c.drawCircle(12, -610, 5, P('#b3200f'))
    arm(c, 74, -372, near[0], near[1], sp)
    c.restore()

def veena(cc, x, y, a):
    cc.save(); cc.translate(x - 30, y); cc.rotate(-32)
    shp(cc, capsule(-150, 0, 150, 0, 8, 8), '#8a4a22', w=3.5); shp(cc, oval(-150, 4, 48, 42), '#c98a2e', w=3.5); dots(cc, [(-176, 4), (-124, 4)], 12, 2.4); shp(cc, oval(150, 2, 26, 24), '#c98a2e', w=3.5)
    for i in range(6): cc.drawPath(poly([(-90 + i * 34, -10), (-90 + i * 34, 10)], False), P(OUT, 1, stroke=2.5))
    cc.restore()

G = '#e0a422'
SARA = dict(skin='#f2c22e', low='#fffaf0', border='#e0a422', top='#fffaf0', fem=True, hair='bun', crown=True, divine=True, bindi=True, gold=G)
ANJ = ((62, 72), (74, 60))                   # hands joined in greeting: (near arm, far arm)
def mixa(a, b, k): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
def hop(t, on=True, rate=7.5, amp=22): return abs(sin(t * rate)) * amp if on else 0

def sc_invoc(c, t, left_cast, right_cast):
    """The opening invocation, about 14 s: the cast pinned at both edges of the screen,
    Ganesha enters from the audience's right and dances, then Saraswati with her veena.
    left_cast / right_cast: three character specs each."""
    off = 620 * eio(t, 12.5, 13.6); a = eio(t, .4, 1.6)
    for (x_, ln), sp_ in zip(((120, -5), (232, 4), (338, -3)), left_cast): puppet(c, x_ - off, sp_, face=1, s=.6, lean=ln, rods=False, alpha=.93 * a)
    for (x_, ln), sp_ in zip(((1800, -5), (1688, 4), (1582, -3)), right_cast): puppet(c, x_ + off, sp_, face=-1, s=.6, lean=ln, rods=False, alpha=.93 * a)
    gx = lerp(2300, 960, eio(t, 1.6, 3.2)) + 1400 * eio(t, 7.0, 8.4)
    if t < 8.5:
        d = sin(t * 6.4); dance = eio(t, 3.0, 3.6) * (1 - eio(t, 6.8, 7.2))
        ganesha(c, gx, t, bob=abs(d) * 26, lean=7 * sin(t * 3.2) * dance, near=(84 + 42 * d * dance, 56), far=(84 - 42 * d * dance, 56))
    sx = lerp(2300, 960, eio(t, 8.3, 9.9)) + 1400 * eio(t, 12.2, 13.5)
    if 8.2 < t < 13.6:
        puppet(c, sx, SARA, face=-1, near=(30, 84 + 6 * sin(t * 5)), far=(44, 72), held=veena, bob=hop(t, t < 9.9 or t > 12.2, 6.4, 16), nod=3 * sin(t * 2.4))

def lamp_dip(c, t, cuts, width=.55):
    """Darken the screen for ~1 s around each scene change, as puppeteers do while swapping cut-outs. Draw after frame()."""
    dip = max([1 - min(abs(t - x) / width, 1) for x in cuts] + [0])
    if dip > 0: c.drawRect(skia.Rect.MakeLTRB(0, 0, W, BAND), P('#0a0503', ss(dip) * .96))

def draw_ink(c, s, size, cx, cy, a=1.0):
    """Title text printed in dark ink on the cloth (Multiply), not floating over it."""
    if a <= .01: return
    img = text_img(s, size, '#3a1408', 0.0); p = skia.Paint(AntiAlias=True); p.setAlphaf(clamp(a) * .92); p.setBlendMode(skia.BlendMode.kMultiply)
    c.drawImage(img, cx - img.width() / 2, cy - img.height() / 2, skia.SamplingOptions(skia.FilterMode.kLinear), p)
