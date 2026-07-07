#!/usr/bin/env python3
"""Compute and print all numeric results reported in the study.

Reproduces, from the two aggregate data files in ../data:
  - annual profile (episodes, deaths, mortality, primary-I63 episodes, ratio);
  - age-specific utilisation ratio (episodes per 1000 primary-I63 episodes);
  - reconstructed age-band in-hospital mortality;
  - pooled discharge disposition (with an arithmetic audit);
  - pooled I63 subcode composition.

Writes results/summary_statistics.csv. No figures are produced here; see
make_figures.py for publication figures.
"""
import json, os, csv

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
RES = os.path.join(HERE, "..", "results")
os.makedirs(RES, exist_ok=True)
B = json.load(open(os.path.join(DATA, "dc_data_base.json"), encoding="utf-8"))
NEW = json.load(open(os.path.join(DATA, "dc_data_v2_new.json"), encoding="utf-8"))
YEARS = ["2019", "2020", "2021", "2022", "2023", "2024"]

GROUPS = [("<40", ["18-29", "30-39"]), ("40-49", ["40-49"]), ("50-54", ["50-54"]),
          ("55-59", ["55-59"]), ("60-64", ["60-64"]), ("65-74", ["65-74"]),
          ("75-79", ["75-79"]), ("80+", ["80+"])]
DC_MAP = {"<40": ["<28 days", "28 days-1 year", "1-2", "3-5", "6-9", "10-15", "16-17", "18-29", "30-39"],
          "40-49": ["40-49"], "50-54": ["50-54"], "55-59": ["55-59"], "60-64": ["60-64"],
          "65-74": ["65-74"], "75-79": ["75-79"], "80+": ["80+"]}
labels = [g for g, _ in GROUPS]
gd = dict(GROUPS)

rows = []
def out(line):
    print(line); rows.append([line])

# ---- annual profile ----
out("ANNUAL PROFILE (unit = discharge episode)")
Ndc = Nd = Ni = 0
for y in YEARS:
    b = B["years"][y]["base_cohort"]; m = B["years"][y]["mortality"]; den = NEW["years"][y]["denominator_all_I63"]
    N = b["episode_count"]; d = m["deaths_count"]; M = den["total"]; Ndc += N; Nd += d; Ni += M
    out(f"  {y}: episodes={N} ge60%={b['age_overlay_pct']['ge60']:.1f} deaths={d} "
        f"mort%={d/N*100:.1f} I63={M} I63ge60%={den['ge60_pct']:.1f} ratio/1000={N/M*1000:.2f}")
out(f"  POOLED: episodes={Ndc} deaths={Nd} mort%={Nd/Ndc*100:.1f} I63={Ni} ratio/1000={Ndc/Ni*1000:.2f}")

# ---- utilisation ratio by age ----
out("\nAGE-SPECIFIC UTILISATION RATIO (episodes per 1000 primary-I63 episodes)")
dc_pool = {g: 0.0 for g in labels}; i63_pool = {g: 0.0 for g in labels}
for y in YEARS:
    b = B["years"][y]["base_cohort"]; N = b["episode_count"]
    den = NEW["years"][y]["denominator_all_I63"]; M = den["total"]
    for g in labels:
        dc_pool[g] += sum(b["age_bands_pct"][x] / 100 * N for x in DC_MAP[g])
        i63_pool[g] += sum(den["age_bands_pct"][x] / 100 * M for x in gd[g])
for g in labels:
    out(f"  {g:>6}: cohort={dc_pool[g]:.0f} I63={i63_pool[g]:.0f} ratio={dc_pool[g]/i63_pool[g]*1000:.2f}")
dc_lt = sum(dc_pool[g] for g in ["<40", "40-49", "50-54", "55-59"]); dc_ge = Ndc - dc_lt
i63_lt = sum(i63_pool[g] for g in ["<40", "40-49", "50-54", "55-59"]); i63_ge = Ni - i63_lt
out(f"  <60: {dc_lt/i63_lt*1000:.2f} per 1000 ; >=60: {dc_ge/i63_ge*1000:.2f} per 1000")

# ---- reconstructed age-band mortality ----
out("\nRECONSTRUCTED AGE-BAND IN-HOSPITAL MORTALITY")
coh = {g: 0.0 for g in labels}; dth = {g: 0.0 for g in labels}
for y in YEARS:
    b = B["years"][y]["base_cohort"]; m = B["years"][y]["mortality"]
    N = b["episode_count"]; D = m["deaths_count"]
    for g in labels:
        coh[g] += sum(b["age_bands_pct"][x] / 100 * N for x in DC_MAP[g])
        dth[g] += sum(m["death_age_bands_pct"][x] / 100 * D for x in DC_MAP[g])
for g in labels:
    out(f"  {g:>6}: episodes={coh[g]:.0f} deaths={dth[g]:.0f} mortality%={dth[g]/coh[g]*100:.1f}")

# ---- disposition (audited) ----
out("\nPOOLED DISCHARGE DISPOSITION")
keys = ["transfer_06", "death_07", "rehabilitation_09", "nursing_10", "home_routine_other_hospice_residual"]
pool = {k: 0 for k in keys}; Ndisp = 0
for y in YEARS:
    dd = NEW["years"][y]["disposition"]; Ndisp += dd["_N"]
    assert sum(dd[k] for k in keys) == dd["_N"], y
    for k in keys:
        pool[k] += dd[k]
for k in keys:
    out(f"  {k:42s} {pool[k]:5d} ({pool[k]/Ndisp*100:.1f}%)")
out(f"  audit: explicit categories sum to N={Ndisp} -> {sum(pool.values())}")

# ---- subcode composition ----
out("\nPOOLED I63 SUBCODE COMPOSITION")
gk = ["cerebral_arterial_I63.3-5", "precerebral_I63.0-2", "other_unspec_I63.8-9", "venous_I63.6"]
sub = {k: 0 for k in gk}; Ns = 0
for y in YEARS:
    Ns += NEW["years"][y]["subtype_composition"]["_N"]
    for k in gk:
        v = NEW["years"][y]["subtype_composition"]["_groups"][k]
        sub[k] += v if isinstance(v, int) else 0
for k in gk:
    out(f"  {k:28s} {sub[k]:5d} ({sub[k]/Ns*100:.1f}%)")

with open(os.path.join(RES, "summary_statistics.csv"), "w", newline="") as f:
    csv.writer(f).writerows(rows)
print("\nWrote results/summary_statistics.csv")
