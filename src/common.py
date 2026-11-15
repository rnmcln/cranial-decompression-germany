"""Shared definitions: data loading, age-band mapping and interval estimators.

Only the Python standard library and numpy are required, so the analysis runs
without scipy or statsmodels.
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
RESULTS = os.path.join(ROOT, "results")
FIGURES = os.path.join(ROOT, "figures")

YEARS = ["2019", "2020", "2021", "2022", "2023", "2024"]
Z = 1.959963984540054  # standard normal 0.975 quantile

# Native DatenBrowser age bands of the cohort output. Paediatric bands are
# folded into the youngest analysis band.
PAED_BANDS = ["<28 days", "28 days-1 year", "1-2", "3-5", "6-9", "10-15", "16-17"]
BANDS = ["<40", "40-49", "50-54", "55-59", "60-64", "65-74", "75-79", "80+"]
COHORT_MAP = {
    "<40": PAED_BANDS + ["18-29", "30-39"],
    "40-49": ["40-49"], "50-54": ["50-54"], "55-59": ["55-59"],
    "60-64": ["60-64"], "65-74": ["65-74"], "75-79": ["75-79"], "80+": ["80+"],
}
# The all-primary-I63 output reports the paediatric bands as one summed share
# ("_paeds_lt18_sum"); it is assigned to "<40" so that numerator and
# denominator cover the same ages.
DENOM_MAP = dict(COHORT_MAP)
DENOM_MAP["<40"] = ["_paeds_lt18_sum", "18-29", "30-39"]
LT60 = ["<40", "40-49", "50-54", "55-59"]
GE60 = ["60-64", "65-74", "75-79", "80+"]

DISPOSITION_KEYS = [
    ("transfer_06", "Transfer to another hospital (06)"),
    ("death_07", "In-hospital death (07)"),
    ("rehabilitation_09", "Rehabilitation facility (09)"),
    ("nursing_10", "Nursing facility (10)"),
    ("home_routine_other_hospice_residual", "Residual: routine, home, other reasons, suppressed hospice"),
]
SUBCODE_GROUPS = [
    ("cerebral_arterial_I63.3-5", "Cerebral arteries (I63.3-I63.5)"),
    ("precerebral_I63.0-2", "Precerebral arteries (I63.0-I63.2)"),
    ("other_unspec_I63.8-9", "Other or unspecified (I63.8, I63.9)"),
    ("venous_I63.6", "Cerebral venous thrombosis (I63.6)"),
]


def load_additional():
    """Queries added in November 2026 (oedema-defined subgroup, disposition by age and
    reperfusion co-coding); see the _meta block of the file."""
    with open(os.path.join(DATA, "additional_queries_by_year.json"), encoding="utf-8") as f:
        return json.load(f)


def load():
    with open(os.path.join(DATA, "cohort_by_year.json"), encoding="utf-8") as f:
        cohort = json.load(f)
    with open(os.path.join(DATA, "subcode_disposition_denominator_by_year.json"), encoding="utf-8") as f:
        extra = json.load(f)
    return cohort, extra


def band_counts(pct, total, mapping):
    """Reconstruct band counts from reported band percentages and an exact total."""
    return {b: sum(pct[k] for k in mapping[b]) / 100.0 * total for b in BANDS}


def wilson(x, n, z=Z):
    """Wilson score interval for a proportion; accepts non-integer x and n."""
    if n <= 0:
        return (float("nan"), float("nan"))
    p = x / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (centre - half, centre + half)


def poisson_byar(x, z=Z):
    """Byar approximation to the exact (Garwood) Poisson interval for a count."""
    lo = 0.0 if x <= 0 else x * (1 - 1 / (9 * x) - z / (3 * math.sqrt(x))) ** 3
    x1 = x + 1
    hi = x1 * (1 - 1 / (9 * x1) + z / (3 * math.sqrt(x1))) ** 3
    return (lo, hi)


def risk_ratio_ci(x1, n1, x0, n0, z=Z):
    """Risk ratio with Katz log interval (group 1 versus group 0)."""
    rr = (x1 / n1) / (x0 / n0)
    se = math.sqrt(1 / x1 - 1 / n1 + 1 / x0 - 1 / n0)
    return rr, rr * math.exp(-z * se), rr * math.exp(z * se)


def risk_difference_newcombe(x1, n1, x0, n0, z=Z):
    """Risk difference with Newcombe hybrid score interval (method 10)."""
    p1, p0 = x1 / n1, x0 / n0
    l1, u1 = wilson(x1, n1, z)
    l0, u0 = wilson(x0, n0, z)
    d = p1 - p0
    lo = d - math.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2)
    return d, lo, hi


def norm_sf(x):
    return 0.5 * math.erfc(x / math.sqrt(2))


def cochran_armitage(successes, totals, scores=None):
    """Two-sided Cochran-Armitage test for a linear trend in proportions."""
    x = np.asarray(successes, float)
    n = np.asarray(totals, float)
    t = np.arange(len(x), dtype=float) if scores is None else np.asarray(scores, float)
    p = x.sum() / n.sum()
    stat = np.sum(t * (x - n * p))
    var = p * (1 - p) * (np.sum(n * t ** 2) - np.sum(n * t) ** 2 / n.sum())
    zval = stat / math.sqrt(var)
    return zval, 2 * norm_sf(abs(zval))


def poisson_trend(counts, offsets, z=Z):
    """Log-linear Poisson model, log(mu) = log(offset) + a + b*t, fitted by IRLS.

    Returns the rate ratio per year exp(b) with a 95% interval whose standard
    error is scaled by the Pearson dispersion when that exceeds 1
    (quasi-Poisson), and the dispersion itself.
    """
    y = np.asarray(counts, float)
    off = np.log(np.asarray(offsets, float))
    t = np.arange(len(y), dtype=float)
    X = np.column_stack([np.ones_like(t), t])
    beta = np.array([math.log(y.sum() / np.exp(off).sum()), 0.0])
    for _ in range(100):
        mu = np.exp(X @ beta + off)
        W = mu
        zw = X @ beta + (y - mu) / mu
        XtW = X.T * W
        new = np.linalg.solve(XtW @ X, XtW @ zw)
        if np.max(np.abs(new - beta)) < 1e-12:
            beta = new
            break
        beta = new
    mu = np.exp(X @ beta + off)
    cov = np.linalg.inv((X.T * mu) @ X)
    disp = float(np.sum((y - mu) ** 2 / mu) / (len(y) - 2))
    se = math.sqrt(cov[1, 1] * max(1.0, disp))
    b = beta[1]
    return math.exp(b), math.exp(b - z * se), math.exp(b + z * se), disp
