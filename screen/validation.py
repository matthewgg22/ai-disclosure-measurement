"""Validation harness: does a red-flag score predict a bad outcome, out of sample, after
controlling for firm size?

This is the scientific spine of the engine, as reusable code. It operates on an abstract
labeled table (score, size, outcome) and never touches issuer identity, so it lives in the
public repo and is unit-tested on synthetic data. Running it on the real issuer universe (with
delisting / drawdown outcomes) is the private Phase 3 step; only the aggregate statistics
(AUC, lift, calibration) it returns would ever be published.

Design choices:
- The primary score is TRANSPARENT (a weighted flag count), so AUC needs no model fit; AUC of
  a fixed score is the rank statistic P(score_bad > score_good) (Mann-Whitney).
- Size control is done by stratification (AUC within size terciles, averaged), which is
  robust and needs no regression. The screen must clear 0.5 AUC *after* this control.
- Confidence intervals are bootstrap, fixed seed, so results are reproducible.
"""
from dataclasses import dataclass
import random

import numpy as np

_RNG_SEED = 20260710


@dataclass(frozen=True)
class ValidationResult:
    n: int
    base_rate: float
    auc_size_only: float
    auc_score_raw: float
    auc_score_size_adjusted: float
    auc_score_size_adjusted_ci: tuple  # (lo, hi), 95% bootstrap
    lift_by_decile: list  # bad-rate per score decile, low to high


def auc(scores, labels):
    """Rank-based AUC = P(score of a positive > score of a negative), ties count 0.5.
    `labels` is a boolean array (True = bad outcome)."""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=bool)
    n_pos = int(labels.sum())
    n_neg = int((~labels).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = scores.argsort(kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1, dtype=float)
    # average ranks for ties
    _, inv, counts = np.unique(scores, return_inverse=True, return_counts=True)
    sums = np.zeros(len(counts))
    np.add.at(sums, inv, ranks)
    ranks = (sums / counts)[inv]
    rank_sum_pos = ranks[labels].sum()
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def size_adjusted_auc(score, labels, size, n_strata=3):
    """Mean within-size-stratum AUC, weighted by stratum size. Isolates the score's signal
    from the part that is just 'small firms fail more'."""
    score = np.asarray(score, float)
    labels = np.asarray(labels, bool)
    size = np.asarray(size, float)
    order = size.argsort(kind="mergesort")
    strata = np.array_split(order, n_strata)
    total, weighted = 0, 0.0
    for idx in strata:
        a = auc(score[idx], labels[idx])
        if not np.isnan(a):
            weighted += a * len(idx)
            total += len(idx)
    return weighted / total if total else float("nan")


def lift_by_decile(score, labels, n_bins=10):
    """Bad-rate within each score decile, ordered low score to high score."""
    score = np.asarray(score, float)
    labels = np.asarray(labels, bool)
    order = score.argsort(kind="mergesort")
    out = []
    for idx in np.array_split(order, n_bins):
        out.append(round(float(labels[idx].mean()), 4) if len(idx) else float("nan"))
    return out


def validate(score, labels, size, n_boot=2000):
    """Full validation of a transparent score against a binary outcome, size-controlled."""
    score = np.asarray(score, float)
    labels = np.asarray(labels, bool)
    size = np.asarray(size, float)
    n = len(score)
    est = size_adjusted_auc(score, labels, size)
    rng = random.Random(_RNG_SEED)
    boots = []
    for _ in range(n_boot):
        idx = np.array([rng.randrange(n) for _ in range(n)])
        b = size_adjusted_auc(score[idx], labels[idx], size[idx])
        if not np.isnan(b):
            boots.append(b)
    boots.sort()
    ci = ((round(boots[int(0.025 * len(boots))], 3), round(boots[int(0.975 * len(boots))], 3))
          if len(boots) >= n_boot // 2 else (float("nan"), float("nan")))
    return ValidationResult(
        n=n,
        base_rate=round(float(labels.mean()), 4),
        auc_size_only=round(auc(size, labels), 3),
        auc_score_raw=round(auc(score, labels), 3),
        auc_score_size_adjusted=round(est, 3),
        auc_score_size_adjusted_ci=ci,
        lift_by_decile=lift_by_decile(score, labels),
    )
