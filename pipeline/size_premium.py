#!/usr/bin/env python3
# Usage: python3 pipeline/size_premium.py   # writes results to ../data/
"""
Is the AI-mention return premium concentrated in the small-cap tail?

Reads russell3000_ai.csv (with the `wt` float-market-cap proxy from russell3000_size.py)
and the already-cached year-end prices in data/_cache_prices/ (no API calls — free/offline).
Splits the universe into size TERCILES by wt, and within each tercile computes the
AI-vs-non annual-return spread (raw + sector-neutral) by year.

Thesis under test: washing lives in the small-cap tail, so if the market
rewards the *label* regardless of substance, the AI premium should be LARGEST in the small
tercile and smallest among large caps that lawyer their claims.
"""
import csv, json, os, collections, statistics

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE = os.path.join(DATA, "_cache_prices")
YEARS = [2015, 2018, 2021, 2024]

def cached_prices(ticker):
    safe = ticker.replace("/", "_").replace(".", "-")
    cp = os.path.join(CACHE, f"{safe}.json")
    if not os.path.exists(cp):
        return None
    return {int(k): v for k, v in json.load(open(cp)).items()}

def ann_ret(px, y):
    return (px[y] / px[y-1] - 1) if (px and y in px and (y-1) in px and px[y-1]) else None

def spread(firms, prices, y):
    """(n_ai, n_non, ai_mean, non_mean, raw, sector_neutral, n_sectors)"""
    ai_r, non_r = [], []
    bysec = collections.defaultdict(lambda: ([], []))
    for f in firms:
        t = f["symbol"]
        r = ann_ret(prices.get(t), y)
        if r is None:
            continue
        isai = f.get(f"ai_{y}") == "1"
        (ai_r if isai else non_r).append(r)
        bysec[f["sector"]][0 if isai else 1].append(r)
    if not ai_r or not non_r:
        return None
    sec_diffs = [statistics.mean(a) - statistics.mean(n) for a, n in bysec.values() if a and n]
    sn = statistics.mean(sec_diffs) if sec_diffs else None
    return (len(ai_r), len(non_r), statistics.mean(ai_r), statistics.mean(non_r),
            statistics.mean(ai_r) - statistics.mean(non_r), sn, len(sec_diffs))

def main():
    firms = list(csv.DictReader(open(os.path.join(DATA, "russell3000_ai.csv"))))
    if "wt" not in firms[0]:
        raise SystemExit("run russell3000_size.py first (no `wt` column)")
    # keep only firms with a size weight AND cached prices
    prices = {}
    for f in firms:
        px = cached_prices(f["symbol"])
        if px:
            prices[f["symbol"]] = px
    sized = [f for f in firms if float(f.get("wt") or 0) > 0 and f["symbol"] in prices]
    sized.sort(key=lambda f: float(f["wt"]))
    n = len(sized)
    cut1, cut2 = n // 3, 2 * n // 3
    terciles = {"SMALL": sized[:cut1], "MID": sized[cut1:cut2], "LARGE": sized[cut2:]}
    print(f"firms with wt + cached prices: {n}  (terciles ~{cut1} each)")
    # IWV is float-weighted, so the ETF dollar position scales 1:1 with float cap.
    # Report ETF-position boundaries + median in $M (positions, not the firm's full cap).
    def m(f): return float(f["wt"]) / 1e6
    def med(g): return m(g[len(g)//2])
    print(f"  SMALL ETF-position: ${m(sized[0]):.2f}M .. ${m(sized[cut1-1]):.1f}M  (median ${med(sized[:cut1]):.2f}M)")
    print(f"  MID   ETF-position: ${m(sized[cut1]):.1f}M .. ${m(sized[cut2-1]):.1f}M  (median ${med(sized[cut1:cut2]):.1f}M)")
    print(f"  LARGE ETF-position: ${m(sized[cut2]):.1f}M .. ${m(sized[-1]):.0f}M  (median ${med(sized[cut2:]):.1f}M)")

    out = {"n": n, "by_tercile": {}}
    for name, grp in terciles.items():
        print(f"\n=== {name} tercile ({len(grp)} firms) — AI-mention vs non, by year ===")
        print(f"{'year':5} {'nAI':>4} {'nNon':>5} {'AIret':>7} {'nonret':>7} {'RAWspr':>7} {'SECneutral':>11}")
        out["by_tercile"][name] = []
        for y in YEARS:
            s = spread(grp, prices, y)
            if not s:
                print(f"{y}  insufficient"); continue
            nai, nnon, aim, nonm, raw, sn, nsec = s
            sns = f"{sn*100:>10.1f}%" if sn is not None else "       n/a"
            print(f"{y}  {nai:>4} {nnon:>5} {aim*100:>6.1f}% {nonm*100:>6.1f}% {raw*100:>6.1f}% {sns}")
            out["by_tercile"][name].append({
                "year": y, "n_ai": nai, "n_non": nnon,
                "ai_ret": round(aim, 4), "non_ret": round(nonm, 4),
                "raw_spread": round(raw, 4),
                "sector_neutral_spread": round(sn, 4) if sn is not None else None,
                "n_sectors": nsec})
    json.dump(out, open(os.path.join(DATA, "ai_premium_by_size.json"), "w"), indent=2)
    print("\n[saved] data/ai_premium_by_size.json")
    print("THESIS: AI premium largest in SMALL tercile (label rewarded where substance is "
          "least verifiable) -> the washing signature.")

if __name__ == "__main__":
    main()
