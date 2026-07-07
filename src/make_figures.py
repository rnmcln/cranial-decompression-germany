#!/usr/bin/env python3
"""Figure generation for the cranial-decompression / ischaemic-stroke study.

Design: restrained, Tufte-oriented. No in-figure titles (captions carry titles),
no top/right spines, light horizontal reference lines only, keys placed below or
beside the data, direct value labelling where it aids reading, one cohesive
palette and typography across every figure. Outputs 600-dpi PNG and vector PDF
into ./figures.

All quantities are recomputed from the two data files, so the figures are
reproducible from source.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "..", "figures")
os.makedirs(FIGDIR, exist_ok=True)
B = json.load(open(os.path.join(HERE, "..", "data", "dc_data_base.json")))
NEW = json.load(open(os.path.join(HERE, "..", "data", "dc_data_v2_new.json")))
YEARS = ["2019", "2020", "2021", "2022", "2023", "2024"]

# ---- shared style ------------------------------------------------------------
INK      = "#20313f"   # axes, text
C_DC     = "#1f3b5c"   # cranial-decompression cohort
C_I63    = "#aebfd1"   # all primary-I63 episodes (lighter)
C_DEATH  = "#9e2a2b"   # in-hospital death / emphasis
C_REHAB  = "#3f6f52"
C_TRANS  = "#2f6690"
C_MUT    = "#8a8f99"
GRID     = "#e4e7eb"
# sequential set for the four subcode groups (dark -> light, one warm accent)
SUB = ["#22405f", "#6d8bad", "#bcc7d4", "#cf9d54"]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": INK,
    "axes.linewidth": 0.8,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "figure.dpi": 120,
})

def finish(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, name + ".png"), dpi=600, bbox_inches="tight")
    fig.savefig(os.path.join(FIGDIR, name + ".pdf"), bbox_inches="tight")
    plt.close(fig)

def hgrid(ax):
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=3)

# ---- recompute pooled quantities --------------------------------------------
GROUPS = [("<40", ["18-29", "30-39"]), ("40-49", ["40-49"]), ("50-54", ["50-54"]),
          ("55-59", ["55-59"]), ("60-64", ["60-64"]), ("65-74", ["65-74"]),
          ("75-79", ["75-79"]), ("80+", ["80+"])]
DC_MAP = {"<40": ["<28 days", "28 days-1 year", "1-2", "3-5", "6-9", "10-15", "16-17", "18-29", "30-39"],
          "40-49": ["40-49"], "50-54": ["50-54"], "55-59": ["55-59"], "60-64": ["60-64"],
          "65-74": ["65-74"], "75-79": ["75-79"], "80+": ["80+"]}
labels = [g for g, _ in GROUPS]

dc_pool = {g: 0.0 for g in labels}
i63_pool = {g: 0.0 for g in labels}
dc_tot = i63_tot = 0
for y in YEARS:
    b = B["years"][y]["base_cohort"]; N = b["episode_count"]; dc_tot += N
    den = NEW["years"][y]["denominator_all_I63"]; M = den["total"]; i63_tot += M
    gd = dict(GROUPS)
    for g in labels:
        dc_pool[g] += sum(b["age_bands_pct"][x] / 100 * N for x in DC_MAP[g])
        i63_pool[g] += sum(den["age_bands_pct"][x] / 100 * M for x in gd[g])

ratio = [dc_pool[g] / i63_pool[g] * 1000 for g in labels]
dc_share = [dc_pool[g] / dc_tot * 100 for g in labels]
i63_share = [i63_pool[g] / i63_tot * 100 for g in labels]

# pooled age-band mortality (reconstructed)
BANDS = ["<28 days", "28 days-1 year", "1-2", "3-5", "6-9", "10-15", "16-17",
         "18-29", "30-39", "40-49", "50-54", "55-59", "60-64", "65-74", "75-79", "80+"]
coh = {g: 0.0 for g in labels}; dth = {g: 0.0 for g in labels}
for y in YEARS:
    b = B["years"][y]["base_cohort"]; m = B["years"][y]["mortality"]
    N = b["episode_count"]; D = m["deaths_count"]
    for g in labels:
        coh[g] += sum(b["age_bands_pct"][x] / 100 * N for x in DC_MAP[g])
        dth[g] += sum(m["death_age_bands_pct"][x] / 100 * D for x in DC_MAP[g])
mort = [dth[g] / coh[g] * 100 for g in labels]

# ============================================================ Figure 1
# Age-specific utilisation ratio
fig, ax = plt.subplots(figsize=(6.6, 3.7))
x = np.arange(len(labels))
ax.plot(x, ratio, color=C_DC, lw=1.6, zorder=3)
ax.scatter(x, ratio, color=C_DC, s=26, zorder=4)
for i, r in enumerate(ratio):
    ax.annotate(f"{r:.1f}", (i, r), textcoords="offset points", xytext=(0, 7),
                ha="center", fontsize=8, color=INK)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_xlabel("Age band (years)")
ax.set_ylabel("Episodes per 1000\nprimary-I63 episodes")
ax.set_ylim(0, max(ratio) * 1.16)
hgrid(ax)
finish(fig, "fig1_utilisation")

# ============================================================ Figure 2
# Age distribution: decompression cohort vs all primary-I63 episodes
fig, ax = plt.subplots(figsize=(6.8, 3.9))
w = 0.4
ax.bar(x - w / 2, dc_share, w, color=C_DC, label="Cranial-decompression episodes")
ax.bar(x + w / 2, i63_share, w, color=C_I63, label="All primary-I63 episodes")
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_xlabel("Age band (years)")
ax.set_ylabel("Share of episodes (%)")
hgrid(ax)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.20),
          ncol=2, fontsize=8, handlelength=1.2)
finish(fig, "fig2_agedist")

# ============================================================ Figure 3
# Age-band in-hospital mortality
fig, ax = plt.subplots(figsize=(6.6, 3.7))
ax.plot(x, mort, color=C_DEATH, lw=1.6, zorder=3)
ax.scatter(x, mort, color=C_DEATH, s=26, zorder=4)
for i, mo in enumerate(mort):
    ax.annotate(f"{mo:.0f}", (i, mo), textcoords="offset points", xytext=(0, 7),
                ha="center", fontsize=8, color=INK)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_xlabel("Age band (years)")
ax.set_ylabel("In-hospital mortality (%)")
ax.set_ylim(8, 47)
hgrid(ax)
finish(fig, "fig3_mortality")

# ============================================================ Figure 4
# I63 subcode composition by year (stacked %)
grp_keys = [("cerebral_arterial_I63.3-5", "Cerebral-artery codes (I63.3–I63.5)"),
            ("precerebral_I63.0-2", "Precerebral codes (I63.0–I63.2)"),
            ("other_unspec_I63.8-9", "Other / unspecified (I63.8–I63.9)"),
            ("venous_I63.6", "Cerebral venous (I63.6)")]
def gv(y, k):
    v = NEW["years"][y]["subtype_composition"]["_groups"][k]
    return v if isinstance(v, int) else 0
yrs = [int(y) for y in YEARS]
fig, ax = plt.subplots(figsize=(6.8, 3.9))
bottom = np.zeros(len(YEARS))
for (k, lab), c in zip(grp_keys, SUB):
    sh = np.array([gv(y, k) / NEW["years"][y]["subtype_composition"]["_N"] * 100 for y in YEARS])
    ax.bar(yrs, sh, bottom=bottom, color=c, label=lab, width=0.66, edgecolor="white", lw=0.5)
    bottom += sh
ax.set_xticks(yrs)
ax.set_xlabel("Data year")
ax.set_ylabel("Share of cohort (%)")
ax.set_ylim(0, 100)
ax.tick_params(length=3)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.20),
          ncol=2, fontsize=7.5, handlelength=1.2)
finish(fig, "fig4_subtype")

# ============================================================ Supp Fig S1
# Annual episodes and share aged >=60
vols = [B["years"][y]["base_cohort"]["episode_count"] for y in YEARS]
share60 = [B["years"][y]["base_cohort"]["age_overlay_pct"]["ge60"] for y in YEARS]
fig, ax = plt.subplots(figsize=(6.6, 3.7))
ax.bar(yrs, vols, width=0.6, color=C_I63, label="Episodes (left axis)")
ax.set_ylabel("Discharge episodes")
ax.set_ylim(0, 1100); ax.set_xticks(yrs); ax.set_xlabel("Data year")
hgrid(ax)
ax2 = ax.twinx()
ax2.spines["top"].set_visible(False)
ax2.plot(yrs, share60, color=C_DC, lw=1.6, marker="o", ms=5, label="Share aged ≥60 (right axis)")
ax2.set_ylabel("Share aged ≥60 (%)"); ax2.set_ylim(0, 100)
for xx, s in zip(yrs, share60):
    ax2.annotate(f"{s:.0f}", (xx, s), textcoords="offset points", xytext=(0, 7),
                 ha="center", fontsize=7.5, color=C_DC)
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, loc="upper center",
          bbox_to_anchor=(0.5, -0.20), ncol=2, fontsize=8, handlelength=1.2)
finish(fig, "figS1_annual")

# ============================================================ Supp Fig S2
# Pooled disposition composition
Nd = sum(NEW["years"][y]["disposition"]["_N"] for y in YEARS)
dpool = {}
for k in ["transfer_06", "death_07", "rehabilitation_09", "nursing_10", "home_routine_other_hospice_residual"]:
    dpool[k] = sum(NEW["years"][y]["disposition"][k] for y in YEARS)
order = [("transfer_06", "Transfer to another hospital", C_TRANS),
         ("death_07", "In-hospital death", C_DEATH),
         ("rehabilitation_09", "Rehabilitation facility", C_REHAB),
         ("home_routine_other_hospice_residual", "Home / routine / other /\nsuppressed hospice (residual)", C_MUT),
         ("nursing_10", "Nursing facility", "#7a5b8e")]
labs = [l for _, l, _ in order]
vals = [dpool[k] / Nd * 100 for k, _, _ in order]
cols = [c for _, _, c in order]
fig, ax = plt.subplots(figsize=(6.8, 3.6))
yp = np.arange(len(labs))[::-1]
ax.barh(yp, vals, color=cols, height=0.62)
for yy, v in zip(yp, vals):
    ax.annotate(f"{v:.1f}", (v, yy), textcoords="offset points", xytext=(4, 0),
                va="center", fontsize=8, color=INK)
ax.set_yticks(yp); ax.set_yticklabels(labs, fontsize=8)
ax.set_xlabel("Share of discharge episodes, pooled 2019–2024 (%)")
ax.set_xlim(0, 46)
ax.xaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True); ax.tick_params(length=3)
finish(fig, "figS2_disposition_pooled")

# ============================================================ Supp Fig S3
# Disposition by year (four main destinations)
series = [("transfer_06", "Transfer", C_TRANS, "o"),
          ("death_07", "In-hospital death", C_DEATH, "s"),
          ("rehabilitation_09", "Rehabilitation", C_REHAB, "^"),
          ("home_routine_other_hospice_residual", "Home / routine / other (residual)", C_MUT, "D")]
fig, ax = plt.subplots(figsize=(6.8, 3.8))
for k, lab, c, mk in series:
    pct = [NEW["years"][y]["disposition"][k] / NEW["years"][y]["disposition"]["_N"] * 100 for y in YEARS]
    ax.plot(yrs, pct, color=c, lw=1.5, marker=mk, ms=5, label=lab)
ax.set_xticks(yrs); ax.set_xlabel("Data year"); ax.set_ylabel("Share of discharge episodes (%)")
ax.set_ylim(0, 48); hgrid(ax)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.20),
          ncol=2, fontsize=8, handlelength=1.6)
finish(fig, "figS3_disposition_trend")

print("Figures written to", FIGDIR)
for f in sorted(os.listdir(FIGDIR)):
    print("  ", f)
