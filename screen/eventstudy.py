"""Event-study estimators for illiquid small-cap returns.

The standard event-study toolkit assumes things that are false for nano-caps: approximately normal
daily returns, stable event-window variance, and prices that move every day. Applied unmodified it
produces confident nonsense. In this project's first uncorrected run, mean cumulative abnormal
returns came back at -172% and +2,299% while the medians sat near -1% — a single stock going from
$0.01 to $0.60 enters a CAR as +59.0 and decides the average by itself.

This module is the corrected toolkit. Four estimators, each present because a specific failure mode
required it:

  ``market_model``   OLS of firm return on a benchmark return. Reported alongside a market-ADJUSTED
                     variant (beta forced to 1) because thin trading biases estimated beta toward
                     zero: stale prices do not co-move, so the regression under-attributes market
                     movement and leaves it in the residual.

  ``bmp_scar``       Boehmer-Musumeci-Poulsen (1991) standardisation. A revelation mechanically
                     raises return variance, and the plain cross-sectional t-test reads that
                     variance jump as significance. Standardising each CAR by its own forecast-error
                     standard deviation removes it.

  ``corrado_z``      Corrado (1989) rank test. Uses only the ORDER of an abnormal return within the
                     firm's own return distribution, so no magnitude can carry the result. This is
                     the load-bearing test on illiquid names.

  ``winsorize``      1/99 trim of the cross-section before any mean is taken. Required, not
                     cosmetic; see the opening paragraph.

And one diagnostic that prevents a common misreading:

  ``auc_ceiling``    The highest AUC a BINARY flag firing on a given fraction of the population can
                     reach against a given base rate. AUC for a binary predictor is
                     (sensitivity + specificity) / 2, so a flag firing on 3% of a population with a
                     23% base rate cannot exceed about 0.56 however good it is. Scoring a rare
                     high-precision trigger by AUC and calling 0.51 "chance" is an instrument error.
                     Use precision, lift and recall for triggers; keep AUC for ranking models.

No dependencies beyond the standard library. All functions are pure and side-effect free.

References
----------
Boehmer, E., Musumeci, J., & Poulsen, A. (1991). Event-study methodology under conditions of
    event-induced variance. *Journal of Financial Economics*, 30(2), 253-272.
Corrado, C. (1989). A nonparametric test for abnormal security-price performance in event studies.
    *Journal of Financial Economics*, 23(2), 385-395.
"""
import math
import statistics as _st

__all__ = ["market_model", "abnormal_returns", "bmp_scar", "corrado_z", "winsorize",
           "cross_sectional_t", "auc_ceiling", "two_sided_p", "MarketModel"]


class MarketModel:
    """Fitted single-factor market model plus the terms the BMP correction needs.

    ``alpha``/``beta`` are the OLS coefficients, ``resid_sd`` the residual standard deviation on
    ``n`` estimation observations, and ``mkt_mean``/``mkt_sxx`` summarise the benchmark over the
    estimation window — the forecast-error variance of a prediction depends on how far the event
    window's market return sits from the estimation window's mean.
    """

    __slots__ = ("alpha", "beta", "resid_sd", "n", "mkt_mean", "mkt_sxx")

    def __init__(self, alpha, beta, resid_sd, n, mkt_mean, mkt_sxx):
        self.alpha, self.beta, self.resid_sd = alpha, beta, resid_sd
        self.n, self.mkt_mean, self.mkt_sxx = n, mkt_mean, mkt_sxx

    def predict(self, mkt_return):
        return self.alpha + self.beta * mkt_return

    def __repr__(self):
        return (f"MarketModel(alpha={self.alpha:+.5f}, beta={self.beta:.3f}, "
                f"resid_sd={self.resid_sd:.5f}, n={self.n})")


def market_model(firm_returns, mkt_returns):
    """Fit ``R_i = alpha + beta * R_m + e`` by OLS. Returns a MarketModel, or None if degenerate.

    None is returned rather than raising when there are fewer than three observations, no variation
    in the benchmark, or zero residual variance — all of which occur naturally for a stock that did
    not trade, and none of which is an error worth interrupting a population sweep for.
    """
    n = len(firm_returns)
    if n < 3 or n != len(mkt_returns):
        return None
    xbar = sum(mkt_returns) / n
    ybar = sum(firm_returns) / n
    sxx = sum((x - xbar) ** 2 for x in mkt_returns)
    if sxx <= 0:
        return None
    beta = sum((mkt_returns[i] - xbar) * (firm_returns[i] - ybar) for i in range(n)) / sxx
    alpha = ybar - beta * xbar
    ss = sum((firm_returns[i] - alpha - beta * mkt_returns[i]) ** 2 for i in range(n))
    sd = math.sqrt(ss / (n - 2))
    if sd <= 0:
        return None
    return MarketModel(alpha, beta, sd, n, xbar, sxx)


