"""
run_event_study.py — end-to-end driver: filings CSV -> returns/factors -> event study -> results.

Usage
-----
  # offline smoke test (synthetic data, no network):
  python run_event_study.py --demo

  # real run on free Stooq data, market model, 3-day window:
  python run_event_study.py --filings sample_filings.csv --source stooq --model market --evt -1 1

  # matched-control design (needs a control universe CSV: ticker,sic,mktcap,price,has_ai_claim):
  python run_event_study.py --filings sample_filings.csv --model control_adjusted \
        --universe universe.csv --source stooq

Filings CSV columns: ident,ticker,event_date[,sic,mktcap,price]
NOTE: a filing in this list merely CONTAINS present-tense AI phrasing. Inclusion is a screening
candidate, NOT an allegation of wrongdoing.
"""
from __future__ import annotations
import argparse
import json
import sys
import numpy as np
import pandas as pd
import eventstudy as es


def _date_range(dates, est_lo, evt_hi, pad=20):
    lo = pd.to_datetime(min(dates)) + pd.Timedelta(days=int(est_lo * 1.6) - pad)
    hi = pd.to_datetime(max(dates)) + pd.Timedelta(days=int(evt_hi) + pad)
    return lo.date(), hi.date()


def _demo_data(n=40, ndays=320, inject=0.04, event_pos=280):
    rng = np.random.default_rng(3)
    cal = pd.bdate_range("2022-06-01", periods=ndays)
    mkt = rng.normal(0.0003, 0.01, ndays)
    rf = np.full(ndays, 8e-5)
    design = pd.DataFrame({"mkt": mkt, "mktrf": mkt - rf, "rf": rf,
                           "smb": rng.normal(0, .004, ndays), "hml": rng.normal(0, .004, ndays),
                           "rmw": rng.normal(0, .003, ndays), "cma": rng.normal(0, .003, ndays)},
                          index=cal)
    cols = {}
    for i in range(n):
        r = rng.normal(1e-4, 2e-4) + rng.uniform(.8, 1.4) * mkt + rng.normal(0, .015, ndays)
        r[event_pos] += inject
        cols[f"DEMO{i:02d}"] = r
    returns = pd.DataFrame(cols, index=cal)
    filings = pd.DataFrame({"ident": returns.columns, "ticker": returns.columns,
                            "event_date": [cal[event_pos]] * n})
    return filings, returns, design, inject


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--filings", default="sample_filings.csv")
    ap.add_argument("--source", default="stooq", choices=["stooq", "yfinance", "crsp"])
    ap.add_argument("--model", default="market",
                    choices=["market", "ff3", "ff5", "market_adjusted", "control_adjusted"])
    ap.add_argument("--est", nargs=2, type=int, default=[-250, -31], metavar=("LO", "HI"))
    ap.add_argument("--evt", nargs=2, type=int, default=[-1, 1], metavar=("LO", "HI"))
    ap.add_argument("--universe", default=None, help="control universe CSV for control_adjusted")
    ap.add_argument("--out", default="results")
    ap.add_argument("--demo", action="store_true", help="run on synthetic data, no network")
    a = ap.parse_args(argv)

    if a.demo:
        filings, returns, design, inject = _demo_data()
        print(f"[demo] synthetic data with a known +{inject*100:.1f}% injected abnormal return")
    else:
        filings = pd.read_csv(a.filings)
        filings["event_date"] = pd.to_datetime(filings["event_date"])
        from returns import load_returns, load_ff_factors
        start, end = _date_range(filings["event_date"], a.est[0], a.evt[1])
        ff_model = a.model if a.model in ("ff3", "ff5") else "ff5"
        print(f"loading factors + returns ({a.source}) {start}..{end} for {len(filings)} filings")
        design = load_ff_factors(start, end, model=ff_model)
        returns = load_returns(filings["ticker"].tolist(), start, end, source=a.source)

    controls = None
    if a.model == "control_adjusted":
        from matching import build_matched_controls
        if a.universe:
            uni = pd.read_csv(a.universe)
            controls = build_matched_controls(
                filings.rename(columns={"ticker": "ident"}).assign(ident=filings["ident"]),
                uni)
        else:
            sys.exit("control_adjusted requires --universe controls.csv")

    per_firm, agg = es.run_panel(filings, returns, design, model=a.model,
                                 est_window=tuple(a.est), evt_window=tuple(a.evt),
                                 controls=controls)
    per_firm.to_csv(f"{a.out}_per_firm.csv", index=False)
    with open(f"{a.out}_aggregate.json", "w") as f:
        json.dump(agg, f, indent=2)

    print(f"\nMODEL={a.model}  EST={tuple(a.est)}  EVT={tuple(a.evt)}")
    if agg.get("N"):
        print(f"  N={agg['N']} (dropped {agg['N_dropped']})   CAAR={agg['CAAR']*100:+.3f}%"
              f"   median={agg['CAAR_median']*100:+.3f}%   %positive={agg['pct_positive']*100:.0f}%")
        print(f"  cross-sec t={agg['t_crosssec']:.2f} (p={agg['p_crosssec']:.2g})")
        print(f"  BMP Z      ={agg.get('Z_bmp', float('nan')):.2f} (p={agg.get('p_bmp', float('nan')):.2g})"
              "   <- lead statistic (robust to event-induced variance)")
        print(f"  Patell Z   ={agg.get('Z_patell', float('nan')):.2f}"
              f"   Wilcoxon p={agg.get('p_wilcoxon', float('nan')):.2g}"
              f"   sign p={agg['p_sign']:.2g}   Corrado t={agg.get('t_corrado', float('nan')):.2f}")
    else:
        print("  no usable firms (check tickers / date coverage)")
    print(f"  wrote {a.out}_per_firm.csv and {a.out}_aggregate.json")
    return agg


if __name__ == "__main__":
    main()
