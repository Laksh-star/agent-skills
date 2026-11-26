#!/usr/bin/env python3
"""Check every arm in a film built on rig.py: run before rendering, and again after changing poses.

  python3 pose_check.py film.py                 # every 0.5 s of the film
  python3 pose_check.py film.py --every 0.25
  python3 pose_check.py film.py --at 12.5 40    # specific moments

Reports, with the times they happen:
  out of reach   the hand target is farther than the arm can reach, so the hand stops short of it
  folded         the elbow closes under 25 degrees (the forearm lies on the upper arm)
  wrist          the requested hand angle bends the wrist past 70 degrees (the rig limits it; fix the 'a' value)
Exits 1 if any problem is found. It reads the arm log the rig keeps; it does not look at pixels,
so still look at the pose sheet and full-size frames for contact and overlap.
"""
import argparse, importlib.util, math, os, sys
from collections import defaultdict

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('film'); ap.add_argument('--every', type=float, default=.5)
    ap.add_argument('--at', type=float, nargs='*'); a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(0, os.path.dirname(os.path.abspath(a.film)))
    spec = importlib.util.spec_from_file_location('film_under_check', a.film); film = importlib.util.module_from_spec(spec); spec.loader.exec_module(film)
    import rig
    times = a.at if a.at else [i * a.every for i in range(int(film.DUR / a.every) + 1)]
    found = defaultdict(list)
    for t in times:
        rig.ARM_LOG.clear(); film.render(t)
        for e in rig.ARM_LOG:
            arm = f"{'left' if e['side'] < 0 else 'right'} arm, {e['pose']}, target {tuple(round(v) for v in e['target'])}"
            if e['short'] > 2: found[(f"out of reach by {e['short']:.0f}px", arm)].append(t)
            if e['fold'] < math.degrees(rig.FOLD_LIMIT): found[(f"folded to {e['fold']:.0f} deg", arm)].append(t)
            if e['wrist_dev'] > math.degrees(rig.WRIST_LIMIT): found[(f"wrist asked to bend {e['wrist_dev']:.0f} deg", arm)].append(t)
    if not found:
        print(f'{len(times)} moments checked: every arm reachable, elbows open, wrists within limits'); return 0
    for (problem, arm), ts in sorted(found.items(), key=lambda kv: kv[1][0]):
        print(f'{ts[0]:.2f}-{ts[-1]:.2f}s  {problem}  ({arm})')
    return 1

if __name__ == '__main__':
    sys.exit(main())
