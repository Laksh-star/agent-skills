#!/usr/bin/env python3
"""Quality gate for the agent-skills catalog.

Stdlib only. Run from the repo root:

    python3 scripts/validate-skills.py            # errors fail, warnings print
    python3 scripts/validate-skills.py --strict   # warnings fail too
    python3 scripts/validate-skills.py --skill wiki-maintainer

Checks (see CONTRIBUTING.md for the rationale behind each gate):
  1. spec        frontmatter, name == folder, kebab-case, description + trigger
  2. size        SKILL.md line/word budget (progressive disclosure)
  3. links       every relative link / referenced bundled file exists
  4. scripts     syntax check for .py / .js / .mjs / .sh (no bytecode written)
  5. secrets     API keys, tokens, private keys, credentialed URLs
  6. privacy     personal home paths and email addresses
  7. portability host-specific paths/variables unless declared in metadata.hosts
  8. freshness   docs/<name>.md carries a "Last verified: YYYY-MM-DD" line
  9. overlap     descriptions that compete for the same requests
 10. hygiene     no bytecode, OS junk, archives, env files inside skills/
 11. catalog     README links the skill; docs/<name>.md exists
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
DOCS_DIR = ROOT / "docs"
README = ROOT / "README.md"

ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TRIGGER_RE = re.compile(r"\buse\b[^.]{0,60}?\bwhen(ever)?\b", re.I)
MAX_LINES = 500
WARN_WORDS = 5000
MAX_DESC = 1024
WARN_DESC = 900
OVERLAP_WARN = 0.30

SECRET_PATTERNS = {
    "OpenAI-style key": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}",
    "GitHub token": r"\bgh[pousr]_[A-Za-z0-9]{30,}",
    "AWS access key": r"\bAKIA[0-9A-Z]{16}\b",
    "Google API key": r"\bAIza[0-9A-Za-z_-]{35}\b",
    "Slack token": r"\bxox[baprs]-[A-Za-z0-9-]{10,}",
    "private key block": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "credentialed URL": r"\b[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s@/<>{}$]{6,}@",
    "bearer token": r"\bBearer\s+[A-Za-z0-9._-]{30,}",
}
PRIVACY_PATTERNS = {
    "personal home path": r"(?<![\w/])(?:/Users|/home)/(?!<|\{|\$|user\b|username\b|you\b|me\b|runner\b|example\b)[A-Za-z0-9._-]+",
    "email address": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
}
EMAIL_ALLOW = re.compile(r"^(git@github\.com|.*@example\.(com|org)|.*noreply.*|.*@users\.noreply\.github\.com)$", re.I)

# token -> host that legitimately owns it
HOST_TOKENS = {
    r"~/\.codex\b": "codex",
    r"\bCODEX_HOME\b": "codex",
    r"~/\.claude\b": "claude",
    r"\$\{?CLAUDE_PLUGIN_ROOT\}?": "claude",
    r"\$ARGUMENTS\b": "claude",
    r"\bmcp__[a-z0-9_-]+__": "claude",
    r"~/\.gemini\b": "antigravity",
}
JUNK_NAMES = {".DS_Store", "Thumbs.db", ".env"}
JUNK_DIRS = {"__pycache__", "node_modules", "dist", ".pytest_cache", ".venv"}
JUNK_SUFFIXES = {".pyc", ".pyo", ".skill", ".zip", ".tar", ".gz", ".tgz"}
TEXT_SUFFIXES = {".md", ".py", ".js", ".mjs", ".cjs", ".ts", ".sh", ".json", ".yaml", ".yml", ".toml", ".txt", ".sql", ".html", ".css", ""}

STOPWORDS = set("""a an and or the to of for in on with from into by as at is are be use used using when whenever this that
it its user users asks ask wants want skill agent any local your their run runs running build builds create make
including include includes such via e g eg etc not only also other more can should will help""".split())


@dataclass
class Report:
    skill: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def err(self, gate: str, msg: str) -> None:
        self.errors.append(f"[{gate}] {msg}")

    def warn(self, gate: str, msg: str) -> None:
        self.warnings.append(f"[{gate}] {msg}")


# ---------------------------------------------------------------- frontmatter
def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Minimal YAML subset: scalars, quoted scalars, folded/literal blocks, one-level maps."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    block, body = text[4:end], text[end + 5:]
    data: dict = {}
    lines = block.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).rstrip()
        if val in (">", ">-", ">+", "|", "|-", "|+"):
            chunk = []
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or lines[i] == ""):
                chunk.append(lines[i].strip())
                i += 1
            joiner = " " if val.startswith(">") else "\n"
            data[key] = joiner.join(c for c in chunk).strip()
            continue
        if val == "":
            sub: dict = {}
            i += 1
            while i < len(lines) and lines[i].startswith(" "):
                sm = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*)$", lines[i])
                if sm:
                    sub[sm.group(1)] = sm.group(2).strip().strip("\"'")
                i += 1
            data[key] = sub
            continue
        data[key] = val.strip().strip("\"'")
        i += 1
    return data, body


# ---------------------------------------------------------------- helpers
def iter_files(skill_dir: Path):
    for dp, dns, fns in os.walk(skill_dir):
        for d in dns:
            yield Path(dp) / d, True
        for f in fns:
            yield Path(dp) / f, False


def strip_code_for_links(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def tokens(desc: str) -> set[str]:
    words = re.findall(r"[a-z][a-z0-9-]{2,}", desc.lower())
    return {w for w in words if w not in STOPWORDS}


def syntax_check(path: Path) -> str | None:
    suffix = path.suffix
    try:
        if suffix == ".py":
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
            return None
        if suffix in (".js", ".mjs", ".cjs"):
            if not shutil.which("node"):
                return "node not installed; skipped"
            p = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        elif suffix == ".sh":
            p = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
        else:
            return None
    except SyntaxError as e:
        return f"{e.msg} (line {e.lineno})"
    return None if p.returncode == 0 else (p.stderr.strip().splitlines() or ["failed"])[-1][:200]


# ---------------------------------------------------------------- checks
def check_skill(skill_dir: Path, readme_text: str) -> tuple[Report, dict]:
    name = skill_dir.name
    r = Report(name)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        r.err("spec", "missing SKILL.md")
        return r, {}
    text = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    # 1. spec
    if fm is None:
        r.err("spec", "missing or malformed YAML frontmatter")
        fm = {}
    extra = set(fm) - ALLOWED_KEYS
    if extra:
        r.err("spec", f"unknown frontmatter keys: {sorted(extra)}")
    fname = fm.get("name", "")
    if fname != name:
        r.err("spec", f"name '{fname}' does not match folder '{name}'")
    if not NAME_RE.match(name) or len(name) > 64:
        r.err("spec", "folder name must be kebab-case, <= 64 chars")
    desc = fm.get("description", "")
    if not desc:
        r.err("spec", "description is empty")
    elif len(desc) > MAX_DESC:
        r.err("spec", f"description is {len(desc)} chars (max {MAX_DESC})")
    elif len(desc) > WARN_DESC:
        r.warn("spec", f"description is {len(desc)} chars (near the {MAX_DESC} limit)")
    if desc and not TRIGGER_RE.search(desc):
        r.err("spec", "description lacks a 'Use when ...' trigger clause")
    meta = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}
    hosts = {h.strip() for h in meta.get("hosts", "").split(",") if h.strip()}

    # 2. size
    n_lines, n_words = text.count("\n") + 1, len(text.split())
    if n_lines > MAX_LINES:
        r.err("size", f"SKILL.md has {n_lines} lines (max {MAX_LINES}); move detail into references/")
    if n_words > WARN_WORDS:
        r.warn("size", f"SKILL.md has {n_words} words; consider moving detail into references/")

    # 3. links
    prose = strip_code_for_links(body)
    refs = set(re.findall(r"\]\(([^)\s#]+)(?:#[^)]*)?\)", prose))
    refs |= set(re.findall(r"`((?:references|scripts|assets|agents)/[^`\s*<>]+)`", body))
    for ref in sorted(refs):
        if re.match(r"^[a-z]+:", ref):
            continue
        if not (skill_dir / ref).resolve().exists():
            r.err("links", f"SKILL.md references missing file: {ref}")

    # walk bundled files
    for path, is_dir in iter_files(skill_dir):
        rel = path.relative_to(skill_dir)
        # 10. hygiene
        if is_dir:
            if path.name in JUNK_DIRS:
                r.err("hygiene", f"remove generated directory: {rel}/")
            continue
        if path.name in JUNK_NAMES or path.suffix in JUNK_SUFFIXES or path.name.startswith(".env"):
            r.err("hygiene", f"remove generated/secret-prone file: {rel}")
            continue
        if any(part in JUNK_DIRS for part in rel.parts):
            continue
        if path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        # 4. scripts
        problem = syntax_check(path)
        if problem:
            (r.warn if "skipped" in problem else r.err)("scripts", f"{rel}: {problem}")
        # 5. secrets
        for label, pat in SECRET_PATTERNS.items():
            for m in re.finditer(pat, content):
                r.err("secrets", f"{rel}: possible {label}: {m.group(0)[:12]}...")
        # 6. privacy
        for m in re.finditer(PRIVACY_PATTERNS["personal home path"], content):
            r.err("privacy", f"{rel}: personal path '{m.group(0)}'")
        for m in re.finditer(PRIVACY_PATTERNS["email address"], content):
            if not EMAIL_ALLOW.match(m.group(0)):
                r.err("privacy", f"{rel}: email address '{m.group(0)}'")
        # 7. portability (agents/<host>.yaml is the sanctioned place for host specifics)
        if rel.parts[0] == "agents":
            continue
        for pat, host in HOST_TOKENS.items():
            if host in hosts:
                continue
            for m in re.finditer(pat, content):
                r.err("portability", f"{rel}: '{m.group(0)}' is {host}-specific; generalize it or declare metadata.hosts: {host}")
                break

    # 8 + 11. docs, freshness, catalog
    doc = DOCS_DIR / f"{name}.md"
    if not doc.exists():
        r.err("catalog", f"missing docs/{name}.md")
    else:
        dtext = doc.read_text(encoding="utf-8")
        if not re.search(r"Last verified:\**\s*\d{4}-\d{2}-\d{2}", dtext):
            r.err("freshness", f"docs/{name}.md lacks a 'Last verified: YYYY-MM-DD' line")
    if f"skills/{name}/SKILL.md" not in readme_text:
        r.err("catalog", "README.md does not link this skill")

    return r, {"desc": desc}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--skill", action="append", help="validate only these skill folders")
    args = ap.parse_args()

    readme_text = README.read_text(encoding="utf-8") if README.exists() else ""
    dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()) if SKILLS_DIR.exists() else []
    if args.skill:
        dirs = [d for d in dirs if d.name in set(args.skill)]
    if not dirs:
        print("no skills found", file=sys.stderr)
        return 1

    reports, descs = [], {}
    for d in dirs:
        rep, info = check_skill(d, readme_text)
        reports.append(rep)
        if info.get("desc"):
            descs[d.name] = tokens(info["desc"])

    # 9. overlap (pairwise Jaccard over description keywords)
    names = sorted(descs)
    by_name = {r.skill: r for r in reports}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            union = descs[a] | descs[b]
            if not union:
                continue
            score = len(descs[a] & descs[b]) / len(union)
            if score >= OVERLAP_WARN:
                by_name[a].warn("overlap", f"description overlaps '{b}' (jaccard {score:.2f}); sharpen triggers")

    n_err = n_warn = 0
    for rep in reports:
        status = "FAIL" if rep.errors or (args.strict and rep.warnings) else "ok"
        print(f"{status:4}  {rep.skill}")
        for e in rep.errors:
            print(f"      error   {e}")
        for w in rep.warnings:
            print(f"      warn    {w}")
        n_err += len(rep.errors)
        n_warn += len(rep.warnings)
    print(f"\n{len(reports)} skills · {n_err} errors · {n_warn} warnings")
    return 1 if n_err or (args.strict and n_warn) else 0


if __name__ == "__main__":
    sys.exit(main())
