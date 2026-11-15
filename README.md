# Cranial decompression for ischaemic stroke in Germany, 2019–2024

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24236654.svg)](https://doi.org/10.5281/zenodo.24236654)

Code and extracted aggregate counts for a descriptive study of how cranial
decompression for ischaemic stroke is used across age in Germany, relative to
the age structure of the inpatient stroke population, and how in-hospital
mortality and discharge destination vary with age.

The repository reproduces every table value and figure of the study from two
small JSON files. It contains no individual-level data.

## Study summary

**Question.** How is cranial decompression for ischaemic stroke distributed
across age in Germany relative to the inpatient stroke population, and how do
in-hospital mortality and discharge destination vary with age?

**Data.** Aggregate counts from the InEK DatenBrowser
(<https://datenbrowser.inek.org>), which publishes the billing data that German
hospitals reimbursed under the Diagnosis Related Groups system submit under
§21 KHEntgG. Data years 2019 to 2024, queried in July 2026, with additional
queries on the same deliveries in November 2026. The unit of observation is the
discharge episode; episodes of the same patient are not linked.

**Cohort.** Discharge episodes with the procedure code OPS 5-012.0 (incision of
the skull bones, decompression) and a primary diagnosis of cerebral infarction
(ICD-10-GM I63.0 to I63.6, I63.8, I63.9). The code does not distinguish
hemicraniectomy from other decompression and does not record infarct territory.

**Measures.**

- Age distribution of the cohort and of all inpatient episodes with a primary
  I63 diagnosis.
- Age-specific utilisation ratio: cohort episodes per 1000 primary-I63
  episodes in the same age band. The denominator includes all ischaemic
  strokes, so the ratio describes utilisation relative to the stroke case mix,
  not a treatment rate among eligible patients.
- Oedema-based utilisation: decompression episodes per 100 primary-I63 episodes
  with a secondary diagnosis of brain compression or cerebral oedema (G93.5,
  G93.6), by age band, as a denominator closer to patients in whom surgery is
  considered.
- Disposition by age, and intracranial thrombectomy (OPS 8-836.80) and systemic
  thrombolysis (8-020.8) coded in the same episode.
- Palliative-care procedure codes (OPS 8-982, 8-98e, 8-98h) among oedema-coded
  primary-I63 episodes, with and without decompression.
- In-hospital mortality (discharge reason 07) overall and by age band.
- Discharge disposition (discharge reasons 06, 07, 09, 10 and a residual).
- Linear change over the six data years.

**Main results (pooled 2019–2024).**

| Measure | Value |
|---|---|
| Decompression episodes | 5,498 (mean 916 per year) |
| Aged 60 years or older | 49.8% of episodes (43.0% aged 60–74, 6.8% aged 75 or older) |
| Primary-I63 episodes aged 60 or older | 85.7% of 1,494,185 |
| Episodes per 1000 primary-I63 episodes | 17.9 below 40 years; 0.2 at 80 years or older; 12.9 below 60 versus 2.14 at 60 or older |
| Change in utilisation | rate ratio per year 0.995 (95% CI 0.974–1.016) |
| Decompression per 100 primary-I63 episodes with coded oedema | 15.1 overall; 34.0 below 60 versus 9.6 at 60 or older; 1.0 at 80 or older |
| In-hospital mortality | 24.5% overall; 13.2% below 40 years to 42.1% at 80 or older |
| Mortality, 60 or older versus below 60 | 29.6% versus 19.5%; risk ratio 1.52 (95% CI 1.38–1.67) |
| Discharge disposition | transfer 39.9%, death 24.5%, rehabilitation 22.9%, residual 11.1%, nursing facility 1.5% |
| Change in disposition | transfer 37.8% to 42.6%; rehabilitation 27.4% to 19.6% |
| Thrombectomy coded in the same episode | 43.2% (2019: 39.6%; 2024: 49.8%) |
| Palliative-care code among oedema-coded episodes | 1.8% overall (2019: 1.2%; 2024: 2.9%); 0.6–0.9% with and 1.9–2.0% without decompression |

**Interpretation.** Half of the decompression episodes involved patients aged
60 years or older, almost all of them younger than 75 years. Relative to the
inpatient stroke population, utilisation fell about sixfold above age 60 and
was rare beyond 75 years, where in-hospital mortality approached 40%. The
gradient persisted among strokes coded with oedema or brain compression.

**Scope.** The analysis is descriptive and unadjusted. Functional outcome,
stroke severity, timing of surgery and decisions to limit treatment are not
recorded in the data source; palliative-care procedure codes record structured
palliative treatment only. A death after interhospital transfer is not recorded in
the operative episode.

## Repository layout

```
data/
  cohort_by_year.json                          cohort counts, sex, length of stay, PCCL,
                                               age distribution, deaths and age distribution
                                               of deaths, by data year
  subcode_disposition_denominator_by_year.json I63 subcode composition, discharge disposition
                                               and the all-primary-I63 denominator with its
                                               age distribution, by data year
  additional_queries_by_year.json              November 2026 queries Q0-Q9 (oedema-defined
                                               subgroup, disposition by age, reperfusion
                                               co-coding and palliative-care codes, with the
                                               code list used in each year), by data year
src/
  common.py      age-band definitions, data loading, interval estimators
  analysis.py    computes every reported value; writes results/
  figures.py     draws the figures from results/; writes figures/
results/         CSV tables and summary.json (generated)
figures/         PDF and 600 dpi PNG figures (generated)
```

Both JSON files contain a `_meta` block documenting the query definitions,
the disposition residual and the handling of suppressed cells.

## Methods in brief

- **Age-band counts.** The source reports age distributions as percentages
  with two decimal places. Band counts of episodes, deaths and denominator
  episodes are reconstructed as total × percentage / 100 and summed over years.
  The rounding error is below 0.1 episodes per native band and year in the
  cohort and below 13 episodes in the denominator. Patients younger than 18
  years are assigned to the band below 40 years in numerator and denominator.
- **Disposition.** Only discharge reasons 06, 07, 09 and 10 return unsuppressed
  counts. The residual (total minus these four reasons) contains routine and
  home discharge, other reasons and hospice discharges, which were suppressed
  (fewer than four) or zero in every year.
- **Suppressed cells in the additional queries.** The decompression subset of
  the palliative-care query (Q9) is below the display threshold in 2019 to
  2022. Each suppressed cell is carried as zero to three episodes, and pooled
  proportions that involve it are reported as ranges.
- **Intervals and tests.** Wilson intervals for proportions; Poisson (Byar)
  intervals for utilisation ratios; Katz interval for the risk ratio; Newcombe
  hybrid score interval for the risk difference; log-linear Poisson model with
  overdispersion-scaled standard error for the trend in utilisation;
  Cochran–Armitage test for trends in proportions.
- **Integrity checks.** `results/integrity_checks.csv` confirms that the annual
  episode counts from independently rebuilt queries agree, that subcode groups
  and disposition categories sum to the annual totals, and that death counts
  agree between queries. `results/integrity_checks_additional.csv` confirms that
  the re-extracted cohort in November 2026 reproduces the July counts and age
  distributions exactly, that the transfer and rehabilitation queries reproduce
  the July disposition counts, and that nested queries are not larger than their
  parent queries. `analysis.py` stops if any check fails.

## Reproduce

Python 3.10 or later.

```bash
pip install -r requirements.txt
cd src
python analysis.py     # writes results/*.csv and results/summary.json
python figures.py      # writes figures/*.pdf and figures/*.png
```

The analysis is deterministic; repeated runs give identical result files.
Figures use Liberation Sans, falling back to Arial, Helvetica or DejaVu Sans.

## Output files

| File | Content |
|---|---|
| `annual_profile.csv` | episodes, sex, length of stay, PCCL, age 60 or older, deaths, mortality with 95% CI, primary-I63 episodes and utilisation ratio, by year and pooled |
| `utilisation_by_age.csv` | cohort and denominator counts and utilisation ratio with 95% CI by age band, below 60, 60 or older, and all ages |
| `mortality_by_age.csv` | reconstructed episodes, deaths and mortality with 95% CI by age band |
| `age_strata.csv` | risk ratio and risk difference for death, 60 or older versus below 60 |
| `disposition_by_year.csv` | disposition counts by year, pooled count and share |
| `subcode_by_year.csv` | I63 subcode groups by year |
| `temporal_trends.csv` | trend estimates for utilisation, transfer, rehabilitation, mortality and the shares from the additional queries |
| `integrity_checks.csv` | consistency checks across queries |
| `integrity_checks_additional.csv` | consistency checks for the November 2026 queries |
| `oedema_subgroup_by_year.csv` | oedema-coded primary-I63 episodes, decompression within them and mortality, by year |
| `oedema_subgroup_by_age.csv` | the same by age band, with 95% CI |
| `disposition_by_age.csv` | transfer, rehabilitation and death by age band |
| `reperfusion_by_year.csv`, `reperfusion_by_age.csv` | thrombectomy and thrombolysis coded in the same episode |
| `palliative_by_year.csv`, `palliative_by_age.csv` | palliative-care codes among oedema-coded episodes, with and without decompression |
| `summary.json` | all reported values in one file |

| Figure | Content |
|---|---|
| `fig1_age_utilisation` | (a) age distribution of the cohort and of all primary-I63 episodes; (b) utilisation ratio by age band, log scale; (c) decompression per 100 oedema-coded primary-I63 episodes by age band |
| `fig2_mortality_by_age` | in-hospital mortality by age band |
| `fig3_disposition_by_year` | discharge disposition by data year |
| `figS1_subcode_by_year` | I63 subcode composition by data year |
| `figS2_disposition_by_age` | discharge disposition by age band |

## Data source and licence

The counts in `data/` were read from the publicly accessible InEK DatenBrowser
of the Institut für das Entgeltsystem im Krankenhaus (InEK GmbH). They are
aggregate published figures, reproduced here with attribution so that the
analysis can be checked; they are not covered by the code licence. Source:
InEK DatenBrowser, Datenveröffentlichung gemäß §21 KHEntgG, data years
2019–2024, <https://datenbrowser.inek.org>.

The code in `src/` is released under the MIT License (see `LICENSE`).

## Citation

See `CITATION.cff`. All versions are archived on Zenodo:
<https://doi.org/10.5281/zenodo.24236654>.
