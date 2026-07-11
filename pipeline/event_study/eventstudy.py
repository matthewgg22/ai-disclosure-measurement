"""
eventstudy.py — core matched-control event-study engine for the AI-washing project.

Implements the toolkit from methodology-and-measurement.md:
  - normal-return models: market model, FF3/FF5, market-adjusted, mean-adjusted, control-adjusted
  - abnormal returns AR_it, cumulative CAR_i, average CAAR
  - exact OLS prediction-error variance for CAR (parameter-uncertainty aware)
  - test statistics: cross-sectional t, Patell Z, Boehmer-Musumeci-Poulsen (BMP) Z,
    Wilcoxon signed-rank, sign test, Corrado rank test

No network or external data here — this operates on returns you hand it, so it is unit-testable
(see synth_test.py). The data-pull layers (returns.py, matching.py) feed it.

Design notes
------------
* Event day 0 = the first trading day on/after the filing date (filings often post after close;
  this is the conservative convention). Change via `event_day_rule` if you prefer same-day.
* AR for model-based methods uses the estimated intercept (alpha) in the prediction by default
  (set include_alpha=False for the textbook "expected = betas . factors" form).
* Var(CAR_i) for OLS models is exact:  sigma_i^2 * (L2 + s' (X'X)^-1 s), s = sum of event-day
  regressor rows. This is what makes Patell/BMP standardization correct rather than approximate.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy import stats

MODELS = {"market", "ff3", "ff5", "market_adjusted", "mean_adjusted", "control_adjusted"}
FACTOR_COLS = {
    "market": ["mkt"],            # total market return (CDR-style)
    "ff3":    ["mktrf", "smb", "hml"],
    "ff5":    ["mktrf", "smb", "hml", "rmw", "cma"],
}


@dataclass
class EventResult:
    ident: str
    car: float
    var_car: float
    scar: float                       # standardized CAR = car / sqrt(var_car)
    sigma: float                      # estimation-window residual sd
    n_evt: int
    ar: np.ndarray = field(repr=False)
    ar_estimation: np.ndarray = field(repr=False)   # for Corrado ranks
    ok: bool = True
    note: str = ""


def _positions(calendar: pd.DatetimeIndex, event_date, lo: int, hi: int):
    """Integer positions for the [lo, hi] trading-day window relative to event day 0."""
    event_date = pd.Timestamp(event_date)
    day0 = calendar.searchsorted(event_date, side="left")  # first trading day >= filing date
    return day0 + lo, day0 + hi


def _excess(dep: pd.Series, rf: pd.Series | None, model: str) -> pd.Series:
    if model in ("ff3", "ff5") and rf is not None:
        return dep - rf
    return dep


def run_single(
    ident: str,
    firm_ret: pd.Series,                 # DatetimeIndex -> simple daily return
    design: pd.DataFrame,                # DatetimeIndex; columns depend on model (see FACTOR_COLS)
    event_date,
    model: str = "market",
    est_window=(-250, -31),             # estimation window in trading days rel. to event
    evt_window=(-1, 1),                 # event window
    control_ret: pd.Series | None = None,
    include_alpha: bool = True,
) -> EventResult:
    """Run the event study for ONE firm. Returns an EventResult (CAR, variance, SCAR, raw ARs)."""
    if model not in MODELS:
        raise ValueError(f"model must be one of {MODELS}")
    cal = firm_ret.dropna().index.sort_values()
    e0, e1 = _positions(cal, event_date, *est_window)
    v0, v1 = _positions(cal, event_date, *evt_window)
    if e0 < 0 or v1 >= len(cal):
        return EventResult(ident, np.nan, np.nan, np.nan, np.nan, 0,
                           np.array([]), np.array([]), ok=False,
                           note="insufficient trading history around event")
    est_idx = cal[e0:e1 + 1]
    evt_idx = cal[v0:v1 + 1]
    L2 = len(evt_idx)

    rf = design["rf"] if "rf" in design.columns else None

    # ---- build dependent + regressors per model ----
    if model == "mean_adjusted":
        y_est = firm_ret.reindex(est_idx)
        mu = y_est.mean()
        ar = (firm_ret.reindex(evt_idx) - mu).to_numpy()
        ar_est = (y_est - mu).to_numpy()
        sigma = y_est.std(ddof=1)
        var_car = sigma ** 2 * L2
    elif model == "market_adjusted":
        mkt = design["mkt"] if "mkt" in design.columns else design["mktrf"]
        diff = firm_ret - mkt
        ar = diff.reindex(evt_idx).to_numpy()
        ar_est = diff.reindex(est_idx).to_numpy()
        sigma = diff.reindex(est_idx).std(ddof=1)
        var_car = sigma ** 2 * L2
    elif model == "control_adjusted":
        if control_ret is None:
            raise ValueError("control_adjusted requires control_ret")
        diff = firm_ret - control_ret
        ar = diff.reindex(evt_idx).to_numpy()
        ar_est = diff.reindex(est_idx).to_numpy()
        sigma = diff.reindex(est_idx).std(ddof=1)
        var_car = sigma ** 2 * L2
    else:  # OLS models: market / ff3 / ff5
        cols = FACTOR_COLS[model]
        dep = _excess(firm_ret, rf, model)
        Xe = design.reindex(est_idx)[cols].to_numpy()
        ye = dep.reindex(est_idx).to_numpy()
        Xe = np.column_stack([np.ones(len(Xe)), Xe])          # add intercept
        beta, *_ = np.linalg.lstsq(Xe, ye, rcond=None)
        resid = ye - Xe @ beta
        k = Xe.shape[1]
        dof = len(ye) - k
        sigma = float(np.sqrt(resid @ resid / dof))
        XtX_inv = np.linalg.inv(Xe.T @ Xe)

        Xv = design.reindex(evt_idx)[cols].to_numpy()
        Xv = np.column_stack([np.ones(len(Xv)), Xv])
        yv = dep.reindex(evt_idx).to_numpy()
        pred = Xv @ beta
        if not include_alpha:
            pred = pred - beta[0]
        ar = yv - pred
        ar_est = resid
        s = Xv.sum(axis=0)                                     # sum of event-day regressor rows
        var_car = sigma ** 2 * (L2 + float(s @ XtX_inv @ s))   # exact OLS forecast variance

    car = float(np.nansum(ar))
    scar = car / np.sqrt(var_car) if var_car and var_car > 0 else np.nan
    return EventResult(ident, car, float(var_car), float(scar), float(sigma),
                       L2, np.asarray(ar, float), np.asarray(ar_est, float))


def _corrado(results: list[EventResult]) -> tuple[float, float]:
    """Corrado (1989) rank test across firms over the event window. Basic implementation."""
    rows = [r for r in results if r.ok and r.ar_estimation.size and r.ar.size]
    if len(rows) < 2:
        return np.nan, np.nan
    L2 = rows[0].n_evt
    rows = [r for r in rows if r.n_evt == L2 and r.ar_estimation.size == rows[0].ar_estimation.size]
    if len(rows) < 2:
        return np.nan, np.nan
    demeaned = []
    for r in rows:
        combined = np.concatenate([r.ar_estimation, r.ar])
        ranks = stats.rankdata(combined)
        L = len(combined)
        demeaned.append(ranks - (L + 1) / 2.0)              # K_it, mean 0
    K = np.vstack(demeaned)                                  # firms x (L1+L2)
    # Canonical Corrado (1989) / Corrado-Zivney (1992) window form:
    #   daily_mean_t = (1/N) sum_i K_it   (cross-firm mean rank deviation each day)
    #   s_K = sqrt( mean_t daily_mean_t^2 )   over the full L1+L2 period
    #   t   = ( sum_{t in event window} daily_mean_t ) / ( sqrt(L2) * s_K )
    # The cross-firm averaging is already in daily_mean, so we do NOT divide again by sqrt(N).
    daily_mean = K.mean(axis=0)
    s_k = np.sqrt((daily_mean ** 2).mean())
    evt_sum = daily_mean[-L2:].sum()
    t = evt_sum / (np.sqrt(L2) * s_k) if s_k > 0 else np.nan
    p = 2 * (1 - stats.norm.cdf(abs(t))) if np.isfinite(t) else np.nan
    return float(t), float(p)


def aggregate(results: list[EventResult]) -> dict:
    """Aggregate single-firm results into CAAR + a battery of test statistics."""
    good = [r for r in results if r.ok and np.isfinite(r.car)]
    N = len(good)
    out = {"N": N, "N_dropped": len(results) - N}
    if N == 0:
        return out
    cars = np.array([r.car for r in good])
    scars = np.array([r.scar for r in good if np.isfinite(r.scar)])

    caar = cars.mean()
    out["CAAR"] = float(caar)
    out["CAAR_median"] = float(np.median(cars))
    out["pct_positive"] = float((cars > 0).mean())

    # 1) plain cross-sectional t
    sd = cars.std(ddof=1)
    t_plain = caar / (sd / np.sqrt(N)) if sd > 0 else np.nan
    out["t_crosssec"] = float(t_plain)
    out["p_crosssec"] = float(2 * stats.t.sf(abs(t_plain), df=N - 1)) if np.isfinite(t_plain) else np.nan

    # 2) Patell Z (standardized residual)
    if scars.size:
        z_patell = scars.sum() / np.sqrt(scars.size)
        out["Z_patell"] = float(z_patell)
        out["p_patell"] = float(2 * stats.norm.sf(abs(z_patell)))
        # 3) BMP — robust to event-induced variance (the one to lead with)
        s_scar = scars.std(ddof=1)
        z_bmp = scars.mean() / (s_scar / np.sqrt(scars.size)) if s_scar > 0 else np.nan
        out["Z_bmp"] = float(z_bmp)
        out["p_bmp"] = float(2 * stats.t.sf(abs(z_bmp), df=scars.size - 1)) if np.isfinite(z_bmp) else np.nan

    # 4) Wilcoxon signed-rank
    if N >= 6 and np.any(cars != 0):
        try:
            w, pw = stats.wilcoxon(cars)
            out["Wilcoxon_stat"], out["p_wilcoxon"] = float(w), float(pw)
        except ValueError:
            pass

    # 5) sign test
    n_pos = int((cars > 0).sum())
    out["sign_n_pos"] = n_pos
    out["p_sign"] = float(stats.binomtest(n_pos, N, 0.5).pvalue)

    # 6) Corrado rank test
    tc, pc = _corrado(good)
    out["t_corrado"], out["p_corrado"] = tc, pc
    return out


def run_panel(
    suspects: pd.DataFrame,             # cols: ident, ticker, event_date  (+ optional control mapping)
    returns: pd.DataFrame,              # wide: index=DatetimeIndex, columns=tickers -> returns
    design: pd.DataFrame,               # index=DatetimeIndex, factor columns + rf
    model: str = "market",
    est_window=(-250, -31),
    evt_window=(-1, 1),
    controls: dict | None = None,       # ident -> list of control tickers (for control_adjusted)
    include_alpha: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """Run the study across all suspects. Returns (per-firm table, aggregate stats dict)."""
    results = []
    for _, row in suspects.iterrows():
        tkr = row["ticker"]
        if tkr not in returns.columns:
            results.append(EventResult(str(row.get("ident", tkr)), np.nan, np.nan, np.nan,
                                       np.nan, 0, np.array([]), np.array([]), ok=False,
                                       note="no return series"))
            continue
        firm_ret = returns[tkr].dropna()
        ctrl = None
        if model == "control_adjusted" and controls:
            names = [c for c in controls.get(row.get("ident", tkr), []) if c in returns.columns]
            if names:
                ctrl = returns[names].mean(axis=1)
        results.append(run_single(
            str(row.get("ident", tkr)), firm_ret, design, row["event_date"],
            model=model, est_window=est_window, evt_window=evt_window,
            control_ret=ctrl, include_alpha=include_alpha))
    per_firm = pd.DataFrame([{
        "ident": r.ident, "CAR": r.car, "SCAR": r.scar, "sigma": r.sigma,
        "n_evt": r.n_evt, "ok": r.ok, "note": r.note} for r in results])
    return per_firm, aggregate(results)
