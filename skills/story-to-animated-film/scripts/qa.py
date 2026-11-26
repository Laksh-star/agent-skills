#!/usr/bin/env python3
"""Measure a rendered film before delivery. Writes a report and two sheets to look at.

  python3 qa.py final.mp4 [--story story.md] [--out qa/] [--aspect 16:9|9:16] [--fps 24]
               [--max 150] [--holds 0-7,140-146] [--caption-band bottom|top|none]

Checks (exit 1 if any fails):
  size and frame rate     match the aspect (1920x1080 or 1080x1920) and fps
  audio                   an audio stream exists and is within 0.25 s of the video's length
  duration                at or under Max duration (+2 s grace)
  loudness                integrated -17 to -15 LUFS; true peak at or under -1 dBTP
  black frames            no black stretch over 0.3 s outside the first and last 1.5 s
  liveliness              the picture never sits still for 4 s or more outside intended holds
                          (title and end cards, listed in --holds or the story's Holds: header);
                          blinks and lamp flicker alone do not count as change
  story                   story.md problems (sources, origin, hook, caption timing and reading speed)

Also writes:
  qa/contact.jpg   one frame every N seconds across the whole film (4 across)
  qa/opening.jpg   the first 6 seconds at 1 frame a second: does it hook with the sound off?
  qa/report.md     the results
Inspired by the QA step in petergyang/video-explainer (MIT); written for this pipeline.
"""
import argparse, json, os, re, subprocess, sys
import numpy as np

LIVE_W, LIVE_H, LIVE_FPS = 96, 54, 2.0
LIVE_THRESH = 0.35       # mean grey-level change per 0.5 s that counts as visible motion
FROZEN_LIMIT = 4.0       # seconds

def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)

