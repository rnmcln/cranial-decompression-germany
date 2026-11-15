#!/usr/bin/env python3
"""Draw the main and supplementary figures from the files written by analysis.py.

Run analysis.py first. Figures are written to figures/ as vector PDF and as
600 dpi PNG. Labels are placed directly on the data; no figure contains a
title or a legend box.
"""
import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FixedLocator, NullLocator  # noqa: E402

from common import BANDS, FIGURES, RESULTS, YEARS  # noqa: E402

os.makedirs(FIGURES, exist_ok=True)
MM = 1 / 25.4
INK = "#2E3440"      # near-black for data and text
GREY = "#7B818C"     # secondary series
LIGHT = "#B8BDC6"    # tertiary series
ACCENT = "#5E81AC"   # single muted accent
LW = 0.7

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
    "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.minor.size": 0,
    "ytick.minor.size": 0, "axes.edgecolor": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    "savefig.dpi": 600, "figure.dpi": 150, "legend.frameon": False,
})
BAND_LABELS = ["<40", "40–49", "50–54", "55–59", "60–64", "65–74", "75–79", "≥80"]


def read(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(fig, stem):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIGURES, f"{stem}.{ext}"), bbox_inches="tight", pad_inches=0.02,
                    metadata={"Creator": None, "Producer": None, "CreationDate": None}
                    if ext == "pdf" else None)
    plt.close(fig)


def panel(ax, letter):
    ax.text(-0.16, 1.04, letter, transform=ax.transAxes, fontsize=8, va="bottom", ha="left")


def age_axis(ax):
    ax.set_xticks(range(len(BANDS)))
    ax.set_xticklabels(BAND_LABELS)
    ax.set_xlim(-0.5, len(BANDS) - 0.5)
    ax.set_xlabel("Age band (years)")
    ax.spines["bottom"].set_bounds(0, len(BANDS) - 1)


S = json.load(open(os.path.join(RESULTS, "summary.json"), encoding="utf-8"))
x = list(range(len(BANDS)))

# ---------------------------------------------------------------- Figure 1
util = {r["age_band"]: r for r in read("utilisation_by_age.csv")}
fig, (a, b) = plt.subplots(1, 2, figsize=(180 * MM, 66 * MM), gridspec_kw={"wspace": 0.32})
coh = [S["cohort_band_share_pct"][k] for k in BANDS]
den = [S["I63_band_share_pct"][k] for k in BANDS]
for i in x:
    a.plot([i, i], [coh[i], den[i]], color=LIGHT, lw=LW, zorder=1)
a.plot(x, den, ls="none", marker="o", ms=3.6, mfc="white", mec=INK, mew=LW, zorder=3)
a.plot(x, coh, ls="none", marker="o", ms=3.6, mfc=ACCENT, mec=ACCENT, mew=LW, zorder=3)
a.text(6.75, den[7], "All primary-I63\nepisodes", ha="right", va="center", fontsize=6.5)
a.text(5.0, coh[5] + 2.0, "Cranial decompression\nepisodes", ha="center", va="bottom",
       fontsize=6.5, color=ACCENT)
a.set_ylim(0, 45)
a.set_yticks([0, 10, 20, 30, 40])
a.spines["left"].set_bounds(0, 40)
a.set_ylabel("Share of episodes (%)")
age_axis(a)
panel(a, "a")

r_ = [float(util[k]["ratio_per_1000"]) for k in BANDS]
lo = [float(util[k]["lcl"]) for k in BANDS]
hi = [float(util[k]["ucl"]) for k in BANDS]
b.vlines(x, lo, hi, color=INK, lw=LW)
b.plot(x, r_, color=INK, lw=LW, marker="o", ms=3.2, mfc="white", mec=INK, mew=LW)
for i, k in enumerate(BANDS):
    v = S["ratio_by_band_unrounded"][k]
    b.text(i + 0.14, v * 1.08, f"{v:.1f}", fontsize=6, ha="left", va="bottom", color=GREY)
b.set_yscale("log")
b.set_ylim(0.1, 30)
b.yaxis.set_major_locator(FixedLocator([0.1, 0.3, 1, 3, 10, 30]))
b.yaxis.set_minor_locator(NullLocator())
b.set_yticklabels(["0.1", "0.3", "1", "3", "10", "30"])
b.set_ylabel("Episodes per 1000 primary-I63 episodes\n(log scale)")
age_axis(b)
panel(b, "b")
save(fig, "fig1_age_utilisation")

