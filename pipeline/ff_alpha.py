#!/usr/bin/env python3
"""
Risk-adjust the AI-mention return premium (FF5 + momentum).

Exhibits 6/6b showed a positive AI-minus-non return spread, but warned it conflates AI with
size/value/quality. This converts that associational spread into a defensible alpha: form the
AI-minus-non long-short as a monthly EQUAL-WEIGHTED return series (each month, firms labeled by
the most recent annual benchmark <= that month, so no look-ahead), regress it on the Fama-French
5 factors + momentum, and read the intercept. Alpha = the abnormal return that survives after
market, size (SMB), value (HML), profitability (RMW), investment (CMA), and momentum are removed.

Standard errors are Newey-West (HAC, Bartlett) because monthly portfolio returns are serially
correlated — plain OLS SEs would overstate the t-stat. Reports the long-short alpha (headline)
plus the long-only AI and non-AI excess-return alphas, and the factor loadings (the story).

Monthly prices: Tiingo (TIINGO_TOKEN env), cached to data/_cache_monthly/ (separate from the
December-only cache). Factors: Ken French data library, cached to data/_cache_factors.json.
Usage: TIINGO_TOKEN=... python3 ff_alpha.py [sp500_ai.csv]
"""
import csv, json, os, sys, io, zipfile, time
import urllib.request, urllib.error
import numpy as np
from scipy import stats

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
MCACHE = os.path.join(DATA, "_cache_monthly")
FCACHE = os.path.join(DATA, "_cache_factors.json")
TOKEN = os.environ.get("TIINGO_TOKEN")
BENCH = [2015, 2018, 2021, 2024]          # the AI-flag benchmark years we have
UA = {"User-Agent": "AI Washing Research (HKS PAE) YOUR_EMAIL@example.com"}

# ---------- prices ----------
def monthly_prices(ticker):
    """{ 'YYYY-MM': adjClose } month-end series 2014-2025, cached."""
    safe = ticker.replace("/", "_").replace(".", "-")
    cp = os.path.join(MCACHE, f"{safe}.json")
    if os.path.exists(cp):
        return json.load(open(cp))
    tk = ticker.replace(".", "-")
    url = (f"https://api.tiingo.com/tiingo/daily/{tk}/prices?startDate=2014-01-01"
           f"&endDate=2025-12-31&resampleFreq=monthly&token={TOKEN}")
    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    px = {row["date"][:7]: row["adjClose"] for row in data}
    json.dump(px, open(cp, "w"))
    return px

def midx(ym):                              # 'YYYY-MM' -> absolute month index
    y, m = ym.split("-"); return int(y) * 12 + int(m)

def monthly_returns(px):
    items = sorted(px.items())
    out = {}
    for i in range(1, len(items)):
        (y0, p0), (y1, p1) = items[i-1], items[i]
        if midx(y1) - midx(y0) == 1 and p0:
            out[y1] = p1 / p0 - 1
    return out

def label_year(y):                         # most recent benchmark <= y (no look-ahead)
    return max([b for b in BENCH if b <= y], default=BENCH[0])

# ---------- Ken French factors ----------
def _parse_french(txt):
    """rows whose first comma-token is exactly 6 digits (YYYYMM); stop at the annual section."""
    out, started = {}, False
    for line in txt.splitlines():
        toks = [t.strip() for t in line.split(",")]
        if toks and len(toks[0]) == 6 and toks[0].isdigit():
            started = True
            out[int(toks[0])] = [float(x) for x in toks[1:] if x not in ("", )]
        elif started:
            break                          # monthly block ended (blank line / annual header)
    return out

def load_factors():
    if os.path.exists(FCACHE):
        return {int(k): v for k, v in json.load(open(FCACHE)).items()}
    def grab(url):
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 research"}), timeout=30).read()
        z = zipfile.ZipFile(io.BytesIO(raw))
        return z.read(z.namelist()[0]).decode("latin-1")
    ff5 = _parse_french(grab("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip"))
    mom = _parse_french(grab("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip"))
    fac = {}
    for ym, v in ff5.items():
        if ym in mom and len(v) == 6:
            mktrf, smb, hml, rmw, cma, rf = v
            m = mom[ym][0]
            if min(mktrf, smb, hml, rmw, cma, rf, m) <= -99:  # missing flag
                continue
            fac[ym] = {k: x / 100.0 for k, x in        # percents -> decimals
                       zip(["mktrf", "smb", "hml", "rmw", "cma", "rf", "mom"],
                           [mktrf, smb, hml, rmw, cma, rf, m])}
    json.dump(fac, open(FCACHE, "w"))
    return fac

