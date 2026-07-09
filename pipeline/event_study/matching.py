"""
matching.py — build the matched-control set (the Cooper-Dimitrov-Rau counterfactual).

For each event firm, pick K "clean" peers that did NOT make an AI capability claim, matched on
industry (SIC 2-digit by default), firm size, and share price. The control benchmark return is the
equal-weight average of the matched peers; AR_it = R_it - R_control_it isolates the premium
attributable to the CLAIM rather than to being an AI-ish firm in an AI-ish industry.

Why price-match (CDR did): many AI-rebrand pops are thin micro-caps; matching on price level helps
control for the bid-ask-bounce / low-price return artifacts that inflate naive CARs.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def sic2(sic) -> str:
    s = str(sic).strip()
    return s[:2].zfill(2) if s and s[0].isdigit() else "NA"


def build_matched_controls(
    event_firms: pd.DataFrame,     # cols: ident, sic, mktcap, price  (one row per event firm)
    universe: pd.DataFrame,        # cols: ticker, sic, mktcap, price, has_ai_claim (bool)
    k: int = 5,
    industry: str = "sic2",
    size_col: str = "mktcap",
    price_col: str = "price",
) -> dict[str, list[str]]:
    """Return {ident -> [control tickers]} using nearest-neighbour on log size & log price within industry."""
    uni = universe.copy()
    uni = uni[~uni["has_ai_claim"].astype(bool)]              # clean controls only
    uni["_ind"] = uni["sic"].map(sic2) if industry == "sic2" else uni["sic"].astype(str)
    uni["_ls"] = np.log(uni[size_col].clip(lower=1e-6))
    uni["_lp"] = np.log(uni[price_col].clip(lower=1e-6))

    out: dict[str, list[str]] = {}
    for _, ev in event_firms.iterrows():
        ind = sic2(ev["sic"]) if industry == "sic2" else str(ev["sic"])
        pool = uni[uni["_ind"] == ind]
        if pool.empty:
            out[ev["ident"]] = []
            continue
        # standardize distance within the industry pool
        ls = (pool["_ls"] - pool["_ls"].mean()) / (pool["_ls"].std(ddof=0) or 1)
        lp = (pool["_lp"] - pool["_lp"].mean()) / (pool["_lp"].std(ddof=0) or 1)
        tgt_ls = (np.log(max(ev[size_col], 1e-6)) - pool["_ls"].mean()) / (pool["_ls"].std(ddof=0) or 1)
        tgt_lp = (np.log(max(ev[price_col], 1e-6)) - pool["_lp"].mean()) / (pool["_lp"].std(ddof=0) or 1)
        dist = np.sqrt((ls - tgt_ls) ** 2 + (lp - tgt_lp) ** 2)
        out[ev["ident"]] = pool.assign(_d=dist).nsmallest(k, "_d")["ticker"].tolist()
    return out


if __name__ == "__main__":   # tiny self-test
    rng = np.random.default_rng(0)
    uni = pd.DataFrame({
        "ticker": [f"C{i}" for i in range(200)],
        "sic": rng.choice(["7372", "7389", "3841", "6021"], 200),
        "mktcap": rng.lognormal(18, 1.5, 200),
        "price": rng.lognormal(2.5, 0.8, 200),
        "has_ai_claim": rng.random(200) < 0.3,
    })
    ev = pd.DataFrame({"ident": ["X"], "sic": ["7372"], "mktcap": [3e8], "price": [12.0]})
    m = build_matched_controls(ev, uni, k=5)
    assert len(m["X"]) == 5 and all(not uni.set_index("ticker").loc[t, "has_ai_claim"] for t in m["X"])
    print("matching self-test OK:", m)
