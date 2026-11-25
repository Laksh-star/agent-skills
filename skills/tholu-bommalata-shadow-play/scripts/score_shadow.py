#!/usr/bin/env python3
"""Synthesised score in the colour of a shadow-play troupe: harmonium drone and melody,
a mridangam pattern, talam cymbals, plus the invocation music (a brisk dance for Ganesha,
a slow phrase for Saraswati). It is a stand-in: a real troupe's voice and instruments are better.

  python3 score_shadow.py --prologue 14 --duration 146 --out score.wav \
      --quiet 17.5-25,89-101 --dark 15-25 --cuts 25,47,55 --hits 17.9

--prologue   invocation length in seconds (0 = none); the story score starts exactly after it
--duration   story length in seconds (after the prologue)
--quiet      story-time ranges with drone and melody only, no drum (solemn scenes)
--dark       story-time ranges whose melody uses the darker scale
--cuts       story-time scene changes (cymbal)
--hits       story-time dramatic moments (low drum)
Output: 44.1 kHz stereo WAV. Loudness-normalise to -16 LUFS when muxing.
"""
import argparse, random, wave
import numpy as np
from scipy.signal import fftconvolve, lfilter

SR = 44100; BRIGHT = [0, 2, 4, 7, 9]; DARK = [0, 2, 3, 7, 9]

def rng_list(s):
    out = []
    for part in filter(None, (s or '').split(',')):
        a, b = part.split('-'); out.append((float(a), float(b)))
    return out

def pts(s): return [float(x) for x in filter(None, (s or '').split(','))]

class Track:
    def __init__(s, dur): s.N = int(dur * SR); s.buf = np.zeros(s.N); s.dur = dur
    def add(s, t, sig):
        i = int(t * SR)
        if 0 <= i < s.N: sig = sig[:s.N - i]; s.buf[i:i + len(sig)] += sig

def drone(N, sa):
    tt = np.arange(N) / SR; d = np.zeros(N)
    for f, g in ((sa, .05), (sa * 1.5, .035), (sa * 2, .03)):
        for k in range(1, 9): d += g / k * np.sin(2 * np.pi * f * k * tt * (1 + 0.0006 * k) + k)
    return d * (0.8 + 0.2 * np.sin(2 * np.pi * 0.23 * tt))      # bellows swell

def reed(f0, f1, d, vol, phase):
    n = int(d * SR); x = np.arange(n) / SR; g = np.clip(x / 0.05, 0, 1); f = f0 + (f1 - f0) * g
    ph = phase[0] + 2 * np.pi * np.cumsum(f) / SR; phase[0] = ph[-1]
    env = np.clip(x / 0.04, 0, 1) * np.clip((d - x) / 0.08, 0, 1) * (0.85 + 0.15 * np.sin(2 * np.pi * 5 * x))
    return vol * env * sum(np.sin(k * ph) / k ** 0.9 for k in range(1, 9)) * 0.4

def thump(f0=92, d=.22, v=1.0):
    x = np.arange(int(d * SR)) / SR; return v * np.sin(2 * np.pi * (f0 * x + 18 * (1 - np.exp(-x * 30)) / 30)) * np.exp(-x * 16)
def ring(f, d=.28, v=1.0):
    x = np.arange(int(d * SR)) / SR; return v * (np.sin(2 * np.pi * f * x) + .4 * np.sin(2 * np.pi * f * 2.01 * x)) * np.exp(-x * 13)
def tick(d=.06, v=1.0):
    n = int(d * SR); x = np.arange(n) / SR; return v * lfilter([1, -1], [1, -.3], np.random.RandomState(n).randn(n)) * np.exp(-x * 70) * .3
def ting(v=1.0):
    x = np.arange(int(1.2 * SR)) / SR; return v * (np.sin(2 * np.pi * 2637 * x) + .6 * np.sin(2 * np.pi * 4187 * x) + .3 * np.sin(2 * np.pi * 6200 * x)) * np.exp(-x * 5)

def note_f(sa, idx, scale): o, dg = divmod(idx, 5); return sa * 2 * 2 ** ((scale[dg] + 12 * o) / 12)

