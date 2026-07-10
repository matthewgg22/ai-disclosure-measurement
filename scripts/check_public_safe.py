#!/usr/bin/env python3
# Usage: python3 scripts/check_public_safe.py   # run BEFORE every commit
"""
Local pre-commit safety gate for this PUBLIC repo.

This repo is the deliberately-scrubbed *measurement layer* of a larger research
project. It must never contain (a) individual issuers named as suspects, (b) a
set of specific network-entity names, or (c) issuer-level (per-company) data —
only aggregate/statistical content. This script is the automated backstop for
that wall. It is meant to be run locally before committing; it is intentionally
NOT wired into public CI, because the entity denylist itself is sensitive and
must never be committed to a public repo.

Two layers of check:

  1. STRUCTURAL (always runs, no secrets needed):
       - no absolute macOS home-directory developer paths in source/docs
       - every data file under data/aggregates/ is AGGREGATE-shaped: it has a
         `year` column, has NO issuer-identifying column (cik/ticker/cusip/
         name/issuer/company/accession/cusip), and has a small row count.

  2. ENTITY DENYLIST (runs only if a LOCAL denylist file is present):
       - scans tracked text for any forbidden entity token.
       - The denylist lives OUTSIDE the repo. Point AI_WASH_DENYLIST at a file
         (one token per line, '#' comments allowed), or drop it at
         ~/.config/ai-washing/denylist.txt. If absent, this layer is SKIPPED
         with a loud warning — the structural layer still runs.

Exit code 0 = clean, 1 = a violation was found (or a hard error).
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGG_DIR = os.path.join(ROOT, "data", "aggregates")

# Columns that would indicate issuer-level (per-company) granularity. If any
# committed aggregate file carries one of these, the file is NOT aggregate and
# must not be public.
FORBIDDEN_COLS = {
    "cik", "cik_str", "ticker", "tickers", "cusip", "isin", "lei",
    "name", "company", "companyname", "issuer", "issuername",
    "accession", "accession_no", "accessionnumber", "filer",
}
MAX_AGG_ROWS = 1000  # per-year (± per-sector) aggregates; a company list would be
                     # larger AND caught by the issuer-column check below

# File extensions we scan for developer paths / entity tokens.
TEXT_EXTS = {".py", ".md", ".txt", ".csv", ".json", ".yml", ".yaml", ".cfg", ".ini", ".cff"}

# Directories to skip while walking.
SKIP_DIRS = {".git", "__pycache__", ".venv", "env", "node_modules"}


def iter_tracked_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in TEXT_EXTS:
                yield os.path.join(dirpath, fn)


def rel(p):
    return os.path.relpath(p, ROOT)


def check_dev_paths():
    """No absolute macOS home paths in source or docs (data/ is exempt: SEC data
    can legitimately contain the substring, and data/ is git-ignored anyway)."""
    # Build the needle from parts so this checker does not flag its own source.
    needle = "/" + "Users" + "/"
    fails = []
    for p in iter_tracked_files():
        ext = os.path.splitext(p)[1].lower()
        if ext not in {".py", ".md", ".txt", ".yml", ".yaml"}:
            continue
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if needle in text:
            fails.append(rel(p))
    return fails


def check_aggregate_schema():
    """Every committed data/aggregates/*.csv must be aggregate-shaped."""
    fails = []
    if not os.path.isdir(AGG_DIR):
        return fails  # nothing committed yet
    for fn in sorted(os.listdir(AGG_DIR)):
        if not fn.lower().endswith(".csv"):
            # Only CSV aggregates are supported for the schema check. Flag
            # anything else so a stray file can't slip in unreviewed.
            if fn.lower() not in {".gitkeep", "readme.md"}:
                fails.append(f"{fn}: non-CSV file in data/aggregates/ (review manually)")
            continue
        path = os.path.join(AGG_DIR, fn)
        try:
            with open(path, newline="", encoding="utf-8", errors="replace") as fh:
                reader = csv.reader(fh)
                header = next(reader, [])
                nrows = sum(1 for _ in reader)
        except OSError as e:
            fails.append(f"{fn}: unreadable ({e})")
            continue
        cols = [c.strip().strip('"').lower() for c in header]
        bad = sorted(set(cols) & FORBIDDEN_COLS)
        if bad:
            fails.append(f"{fn}: issuer-level column(s) present: {bad}")
        if "year" not in cols:
            fails.append(f"{fn}: no 'year' column — not a per-year aggregate")
        if nrows > MAX_AGG_ROWS:
            fails.append(f"{fn}: {nrows} rows > {MAX_AGG_ROWS} — too granular to be an aggregate")
    return fails


def load_denylist():
    path = os.environ.get("AI_WASH_DENYLIST") or os.path.expanduser(
        "~/.config/ai-washing/denylist.txt"
    )
    if not os.path.isfile(path):
        return None, path
    tokens = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line and not line.startswith("#"):
            tokens.append(line.lower())
    return tokens, path


def check_entities(tokens):
    fails = []
    for p in iter_tracked_files():
        # data/ is git-ignored; only data/aggregates/ is tracked, and it is
        # scanned too (a stray issuer name in an aggregate would be caught here).
        try:
            text = open(p, encoding="utf-8", errors="replace").read().lower()
        except OSError:
            continue
        for tok in tokens:
            if tok in text:
                fails.append(f"{rel(p)}: forbidden token '{tok}'")
    return fails


def main():
    all_fails = []

    dev = check_dev_paths()
    all_fails += [f"[dev-path] {x}" for x in dev]

    schema = check_aggregate_schema()
    all_fails += [f"[schema] {x}" for x in schema]

    tokens, dl_path = load_denylist()
    if tokens is None:
        sys.stderr.write(
            "WARNING: entity denylist not found at %s (set AI_WASH_DENYLIST).\n"
            "         Structural checks ran; entity-name scan SKIPPED.\n" % dl_path
        )
    else:
        ent = check_entities(tokens)
        all_fails += [f"[entity] {x}" for x in ent]

    if all_fails:
        print("PUBLIC-SAFE CHECK: FAIL")
        for f in all_fails:
            print("  " + f)
        return 1
    print("PUBLIC-SAFE CHECK: clean"
          + ("" if tokens is not None else " (entity scan skipped — no denylist)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
