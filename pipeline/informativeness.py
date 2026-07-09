#!/usr/bin/env python3
# Usage: python3 pipeline/informativeness.py   # writes results to ../data/
"""
The declining-label-informativeness test — the lemons precondition (damages-design step 1).

Claim: early on, carrying the "AI" label correlated with genuine capability (the label
SEPARATED firms); as the label proliferated, that link decayed (POOLING). We measure
capability with AUDITED R&D (hard to fake; and the diluters — banks/holding cos from
Exhibit 1b — don't report it), via the XBRL frames cross-section (whole market per year
in one call). The AI label is "mentions 'artificial intelligence' in its 10-K" (EDGAR FTS).

For each benchmark year we compute, over the AI-labeled pool:
  - % of AI-labeled firms that report R&D at all   (pool quality; falls => dilution)
  - median R&D / revenue among AI-labeled firms     (substance intensity)
  - the GAP vs the all-filer baseline               (the label's "substance premium")
Lemons signature: % falls, intensity falls, premium compresses over time.

Heavy step (cached/resumable): the full AI CIK list per year via FTS paging.
"""
import json, os, sys, time, urllib.parse, urllib.request, statistics
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
UA = {"User-Agent": "AI Washing Research (HKS PAE) matthewgreergentis@gmail.com"}
YEARS = [2015, 2018, 2021, 2024]   # pre / ramp / post-ChatGPT-onset / post

def get(url, tries=8):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception:
            time.sleep(2.5 * (i + 1))
    return None

def cache_path(name): return os.path.join(DATA, name)
def load(name):
    p = cache_path(name)
    return json.load(open(p)) if os.path.exists(p) else None
def save(name, obj): json.dump(obj, open(cache_path(name), "w"))

def frames(concept, year):
    name = f"_cache_frames_{concept}_{year}.json"
    c = load(name)
    if c is not None: return {int(k): v for k, v in c.items()}
    raw = get(f"https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/USD/CY{year}.json")
    if not raw: return {}
    d = json.loads(raw)
    out = {int(x["cik"]): x["val"] for x in d.get("data", [])}
    save(name, out); time.sleep(0.2)
    return out

def ai_ciks(year):
    name = f"_cache_ai_ciks_{year}.json"
    st = load(name) or {"ciks": [], "next_from": 0, "done": False}
    if st["done"]:
        return set(int(c) for c in st["ciks"])
    seen = set(int(c) for c in st["ciks"])
    frm = st["next_from"]
    total = None
    while True:
        p = {"q": '"artificial intelligence"', "forms": "10-K",
             "startdt": f"{year}-01-01", "enddt": f"{year}-12-31", "from": frm}
        time.sleep(0.3)
        raw = get("https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(p))
        if not raw:
            sys.stderr.write(f"   {year} page from={frm} failed; skipping\n"); frm += 10
            if total and frm >= min(total, 10000): break
            continue
        d = json.loads(raw)
        if total is None:
            total = d.get("hits", {}).get("total", {}).get("value", 0)
        hits = d.get("hits", {}).get("hits", [])
        for h in hits:
            for c in (h["_source"].get("ciks") or []):
                seen.add(int(c))
        frm += 10
        if frm % 200 == 0 or frm >= (total or 0):
            save(name, {"ciks": sorted(seen), "next_from": frm, "done": frm >= min(total or 0, 10000)})
            print(f"   {year}: {len(seen)} AI ciks ({frm}/{total})", flush=True)
        if frm >= (total or 0) or frm >= 10000:
            break
    save(name, {"ciks": sorted(seen), "next_from": frm, "done": True})
    return seen

def main():
    rows = []
    for y in YEARS:
        print(f"[gather {y}]", flush=True)
        rnd = frames("ResearchAndDevelopmentExpense", y)
        rev = frames("Revenues", y)
        for k, v in frames("RevenueFromContractWithCustomerExcludingAssessedTax", y).items():
            rev.setdefault(k, v)
        ai = ai_ciks(y)
        # baseline population = firms reporting R&D with positive revenue
        base_int = [rnd[c] / rev[c] for c in rnd if c in rev and rev[c] and rev[c] > 0 and rnd[c] >= 0]
        # AI-labeled pool
        ai_n = len(ai)
        ai_with_rnd = [c for c in ai if c in rnd]
        ai_int = [rnd[c] / rev[c] for c in ai if c in rnd and c in rev and rev[c] and rev[c] > 0 and rnd[c] >= 0]
        rec = {"year": y, "ai_firms": ai_n,
               "pct_ai_reporting_rnd": round(100 * len(ai_with_rnd) / ai_n, 1) if ai_n else 0,
               "ai_median_rnd_intensity": round(statistics.median(ai_int), 3) if ai_int else None,
               "baseline_median_rnd_intensity": round(statistics.median(base_int), 3) if base_int else None,
               "rnd_reporters_total": len(rnd)}
        rec["substance_premium"] = (round(rec["ai_median_rnd_intensity"] - rec["baseline_median_rnd_intensity"], 3)
                                    if rec["ai_median_rnd_intensity"] and rec["baseline_median_rnd_intensity"] else None)
        rows.append(rec)
        print(f"   {y}: AI firms={ai_n}  %reporting R&D={rec['pct_ai_reporting_rnd']}  "
              f"AI med R&D/rev={rec['ai_median_rnd_intensity']}  baseline={rec['baseline_median_rnd_intensity']}  "
              f"premium={rec['substance_premium']}", flush=True)

    cols = ["year","ai_firms","pct_ai_reporting_rnd","ai_median_rnd_intensity",
            "baseline_median_rnd_intensity","substance_premium","rnd_reporters_total"]
    with open(os.path.join(DATA, "informativeness.csv"), "w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    print("\n=== Lemons-precondition signature (do these FALL over time?) ===")
    print(f"{'year':6} {'%AI w/ R&D':>11} {'AI R&D/rev':>11} {'baseline':>9} {'premium':>8}")
    for r in rows:
        print(f"{r['year']:<6} {r['pct_ai_reporting_rnd']:>10}% {str(r['ai_median_rnd_intensity']):>11} "
              f"{str(r['baseline_median_rnd_intensity']):>9} {str(r['substance_premium']):>8}")
    print("\n[done] data/informativeness.csv")

if __name__ == "__main__":
    main()
