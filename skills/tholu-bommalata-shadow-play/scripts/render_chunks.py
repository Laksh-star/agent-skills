#!/usr/bin/env python3
"""Render a film module to MP4 in chunks, then join and add the score.

A film module defines W, H, FPS, DUR and render(t) -> RGBA numpy array.

  # one chunk (keep each under ~10 minutes of wall time; ~1300 frames on 2 cores)
  python3 render_chunks.py chunk path/to/film.py 0 1300 part_a.mp4
  # join chunks and mux audio, loudness-normalised to -16 LUFS
  python3 render_chunks.py join final.mp4 score.wav part_a.mp4 part_b.mp4 ...
  # print the chunk commands for a whole film
  python3 render_chunks.py plan path/to/film.py

Why chunks: many agent sandboxes stop background processes soon after the agent's turn ends.
Rendering in short foreground chunks survives that; the join is a lossless concat.
Environment variables (FONTS_DIR, FILM_LANG, ...) pass through to the film module.
"""
import importlib.util, os, subprocess, sys, tempfile
from multiprocessing import Pool

_film = None
def _load(path):
    spec = importlib.util.spec_from_file_location('film', os.path.abspath(path)); m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(os.path.abspath(path))); spec.loader.exec_module(m); return m

def _init(path):
    global _film; _film = _load(path)

def _job(i): return _film.render(i / _film.FPS)[..., :3].tobytes()

def chunk(path, a, b, out):
    film = _load(path)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{film.W}x{film.H}', '-r', str(film.FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=_init, initargs=(path,)) as p:
        for fr in p.imap(_job, range(a, b), chunksize=4): ff.stdin.write(fr)
    ff.stdin.close(); ff.wait(); print('done', out, b - a, 'frames')

def join(out, audio, parts):
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
        for p in parts: f.write(f"file '{os.path.abspath(p)}'\n")
        lst = f.name
    video = out + '.video.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', video], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-i', audio, '-map', '0:v', '-map', '1:a', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
                    '-ar', '48000', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '224k', '-shortest', '-movflags', '+faststart', out], check=True)
    os.remove(video); os.remove(lst); print('wrote', out)

def plan(path, size=1300):
    film = _load(path); n = int(film.DUR * film.FPS); parts = []
    for i, a in enumerate(range(0, n, size)):
        part = f'part_{i:02d}.mp4'; parts.append(part)
        print(f'python3 {sys.argv[0]} chunk {path} {a} {min(n, a + size)} {part}')
    print(f'python3 {sys.argv[0]} join final.mp4 score.wav ' + ' '.join(parts))

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'chunk': chunk(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
    elif cmd == 'join': join(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif cmd == 'plan': plan(sys.argv[2])
    else: sys.exit(__doc__)
