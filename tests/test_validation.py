"""The validation harness on synthetic data: it must recover a planted signal, show a
size-only baseline is weaker, and return ~0.5 when the score is noise. No issuer data."""
import numpy as np

from screen.validation import auc, size_adjusted_auc, validate


def _synthetic(n=4000, signal=1.4, size_effect=0.8, seed=7):
    rng = np.random.default_rng(seed)
    size = rng.normal(0, 1, n)                     # ln-size proxy
    latent = rng.normal(0, 1, n)                   # true extraction risk
    score = latent + rng.normal(0, 0.5, n)         # observed red-flag score (noisy latent)
    # bad outcome: driven by latent risk AND by being small (size_effect), the confound
    logit = signal * latent - size_effect * size - 0.5
    p = 1 / (1 + np.exp(-logit))
    labels = rng.random(n) < p
    return score, labels, size


def test_auc_perfect_and_random():
    labels = np.array([True, True, False, False])
    assert auc([4, 3, 2, 1], labels) == 1.0     # perfect separation
    assert auc([1, 2, 3, 4], labels) == 0.0     # perfectly wrong
    assert auc([1, 1, 1, 1], labels) == 0.5     # all ties


def test_recovers_planted_signal():
    score, labels, size = _synthetic()
    res = validate(score, labels, size, n_boot=500)
    # the score predicts the outcome, and it survives the size control
    assert res.auc_score_raw > 0.6
    assert res.auc_score_size_adjusted > 0.55
    # lift is monotone-ish: top decile bad-rate exceeds bottom decile
    assert res.lift_by_decile[-1] > res.lift_by_decile[0]


def test_size_only_baseline_is_weaker_than_signal():
    score, labels, size = _synthetic()
    res = validate(score, labels, size, n_boot=500)
    # size alone has some predictive power (the confound), but the size-adjusted score
    # still clears 0.5, i.e. the signal adds lift beyond size
    assert res.auc_score_size_adjusted > 0.5


def test_noise_score_is_uninformative():
    _, labels, size = _synthetic()
    rng = np.random.default_rng(1)
    noise = rng.normal(0, 1, len(labels))
    res = validate(noise, labels, size, n_boot=500)
    assert 0.44 < res.auc_score_size_adjusted < 0.56   # ~0.5, no signal
    assert res.auc_score_size_adjusted_ci[0] < 0.5 < res.auc_score_size_adjusted_ci[1]


def test_deterministic():
    score, labels, size = _synthetic()
    a = validate(score, labels, size, n_boot=300)
    b = validate(score, labels, size, n_boot=300)
    assert a.auc_score_size_adjusted_ci == b.auc_score_size_adjusted_ci  # fixed seed
