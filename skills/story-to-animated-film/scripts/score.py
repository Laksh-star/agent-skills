#!/usr/bin/env python3
"""Generate a gentle Indian-classical-coloured score for a film: tambura drone, a wandering
bamboo-flute line, bells on scene changes, and low hits on dramatic events.

  python3 score.py --duration 146 --out score.wav \
      --scale mohanam --dark 15-25,107-117 --dark-scale shivaranjani \
      --bells 25,47,55,71 --hits 17.9,110.6 --sa 146.83

--dark     time ranges that switch the melody to --dark-scale and soften it (grief, curse)
--bells    scene-change times (a soft bell)
--hits     dramatic moments (a low struck tone)
--sa       tonic in Hz (146.83 = D)
Scales are given as semitone steps from Sa (5-note scales). Add your own in SCALES.
Output: 44.1 kHz stereo WAV, peak-normalised. Loudness-normalise when muxing (-16 LUFS).
"""
import argparse, random, wave
import numpy as np
from scipy.signal import fftconvolve

SCALES = {'mohanam': [0, 2, 4, 7, 9], 'shivaranjani': [0, 2, 3, 7, 9], 'hindolam': [0, 3, 5, 8, 10],
          'madhyamavati': [0, 2, 5, 7, 10], 'hamsadhwani': [0, 4, 4, 7, 11]}
SR = 44100

def ranges(s):
    out = []
    for part in filter(None, (s or '').split(',')):
        a, b = part.split('-'); out.append((float(a), float(b)))
    return out

def times(s): return [float(x) for x in filter(None, (s or '').split(','))]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--duration', type=float, required=True); ap.add_argument('--out', default='score.wav')
    ap.add_argument('--scale', default='mohanam'); ap.add_argument('--dark-scale', default='shivaranjani'); ap.add_argument('--dark', default='')
    ap.add_argument('--bells', default=''); ap.add_argument('--hits', default=''); ap.add_argument('--sa', type=float, default=146.83)
    ap.add_argument('--start', type=float, default=6.5, help='when the flute enters'); ap.add_argument('--seed', type=int, default=11)
    a = ap.parse_args(); D = a.duration; N = int(SR * D); SA = a.sa; dark = ranges(a.dark)
    isdark = lambda t: any(x <= t < y for x, y in dark)
    def add(buf, start, sig):
        i = int(start * SR)
        if 0 <= i < N: sig = sig[:N - i]; buf[i:i + len(sig)] += sig
    # tambura: plucked Pa-Sa'-Sa'-Sa cycle with a jawari-like moving partial
    def pluck(f, d=4.2):
        t = np.arange(int(d * SR)) / SR; s = np.zeros_like(t)
        for k in range(1, 16):
            amp = (1 / k) * (1 + 1.6 * np.exp(-((k - 6) / 2.5) ** 2) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.45 * t + k)))
            s += amp * np.sin(2 * np.pi * f * k * t + 0.3 * k) * np.exp(-t * (0.55 + 0.07 * k))
        return s * np.minimum(1, t / 0.012)
    tam = np.zeros(N); cyc = [SA * 1.5, SA * 2, SA * 2, SA]; pl = {f: pluck(f) for f in set(cyc)}; t = 0.3; i = 0
    while t < D - 3: add(tam, t, pl[cyc[i % 4]] * 0.11); t += 1.15; i += 1
    # flute
    rng = random.Random(a.seed); fl = np.zeros(N); phase = [0.0]
    def note(f0, f1, d, vol):
        n = int(d * SR); tt = np.arange(n) / SR; g = np.clip(tt / 0.07, 0, 1); f = f0 + (f1 - f0) * (g * g * (3 - 2 * g))
        vib = 1 + 0.005 * np.sin(2 * np.pi * 5.2 * tt) * np.clip((tt - 0.25) / 0.3, 0, 1)
        ph = phase[0] + 2 * np.pi * np.cumsum(f * vib) / SR; phase[0] = ph[-1]
        env = np.clip(tt / 0.08, 0, 1) * np.clip((d - tt) / 0.14, 0, 1)
        return vol * env * (np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.07 * np.sin(3 * ph))
    t = a.start; idx = 5; prev = None
    while t < D - 12:
        sc = SCALES[a.dark_scale if isdark(t) else a.scale]; vol = 0.13 if isdark(t) else 0.16
        ln = rng.choice([4, 5, 6, 7])
        for k in range(ln):
            last = k == ln - 1
            idx = min([0, 3, 5, 8], key=lambda x: abs(x - idx)) if last else max(-2, min(9, idx + rng.choice([-2, -1, -1, 1, 1, 2])))
            d = rng.choice([1.9, 2.4]) if last else rng.choice([.45, .6, .6, .9, 1.2])
            o, dg = divmod(idx, 5); f = SA * 2 * 2 ** ((sc[dg] + 12 * o) / 12)
            add(fl, t, note(prev or f, f, d, vol)); prev = f; t += d * 0.97
        prev = None; t += rng.choice([1.4, 2.0, 2.6])
    def bell(f=1760, d=3.0):
        tt = np.arange(int(d * SR)) / SR
        return (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 2.76 * tt) + 0.25 * np.sin(2 * np.pi * f * 5.4 * tt)) * np.exp(-tt * 2.2) * np.clip(tt / 0.004, 0, 1)   # 4 ms attack: no click for AAC to overshoot on
    bl = np.zeros(N)
    for bt in [0.8] + times(a.bells): add(bl, bt, bell() * 0.05)
    for ht in times(a.hits): add(bl, ht, bell(210, 2.5) * 0.25)
    dry = tam + fl + bl; n_ir = int(1.6 * SR); r = np.random.RandomState(3)
    wet = lambda: fftconvolve(fl + bl + 0.3 * tam, r.randn(n_ir) * np.exp(-np.arange(n_ir) / SR * 3.2))[:N] * 0.035
    tt = np.arange(N) / SR; fade = np.clip(tt / 1.5, 0, 1) * np.clip((D - tt) / 3.0, 0, 1)
    st = np.stack([dry + wet(), dry + wet()], 1) * fade[:, None]; st /= np.abs(st).max() / 0.85
    w = wave.open(a.out, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes()); w.close()
    print('wrote', a.out, D, 's')

if __name__ == '__main__':
    main()