def abnormal_returns(firm_returns, mkt_returns, model=None):
    """Abnormal returns. With ``model``, market-model residuals; without, market-adjusted.

    The market-adjusted form (beta forced to 1) is not a lesser fallback — on thinly traded names it
    is often the more honest specification, because an estimated beta near zero silently reclassifies
    market movement as abnormal. Report both.
    """
    if model is None:
        return [firm_returns[i] - mkt_returns[i] for i in range(len(firm_returns))]
    return [firm_returns[i] - model.predict(mkt_returns[i]) for i in range(len(firm_returns))]


def bmp_scar(car, model, event_mkt_returns):
    """Standardised CAR with the BMP forecast-error correction.

        S = resid_sd * sqrt( L + L^2/n + (sum_event(R_m - mean R_m))^2 / sxx )

    The three terms are the event-window variance, the uncertainty in the estimated mean, and the
    penalty for an event window whose market return sits far from the estimation-window mean.
    Running the plain cross-sectional t-test on these standardised values is the BMP test.
    """
    if model is None or not event_mkt_returns:
        return None
    L = len(event_mkt_returns)
    dm = sum(r - model.mkt_mean for r in event_mkt_returns)
    s = model.resid_sd * math.sqrt(L + (L * L) / model.n + (dm * dm) / model.mkt_sxx)
    return car / s if s > 0 else None


def corrado_z(ar_by_firm, event_days, estimation_days, min_firms=5):
    """Corrado rank test.

    ``ar_by_firm`` maps a firm key to ``{relative_day: abnormal_return}``. Each firm's abnormal
    returns are ranked WITHIN that firm's own series and mapped to ``rank/(m+1) - 0.5``, so under the
    null an event-window observation has expected standardised rank zero. The daily cross-sectional
    statistic is scaled by its own dispersion over the estimation period.

    Because only ordering enters, a firm with one enormous return contributes no more than a firm
    with one mildly large return — which is exactly why this test survives a population where a
    single name can move a mean by several hundred percent.

    Returns None when the estimation period yields fewer than 30 usable days.
    """
    U = {}
    for key, ar in ar_by_firm.items():
        order = sorted(ar, key=lambda t: ar[t])
        m = len(order)
        if m < 2:
            continue
        U[key] = {t: (i + 1) / (m + 1) - 0.5 for i, t in enumerate(order)}
    if not U:
        return None

    def day_stat(t):
        vals = [u[t] for u in U.values() if t in u]
        if len(vals) < min_firms:
            return None
        return sum(vals) / math.sqrt(len(vals))

    acc = m_days = 0
    for t in estimation_days:
        s = day_stat(t)
        if s is not None:
            acc += s * s
            m_days += 1
    if m_days < 30:
        return None
    s_u = math.sqrt(acc / m_days)
    if s_u <= 0:
        return None
    tot = n_days = 0
    for t in event_days:
        s = day_stat(t)
        if s is not None:
            tot += s
            n_days += 1
    if not n_days:
        return None
    return tot / (math.sqrt(n_days) * s_u)


def winsorize(values, p=0.01):
    """Winsorize a cross-section at ``p``/``1-p``. Returns the input unchanged below 20 values.

    Mandatory before taking any mean of small-cap CARs. The median and the rank test need no such
    treatment, because neither is a function of magnitude.
    """
    n = len(values)
    if n < 20:
        return list(values)
    s = sorted(values)
    # Symmetric index pair. Writing the upper bound as int((1-p)*n) is off by one whenever (1-p)*n
    # lands on an integer — at n=100 that selects the maximum and trims nothing at all, silently
    # disabling the correction on exactly the round sample sizes people reach for.
    k = int(p * n)
    return [min(max(v, s[k]), s[n - 1 - k]) for v in values]


def cross_sectional_t(values):
    """Standard cross-sectional t-statistic. Reported for comparability, not relied upon."""
    n = len(values)
    if n < 3:
        return None
    sd = _st.stdev(values)
    return _st.mean(values) / (sd / math.sqrt(n)) if sd > 0 else None


def two_sided_p(stat):
    """Normal-approximation two-sided p-value. Adequate at the sample sizes used here."""
    if stat is None:
        return None
    return 2 * (1 - 0.5 * (1 + math.erf(abs(stat) / math.sqrt(2))))


def auc_ceiling(flag_rate, base_rate):
    """Highest AUC a binary flag at ``flag_rate`` can reach against ``base_rate``.

    If the flag fires on fewer firms than there are positives, perfection means every flagged firm
    is a positive: sensitivity = flag_rate/base_rate, specificity = 1. If it fires on more,
    perfection means every positive is flagged and the excess is false.

    Compare an observed AUC against this, not against 1.0. A trigger scoring 0.51 against a ceiling
    of 0.52 is working near its limit; the same 0.51 against a ceiling of 0.96 is not.
    """
    f, b = flag_rate, base_rate
    if not 0 < b < 1 or not 0 <= f <= 1:
        return None
    if f <= b:
        return (f / b + 1) / 2
    return (1 + 1 - (f - b) / (1 - b)) / 2
