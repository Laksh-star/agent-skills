#!/usr/bin/env python3
"""Read story.md, the single project file: headers, scenes and captions per language.

    from story import load
    S = load('story.md')
    S.header('Max duration', 150)        # -> 150.0 (numbers are converted)
    S.scene_starts['meet']               # -> 0.0
    S.captions('te')                     # -> [(start, end, [line1, line2]), ...]

    python3 story.py story.md            # validate and print a summary (exit 1 on problems)

Format (see ../references/story-format.md):

    # story.md: <slug>
    Style: storybook
    Languages: en, te
    Max duration: 150
    Hook: <the opening question or tension, in one line>
    Holds: 21-27                        # ranges where a still frame is intended (cards)

    ## Scenes
    | id | start | source | origin | beat |
    |---|---|---|---|---|
    | meet | 0 | Ch. 1, p. 3 | source | A girl walks to the teacher's tree |

    ## Captions: en
    - 5.6-10.6 | First line / second line

Any '## <Kind>: <lang>' block of timed lines is read the same way (the shadow play uses '## Prologue: te').
"""
import re, sys, unicodedata

class Story:
    def __init__(self, headers, scenes, caps):
        self.headers, self.scenes, self._caps = headers, scenes, caps
        self.scene_starts = {s['id']: s['start'] for s in scenes}

    def header(self, key, default=None):
        v = self.headers.get(key.lower(), default)
        if isinstance(v, str):
            try: return float(v)
            except ValueError: return v
        return v

    def languages(self):
        v = self.headers.get('languages', 'en')
        return [x.strip() for x in v.split(',') if x.strip()]

    def captions(self, lang, kind='captions'):
        """Cues from a '## Captions: <lang>' block, or another timed block such as '## Prologue: <lang>'."""
        return self._caps.get((kind.lower(), lang), [])

    def ranges(self, key):
        out = []
        for part in filter(None, str(self.headers.get(key.lower(), '')).split(',')):
            a, b = part.strip().split('-'); out.append((float(a), float(b)))
        return out

def load(path):
    headers, scenes, caps, section = {}, [], {}, None
    for raw in open(path, encoding='utf-8'):
        line = raw.rstrip('\n')
        if line.startswith('## '):
            title = line[3:].strip(); section = title.lower()
            if ':' in title and section.split(':')[0] != 'scenes':
                kind, lang = (x.strip() for x in title.split(':', 1)); caps.setdefault((kind.lower(), lang), [])
            continue
        if section is None:
            m = re.match(r'^([A-Za-z][A-Za-z ]+):\s*(.*?)\s*(#.*)?$', line)
            if m: headers[m.group(1).strip().lower()] = m.group(2)
        elif section == 'scenes' and line.startswith('|'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            if cells[0] in ('id', '') or set(cells[0]) <= set('-: '): continue
            scenes.append(dict(id=cells[0], start=float(cells[1]), source=cells[2] if len(cells) > 2 else '',
                               origin=cells[3] if len(cells) > 3 else '', beat=cells[4] if len(cells) > 4 else ''))
        elif section and ':' in section and line.lstrip().startswith('- '):
            m = re.match(r'^\s*-\s*([\d.]+)\s*-\s*([\d.]+)\s*\|\s*(.+)$', line)
            if m:
                kind, lang = (x.strip() for x in section.split(':', 1))
                key = next(k for k in caps if k[0] == kind and k[1].lower() == lang)
                caps[key].append((float(m.group(1)), float(m.group(2)), [t.strip() for t in m.group(3).split(' / ')]))
    return Story(headers, scenes, caps)

def problems(S):
    """Checks that need no video: caption timing and reading speed, scene order, source refs, the hook."""
    out = []
    starts = [s['start'] for s in S.scenes]
    if starts != sorted(starts): out.append('scene starts are not in order')
    for s in S.scenes:
        if not s['source']: out.append(f"scene {s['id']}: no source reference")
        if s['origin'] not in ('source', 'invented', 'mixed'): out.append(f"scene {s['id']}: origin must be source, invented or mixed")
    if not S.headers.get('hook'): out.append('no Hook: header (the opening question or tension)')
    for lang in S.languages():
        if not S.captions(lang): out.append(f'no captions for {lang}')
    for (kind, lang), caps in S._caps.items():
        prev_end = -1
        for a, b, lines in caps:
            if b <= a: out.append(f'{lang} {a}-{b}: ends before it starts')
            if a < prev_end: out.append(f'{lang} {a}-{b}: overlaps the previous caption')
            if len(lines) > 2: out.append(f'{lang} {a}-{b}: more than two lines')
            chars = sum(sum(1 for ch in l if not unicodedata.category(ch).startswith('M')) for l in lines)   # vowel signs ride on letters
            cps = chars / max(b - a, .1)
            if cps > 21: out.append(f'{lang} {a}-{b}: {cps:.0f} characters per second; keep under 21 so it can be read')
            prev_end = b
    return out

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'): print(__doc__); sys.exit(0)
    S = load(sys.argv[1]); P = problems(S)
    print(f"{len(S.scenes)} scenes, languages {S.languages()}, max duration {S.header('Max duration')}")
    for p in P: print('PROBLEM:', p)
    sys.exit(1 if P else 0)
