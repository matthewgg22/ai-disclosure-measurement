"""Event-study estimators, validated against synthetic data with planted answers.

Every test plants a known truth and checks the estimator recovers it. The last three are the ones
that matter: they encode the specific ways this toolkit fails on illiquid small-caps, so a later
refactor cannot quietly reintroduce a failure mode the corrections exist to prevent.
"""
import random

import pytest

from screen.eventstudy import (abnormal_returns, auc_ceiling, bmp_scar, corrado_z,
                               cross_sectional_t, market_model, two_sided_p, winsorize)

EST = list(range(-250, -30))
EVENT = [0, 1]
SPAN = list(range(-250, 21))


def _mkt(rnd):
    return {t: rnd.gauss(0, 0.012) for t in SPAN}


def _firm(rnd, sd=0.03, shock=0.0, shock_days=(0, 1), event_sd=None):
    ar = {}
    for t in SPAN:
        s = event_sd if (event_sd is not None and t in shock_days) else sd
        ar[t] = rnd.gauss(0, s) + (shock if t in shock_days else 0.0)
    return ar


def _car(ar, days=EVENT):
    return sum(ar[t] for t in days)


# --------------------------------------------------------------------------- market model

def test_market_model_recovers_planted_coefficients():
    rnd = random.Random(11)
    x = [rnd.gauss(0, 0.012) for _ in range(250)]
    y = [0.0004 + 1.35 * xi + rnd.gauss(0, 0.004) for xi in x]
    m = market_model(y, x)
    assert m is not None
    assert abs(m.alpha - 0.0004) < 0.0008
    assert abs(m.beta - 1.35) < 0.12
    assert abs(m.resid_sd - 0.004) < 0.0015


@pytest.mark.parametrize("y,x", [([0.1, 0.2], [0.1, 0.2]),          # too few observations
                                 ([0.1, 0.2, 0.3], [0.5, 0.5, 0.5])])  # no benchmark variation
def test_market_model_returns_none_when_degenerate(y, x):
    """A stock that did not trade is a normal occurrence in this population, not an exception."""
    assert market_model(y, x) is None


def test_market_adjusted_forces_beta_to_one():
    fr, mr = [0.05, -0.02], [0.01, 0.01]
    assert abnormal_returns(fr, mr) == pytest.approx([0.04, -0.03])


# --------------------------------------------------------------------------- null behaviour

def test_all_tests_quiet_under_the_null():
    rnd = random.Random(3)
    mkt = _mkt(rnd)
    firms = {i: _firm(rnd) for i in range(200)}
    cars = [_car(a) for a in firms.values()]
    assert abs(cross_sectional_t(cars)) < 1.96
    assert abs(corrado_z(firms, EVENT, EST)) < 1.96
    del mkt


def test_all_tests_fire_with_correct_sign_on_a_planted_shock():
    rnd = random.Random(5)
    firms = {i: _firm(rnd, shock=-0.04) for i in range(200)}
    cars = [_car(a) for a in firms.values()]
    assert sum(cars) / len(cars) == pytest.approx(-0.08, abs=0.01)
    assert cross_sectional_t(cars) < -1.96
    assert corrado_z(firms, EVENT, EST) < -1.96


# --------------------------------------------------------------------------- the failure modes

def test_rank_test_ignores_a_single_extreme_outlier():
    """The nano-cap failure mode: one stock moving $0.01 -> $0.07 enters a CAR as +6.0 and decides
    the mean by itself. The rank test must not follow it."""
    rnd = random.Random(7)
    firms = {i: _firm(rnd) for i in range(200)}
    firms[0][0] = 6.0
    cars = [_car(a) for a in firms.values()]
    assert sum(cars) / len(cars) > 0.02          # the mean is visibly distorted
    assert abs(corrado_z(firms, EVENT, EST)) < 1.96   # the rank test is not


def test_bmp_does_not_fire_under_event_induced_variance_alone():
    """A revelation raises variance whether or not it moves the mean. BMP must not read the
    variance jump as an effect."""
    rnd = random.Random(9)
    mkt = _mkt(rnd)
    firms = {i: _firm(rnd, event_sd=0.03 * 6) for i in range(200)}
    scars = []
    for ar in firms.values():
        m = market_model([ar[t] for t in EST], [mkt[t] for t in EST])
        scars.append(bmp_scar(_car(ar), m, [mkt[t] for t in EVENT]))
    assert abs(cross_sectional_t([s for s in scars if s is not None])) < 1.96


def test_winsorize_bounds_the_mean_without_touching_the_median():
    vals = [0.01] * 99 + [59.0]
    w = winsorize(vals)
    assert max(w) < 1.0                                    # the +5,900% day is pulled in
    assert sorted(w)[len(w) // 2] == pytest.approx(0.01)   # the median is untouched


def test_winsorize_passes_small_samples_through():
    vals = [1.0, 2.0, 99.0]
    assert winsorize(vals) == vals


# --------------------------------------------------------------------------- AUC ceiling

def test_auc_ceiling_bounds_a_rare_binary_flag():
    """A flag on 3% of a population with a 23% base rate cannot exceed ~0.57 however good it is,
    so reading its 0.51 as 'chance' is an instrument error, not a finding."""
    assert auc_ceiling(0.03, 0.23) == pytest.approx(0.565, abs=0.005)


def test_auc_ceiling_is_high_when_base_rate_matches_flag_rate():
    """The mirror case, and the reason the ceiling must be computed rather than assumed: when the
    flag rate approaches the base rate a perfect flag catches nearly everything, so a low observed
    AUC there really is weak ranking."""
    assert auc_ceiling(0.038, 0.041) > 0.95


def test_auc_ceiling_handles_a_flag_firing_more_often_than_the_base_rate():
    assert auc_ceiling(0.50, 0.10) == pytest.approx(1 - (0.40 / 0.90) / 2, abs=1e-9)


@pytest.mark.parametrize("f,b", [(0.1, 0.0), (0.1, 1.0), (1.5, 0.2)])
def test_auc_ceiling_rejects_impossible_inputs(f, b):
    assert auc_ceiling(f, b) is None


# --------------------------------------------------------------------------- misc

def test_corrado_returns_none_without_enough_estimation_days():
    rnd = random.Random(13)
    firms = {i: {t: rnd.gauss(0, 0.03) for t in range(-10, 3)} for i in range(50)}
    assert corrado_z(firms, [0, 1], list(range(-10, -1))) is None


def test_two_sided_p_matches_known_normal_quantiles():
    assert two_sided_p(1.959964) == pytest.approx(0.05, abs=1e-4)
    assert two_sided_p(0.0) == pytest.approx(1.0)
    assert two_sided_p(None) is None
