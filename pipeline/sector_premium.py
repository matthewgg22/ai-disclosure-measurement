#!/usr/bin/env python3
"""
AI-mention return premium by industry sector (Russell 3000).

Maps 2-digit SIC codes to named sectors and computes the equal-weighted
AI vs non-AI annual return spread within each sector for each benchmark year.
This controls for sector composition far more tightly than the market-level
analysis and directly tests: in which industries does the AI label predict
returns, and in which does it not?

Uses only the cached monthly prices — no API calls.
Output: printed table + data/ai_premium_by_sector.json
"""
import csv, json, os, statistics

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
MCACHE = os.path.join(DATA, "_cache_monthly")
YEARS = [2015, 2018, 2021, 2024]
BENCH = [2015, 2018, 2021, 2024]
MIN_EACH = 10   # minimum n_ai AND n_non required to report a cell

# 2-digit SIC → named sector
def sic_sector(sic2):
    s = int(sic2) if sic2 and sic2.isdigit() else -1
    if s < 0:                   return "Unknown"
    if s <= 9:                  return "Agriculture"
    if s <= 14:                 return "Mining & Energy"
    if s <= 17:                 return "Construction"
    if s in (28, 29):           return "Chemicals & Pharma"
    if 20 <= s <= 27:           return "Food & Consumer Mfg"
    if 30 <= s <= 34:           return "Industrial Mfg"
    if 35 <= s <= 36:           return "Tech Hardware"
    if s == 37:                 return "Autos & Transport Equip"
    if 38 <= s <= 39:           return "Instruments & Misc Mfg"
    if 40 <= s <= 49:           return "Transport & Utilities"
    if 50 <= s <= 51:           return "Wholesale Trade"
    if 52 <= s <= 59:           return "Retail"
    if 60 <= s <= 67:           return "Finance & Insurance"
    if s == 65:                 return "Real Estate"
    if s == 73:                 return "Software & IT Services"
    if 70 <= s <= 72:           return "Hotels & Leisure"
    if 74 <= s <= 79:           return "Other Business Services"
    if s == 80:                 return "Healthcare Services"
    if 81 <= s <= 89:           return "Prof & Tech Services"
    if s >= 90:                 return "Government / Other"
    return "Other"

def cached_annual_ret(ticker, y):
    safe = ticker.replace("/", "_").replace(".", "-")
    cp = os.path.join(MCACHE, f"{safe}.json")
    if not os.path.exists(cp):
        return None
    px = json.load(open(cp))
    dec_cur = px.get(f"{y}-12")
    dec_prv = px.get(f"{y-1}-12")
    if dec_cur is None or dec_prv is None or not dec_prv:
        return None
    return dec_cur / dec_prv - 1

def label_year(y):
    return max([b for b in BENCH if b <= y], default=BENCH[0])

def main():
    firms = list(csv.DictReader(open(os.path.join(DATA, "russell3000_ai.csv"))))

    # assign named sector to each firm
    for f in firms:
        f["named_sector"] = sic_sector(f.get("sic", "")[:2])

    sectors = sorted({f["named_sector"] for f in firms})
    print(f"sectors: {len(sectors)}")

    out = {"sectors": {}}
    all_rows = []   # for the summary print

    for sec in sectors:
        grp = [f for f in firms if f["named_sector"] == sec]
        sec_rows = []
        for y in YEARS:
            ly = label_year(y)
            ai_r, non_r = [], []
            for f in grp:
                r = cached_annual_ret(f["symbol"], y)
                if r is None:
                    continue
                (ai_r if f.get(f"ai_{ly}") == "1" else non_r).append(r)
            if len(ai_r) < MIN_EACH or len(non_r) < MIN_EACH:
                continue
            spr = statistics.mean(ai_r) - statistics.mean(non_r)
            sec_rows.append({
                "year": y, "n_ai": len(ai_r), "n_non": len(non_r),
                "ai_ret": round(statistics.mean(ai_r), 4),
                "non_ret": round(statistics.mean(non_r), 4),
                "raw_spread": round(spr, 4),
            })
        out["sectors"][sec] = {"n_firms": len(grp), "by_year": sec_rows}
        if sec_rows:
            all_rows.append((sec, len(grp), sec_rows))

    # print by sector
    for sec, n_firms, rows in sorted(all_rows, key=lambda x: x[0]):
        print(f"\n=== {sec} (n={n_firms}) ===")
        print(f"{'year':5} {'nAI':>4} {'nNon':>5} {'AIret':>7} {'nonret':>7} {'SPREAD':>8}")
        for r in rows:
            print(
                f"{r['year']}  {r['n_ai']:>4} {r['n_non']:>5} "
                f"{r['ai_ret']*100:>6.1f}% {r['non_ret']*100:>6.1f}% "
                f"{r['raw_spread']*100:>+7.1f}%"
            )

    # compact 2024-only summary sorted by spread descending
    print("\n\n=== 2024 SECTOR SUMMARY (sorted by AI-mention spread) ===")
    print(f"{'sector':<30} {'nAI':>4} {'nNon':>5} {'SPREAD':>8}")
    summary_2024 = []
    for sec, n_firms, rows in all_rows:
        r24 = next((r for r in rows if r["year"] == 2024), None)
        if r24:
            summary_2024.append((sec, r24))
    for sec, r in sorted(summary_2024, key=lambda x: x[1]["raw_spread"], reverse=True):
        print(f"{sec:<30} {r['n_ai']:>4} {r['n_non']:>5} {r['raw_spread']*100:>+7.1f}%")

    json.dump(out, open(os.path.join(DATA, "ai_premium_by_sector.json"), "w"), indent=2)
    print("\n[saved] data/ai_premium_by_sector.json")

if __name__ == "__main__":
    main()
