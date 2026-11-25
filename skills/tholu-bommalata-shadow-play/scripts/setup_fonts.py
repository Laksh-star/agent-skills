#!/usr/bin/env python3
"""Fetch and convert the fonts the films use, and print a FONTS dict for core.py.

Usage:  python3 setup_fonts.py <out_dir> [la] [te] [dev] [ta] [kn]

Fonts come from the npm registry (@fontsource/*), which most sandboxes can reach.
  la   Cormorant Garamond 600, with its latin and latin-ext subsets MERGED, so IAST
       diacritics (a-macron, s-dot, n-dot) render instead of boxes
  te   Noto Serif Telugu 600
  dev  Tiro Devanagari Sanskrit 400
  ta   Noto Serif Tamil 600      (untested: render a test line first)
  kn   Noto Serif Kannada 600    (untested: render a test line first)
Requires: npm, fonttools, brotli.
"""
import glob, json, os, subprocess, sys, tarfile, tempfile
from fontTools.ttLib import TTFont
from fontTools.merge import Merger

PACKS = {
    'la': ('cormorant-garamond', ['latin-600-normal', 'latin-ext-600-normal']),
    'te': ('noto-serif-telugu', ['telugu-600-normal']),
    'dev': ('tiro-devanagari-sanskrit', ['devanagari-400-normal']),
    'ta': ('noto-serif-tamil', ['tamil-600-normal']),
    'kn': ('noto-serif-kannada', ['kannada-600-normal']),
}

def fetch(pkg, work):
    subprocess.run(['npm', 'pack', f'@fontsource/{pkg}'], cwd=work, check=True, capture_output=True)
    tgz = sorted(glob.glob(os.path.join(work, f'fontsource-{pkg}-*.tgz')))[-1]
    dest = os.path.join(work, pkg)
    with tarfile.open(tgz) as t:
        try: t.extractall(dest, filter='data')
        except TypeError: t.extractall(dest)
    return os.path.join(dest, 'package', 'files')

def to_ttf(src, out):
    f = TTFont(src); f.flavor = None; f.save(out); return out

def main():
    out = os.path.abspath(sys.argv[1]); keys = sys.argv[2:] or ['la', 'te', 'dev']
    os.makedirs(out, exist_ok=True); fonts = {}
    with tempfile.TemporaryDirectory() as work:
        for k in keys:
            pkg, subsets = PACKS[k]; files = fetch(pkg, work)
            ttfs = [to_ttf(os.path.join(files, f'{pkg}-{s}.woff2'), os.path.join(work, f'{k}-{i}.ttf')) for i, s in enumerate(subsets)]
            dst = os.path.join(out, f'{k}.ttf')
            if len(ttfs) > 1: Merger().merge(ttfs).save(dst)
            else: os.replace(ttfs[0], dst)
            fonts[k] = dst
    print(json.dumps(fonts, indent=1))

if __name__ == '__main__':
    main()
