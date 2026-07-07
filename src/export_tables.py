#!/usr/bin/env python3
"""Export tidy CSV tables from the aggregate JSON data, for transparency.

Writes human-readable CSVs into data/csv/. Each file corresponds to a table or
figure in the study. Age-band counts in the utilisation and mortality tables are
reconstructed from reported age-band percentages and annual totals and are
approximate; overall counts are exact.
"""
import json, os, csv

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "csv")
os.makedirs(OUT, exist_ok=True)
B = json.load(open(os.path.join(DATA, "dc_data_base.json"), encoding="utf-8"))
NEW = json.load(open(os.path.join(DATA, "dc_data_v2_new.json"), encoding="utf-8"))
YEARS = ["2019", "2020", "2021", "2022", "2023", "2024"]

def w(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)

# 1. annual profile
rows = []
Ndc = Nd = Ni = 0
for y in YEARS:
    b = B["years"][y]["base_cohort"]; m = B["years"][y]["mortality"]; den = NEW["years"][y]["denominator_all_I63"]
    N = b["episode_count"]; d = m["deaths_count"]; M = den["total"]; Ndc += N; Nd += d; Ni += M
    rows.append([y, N, round(b["age_overlay_pct"]["ge60"], 1), d, round(d / N * 100, 1), M, den["ge60_pct"], round(N / M * 1000, 2)])
rows.append(["pooled", Ndc, 49.8, Nd, round(Nd / Ndc * 100, 1), Ni, 85.8, round(Ndc / Ni * 1000, 2)])
w("annual_profile.csv", ["year", "episodes", "aged_ge60_pct", "in_hospital_deaths", "mortality_pct",
                         "primary_I63_episodes", "I63_aged_ge60_pct", "ratio_per_1000"], rows)

# age-band helpers
GROUPS = [("<40", ["18-29", "30-39"]), ("40-49", ["40-49"]), ("50-54", ["50-54"]),
          ("55-59", ["55-59"]), ("60-64", ["60-64"]), ("65-74", ["65-74"]),
          ("75-79", ["75-79"]), ("80+", ["80+"])]
DC_MAP = {"<40": ["<28 days", "28 days-1 year", "1-2", "3-5", "6-9", "10-15", "16-17", "18-29", "30-39"],
          "40-49": ["40-49"], "50-54": ["50-54"], "55-59": ["55-59"], "60-64": ["60-64"],
          "65-74": ["65-74"], "75-79": ["75-79"], "80+": ["80+"]}
labels = [g for g, _ in GROUPS]; gd = dict(GROUPS)

# 2. utilisation by age (pooled, reconstructed)
dc = {g: 0.0 for g in labels}; i63 = {g: 0.0 for g in labels}
for y in YEARS:
    b = B["years"][y]["base_cohort"]; N = b["episode_count"]
    den = NEW["years"][y]["denominator_all_I63"]; M = den["total"]
    for g in labels:
        dc[g] += sum(b["age_bands_pct"][x] / 100 * N for x in DC_MAP[g])
        i63[g] += sum(den["age_bands_pct"][x] / 100 * M for x in gd[g])
rows = [[g, round(dc[g]), round(i63[g]), round(dc[g] / i63[g] * 1000, 2)] for g in labels]
w("utilisation_by_age_pooled.csv", ["age_band", "cohort_episodes_reconstructed", "primary_I63_episodes_reconstructed", "ratio_per_1000"], rows)

# 3. mortality by age (pooled, reconstructed)
coh = {g: 0.0 for g in labels}; dth = {g: 0.0 for g in labels}
for y in YEARS:
    b = B["years"][y]["base_cohort"]; m = B["years"][y]["mortality"]; N = b["episode_count"]; D = m["deaths_count"]
    for g in labels:
        coh[g] += sum(b["age_bands_pct"][x] / 100 * N for x in DC_MAP[g])
        dth[g] += sum(m["death_age_bands_pct"][x] / 100 * D for x in DC_MAP[g])
rows = [[g, round(coh[g]), round(dth[g]), round(dth[g] / coh[g] * 100, 1)] for g in labels]
w("mortality_by_age_pooled.csv", ["age_band", "cohort_episodes_reconstructed", "deaths_reconstructed", "mortality_pct"], rows)

# 4. disposition by year
dk = ["transfer_06", "death_07", "rehabilitation_09", "nursing_10", "home_routine_other_hospice_residual"]
rows = []
for y in YEARS:
    dd = NEW["years"][y]["disposition"]
    rows.append([y] + [dd[k] for k in dk] + [dd["_N"]])
w("disposition_by_year.csv", ["year", "transfer_06", "death_07", "rehabilitation_09",
                              "nursing_10", "home_routine_other_residual", "total_episodes"], rows)

# 5. subtype by year
gk = ["cerebral_arterial_I63.3-5", "precerebral_I63.0-2", "other_unspec_I63.8-9", "venous_I63.6"]
rows = []
for y in YEARS:
    g = NEW["years"][y]["subtype_composition"]["_groups"]
    rows.append([y] + [g[k] if isinstance(g[k], int) else 0 for k in gk] + [NEW["years"][y]["subtype_composition"]["_N"]])
w("subtype_by_year.csv", ["year", "cerebral_artery_I63_3_5", "precerebral_I63_0_2",
                          "other_unspecified_I63_8_9", "cerebral_venous_I63_6", "total_episodes"], rows)

# 6. denominators by year
bands = ["18-29", "30-39", "40-49", "50-54", "55-59", "60-64", "65-74", "75-79", "80+"]
rows = []
for y in YEARS:
    den = NEW["years"][y]["denominator_all_I63"]
    rows.append([y, den["total"], den["ge60_pct"]] + [den["age_bands_pct"][b] for b in bands])
w("denominator_by_year.csv", ["year", "primary_I63_episodes", "aged_ge60_pct"] + [f"pct_{b}" for b in bands], rows)

print("Wrote tidy CSV tables to", OUT)
for f in sorted(os.listdir(OUT)):
    print("  data/csv/" + f)
