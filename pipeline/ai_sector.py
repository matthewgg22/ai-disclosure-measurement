#!/usr/bin/env python3
# Usage: python3 pipeline/ai_sector.py   # writes results to ../data/
"""
Sector segmentation of AI-mentioning 10-Ks (2001-2025): the "AI tourists" cut.

For each year, one EDGAR full-text-search call for "artificial intelligence" (forms=10-K)
captures the sic_filter aggregation — the SIC distribution of AI-mentioning filings.
Rolls up by SIC 2-digit major group and tracks how AI language DIFFUSES out of software
(SIC 73) into finance, health, industrials, etc. over time.

Reuses data/_cache_sic.json (partially populated by ai_lexicon.py). ~14 new calls.
Outputs data/ai_sector_by_year.csv. Caveat: the aggregation returns the top SIC buckets
per year (a long tail of rare sectors may be omitted), so shares are of the top-bucket mass.
"""
import urllib.request, urllib.parse, json, os, sys, time
from collections import defaultdict

UA = {"User-Agent": "AI Washing Research (HKS PAE) matthewgreergentis@gmail.com"}
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SIC_CACHE = os.path.join(DATA, "_cache_sic.json")
START, END = 2001, 2025

SIC2 = {
    "01":"Agriculture","10":"Metal mining","12":"Coal","13":"Oil & gas","14":"Mining",
    "15":"Construction","16":"Construction","17":"Construction","20":"Food","22":"Textiles",
    "23":"Apparel","24":"Lumber","26":"Paper","27":"Printing/Publishing","28":"Chemicals/Pharma",
    "29":"Petroleum","30":"Rubber/Plastics","32":"Stone/Glass","33":"Primary metals",
    "34":"Fabricated metals","35":"Machinery & computers","36":"Electronic equipment",
    "37":"Transportation equip","38":"Instruments & med devices","39":"Misc manufacturing",
    "42":"Trucking","44":"Water transport","45":"Air transport","47":"Transport services",
    "48":"Communications","49":"Utilities","50":"Wholesale durable","51":"Wholesale nondurable",
    "52":"Retail","53":"Retail general","54":"Retail food","55":"Auto dealers","56":"Apparel retail",
    "57":"Home furnishings","58":"Restaurants","59":"Retail misc","60":"Banks (depository)",
    "61":"Nondepository credit","62":"Securities/brokers","63":"Insurance","64":"Insurance agents",
    "65":"Real estate","67":"Holding/investment offices","70":"Hotels","72":"Personal services",
    "73":"Business & IT services","75":"Auto repair","78":"Motion pictures","79":"Amusement",
    "80":"Health services","82":"Education","83":"Social services","87":"Engineering/R&D/Mgmt svcs",
    "99":"Nonclassifiable",
}

def fts_sic(year):
    p = {"q": '"artificial intelligence"', "forms": "10-K",
         "startdt": f"{year}-01-01", "enddt": f"{year}-12-31"}
    url = "https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(p)
    for i in range(6):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45))
            return {b["key"]: b["doc_count"]
                    for b in d.get("aggregations", {}).get("sic_filter", {}).get("buckets", [])}
        except Exception as e:
            sys.stderr.write(f"  retry {i+1} {type(e).__name__}\n"); time.sleep(2*(i+1))
    raise RuntimeError("fts sic failed " + str(year))

def main():
    cache = json.load(open(SIC_CACHE)) if os.path.exists(SIC_CACHE) else {}
    for y in range(START, END + 1):
        if str(y) not in cache:
            cache[str(y)] = fts_sic(y); json.dump(cache, open(SIC_CACHE, "w")); time.sleep(0.2)
        print(f"{y}: {len(cache[str(y)])} sectors", flush=True)

    # roll up by SIC 2-digit, write long CSV + print diffusion summary
    rows = []
    summary = {}
    for y in range(START, END + 1):
        buckets = cache.get(str(y), {})
        by2 = defaultdict(int)
        for sic, c in buckets.items():
            by2[str(sic)[:2].zfill(2)] += c
        total = sum(by2.values()) or 1
        for s2, c in by2.items():
            rows.append((y, s2, SIC2.get(s2, "Other"), c, round(100*c/total, 1)))
        sw = by2.get("73", 0)  # Business & IT services (software lives here)
        summary[y] = {"total": total, "software_share": round(100*sw/total, 1),
                      "top": sorted(by2.items(), key=lambda x: -x[1])[:6]}

    with open(os.path.join(DATA, "ai_sector_by_year.csv"), "w") as f:
        f.write("year,sic2,sector,ai_mention_count,pct_of_ai_filings\n")
        for r in rows:
            f.write(f'{r[0]},{r[1]},"{r[2]}",{r[3]},{r[4]}\n')

    print("\n=== AI-mention sector composition (share of AI-mentioning 10-Ks) ===")
    for y in (2001, 2010, 2018, 2022, 2025):
        s = summary.get(y)
        if not s: continue
        tops = ", ".join(f"{SIC2.get(s2,'?')} {round(100*c/s['total'])}%" for s2, c in s["top"])
        print(f"{y}: SIC-73 software/IT = {s['software_share']}%  | top: {tops}")
    print("\n[done] wrote data/ai_sector_by_year.csv")
    print("Diffusion read: a FALLING SIC-73 share = AI language spreading out of software into other sectors.")

if __name__ == "__main__":
    main()