def story(a):
    D = a.duration; tr = Track(D); quiet = rng_list(a.quiet); dark = rng_list(a.dark)
    isq = lambda t: t < 6 or any(x <= t < y for x, y in quiet); isd = lambda t: any(x <= t < y for x, y in dark)
    r = random.Random(5); mel = Track(D); ph = [0.0]; t = 6.5; idx = 5; prev = None
    while t < D - 11:
        sc = DARK if isd(t) else BRIGHT; vol = .07 if isq(t) else .085; beat = 60 / 84 / 2
        for k in range(r.choice([5, 6, 7, 8])):
            last = k == 7 or r.random() < .15
            idx = min([0, 3, 5, 8], key=lambda x: abs(x - idx)) if last else max(-2, min(9, idx + r.choice([-2, -1, -1, 1, 1, 2])))
            d = beat * (r.choice([4, 6]) if last else r.choice([1, 1, 2, 2, 3])); f = note_f(a.sa, idx, sc)
            mel.add(t, reed(prev or f, f, d, vol, ph)); prev = f; t += d
            if last: break
        prev = None; t += beat * r.choice([2, 4])
    pc = Track(D); beat = 60 / 84; PAT = 'T.kkT.rkTkrkTkrr'; i = 0; t = 7.0
    while t < D - 12:
        if not isq(t):
            h = PAT[i % 16]; v = .9 + .2 * ((i % 8) == 0)
            if h == 'T': pc.add(t, thump(v=.26 * v))
            elif h == 'r': pc.add(t, ring(a.sa * 2, v=.12 * v))
            elif h == 'k': pc.add(t, tick(v=.5 * v))
            if i % 8 == 0: pc.add(t, ting(.035))
            if i % 8 == 4: pc.add(t, ting(.02))
        i += 1; t += beat / 2
    for c in pts(a.cuts): pc.add(c - .1, ting(.07)); pc.add(c + .25, ting(.05))
    for h in pts(a.hits): pc.add(h, thump(60, .9, .5))
    n_ir = int(1.1 * SR)
    wet = lambda seed: fftconvolve(mel.buf + pc.buf, np.random.RandomState(seed).randn(n_ir) * np.exp(-np.arange(n_ir) / SR * 4.5))[:tr.N] * 0.02
    dry = drone(tr.N, a.sa) + mel.buf + pc.buf; tt = np.arange(tr.N) / SR
    fade = np.clip(tt / 1.5, 0, 1) * np.clip((D - tt) / 3.0, 0, 1)
    return np.stack([dry + wet(1), dry + wet(2)], 1) * fade[:, None]

def prologue(a, xf):
    D = a.prologue + xf; tr = Track(D); pc = Track(D); mel = Track(D); ph = [0.0]
    pc.add(.6, ting(.08)); pc.add(1.1, ting(.06))
    beat = np.pi / 6.4; t = 1.8; i = 0; PAT = 'TkrkTTrk'                 # Ganesha's dance, matched to his hops
    while t < D * .58:
        h = PAT[i % 8]
        if h == 'T': pc.add(t, thump(v=.3))
        elif h == 'r': pc.add(t, ring(a.sa * 2, v=.14))
        else: pc.add(t, tick(v=.55))
        if i % 4 == 0: pc.add(t, ting(.04))
        i += 1; t += beat / 2
    t = 2.0
    for k in [5, 6, 7, 6, 5, 7, 8, 7, 5, 6, 5, 3, 5, 6, 7, 8, 9, 8, 7, 5]:
        if t > D * .57: break
        mel.add(t, reed(note_f(a.sa, k, BRIGHT), note_f(a.sa, k, BRIGHT), beat * .98, .085, ph)); t += beat
    t = D * .64
    for k, d0 in ((5, 1.0), (7, .7), (8, 1.2), (7, .5), (5, 1.3)):     # Saraswati: slow, no drum
        mel.add(t, reed(note_f(a.sa, k, BRIGHT), note_f(a.sa, k, BRIGHT), d0, .07, ph)); t += d0
    pc.add(D * .61, ting(.06)); pc.add(a.prologue - .9, ting(.06))
    x = drone(tr.N, a.sa) + mel.buf + pc.buf; x *= np.clip(np.arange(tr.N) / SR / 1.2, 0, 1)
    return np.stack([x, x], 1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--prologue', type=float, default=14.0); ap.add_argument('--duration', type=float, required=True)
    ap.add_argument('--out', default='score.wav'); ap.add_argument('--quiet', default=''); ap.add_argument('--dark', default='')
    ap.add_argument('--cuts', default=''); ap.add_argument('--hits', default=''); ap.add_argument('--sa', type=float, default=146.83)
    a = ap.parse_args(); xf = 0.6
    s = story(a)
    if a.prologue > 0:
        p = prologue(a, xf); n = int(xf * SR); ramp = np.linspace(0, 1, n)[:, None]
        p[-n:] = p[-n:] * (1 - ramp) + s[:n] * ramp      # crossfade; the prologue is xf longer so the story starts on time
        s = np.concatenate([p, s[n:]])
    s /= np.abs(s).max() / 0.85
    w = wave.open(a.out, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((s * 32767).astype(np.int16).tobytes()); w.close()
    print('wrote', a.out, round(len(s) / SR, 2), 's')

if __name__ == '__main__':
    main()
