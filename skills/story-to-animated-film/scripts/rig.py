"""Storybook character rig: expressive front-facing people built on core.py.

person(c, x, y, s, spec, pose='stand'|'sit'|'kneel', ...) draws a whole figure with
its feet at (x, y). A spec is a dict, e.g.
    dict(skin='#d09a6c', low='#f1e6cf', sash='#e8a23a', thread=True, hair='shikha', hairc='#1b1012', tilak=True)
    dict(skin='#c98d5e', low='#c2413a', top='#2f7a6a', fem=True, hair='bun', hairc='#1b1012', bindi=True)
hair: shikha | short | bun.  Optional: beard, mous, band, thread, sash, tilak, bindi, hairc.
Arms: L/R=dict(p=(x, y) wrist target in body space, a=hand angle, pose=open|flat|grip|pinch, ts=thumb side, held=fn,
      elbow='down'|'out'|'in' (default down: elbows hang with gravity), behind=True to draw the arm behind the body).
      Or use a named gesture: L, R = gesture('bless', 'speak') or R=gesture('point', side=1).
Arm rules the rig enforces (and logs to ARM_LOG for pose_check.py):
  elbows hang down unless a gesture asks otherwise (a near hand is reached by bringing the forearm toward the viewer); the wrist bends at most 70 degrees off the forearm;
  a hand target out of reach or folding the elbow under 25 degrees is reported.
"""
import math, skia
from core import *
pi = math.pi

SHOULDER = (46, -112)          # body space, right side; left is mirrored
UPPER, FORE = 70, 66           # arm lengths: the wrist hangs just below the hip line, as on a person
WRIST_LIMIT = math.radians(70)    # a wrist bends back about 70 degrees (joined hands need most of it)
FOLD_LIMIT = math.radians(25)
ARM_LOG = []                   # one entry per arm drawn: read by pose_check.py

# Gestures for the RIGHT arm (side=+1) in body space; gesture() mirrors them for the left.
GESTURES = {
    'rest':   None,                                                         # pose-aware default (see REST)
    'chest':  dict(p=(18, -62), a=pi * 1.1, pose='flat'),                   # hand on heart
    'speak':  dict(p=(96, -50), a=-.35, pose='open'),                       # palm-up explaining
    'raise':  dict(p=(86, -168), a=-pi / 2 + .15, pose='open'),             # hand up, as when making a point
    'bless':  dict(p=(94, -148), a=-pi / 2 + .1, pose='open'),              # palm forward, fingers up
    'point':  dict(p=(152, -108), a=-.22, pose='open'),                     # arm out to the side
    'offer':  dict(p=(74, -36), a=-.1, pose='flat'),                        # palm up, giving or receiving
    'akimbo': dict(p=(54, -18), a=pi * .85, pose='grip', elbow='out'),      # hand on hip; only when meant
    'lap':    dict(p=(26, 6), a=pi * .92, pose='flat'),                     # seated: hands meet in the lap
    'knee':   dict(p=(88, 6), a=.62, pose='flat'),                          # seated: hand rests on the knee
}
REST = {'stand': dict(p=(60, 22), pose='flat'),          # arms hang, nearly straight
        'sit':   dict(p=(88, 6), a=.62, pose='flat'),     # hands on knees
        'kneel': dict(p=(50, 12), pose='flat')}           # hands on thighs; the hand follows the forearm

def mirror(spec):
    if spec is None: return None
    q = dict(spec); q['p'] = (-spec['p'][0], spec['p'][1])
    if 'a' in spec: q['a'] = pi - spec['a']
    if 'ts' in spec: q['ts'] = -spec['ts']
    return q

def gesture(*names, side=None):
    """gesture('bless') -> right-arm spec; gesture('bless', side=-1) -> left; gesture('chest', 'speak') -> (L, R)."""
    if len(names) == 2: return gesture(names[0], side=-1), gesture(names[1], side=1)
    g = GESTURES[names[0]]; g = dict(g) if g else None
    return mirror(g) if side == -1 else g

