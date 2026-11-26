#!/usr/bin/env python3
"""Draw every character pose with every gesture at full size, so arms and hands can be judged before a film is built.

  python3 pose_sheet.py poses.jpg                  # sheet with the rig in this folder
  python3 pose_sheet.py old.jpg --rig old_rig.py   # the same sheet through another rig, for a before/after

Rows are stand, sit and kneel; columns are the named gestures in rig.GESTURES (both hands for anjali).
It also prints any arm the rig reports as out of reach, folded too far or with a bent-back wrist.
Look for: elbows that hang (not splayed), hands that rest on something when at rest, shoulders that
join the body, wrists in line with the forearm.
"""
import argparse, importlib.util, math, os, sys
import numpy as np, skia
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import core

COLS = {'stand': ['rest', 'anjali', 'chest', 'speak', 'offer', 'raise', 'bless', 'point', 'akimbo'],
        'sit':   ['rest', 'anjali', 'chest', 'speak', 'offer', 'raise', 'bless', 'point', 'lap'],
        'kneel': ['rest', 'anjali', 'chest', 'speak', 'offer', 'raise', 'bless', 'point', 'lap']}
# The same gesture targets, for a rig that predates rig.GESTURES (used for before/after sheets).
FALLBACK = {'chest': dict(p=(18, -62), a=math.pi * 1.1, pose='flat'), 'speak': dict(p=(96, -50), a=-.35, pose='open'),
            'raise': dict(p=(86, -168), a=-math.pi / 2 + .15, pose='open'), 'bless': dict(p=(94, -148), a=-math.pi / 2 + .1, pose='open'),
            'point': dict(p=(152, -108), a=-.22, pose='open'), 'offer': dict(p=(74, -36), a=-.1, pose='flat'),
            'akimbo': dict(p=(54, -18), a=math.pi * .85, pose='grip', bend=-1), 'lap': dict(p=(26, 6), a=math.pi * .92, pose='flat')}
SPEC = dict(skin='#d09a6c', low='#f1e6cf', sash='#e8a23a', thread=True, hair='shikha', hairc='#1b1012', tilak=True)
TW, TH, S = 300, 470, .82

def load_rig(path):
    spec = importlib.util.spec_from_file_location('rig_under_test', path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def arms(rig, name):
    if name == 'rest': return None, None
    if name == 'anjali': return rig.anjali()
    if hasattr(rig, 'gesture'): return None, rig.gesture(name, side=1)
    return None, dict(FALLBACK[name])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--rig', default=os.path.join(HERE, 'rig.py'))
    ap.add_argument('--title', default=None); a = ap.parse_args()
    rig = load_rig(a.rig); ncol = max(len(v) for v in COLS.values())
    W, H = TW * ncol, TH * 3 + 60
    surf = skia.Surface(W, H); c = surf.getCanvas(); c.clear(skia.ColorSetRGB(0xf6, 0xee, 0xdf))
    font = skia.Font(skia.Typeface('DejaVu Sans'), 22); fontb = skia.Font(skia.Typeface('DejaVu Sans'), 26)
    c.drawString(a.title or os.path.basename(a.rig), 16, 38, fontb, core.P('#2a1530'))
    for r, pose in enumerate(('stand', 'sit', 'kneel')):
        for k, name in enumerate(COLS[pose]):
            x0, y0 = k * TW, 60 + r * TH
            c.drawRect(skia.Rect.MakeXYWH(x0 + 4, y0 + 4, TW - 8, TH - 8), core.P('#ffffff', .55))
            L, R = arms(rig, name)
            if hasattr(rig, 'ARM_LOG'): rig.ARM_LOG.clear()
            rig.person(c, x0 + TW / 2, y0 + TH - 34, S, SPEC, pose=pose, L=L, R=R, mood='serene', t=0.3)
            c.drawString(f'{pose} · {name}', x0 + 14, y0 + 30, font, core.P('#2a1530', .8))
            for e in getattr(rig, 'ARM_LOG', []):
                msgs = []
                if e['short'] > 2: msgs.append(f"out of reach by {e['short']:.0f}px")
                if e['fold'] < math.degrees(getattr(rig, 'FOLD_LIMIT', 0)): msgs.append(f"elbow folded to {e['fold']:.0f} deg")
                if e['wrist_dev'] > math.degrees(getattr(rig, 'WRIST_LIMIT', 7)): msgs.append(f"wrist asked to bend {e['wrist_dev']:.0f} deg (limited)")
                for m in msgs: print(f"{pose} {name} {'left' if e['side'] < 0 else 'right'} arm: {m}")
    img = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    Image.fromarray(np.ascontiguousarray(img[..., :3])).save(a.out, quality=90)

if __name__ == '__main__':
    main()