# ---------- regression ----------
def newey_west(X, y, L=None):
    """OLS beta with Newey-West (Bartlett) HAC standard errors. Returns beta, se, t, p, r2, n."""
    T, k = X.shape
    if L is None:
        L = int(np.floor(4 * (T / 100.0) ** (2.0 / 9.0)))
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    e = y - X @ beta
    g = X * e[:, None]                      # T x k score rows x_t * e_t
    S = g.T @ g                             # Gamma_0
    for l in range(1, L + 1):
        w = 1 - l / (L + 1)
        Gl = g[l:].T @ g[:-l]
        S += w * (Gl + Gl.T)
    V = XtX_inv @ S @ XtX_inv               # HAC sandwich
    se = np.sqrt(np.diag(V))
    tt = beta / se
    p = 2 * (1 - stats.t.cdf(np.abs(tt), df=T - k))
    ss_res = float(e @ e); ss_tot = float(((y - y.mean()) @ (y - y.mean())))
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    return beta, se, tt, p, r2, T, L

FACS = ["mktrf", "smb", "hml", "rmw", "cma", "mom"]

def run(name, y, Xrows):
    X = np.column_stack([np.ones(len(Xrows))] + [np.array([r[f] for r in Xrows]) for f in FACS])
    y = np.asarray(y)
    beta, se, tt, p, r2, T, L = newey_west(X, y)
    a_m = beta[0]                           # monthly alpha (decimal)
    a_ann = a_m * 12
    star = "***" if p[0] < .01 else "**" if p[0] < .05 else "*" if p[0] < .1 else ""
    print(f"\n=== {name}  (n={T} months, NW lag={L}, R²={r2:.2f}) ===")
    print(f"  ALPHA  {a_m*100:+.3f}%/mo  ({a_ann*100:+.2f}%/yr)   t={tt[0]:+.2f}  p={p[0]:.3f} {star}")
    print(f"  loadings:  " + "  ".join(f"{f}={beta[i+1]:+.2f}(t{tt[i+1]:+.1f})" for i, f in enumerate(FACS)))
    return {"name": name, "n": T, "nw_lag": L, "r2": round(r2, 3),
            "alpha_monthly": round(a_m, 5), "alpha_annual": round(a_ann, 4),
            "alpha_t": round(float(tt[0]), 2), "alpha_p": round(float(p[0]), 4),
            "loadings": {f: round(float(beta[i+1]), 3) for i, f in enumerate(FACS)},
            "loadings_t": {f: round(float(tt[i+1]), 2) for i, f in enumerate(FACS)}}

def main():
    if not TOKEN:
        sys.exit("set TIINGO_TOKEN env var")
    os.makedirs(MCACHE, exist_ok=True)
    inp = sys.argv[1] if len(sys.argv) > 1 else "sp500_ai.csv"
    firms = list(csv.DictReader(open(os.path.join(DATA, inp))))
    print(f"universe: {inp}  ({len(firms)} firms)")

    print("loading Ken French FF5 + momentum factors ...")
    fac = load_factors()
    print(f"  factors: {len(fac)} months, {min(fac)}–{max(fac)}")

    rets, pulled = {}, 0
    for f in firms:
        try:
            rets[f["symbol"]] = monthly_returns(monthly_prices(f["symbol"]))
            pulled += 1
        except urllib.error.HTTPError as e:
            if e.code in (429, 403):
                sys.stderr.write(f"rate-limited after {pulled} (HTTP {e.code}); using cache for rest\n"); break
            continue
        except Exception:
            continue
        if pulled % 100 == 0:
            print(f"  ...{pulled} priced", flush=True)
        if not os.path.exists(os.path.join(MCACHE, f["symbol"].replace('/','_').replace('.','-') + ".json")):
            time.sleep(0.15)
    print(f"firms priced: {len(rets)}")

    months = sorted({ym for mr in rets.values() for ym in mr})
    ls, ai_only, non_only, Xrows = [], [], [], []
    for ym in months:
        key = int(ym.replace("-", ""))
        fa = fac.get(key)
        if not fa:
            continue
        ly = label_year(int(ym[:4]))
        ai, non = [], []
        for f in firms:
            r = rets.get(f["symbol"], {}).get(ym)
            if r is None:
                continue
            (ai if f.get(f"ai_{ly}") == "1" else non).append(r)
        if not ai or not non:
            continue
        Rai, Rnon = float(np.mean(ai)), float(np.mean(non))
        ls.append(Rai - Rnon)               # long-short: RF cancels
        ai_only.append(Rai - fa["rf"])      # long-only excess returns
        non_only.append(Rnon - fa["rf"])
        Xrows.append(fa)
    print(f"aligned months: {len(Xrows)}  ({months[0]}..{months[-1]})")

    out = {"universe": inp, "n_firms": len(rets), "n_months": len(Xrows),
           "results": [run("AI-minus-non  LONG-SHORT", ls, Xrows),
                       run("AI-mention    long-only (excess)", ai_only, Xrows),
                       run("non-mention   long-only (excess)", non_only, Xrows)]}
    tag = inp.replace("_ai.csv", "").replace(".csv", "")
    json.dump(out, open(os.path.join(DATA, f"ff_alpha_{tag}.json"), "w"), indent=2)
    print(f"\n[saved] data/ff_alpha_{tag}.json")
    print("READ: long-short ALPHA = AI-mention premium after FF5+momentum. If it shrinks toward 0 / "
          "loses significance, the raw spread was mostly size+growth, not an AI-label abnormal return.")

if __name__ == "__main__":
    main()
