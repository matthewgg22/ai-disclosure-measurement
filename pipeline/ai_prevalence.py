#!/usr/bin/env python3
"""
Measure the rise of AI language in 10-K filings over time (2001-present) — CORRECTLY.

Numerator  : # of 10-Ks mentioning each AI term per year, from EDGAR full-text search.
Denominator: # of distinct companies that filed a 10-K that year, from EDGAR's master
             index (full-index/{year}/QTR{q}/master.idx). The earlier "fiscal year" FTS
             proxy was WRONG because EDGAR FTS caps its total at 10,000 (relation 'gte');
             the master index is the rigorous filing-level population.

Both numerator and denominator are cached to data/ so reruns are instant and the job is
resumable if EDGAR throttles. Output: data/ai_prevalence.csv (+ .xlsx w/ chart if openpyxl).
Pure standard library otherwise.
"""
import urllib.request, urllib.parse, json, os, sys, time

UA = {"User-Agent": "AI Washing Research (HKS PAE) YOUR_EMAIL@example.com"}
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
START_YEAR, END_YEAR = 2001, 2025
TERMS = {
    "artificial_intelligence": '"artificial intelligence"',
    "machine_learning": '"machine learning"',
    "generative_ai": '"generative AI"',
}
NUM_CACHE = os.path.join(DATA, "_cache_numerators.json")
DEN_CACHE = os.path.join(DATA, "_cache_tenk_counts.json")

_last = [0.0]
def _throttle(s):
    dt = time.time() - _last[0]
    if dt < s: time.sleep(s - dt)
    _last[0] = time.time()

def _load(path):
    return json.load(open(path)) if os.path.exists(path) else {}
def _save(path, obj):
    json.dump(obj, open(path, "w"))

def fts_total(q, year):
    _throttle(0.25)
    p = {"q": q, "forms": "10-K", "startdt": f"{year}-01-01", "enddt": f"{year}-12-31"}
    url = "https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(p)
    for i in range(6):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45))
            t = d.get("hits", {}).get("total", {})
            return t.get("value", 0), t.get("relation", "")
        except Exception as e:
            sys.stderr.write(f"   fts retry {i+1} {type(e).__name__}\n"); time.sleep(2*(i+1))
    raise RuntimeError("fts failed: " + url)

def tenk_ciks_for_quarter(year, q):
    _throttle(0.4)
    url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{q}/master.idx"
    for i in range(5):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
            ciks = set()
            for ln in raw.decode("latin-1").splitlines():
                p = ln.split("|")
                if len(p) == 5 and p[2] == "10-K":
                    ciks.add(p[0])
            return ciks
        except urllib.error.HTTPError as e:
            if e.code == 404: return set()       # quarter may not exist yet
            sys.stderr.write(f"   idx retry {i+1} HTTP{e.code}\n"); time.sleep(2*(i+1))
        except Exception as e:
            sys.stderr.write(f"   idx retry {i+1} {type(e).__name__}\n"); time.sleep(2*(i+1))
    raise RuntimeError("idx failed: " + url)

def denom_for_year(year, cache):
    key = str(year)
    if key in cache: return cache[key]
    ciks = set()
    for q in (1, 2, 3, 4):
        ciks |= tenk_ciks_for_quarter(year, q)
    cache[key] = len(ciks); _save(DEN_CACHE, cache)
    return cache[key]

def main():
    os.makedirs(DATA, exist_ok=True)
    num_cache, den_cache = _load(NUM_CACHE), _load(DEN_CACHE)
    rows = []
    for y in range(START_YEAR, END_YEAR + 1):
        den = denom_for_year(y, den_cache)
        rec = {"year": y, "n_10k_filers": den}
        line = f"{y}: 10-K filers={den}"
        for key, q in TERMS.items():
            ck = f"{y}:{key}"
            if ck not in num_cache:
                n, rel = fts_total(q, y); num_cache[ck] = n; _save(NUM_CACHE, num_cache)
            n = num_cache[ck]
            rec[f"n_{key}"] = n
            rec[f"pct_{key}"] = round(100.0 * n / den, 2) if den else 0.0
            line += f"  {key}={n}({rec[f'pct_{key}']}%)"
        rows.append(rec); print(line, flush=True)

    cols = (["year", "n_10k_filers"] +
            [f"n_{k}" for k in TERMS] + [f"pct_{k}" for k in TERMS])
    with open(os.path.join(DATA, "ai_prevalence.csv"), "w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    print(f"\n[done] wrote data/ai_prevalence.csv")

    try:
        from openpyxl import Workbook
        from openpyxl.chart import LineChart, Reference
        wb = Workbook(); ws = wb.active; ws.title = "AI prevalence"
        ws.append(["Year", "% AI", "% Machine learning", "% Generative AI", "10-K filers"])
        for r in rows:
            ws.append([r["year"], r["pct_artificial_intelligence"], r["pct_machine_learning"],
                       r["pct_generative_ai"], r["n_10k_filers"]])
        ch = LineChart(); ch.title = "Share of 10-Ks mentioning AI terms (2001-2025)"
        ch.y_axis.title = "% of 10-K filers"; ch.x_axis.title = "Year"; ch.height = 9; ch.width = 18
        data = Reference(ws, min_col=2, max_col=4, min_row=1, max_row=len(rows)+1)
        cats = Reference(ws, min_col=1, min_row=2, max_row=len(rows)+1)
        ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
        ws.add_chart(ch, "G2")
        wb.save(os.path.join(DATA, "ai_prevalence.xlsx"))
        print("[done] wrote data/ai_prevalence.xlsx (with chart)")
    except ImportError:
        print("[note] openpyxl not installed; CSV only — open in Excel and insert a line chart")

if __name__ == "__main__":
    main()
