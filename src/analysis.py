#!/usr/bin/env python3
"""Compute every quantity reported in the study from the two extraction files.

Outputs (results/):
  annual_profile.csv        cohort and denominator by data year
  utilisation_by_age.csv    episodes per 1000 primary-I63 episodes, by age band
  mortality_by_age.csv      reconstructed in-hospital mortality, by age band
  age_strata.csv            <60 versus >=60 contrast (risk ratio, risk difference)
  disposition_by_year.csv   discharge disposition by year and pooled
  subcode_by_year.csv       I63 subcode groups by year and pooled
  temporal_trends.csv       linear trend estimates across 2019-2024
  integrity_checks.csv      arithmetic and reproduction checks
  oedema_subgroup_by_*.csv, disposition_by_age.csv, reperfusion_by_*.csv,
  palliative_by_*.csv       measures from the additional queries
  summary.json              all reported values in one machine-readable file
"""
import csv
import json
import os

from common import (BANDS, COHORT_MAP, DENOM_MAP, DISPOSITION_KEYS, GE60, LT60,
                    RESULTS, SUBCODE_GROUPS, YEARS, band_counts, cochran_armitage,
                    load, poisson_byar, poisson_trend, risk_difference_newcombe,
                    risk_ratio_ci, wilson)

os.makedirs(RESULTS, exist_ok=True)
COH, EXT = load()
S = {}  # summary registry


