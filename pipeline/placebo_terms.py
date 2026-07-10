#!/usr/bin/env python3
# Usage: python3 pipeline/placebo_terms.py   # writes data/placebo_terms.csv (aggregate)
"""
Placebo comparison: is the AI label's marketing inflation distinctive, or does every
buzzword get the same treatment?

For a small set of hot terms (AI + controls), measure two shares of 10-K filers per year,
using the SAME construction for every term so the comparison is fair:
  - mention  : filers using the bare term
  - marketing: filers using the "<term>-powered" / "<term>-driven" marketing form

If "AI-powered / AI-driven" language towers over "blockchain-powered", "cloud-powered",
"quantum-powered", then the marketing-vs-substance decoupling documented for AI is not a
generic buzzword effect; it is specific to AI. That is the point of the uniform template:
the near-absence of "-powered" language for the controls is itself the finding.

Reuses ai_prevalence.py's cached 10-K denominator (data/_cache_tenk_counts.json). Pure
standard library. Output: data/placebo_terms.csv (aggregate: year, term, mention_pct,
marketing_pct). No issuer-level data.
"""
import csv, json, os, sys, time, urllib.parse, urllib.request

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
UA = {"User-Agent": "AI Washing Research (HKS PAE) matthewgreergentis@gmail.com"}
DEN_CACHE = os.path.join(DATA, "_cache_tenk_counts.json")   # {year: n_filers}, from ai_prevalence.py
DEN_CSV = os.path.join(DATA, "aggregates", "ai_prevalence.csv")  # committed fallback denominator
NUM_CACHE = os.path.join(DATA, "_cache_placebo.json")
START_YEAR, END_YEAR = 2001, 2025

# label -> (bare term, [uniform marketing forms]). Same "-powered/-driven" template for all.
TERMS = {
    "AI":         ('"artificial intelligence"', ['"AI-powered"', '"AI-driven"']),
    "blockchain": ('"blockchain"',              ['"blockchain-powered"', '"blockchain-driven"']),
    "cloud":      ('"cloud computing"',         ['"cloud-powered"', '"cloud-driven"']),
    "quantum":    ('"quantum computing"',       ['"quantum-powered"', '"quantum-driven"']),
}

_last = [0.0]
def _throttle(s=0.5):
    dt = time.time() - _last[0]
    if dt < s: time.sleep(s - dt)
    _last[0] = time.time()

def _load(p): return json.load(open(p)) if os.path.exists(p) else {}
def _save(p, o): json.dump(o, open(p, "w"))

def fts_count(phrase, year):
    """Number of 10-Ks matching a quoted phrase in a year (EDGAR full-text search)."""
    _throttle()
    p = {"q": phrase, "forms": "10-K", "startdt": f"{year}-01-01", "enddt": f"{year}-12-31"}
    url = "https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(p)
    for i in range(8):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45))
            return d.get("hits", {}).get("total", {}).get("value", 0)
        except Exception:
            sys.stderr.write(f"   retry {i+1} {phrase} {year}\n"); time.sleep(2.0 * (i + 1))
    return None

def load_denominator():
    """{year: n_10k_filers}. Prefer ai_prevalence.py's cache; fall back to the committed
    aggregate CSV so this script is self-contained after a fresh clone."""
    den = _load(DEN_CACHE)
    if den:
        return {int(k): int(v) for k, v in den.items()}
    if os.path.exists(DEN_CSV):
        return {int(r["year"]): int(r["n_10k_filers"]) for r in csv.DictReader(open(DEN_CSV))}
    return {}

def main():
    den = {str(k): v for k, v in load_denominator().items()}
    if not den:
        sys.exit("No denominator: run ai_prevalence.py, or ensure data/aggregates/ai_prevalence.csv exists.")
    num = _load(NUM_CACHE)
    rows = []
    for y in range(START_YEAR, END_YEAR + 1):
        d = den.get(str(y))
        if not d:
            sys.stderr.write(f"no denom for {y}, skipping\n"); continue
        for label, (bare, mkt_forms) in TERMS.items():
            # bare mention
            bk = f"{y}|{label}|bare"
            if bk not in num:
                v = fts_count(bare, y)
                if v is not None: num[bk] = v; _save(NUM_CACHE, num)
            # marketing forms (union approximated by summing; forms rarely co-occur)
            mk = f"{y}|{label}|mkt"
            if mk not in num:
                tot = 0
                for ph in mkt_forms:
                    v = fts_count(ph, y)
                    if v is not None: tot += v
                num[mk] = tot; _save(NUM_CACHE, num)
            mention_pct = round(100.0 * num.get(bk, 0) / d, 3)
            marketing_pct = round(100.0 * num.get(mk, 0) / d, 3)
            rows.append((y, label, d, mention_pct, marketing_pct))
        print(f"{y}: " + "  ".join(f"{lab} mkt={next(r[4] for r in rows if r[0]==y and r[1]==lab)}%"
                                   for lab in TERMS), flush=True)

    out = os.path.join(DATA, "placebo_terms.csv")
    with open(out, "w") as f:
        f.write("year,term,n_10k_filers,mention_pct,marketing_pct\n")
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")
    print(f"\n[done] wrote {os.path.relpath(out)}")

if __name__ == "__main__":
    main()