def probe(video):
    j = json.loads(run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate,duration:format=duration', '-of', 'json', video]).stdout)
    v = next(s for s in j['streams'] if s['codec_type'] == 'video'); a = next((s for s in j['streams'] if s['codec_type'] == 'audio'), None)
    num, den = v['r_frame_rate'].split('/')
    return dict(w=v['width'], h=v['height'], fps=float(num) / float(den), vdur=float(v.get('duration') or j['format']['duration']),
                adur=float(a['duration']) if a and a.get('duration') else None, audio=a is not None)

def loudness(video):
    err = run(['ffmpeg', '-nostats', '-i', video, '-af', 'ebur128=peak=true', '-f', 'null', '-']).stderr
    i = re.findall(r'I:\s+(-?[\d.]+)\s+LUFS', err); p = re.findall(r'Peak:\s+(-?inf|-?[\d.]+)\s+dBFS', err)
    return (float(i[-1]) if i else None), (float(p[-1]) if p and p[-1] != '-inf' else None)

def blacks(video):
    err = run(['ffmpeg', '-nostats', '-i', video, '-vf', 'blackdetect=d=0.3:pix_th=0.06', '-an', '-f', 'null', '-']).stderr
    return [(float(a), float(b)) for a, b in re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', err)]

def liveliness(video, band, holds):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vf', f'fps={LIVE_FPS:g},scale={LIVE_W}:{LIVE_H}', '-an', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    n = len(raw) // (LIVE_W * LIVE_H)
    if n < 3: return [], []
    fr = np.frombuffer(raw[:n * LIVE_W * LIVE_H], np.uint8).reshape(n, LIVE_H, LIVE_W).astype(np.float32)
    if band == 'bottom': fr = fr[:, :int(LIVE_H * .78)]
    elif band == 'top': fr = fr[:, int(LIVE_H * .34):]
    d = np.abs(fr[1:] - fr[:-1])
    d = np.where(d > 6, d, 0).mean(axis=(1, 2))          # ignore tiny changes: flicker, film grain, blinks in a wide shot
    t = (np.arange(len(d)) + 1) / LIVE_FPS
    frozen, start = [], None
    for ti, di in zip(t, d):
        held = any(a <= ti <= b for a, b in holds)
        if di < LIVE_THRESH and not held:
            start = ti if start is None else start
        else:
            if start is not None and ti - start >= FROZEN_LIMIT: frozen.append((start, ti))
            start = None
    if start is not None and t[-1] - start >= FROZEN_LIMIT: frozen.append((start, t[-1]))
    return frozen, d

def sheet(video, out, times, cols=4, w=480):
    from PIL import Image
    ims = []
    for t in times:
        p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', video, '-frames:v', '1', '-vf', f'scale={w}:-2', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
        if p:
            import io; ims.append(Image.open(io.BytesIO(p)).convert('RGB'))
    if not ims: return
    h = ims[0].height; S = Image.new('RGB', (cols * w, ((len(ims) + cols - 1) // cols) * h))
    for i, im in enumerate(ims): S.paste(im, ((i % cols) * w, (i // cols) * h))
    S.save(out, quality=85)

def ranges(s):
    out = []
    for part in filter(None, (s or '').split(',')):
        a, b = part.split('-'); out.append((float(a), float(b)))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--story'); ap.add_argument('--out', default='qa')
    ap.add_argument('--aspect'); ap.add_argument('--fps', type=float, default=24); ap.add_argument('--max', type=float)
    ap.add_argument('--holds', default=''); ap.add_argument('--caption-band', default=None)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    S = None
    if a.story:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from story import load, problems; S = load(a.story)
    m = probe(a.video); rows = []
    aspect = a.aspect or (S.header('Aspect') if S else None) or ('9:16' if m['h'] > m['w'] else '16:9')
    want = (1080, 1920) if aspect == '9:16' else (1920, 1080)
    band = a.caption_band or ('top' if aspect == '9:16' else 'bottom')
    mx = a.max or (S.header('Max duration') if S else None)
    holds = ranges(a.holds) + (S.ranges('Holds') if S else [])
    def check(name, ok, detail): rows.append((name, bool(ok), detail))
    check('size and frame rate', (m['w'], m['h']) == want and abs(m['fps'] - a.fps) < .01, f"{m['w']}x{m['h']} at {m['fps']:g} fps (want {want[0]}x{want[1]} at {a.fps:g})")
    check('audio', m['audio'] and m['adur'] is not None and abs(m['adur'] - m['vdur']) <= .25,
          f"audio {m['adur']}s vs video {m['vdur']:.2f}s" if m['audio'] else 'no audio stream')
    check('duration', mx is None or m['vdur'] <= mx + 2, f"{m['vdur']:.1f}s" + (f" (max {mx:g}s)" if mx else ' (no maximum set)'))
    lufs, peak = loudness(a.video)
    check('loudness', lufs is not None and -17 <= lufs <= -15 and peak is not None and peak <= -1.0, f'{lufs} LUFS integrated, true peak {peak} dBTP')
    bl = [(s, e) for s, e in blacks(a.video) if s > 1.5 and e < m['vdur'] - 1.5]
    check('black frames', not bl, ', '.join(f'{s:.1f}-{e:.1f}s' for s, e in bl) or 'none outside the fades')
    frozen, d = liveliness(a.video, band, holds)
    check('liveliness', not frozen, ('still for ' + ', '.join(f'{s:.1f}-{e:.1f}s' for s, e in frozen)) if frozen else
          f"never still for {FROZEN_LIMIT:g}s outside holds; {100 * float(np.mean(np.asarray(d) >= LIVE_THRESH)):.0f}% of half-seconds show visible change")
    if S:
        P = problems(S); check('story', not P, '; '.join(P) or 'sources, origin, hook and caption timing OK')
    step = max(2.0, m['vdur'] / 24)
    sheet(a.video, os.path.join(a.out, 'contact.jpg'), list(np.arange(step / 2, m['vdur'], step)))
    sheet(a.video, os.path.join(a.out, 'opening.jpg'), [0.5, 1.5, 2.5, 3.5, 4.5, 5.5], cols=3)
    passed = sum(ok for _, ok, _ in rows)
    lines = [f'# QA: {os.path.basename(a.video)}', '', f'{passed}/{len(rows)} checks passed', '', '| Check | Result | Detail |', '|---|---|---|']
    lines += [f"| {n} | {'pass' if ok else 'FAIL'} | {det} |" for n, ok, det in rows]
    lines += ['', 'Look at contact.jpg and opening.jpg before delivering; then answer eval.md.']
    open(os.path.join(a.out, 'report.md'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    sys.exit(0 if passed == len(rows) else 1)

if __name__ == '__main__':
    main()