def write(name, header, rows):
    with open(os.path.join(RESULTS, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def r(x, k):
    return round(float(x), k)


# ------------------------------------------------------------------ annual
annual = []
tot = {"N": 0, "D": 0, "I63": 0}
pool_coh = {b: 0.0 for b in BANDS}
pool_den = {b: 0.0 for b in BANDS}
pool_dth = {b: 0.0 for b in BANDS}
for y in YEARS:
    b = COH["years"][y]["base_cohort"]
    m = COH["years"][y]["mortality"]
    den = EXT["years"][y]["denominator_all_I63"]
    N, D, M = b["episode_count"], m["deaths_count"], den["total"]
    cb = band_counts(b["age_bands_pct"], N, COHORT_MAP)
    db = band_counts(den["age_bands_pct"], M, DENOM_MAP)
    xb = band_counts(m["death_age_bands_pct"], D, COHORT_MAP)
    for k in BANDS:
        pool_coh[k] += cb[k]
        pool_den[k] += db[k]
        pool_dth[k] += xb[k]
    ge60 = sum(b["age_bands_pct"][k] for k in COHORT_MAP["60-64"] + COHORT_MAP["65-74"]
               + COHORT_MAP["75-79"] + COHORT_MAP["80+"])
    den_ge60 = sum(den["age_bands_pct"][k] for k in GE60)
    lo, hi = wilson(D, N)
    plo, phi = poisson_byar(N)
    pccl4 = sum(b["pccl_pct"][k] for k in ("4", "5", "6"))
    annual.append([y, N, r(b["sex_pct"]["maennlich"], 1), r(b["los"]["mean_vwd_days"], 1),
                   r(b["los"]["sd_vwd_days"], 1), r(pccl4, 1), r(ge60, 1), D,
                   r(100 * D / N, 1), r(100 * lo, 1), r(100 * hi, 1), M, r(den_ge60, 1),
                   r(1000 * N / M, 2), r(1000 * plo / M, 2), r(1000 * phi / M, 2)])
    tot["N"] += N
    tot["D"] += D
    tot["I63"] += M
N, D, M = tot["N"], tot["D"], tot["I63"]
# pooled descriptive values, weighting each year by its episode count; the pooled
# SD of length of stay combines within-year and between-year variance
w = {y: COH["years"][y]["base_cohort"]["episode_count"] for y in YEARS}
yb = {y: COH["years"][y]["base_cohort"] for y in YEARS}
male_p = sum(w[y] * yb[y]["sex_pct"]["maennlich"] for y in YEARS) / N
los_m = sum(w[y] * yb[y]["los"]["mean_vwd_days"] for y in YEARS) / N
los_sd = (sum(w[y] * (yb[y]["los"]["sd_vwd_days"] ** 2 + (yb[y]["los"]["mean_vwd_days"] - los_m) ** 2)
              for y in YEARS) / N) ** 0.5
pccl_p = sum(w[y] * sum(yb[y]["pccl_pct"][k] for k in ("4", "5", "6")) for y in YEARS) / N
lo, hi = wilson(D, N)
plo, phi = poisson_byar(N)
coh_ge60 = sum(pool_coh[k] for k in GE60)
den_ge60 = sum(pool_den[k] for k in GE60)
annual.append(["Pooled", N, r(male_p, 1), r(los_m, 1), r(los_sd, 1), r(pccl_p, 1), r(100 * coh_ge60 / N, 1), D, r(100 * D / N, 1),
               r(100 * lo, 1), r(100 * hi, 1), M, r(100 * den_ge60 / M, 1), r(1000 * N / M, 2),
               r(1000 * plo / M, 2), r(1000 * phi / M, 2)])
write("annual_profile.csv",
      ["year", "episodes", "male_pct", "los_mean_days", "los_sd_days", "pccl_4plus_pct",
       "aged_60plus_pct", "deaths", "mortality_pct", "mortality_lcl", "mortality_ucl",
       "primary_I63_episodes", "I63_aged_60plus_pct", "ratio_per_1000", "ratio_lcl", "ratio_ucl"],
      annual)
rows = annual[:-1]
S["episodes_total"] = N
S["episodes_mean_per_year"] = r(N / 6, 0)
S["episodes_min"] = min(x[1] for x in rows)
S["episodes_max"] = max(x[1] for x in rows)
S["male_pct_range"] = [min(x[2] for x in rows), max(x[2] for x in rows)]
S["male_pct_pooled"] = r(male_p, 1)
S["los_pooled_mean_sd"] = [r(los_m, 1), r(los_sd, 1)]
S["pccl4_pooled"] = r(pccl_p, 1)
S["los_mean_range"] = [min(x[3] for x in rows), max(x[3] for x in rows)]
S["pccl4_range"] = {str(x[0]): x[5] for x in rows}
S["cohort_ge60_pct_range"] = [min(x[6] for x in rows), max(x[6] for x in rows)]
S["cohort_ge60_pct_pooled"] = r(100 * coh_ge60 / N, 1)
S["deaths_total"] = D
S["mortality_pooled"] = [r(100 * D / N, 1), r(100 * lo, 1), r(100 * hi, 1)]
S["mortality_annual"] = {str(x[0]): x[8] for x in rows}
S["I63_total"] = M
S["I63_range"] = [min(x[11] for x in rows), max(x[11] for x in rows)]
S["I63_ge60_pct_range"] = [min(x[12] for x in rows), max(x[12] for x in rows)]
S["I63_ge60_pct_pooled"] = r(100 * den_ge60 / M, 1)
S["ratio_pooled"] = [r(1000 * N / M, 2), r(1000 * plo / M, 2), r(1000 * phi / M, 2)]
S["ratio_annual"] = {str(x[0]): x[13] for x in rows}

# ------------------------------------------------------- utilisation by age
util = []
for k in BANDS:
    lo, hi = poisson_byar(pool_coh[k])
    util.append([k, round(pool_coh[k]), round(pool_den[k]), r(1000 * pool_coh[k] / pool_den[k], 3),
                 r(1000 * lo / pool_den[k], 3), r(1000 * hi / pool_den[k], 3)])
strata = {}
for name, group in (("<60", LT60), (">=60", GE60)):
    c = sum(pool_coh[k] for k in group)
    d = sum(pool_den[k] for k in group)
    lo, hi = poisson_byar(c)
    strata[name] = (c, d)
    util.append([name, round(c), round(d), r(1000 * c / d, 3), r(1000 * lo / d, 3), r(1000 * hi / d, 3)])
util.append(["All ages (exact totals)", N, M, r(1000 * N / M, 2), r(1000 * plo / M, 2), r(1000 * phi / M, 2)])
write("utilisation_by_age.csv",
      ["age_band", "cohort_episodes", "primary_I63_episodes", "ratio_per_1000", "lcl", "ucl"], util)
S["ratio_by_band"] = {x[0]: x[3] for x in util}
S["ratio_by_band_unrounded"] = {k: 1000 * pool_coh[k] / pool_den[k] for k in BANDS}
S["ratio_by_band_ci"] = {x[0]: [x[4], x[5]] for x in util}
(c1, d1), (c0, d0) = strata[">=60"], strata["<60"]
S["ratio_lt60_vs_ge60_fold"] = r((c0 / d0) / (c1 / d1), 1)
S["I63_band_share_pct"] = {k: r(100 * pool_den[k] / sum(pool_den.values()), 1) for k in BANDS}
S["cohort_band_share_pct"] = {k: r(100 * pool_coh[k] / sum(pool_coh.values()), 1) for k in BANDS}
S["cohort_share_60_74_pct"] = r(100 * (pool_coh["60-64"] + pool_coh["65-74"]) / sum(pool_coh.values()), 1)
S["cohort_share_75plus_pct"] = r(100 * (pool_coh["75-79"] + pool_coh["80+"]) / sum(pool_coh.values()), 1)
S["I63_share_75plus_pct"] = r(100 * (pool_den["75-79"] + pool_den["80+"]) / sum(pool_den.values()), 1)
S["I63_share_80plus_pct"] = r(100 * pool_den["80+"] / sum(pool_den.values()), 1)

# --------------------------------------------------------- mortality by age
mort = []
for k in BANDS:
    lo, hi = wilson(pool_dth[k], pool_coh[k])
    mort.append([k, round(pool_coh[k]), round(pool_dth[k]), r(100 * pool_dth[k] / pool_coh[k], 2),
                 r(100 * lo, 2), r(100 * hi, 2)])
st = {}
for name, group in (("<60", LT60), (">=60", GE60)):
    e = sum(pool_coh[k] for k in group)
    d = sum(pool_dth[k] for k in group)
    lo, hi = wilson(d, e)
    st[name] = (d, e)
    mort.append([name, round(e), round(d), r(100 * d / e, 2), r(100 * lo, 2), r(100 * hi, 2)])
write("mortality_by_age.csv",
      ["age_band", "episodes_reconstructed", "deaths_reconstructed", "mortality_pct", "lcl", "ucl"], mort)
S["mortality_by_band"] = {x[0]: x[3] for x in mort}
S["mortality_by_band_ci"] = {x[0]: [x[4], x[5]] for x in mort}
(x1, n1), (x0, n0) = st[">=60"], st["<60"]
rr = risk_ratio_ci(x1, n1, x0, n0)
rd = risk_difference_newcombe(x1, n1, x0, n0)
write("age_strata.csv", ["measure", "estimate", "lcl", "ucl"],
      [["risk_ratio_ge60_vs_lt60", r(rr[0], 2), r(rr[1], 2), r(rr[2], 2)],
       ["risk_difference_pp_ge60_minus_lt60", r(100 * rd[0], 1), r(100 * rd[1], 1), r(100 * rd[2], 1)],
       ["utilisation_ratio_lt60_over_ge60", r((c0 / d0) / (c1 / d1), 2), "", ""]])
S["risk_ratio"] = [r(x, 2) for x in rr]
S["risk_difference_pp"] = [r(100 * x, 1) for x in rd]

# ------------------------------------------------------------ disposition
disp_rows = []
pool = {k: 0 for k, _ in DISPOSITION_KEYS}
for k, label in DISPOSITION_KEYS:
    row = [label]
    for y in YEARS:
        row.append(EXT["years"][y]["disposition"][k])
        pool[k] += EXT["years"][y]["disposition"][k]
    row += [pool[k], r(100 * pool[k] / N, 1)]
    disp_rows.append(row)
disp_rows.append(["Total"] + [EXT["years"][y]["disposition"]["_N"] for y in YEARS] + [N, 100.0])
disp_rows.append(["Hospice (11), raw query result"] +
                 [EXT["years"][y]["disposition"]["hospice_11_query"] for y in YEARS] + ["", ""])
write("disposition_by_year.csv", ["disposition"] + YEARS + ["pooled_n", "pooled_pct"], disp_rows)
S["disposition_pooled"] = {k: [pool[k], r(100 * pool[k] / N, 1)] for k, _ in DISPOSITION_KEYS}
share = {}
for k, _ in DISPOSITION_KEYS:
    share[k] = {y: r(100 * EXT["years"][y]["disposition"][k] / EXT["years"][y]["disposition"]["_N"], 1)
                for y in YEARS}
S["disposition_share_by_year"] = share
S["transfer_largest_every_year"] = all(
    max(EXT["years"][y]["disposition"][k] for k, _ in DISPOSITION_KEYS) ==
    EXT["years"][y]["disposition"]["transfer_06"] for y in YEARS)

# --------------------------------------------------------------- subcodes
sub_rows = []
spool = {k: 0 for k, _ in SUBCODE_GROUPS}
for k, label in SUBCODE_GROUPS:
    row = [label]
    for y in YEARS:
        v = EXT["years"][y]["subtype_composition"]["_groups"][k]
        row.append(v if isinstance(v, int) else "<4 (in other/unspecified)")
        spool[k] += v if isinstance(v, int) else 0
    row += [spool[k], r(100 * spool[k] / N, 1)]
    sub_rows.append(row)
write("subcode_by_year.csv", ["group"] + YEARS + ["pooled_n", "pooled_pct"], sub_rows)
S["subcode_pooled"] = {k: [spool[k], r(100 * spool[k] / N, 1)] for k, _ in SUBCODE_GROUPS}
S["arterial_share_by_year"] = {
    y: r(100 * EXT["years"][y]["subtype_composition"]["_groups"]["cerebral_arterial_I63.3-5"] /
         EXT["years"][y]["subtype_composition"]["_N"], 1) for y in YEARS}

# ---------------------------------------------------------------- trends
Ns = [COH["years"][y]["base_cohort"]["episode_count"] for y in YEARS]
Ms = [EXT["years"][y]["denominator_all_I63"]["total"] for y in YEARS]
trend_rows = []
rr_t = poisson_trend(Ns, Ms)
trend_rows.append(["utilisation_ratio_rate_ratio_per_year", r(rr_t[0], 3), r(rr_t[1], 3), r(rr_t[2], 3),
                   "", r(rr_t[3], 2)])
for key, label in (("rehabilitation_09", "rehabilitation_share"), ("transfer_06", "transfer_share"),
                   ("death_07", "in_hospital_mortality")):
    x = [EXT["years"][y]["disposition"][key] for y in YEARS]
    zval, p = cochran_armitage(x, Ns)
    trend_rows.append([f"{label}_cochran_armitage_z", r(zval, 2), "", "", f"{p:.2g}", ""])
    S[f"trend_{label}"] = {"z": r(zval, 2), "p": float(f"{p:.2g}")}
write("temporal_trends.csv", ["measure", "estimate", "lcl", "ucl", "p_two_sided", "pearson_dispersion"],
      trend_rows)
S["trend_utilisation_rate_ratio_per_year"] = [r(rr_t[0], 3), r(rr_t[1], 3), r(rr_t[2], 3)]
S["trend_utilisation_dispersion"] = r(rr_t[3], 2)

# -------------------------------------------------------------- integrity
chk = []
for y in YEARS:
    base = COH["years"][y]["base_cohort"]["episode_count"]
    sub_n = EXT["years"][y]["subtype_composition"]["_N"]
    disp = EXT["years"][y]["disposition"]
    gsum = sum(v for v in EXT["years"][y]["subtype_composition"]["_groups"].values() if isinstance(v, int))
    dsum = sum(disp[k] for k, _ in DISPOSITION_KEYS)
    chk.append([y, base, sub_n, disp["_N"], base == sub_n == disp["_N"], gsum, dsum == disp["_N"],
                COH["years"][y]["mortality"]["deaths_count"] == disp["death_07"]])
write("integrity_checks.csv",
      ["year", "episodes_first_extraction", "episodes_rebuilt_subcode_query",
       "episodes_rebuilt_disposition_query", "counts_match", "subcode_groups_sum",
       "disposition_categories_sum_to_total", "death_count_consistent"], chk)
assert all(row[4] and row[6] and row[7] for row in chk), "integrity check failed"

with open(os.path.join(RESULTS, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(S, f, indent=1, ensure_ascii=False)
print(json.dumps(S, indent=1, ensure_ascii=False))


# ======================================================================
# Additional queries (November 2026): oedema-defined subgroup, disposition
# by age and reperfusion co-coding
# ======================================================================
from common import load_additional  # noqa: E402

A = load_additional()["years"]


def bands(rec):
    """Reconstructed age-band counts for one query record."""
    return band_counts(rec["age_bands_pct"], rec["n"], COHORT_MAP)


def pooled(q):
    tot = {b: 0.0 for b in BANDS}
    for y in YEARS:
        for b, v in bands(A[y][q]).items():
            tot[b] += v
    return tot


add_chk = []
for y in YEARS:
    base = COH["years"][y]["base_cohort"]
    disp = EXT["years"][y]["disposition"]
    q = A[y]
    same_age = all(abs(q["Q0"]["age_bands_pct"][k] - base["age_bands_pct"][k]) < 1e-9
                   for k in base["age_bands_pct"])
    row = [y, q["Q0"]["n"], base["episode_count"], q["Q0"]["n"] == base["episode_count"], same_age,
           q["Q4"]["n"] == disp["transfer_06"], q["Q5"]["n"] == disp["rehabilitation_09"],
           q["Q2"]["n"] <= q["Q1"]["n"] and q["Q2"]["n"] <= q["Q0"]["n"] and q["Q3"]["n"] <= q["Q2"]["n"],
           q["Q6"]["n"] <= q["Q0"]["n"] and q["Q7"]["n"] <= q["Q0"]["n"],
           q["Q8"]["n"] <= q["Q1"]["n"] and (q["Q9"]["n"] is None
                                              or (q["Q9"]["n"] <= q["Q8"]["n"] and q["Q9"]["n"] <= q["Q2"]["n"]))]
    add_chk.append(row)
write("integrity_checks_additional.csv",
      ["year", "cohort_reextracted", "cohort_original", "cohort_count_match", "cohort_age_distribution_match",
       "transfer_count_match", "rehabilitation_count_match", "oedema_subsets_nested",
       "reperfusion_subsets_nested", "palliative_subsets_nested"], add_chk)
assert all(all(r[3:]) for r in add_chk), "additional integrity check failed"

# ---- oedema-defined subgroup by year
oe_rows = []
for y in YEARS:
    q = A[y]
    n0, n1, n2, n3 = q["Q0"]["n"], q["Q1"]["n"], q["Q2"]["n"], q["Q3"]["n"]
    l1, u1 = wilson(n2, n1)
    oe_rows.append([y, n1, n2, r(100 * n2 / n0, 1), r(100 * n2 / n1, 2), r(100 * l1, 2), r(100 * u1, 2),
                    n3, r(100 * n3 / n2, 1)])
T1 = sum(A[y]["Q1"]["n"] for y in YEARS); T2 = sum(A[y]["Q2"]["n"] for y in YEARS)
T3 = sum(A[y]["Q3"]["n"] for y in YEARS)
l1, u1 = wilson(T2, T1); lm, um = wilson(T3, T2)
oe_rows.append(["Pooled", T1, T2, r(100 * T2 / N, 1), r(100 * T2 / T1, 2), r(100 * l1, 2), r(100 * u1, 2),
                T3, r(100 * T3 / T2, 1)])
write("oedema_subgroup_by_year.csv",
      ["year", "I63_with_oedema_code", "decompression_with_oedema_code", "share_of_cohort_pct",
       "decompression_pct_of_oedema_episodes", "lcl", "ucl", "deaths", "mortality_pct"], oe_rows)
S["oedema"] = {"I63_with_oedema_total": T1, "decompression_with_oedema_total": T2,
               "share_of_cohort_pct": r(100 * T2 / N, 1),
               "share_of_cohort_range": [min(x[3] for x in oe_rows[:-1]), max(x[3] for x in oe_rows[:-1])],
               "operated_pct": [r(100 * T2 / T1, 1), r(100 * l1, 1), r(100 * u1, 1)],
               "operated_pct_range": [min(x[4] for x in oe_rows[:-1]), max(x[4] for x in oe_rows[:-1])],
               "deaths": T3, "mortality_pct": [r(100 * T3 / T2, 1), r(100 * lm, 1), r(100 * um, 1)]}
z, p = cochran_armitage([A[y]["Q2"]["n"] for y in YEARS], [A[y]["Q1"]["n"] for y in YEARS])
S["oedema"]["trend_operated_z_p"] = [r(z, 2), float(f"{p:.2g}")]

# ---- oedema-defined subgroup by age
P1, P2, P3 = pooled("Q1"), pooled("Q2"), pooled("Q3")
oa = []
for name, grp in [(b, [b]) for b in BANDS] + [("<60", LT60), (">=60", GE60)]:
    d1 = sum(P1[b] for b in grp); d2 = sum(P2[b] for b in grp); d3 = sum(P3[b] for b in grp)
    lo, hi = wilson(d2, d1); ml, mh = wilson(d3, d2)
    oa.append([name, round(d1), round(d2), r(100 * d2 / d1, 2), r(100 * lo, 2), r(100 * hi, 2),
               round(d3), r(100 * d3 / d2, 2), r(100 * ml, 2), r(100 * mh, 2)])
write("oedema_subgroup_by_age.csv",
      ["age_band", "I63_with_oedema_code", "decompression_with_oedema_code", "decompression_pct", "lcl", "ucl",
       "deaths", "mortality_pct", "mortality_lcl", "mortality_ucl"], oa)
S["oedema_by_band_pct"] = {x[0]: x[3] for x in oa}
S["oedema_by_band_ci"] = {x[0]: [x[4], x[5]] for x in oa}
S["oedema_mortality_by_band"] = {x[0]: x[7] for x in oa}
S["oedema_mortality_by_band_ci"] = {x[0]: [x[8], x[9]] for x in oa}
lt = next(x for x in oa if x[0] == "<60"); ge = next(x for x in oa if x[0] == ">=60")
S["oedema_lt60_vs_ge60_fold"] = r(lt[3] / ge[3], 1)
S["oedema_I63_share_75plus_pct"] = r(100 * (P1["75-79"] + P1["80+"]) / sum(P1.values()), 1)

# ---- disposition by age (study cohort)
P0, P4, P5 = pooled("Q0"), pooled("Q4"), pooled("Q5")
da = []
for name, grp in [(b, [b]) for b in BANDS] + [("<60", LT60), (">=60", GE60)]:
    e = sum(P0[b] for b in grp); t = sum(P4[b] for b in grp); h = sum(P5[b] for b in grp)
    x = sum(pool_dth[b] for b in grp)
    tl, tu = wilson(t, e); hl, hu = wilson(h, e)
    da.append([name, round(e), round(t), r(100 * t / e, 2), r(100 * tl, 2), r(100 * tu, 2),
               round(h), r(100 * h / e, 2), r(100 * hl, 2), r(100 * hu, 2), r(100 * x / e, 2)])
write("disposition_by_age.csv",
      ["age_band", "episodes", "transfer", "transfer_pct", "transfer_lcl", "transfer_ucl",
       "rehabilitation", "rehabilitation_pct", "rehabilitation_lcl", "rehabilitation_ucl", "death_pct"], da)
S["transfer_by_band_pct"] = {x[0]: x[3] for x in da}
S["rehab_by_band_pct"] = {x[0]: x[7] for x in da}

# ---- reperfusion co-coding in the study cohort
rp = []
for y in YEARS:
    n0, mt, ivt = A[y]["Q0"]["n"], A[y]["Q6"]["n"], A[y]["Q7"]["n"]
    rp.append([y, n0, mt, r(100 * mt / n0, 1), ivt, r(100 * ivt / n0, 1)])
MT = sum(A[y]["Q6"]["n"] for y in YEARS); IVT = sum(A[y]["Q7"]["n"] for y in YEARS)
rp.append(["Pooled", N, MT, r(100 * MT / N, 1), IVT, r(100 * IVT / N, 1)])
write("reperfusion_by_year.csv", ["year", "episodes", "thrombectomy", "thrombectomy_pct", "thrombolysis",
                                  "thrombolysis_pct"], rp)
zmt, pmt = cochran_armitage([A[y]["Q6"]["n"] for y in YEARS], Ns)
ziv, piv = cochran_armitage([A[y]["Q7"]["n"] for y in YEARS], Ns)
P6, P7 = pooled("Q6"), pooled("Q7")
ra = []
for name, grp in [(b, [b]) for b in BANDS] + [("<60", LT60), (">=60", GE60)]:
    e = sum(P0[b] for b in grp); m_ = sum(P6[b] for b in grp); i_ = sum(P7[b] for b in grp)
    ra.append([name, round(e), round(m_), r(100 * m_ / e, 2), round(i_), r(100 * i_ / e, 2)])
write("reperfusion_by_age.csv", ["age_band", "episodes", "thrombectomy", "thrombectomy_pct", "thrombolysis",
                                 "thrombolysis_pct"], ra)
S["reperfusion"] = {"thrombectomy_pooled": [MT, r(100 * MT / N, 1)], "thrombolysis_pooled": [IVT, r(100 * IVT / N, 1)],
                    "thrombectomy_pct_by_year": {x[0]: x[3] for x in rp[:-1]},
                    "thrombolysis_pct_by_year": {x[0]: x[5] for x in rp[:-1]},
                    "trend_thrombectomy_z_p": [r(zmt, 2), float(f"{pmt:.2g}")],
                    "trend_thrombolysis_z_p": [r(ziv, 2), float(f"{piv:.2g}")],
                    "thrombectomy_by_band_pct": {x[0]: x[3] for x in ra}}

# ---- palliative-care procedure codes in the oedema-defined subgroup
# Q8: oedema-coded primary-I63 episodes with a palliative-care code (8-982, 8-98e, 8-98h);
# Q9: the same within decompression episodes. A suppressed cell (below the display
# threshold) holds 0 to SUPPRESSED_MAX episodes and is carried as a bound, not imputed.
SUPPRESSED_MAX = 3
pl = []
lo9 = hi9 = 0
for y in YEARS:
    q = A[y]
    n1, n2, n8, n9 = q["Q1"]["n"], q["Q2"]["n"], q["Q8"]["n"], q["Q9"]["n"]
    a, b = (n9, n9) if n9 is not None else (0, SUPPRESSED_MAX)
    lo9 += a; hi9 += b
    l8, u8 = wilson(n8, n1)
    pl.append([y, n1, n8, r(100 * n8 / n1, 2), r(100 * l8, 2), r(100 * u8, 2), len(q["Q8"]["further_procedure_codes"]),
               n2, n9 if n9 is not None else f"suppressed (0-{SUPPRESSED_MAX})",
               r(100 * a / n2, 2), r(100 * b / n2, 2),
               r(100 * (n8 - b) / (n1 - n2), 2), r(100 * (n8 - a) / (n1 - n2), 2)])
T8 = sum(A[y]["Q8"]["n"] for y in YEARS)
l8, u8 = wilson(T8, T1)
pl.append(["Pooled", T1, T8, r(100 * T8 / T1, 2), r(100 * l8, 2), r(100 * u8, 2), "",
           T2, f"{lo9}-{hi9}", r(100 * lo9 / T2, 2), r(100 * hi9 / T2, 2),
           r(100 * (T8 - hi9) / (T1 - T2), 2), r(100 * (T8 - lo9) / (T1 - T2), 2)])
write("palliative_by_year.csv",
      ["year", "I63_with_oedema_code", "palliative_coded", "palliative_pct", "lcl", "ucl", "palliative_codes_listed",
       "decompression_with_oedema_code", "decompression_with_palliative", "decompression_palliative_pct_low",
       "decompression_palliative_pct_high", "no_decompression_palliative_pct_low",
       "no_decompression_palliative_pct_high"], pl)
P8 = pooled("Q8")
pa = []
for name, grp in [(b, [b]) for b in BANDS] + [("<60", LT60), (">=60", GE60), (">=75", ["75-79", "80+"])]:
    d1 = sum(P1[b] for b in grp); d8 = sum(P8[b] for b in grp)
    lo, hi = wilson(d8, d1)
    pa.append([name, round(d1), round(d8), r(100 * d8 / d1, 2), r(100 * lo, 2), r(100 * hi, 2)])
write("palliative_by_age.csv", ["age_band", "I63_with_oedema_code", "palliative_coded", "palliative_pct", "lcl", "ucl"], pa)
zpl, ppl = cochran_armitage([A[y]["Q8"]["n"] for y in YEARS], [A[y]["Q1"]["n"] for y in YEARS])
S["palliative"] = {"pooled": [T8, r(100 * T8 / T1, 1), r(100 * l8, 1), r(100 * u8, 1)],
                   "pct_by_year": {x[0]: x[3] for x in pl[:-1]},
                   "decompression_with_palliative_bounds": [lo9, hi9],
                   "decompression_palliative_pct_bounds": [r(100 * lo9 / T2, 1), r(100 * hi9 / T2, 1)],
                   "no_decompression_palliative_pct_bounds": [r(100 * (T8 - hi9) / (T1 - T2), 1),
                                                              r(100 * (T8 - lo9) / (T1 - T2), 1)],
                   "by_band_pct": {x[0]: x[3] for x in pa},
                   "share_aged_75plus_pct": r(100 * (P8["75-79"] + P8["80+"]) / sum(P8.values()), 1),
                   "trend_z_p": [r(zpl, 2), float(f"{ppl:.2g}")],
                   "suppressed_max": SUPPRESSED_MAX}
trend_rows += [["palliative_share_oedema_cochran_armitage_z", r(zpl, 2), "", "", f"{ppl:.2g}", ""]]
trend_rows += [["thrombectomy_share_cochran_armitage_z", r(zmt, 2), "", "", f"{pmt:.2g}", ""],
               ["thrombolysis_share_cochran_armitage_z", r(ziv, 2), "", "", f"{piv:.2g}", ""],
               ["oedema_decompression_share_cochran_armitage_z", r(z, 2), "", "", f"{p:.2g}", ""]]
write("temporal_trends.csv", ["measure", "estimate", "lcl", "ucl", "p_two_sided", "pearson_dispersion"],
      trend_rows)

with open(os.path.join(RESULTS, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(S, f, indent=1, ensure_ascii=False)
