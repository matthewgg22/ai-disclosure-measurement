#!/usr/bin/env python3
# Usage: python3 pipeline/screen_signals.py   # writes data/screen_signals.csv (aggregate)
"""
Extraction-structure screening signals: measure, market-wide and over time, the disclosure
language of the capital-extraction toolkit that recurs in small-cap securities fraud.

This is the DETECTION-METHODOLOGY layer, kept strictly aggregate. It counts, per year, how
many 10-K filers use each red-flag phrase, as a share of all 10-K filers (the same
denominator as the AI figures). It names no issuer and ranks no issuer.

Signals (each computable from public EDGAR full-text search):
  - "pre-funded warrant"              the dilution instrument
  - "beneficial ownership limitation" the ownership blocker that keeps a holder below the
                                      Section 16 / 5% reporting threshold
  - BOTH in the same filing           the paired structure that routes dilution around
                                      Section 16 insider-disclosure (the sharpest fingerprint)
  - "reverse stock split"             the post-dilution reset (context; has legitimate uses)

IMPORTANT: these phrases all have legitimate uses. Rising prevalence means the extraction
TOOLKIT is spreading through public filings; it is a screening INPUT, not a finding of fraud.
A fraud determination requires the full multi-flag screen plus realized outcomes at the
issuer level, which is out of scope for this public, aggregate repo (see docs/SCREEN.md).

Reuses ai_prevalence.py's cached 10-K denominator (self-contained fallback to the committed
data/aggregates/ai_prevalence.csv). Pure standard library. Output: data/screen_signals.csv.
"""
import csv, json, os, sys, time, urllib.parse, urllib.request

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
UA = {"User-Agent": "AI Washing Research (HKS PAE) matthewgreergentis@gmail.com"}
DEN_CACHE = os.path.join(DATA, "_cache_tenk_counts.json")
DEN_CSV = os.path.join(DATA, "aggregates", "ai_prevalence.csv")
NUM_CACHE = os.path.join(DATA, "_cache_screen.json")
START_YEAR, END_YEAR = 2001, 2025

# label -> FTS query (quoted phrases; space-separated quoted phrases are AND-ed by EDGAR FTS)
SIGNALS = {
    "prefunded_warrant":  '"pre-funded warrant"',
    "ownership_blocker":  '"beneficial ownership limitation"',
    "paired_structure":   '"pre-funded warrant" "beneficial ownership limitation"',
    "reverse_split":      '"reverse stock split"',
}

_last = [0.0]
def _throttle(s=0.5):
    dt = time.time() - _last[0]
    if dt < s: time.sleep(s - dt)
    _last[0] = time.time()

def _load(p): return json.load(open(p)) if os.path.exists(p) else {}
def _save(p, o): json.dump(o, open(p, "w"))

def fts_count(query, year):
    _throttle()
    p = {"q": query, "forms": "10-K", "startdt": f"{year}-01-01", "enddt": f"{year}-12-31"}
    url = "https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(p)
    for i in range(8):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45))
            return d.get("hits", {}).get("total", {}).get("value", 0)
        except Exception:
            sys.stderr.write(f"   retry {i+1} {query} {year}\n"); time.sleep(2.0 * (i + 1))
    return None

def load_denominator():
    den = _load(DEN_CACHE)
    if den:
        return {int(k): int(v) for k, v in den.items()}
    if os.path.exists(DEN_CSV):
        return {int(r["year"]): int(r["n_10k_filers"]) for r in csv.DictReader(open(DEN_CSV))}
    return {}

def main():
    den = load_denominator()
    if not den:
        sys.exit("No denominator: run ai_prevalence.py, or ensure data/aggregates/ai_prevalence.csv exists.")
    num = _load(NUM_CACHE)
    rows = []
    for y in range(START_YEAR, END_YEAR + 1):
        d = den.get(y)
        if not d:
            continue
        rec = {"year": y, "n_10k_filers": d}
        for label, q in SIGNALS.items():
            k = f"{y}|{label}"
            if k not in num:
                v = fts_count(q, y)
                if v is not None:
                    num[k] = v; _save(NUM_CACHE, num)
            n = num.get(k, 0)
            rec[f"n_{label}"] = n
            rec[f"pct_{label}"] = round(100.0 * n / d, 3)
        rows.append(rec)
        print(f"{y}: pre-funded={rec['pct_prefunded_warrant']}%  blocker={rec['pct_ownership_blocker']}%  "
              f"paired={rec['pct_paired_structure']}%", flush=True)

    cols = ["year", "n_10k_filers"]
    for label in SIGNALS:
        cols += [f"n_{label}", f"pct_{label}"]
    out = os.path.join(DATA, "screen_signals.csv")
    with open(out, "w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    print(f"\n[done] wrote {os.path.relpath(out)}")

if __name__ == "__main__":
    main()