# ---------------------------------------------------------------- Figure 2
mort = {r["age_band"]: r for r in read("mortality_by_age.csv")}
fig, ax = plt.subplots(figsize=(88 * MM, 64 * MM))
m = [float(mort[k]["mortality_pct"]) for k in BANDS]
lo = [float(mort[k]["lcl"]) for k in BANDS]
hi = [float(mort[k]["ucl"]) for k in BANDS]
pooled = S["mortality_pooled"][0]
ax.axhline(pooled, color=LIGHT, lw=LW, ls=(0, (2, 2)), zorder=0)
ax.text(-0.35, pooled + 1.0, f"All ages {pooled:.1f}%", fontsize=6, color=GREY, va="bottom")
ax.vlines(x, lo, hi, color=INK, lw=LW)
ax.plot(x, m, ls="none", marker="o", ms=3.4, mfc="white", mec=INK, mew=LW)
ax.set_ylim(0, 55)
ax.set_yticks([0, 10, 20, 30, 40, 50])
ax.spines["left"].set_bounds(0, 50)
ax.set_ylabel("In-hospital mortality (%)")
age_axis(ax)
save(fig, "fig2_mortality_by_age")

# ---------------------------------------------------------------- Figure 3
disp = read("disposition_by_year.csv")
order = [("Transfer to another hospital (06)", "Transfer to another hospital", ACCENT, "o", ACCENT),
         ("In-hospital death (07)", "In-hospital death", INK, "o", "white"),
         ("Rehabilitation facility (09)", "Rehabilitation facility", INK, "s", "white"),
         ("Residual: routine, home, other reasons, suppressed hospice", "Home, routine and other", GREY, "^", "white"),
         ("Nursing facility (10)", "Nursing facility", GREY, "D", "white")]
fig, ax = plt.subplots(figsize=(120 * MM, 66 * MM))
yrs = [int(y) for y in YEARS]
tot = {y: float(next(r for r in disp if r["disposition"] == "Total")[y]) for y in YEARS}
for key, label, col, mk, face in order:
    row = next(r for r in disp if r["disposition"] == key)
    v = [100 * float(row[y]) / tot[y] for y in YEARS]
    ax.plot(yrs, v, color=col, lw=LW, marker=mk, ms=3.0, mfc=face, mec=col, mew=LW)
    dy = {"In-hospital death": 0.8, "Rehabilitation facility": -1.0}.get(label, 0)
    ax.text(2024.2, v[-1] + dy, label, fontsize=6.5, va="center", ha="left", color=col)
ax.set_xlim(2018.7, 2024.3)
ax.set_xticks(yrs)
ax.spines["bottom"].set_bounds(2019, 2024)
ax.set_ylim(0, 50)
ax.set_yticks([0, 10, 20, 30, 40, 50])
ax.spines["left"].set_bounds(0, 50)
ax.set_ylabel("Share of episodes (%)")
ax.set_xlabel("Data year")
save(fig, "fig3_disposition_by_year")

# ------------------------------------------------------- Supplementary S1
sub = read("subcode_by_year.csv")
labels = {"Cerebral arteries (I63.3-I63.5)": ("Cerebral arteries (I63.3–I63.5)", ACCENT, "o", ACCENT),
          "Precerebral arteries (I63.0-I63.2)": ("Precerebral arteries (I63.0–I63.2)", INK, "o", "white"),
          "Other or unspecified (I63.8, I63.9)": ("Other or unspecified (I63.8, I63.9)", GREY, "s", "white"),
          "Cerebral venous thrombosis (I63.6)": ("Cerebral venous thrombosis (I63.6)", GREY, "^", "white")}
fig, ax = plt.subplots(figsize=(120 * MM, 66 * MM))
for row in sub:
    lab, col, mk, face = labels[row["group"]]
    # a suppressed cell is drawn as a gap in the line
    pts = [(int(y), float("nan") if row[y].startswith("<") else 100 * float(row[y]) / tot[y])
           for y in YEARS]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, lw=LW, marker=mk, ms=3.0,
            mfc=face, mec=col, mew=LW)
    ax.text(2024.2, pts[-1][1], lab, fontsize=6.5, va="center", ha="left", color=col)
ax.set_xlim(2018.7, 2024.3)
ax.set_xticks(yrs)
ax.spines["bottom"].set_bounds(2019, 2024)
ax.set_ylim(0, 100)
ax.set_yticks([0, 20, 40, 60, 80, 100])
ax.spines["left"].set_bounds(0, 100)
ax.set_ylabel("Share of cohort episodes (%)")
ax.set_xlabel("Data year")
save(fig, "figS1_subcode_by_year")
print("figures written to", FIGURES)