def _wrap(a): return (a + pi) % (2 * pi) - pi

def nat_arm(c, S, T, skin, side, elbow='down', bend=None, r=(18, 14, 11)):
    """Two-bone arm from shoulder S toward target T. The elbow picks the natural side (down) unless told."""
    dx, dy = T[0] - S[0], T[1] - S[1]; d0 = math.hypot(dx, dy); reach = UPPER + FORE
    d = max(1e-3, min(d0, reach - .5)); base = math.atan2(dy, dx)
    a = math.acos(clamp((UPPER ** 2 + d * d - FORE ** 2) / (2 * UPPER * d), -1, 1))
    sols = [(S[0] + UPPER * math.cos(base + k * a), S[1] + UPPER * math.sin(base + k * a)) for k in (1, -1)]
    W = (S[0] + d * math.cos(base), S[1] + d * math.sin(base))
    hang = (S[0] + UPPER * math.cos(pi / 2 - side * .15), S[1] + UPPER * math.sin(pi / 2 - side * .15))
    if bend is not None: E = sols[0] if bend > 0 else sols[1]
    elif elbow == 'out': E = max(sols, key=lambda e: e[0] * side)
    elif elbow == 'in': E = min(sols, key=lambda e: e[0] * side)
    elif math.hypot(W[0] - hang[0], W[1] - hang[1]) <= FORE:
        E = hang          # upper arm hangs at the side; the forearm comes forward toward the viewer (shorter on screen)
    else:                 # hand far or high: the lower elbow, never folded in across the body
        E = min(sols, key=lambda e: -e[1] + 2.0 * max(0.0, (S[0] - e[0]) * side))
    cap = capsule(S[0] - side * 16, S[1] - 6, S[0], S[1], 15, r[0] + 1)  # shoulder rounds into the torso
    ink(c, union([cap, capsule(*S, *E, r[0], r[1]), capsule(*E, *W, r[1], r[2])]), skin)
    u1, u2 = (S[0] - E[0], S[1] - E[1]), (W[0] - E[0], W[1] - E[1])
    fold = math.acos(clamp((u1[0] * u2[0] + u1[1] * u2[1]) / ((math.hypot(*u1) * math.hypot(*u2)) or 1), -1, 1))  # elbow angle as drawn
    return E, W, math.atan2(W[1] - E[1], W[0] - E[0]), d0 - reach, fold

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
    for side, spec in ((-1, L), (1, R)):
        if spec is not None and spec.get('behind') and not (side == -1 and skipL): _arm(c, side, spec, pose, skin, dim=.12)
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
    for side, spec in ((-1, L), (1, R)):
        if side == -1 and skipL: continue
        if spec is not None and spec.get('behind'): continue                     # drawn before the torso
        _arm(c, side, spec, pose, skin)
    c.restore()


def _arm(c, side, spec, pose, skin, dim=0.0):
    dflt = REST[pose] if side == 1 else mirror(REST[pose])
    q = dict(dflt); q.update(spec or {})
    S = (side * SHOULDER[0], SHOULDER[1])
    col_ = mixh(skin, '#000000', dim) if dim else skin
    E, Wr, fang, short, fold = nat_arm(c, S, q['p'], col_, side, q.get('elbow', 'down'), q.get('bend'))
    want = q.get('a', fang); dev = _wrap(want - fang)
    ha = fang + clamp(dev, -WRIST_LIMIT, WRIST_LIMIT)
    hand(c, Wr[0], Wr[1], ha, q.get('pose', 'open'), ts=q.get('ts', -side), hs=.78, skin=col_, w=3, held=q.get('held'))
    ARM_LOG.append(dict(side=side, pose=pose, target=q['p'], shoulder=S, elbow=E, wrist=Wr, short=short,
                        fold=math.degrees(fold), wrist_dev=math.degrees(abs(dev))))


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
