#!/usr/bin/env python3
"""
Bucketed AI-lexicon prevalence in 10-Ks + sector segmentation (2001-2025).

Extends ai_prevalence.py: instead of one term, it measures ~30 de-noised phrases
grouped into six FUNCTIONAL buckets that mean different things for AI washing:
  A core (trend backbone)   B marketing (washing-prone)   C substance (anti-washing)
  D aspirational (red flag)  E governance (risk-factor)    F hype/new (gen-AI wave)
The marketing:substance ratio (B vs C) is the washing fingerprint.

Also pulls EDGAR FTS's sic_filter aggregation for "artificial intelligence" each year,
showing which SECTORS the AI language concentrates in over time (the "AI tourists" cut).

Reuses ai_prevalence.py's cached 10-K denominator. Phrases are quoted (EDGAR phrase
search) to avoid token false positives (e.g. electrical "transformers", sales "agents").
"""
import urllib.request, urllib.parse, json, os, sys, time

UA = {"User-Agent": "AI Washing Research (HKS PAE) YOUR_EMAIL@example.com"}
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
START_YEAR, END_YEAR = 2001, 2025
DEN_CACHE = os.path.join(DATA, "_cache_tenk_counts.json")   # shared with ai_prevalence.py
NUM_CACHE = os.path.join(DATA, "_cache_lexicon.json")
SIC_CACHE = os.path.join(DATA, "_cache_sic.json")

BUCKETS = {
    "A_core": ['"artificial intelligence"', '"machine learning"', '"deep learning"',
               '"neural network"', '"natural language processing"', '"computer vision"'],
    "B_marketing": ['"AI-powered"', '"AI-native"', '"AI-driven"', '"powered by AI"',
                    '"intelligent automation"'],
    "C_substance": ['"large language model"', '"foundation model"', '"transformer model"',
                    '"reinforcement learning"', '"fine-tuning"', '"retrieval-augmented generation"',
                    '"vector database"', '"training compute"', '"mixture of experts"'],
    "D_aspirational": ['"artificial general intelligence"', '"superintelligence"', '"frontier model"'],
    "E_governance": ['"responsible AI"', '"explainable AI"', '"AI governance"',
                     '"AI safety"', '"algorithmic bias"'],
    "F_hype_new": ['"generative AI"', '"agentic AI"', '"AI agent"', '"prompt engineering"',
                   '"synthetic data"'],
}
ALL = [(b, p) for b, ps in BUCKETS.items() for p in ps]

_last = [0.0]
def _throttle(s):
    dt = time.time() - _last[0]
    if dt < s: time.sleep(s - dt)
    _last[0] = time.time()
def _load(p): return json.load(open(p)) if os.path.exists(p) else {}
def _save(p, o): json.dump(o, open(p, "w"))

def fts(q, year, want_agg=False):
    _throttle(0.5)
    p = {"q": q, "forms": "10-K", "startdt": f"{year}-01-01", "enddt": f"{year}-12-31"}
    url = "https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(p)
    for i in range(8):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45))
            tot = d.get("hits", {}).get("total", {}).get("value", 0)
            if want_agg:
                aggs = d.get("aggregations", {}).get("sic_filter", {}).get("buckets", [])
                return tot, {b["key"]: b["doc_count"] for b in aggs}
            return tot
        except Exception as e:
            sys.stderr.write(f"   retry {i+1} {type(e).__name__}\n"); time.sleep(3*(i+1))
    sys.stderr.write(f"   GAVE UP (will retry on next run): {url}\n")
    return (None, None) if want_agg else None   # skip, don't crash; resume fills the gap

def main():
    den = _load(DEN_CACHE)            # {year: n_filers} from ai_prevalence.py (run that first)
    num = _load(NUM_CACHE)
    sic = _load(SIC_CACHE)
    if not den:
        sys.exit("Run ai_prevalence.py first to populate the 10-K denominator cache.")
    for y in range(START_YEAR, END_YEAR + 1):
        d = den.get(str(y))
        if not d:
            sys.stderr.write(f"no denom for {y}, skipping\n"); continue
        # term counts
        for bucket, phrase in ALL:
            k = f"{y}|{phrase}"
            if k not in num:
                v = fts(phrase, y)
                if v is not None:
                    num[k] = v; _save(NUM_CACHE, num)
        # sector aggregation for the core AI phrase (already cached by ai_sector.py)
        if str(y) not in sic:
            res = fts('"artificial intelligence"', y, want_agg=True)
            if res and res[1] is not None:
                sic[str(y)] = res[1]; _save(SIC_CACHE, sic)
        ai = num.get(f'{y}|"artificial intelligence"', 0)
        print(f"{y}: filers={d}  AI={ai}({100*ai/d:.1f}%)  sectors={len(sic[str(y)])}", flush=True)

    # write term-level CSV (pct of filers per phrase per year)
    labels = [p.strip('"') for _, p in ALL]
    with open(os.path.join(DATA, "ai_lexicon_by_year.csv"), "w") as f:
        f.write("year,n_10k_filers," + ",".join(f'"{l}"' for l in labels) + "\n")
        for y in range(START_YEAR, END_YEAR + 1):
            d = den.get(str(y))
            if not d: continue
            cells = [str(y), str(d)]
            for _, phrase in ALL:
                n = num.get(f"{y}|{phrase}", "")
                cells.append(f"{100*n/d:.2f}" if isinstance(n, int) and d else "")
            f.write(",".join(cells) + "\n")
    # bucket rollup (sum of term counts within bucket / filers — note: upper bound, terms overlap)
    with open(os.path.join(DATA, "ai_buckets_by_year.csv"), "w") as f:
        f.write("year,n_10k_filers," + ",".join(BUCKETS.keys()) + "\n")
        for y in range(START_YEAR, END_YEAR + 1):
            d = den.get(str(y))
            if not d: continue
            cells = [str(y), str(d)]
            for bucket, phrases in BUCKETS.items():
                s = sum(num.get(f"{y}|{p}", 0) for p in phrases)
                cells.append(f"{100*s/d:.2f}")
            f.write(",".join(cells) + "\n")
    # sector CSV (long format: year, sic, ai_mention_count)
    with open(os.path.join(DATA, "ai_sector_by_year.csv"), "w") as f:
        f.write("year,sic,ai_mention_count\n")
        for y in range(START_YEAR, END_YEAR + 1):
            for s, c in sorted(sic.get(str(y), {}).items(), key=lambda x: -x[1]):
                f.write(f"{y},{s},{c}\n")
    print("\n[done] wrote ai_lexicon_by_year.csv, ai_buckets_by_year.csv, ai_sector_by_year.csv")

if __name__ == "__main__":
    main()
