# Cranial decompression in hospitalised ischaemic stroke in Germany, 2019–2024

Reproducibility repository for a descriptive study of cranial decompression
associated with a primary diagnosis of cerebral infarction, using national
aggregate inpatient billing data from the German InEK DatenBrowser.

This repository contains the extracted aggregate data, the analysis and
figure code, and the generated figures and results workbook. It does not
contain the manuscript text.

## Summary

**Question.** How is cranial decompression for ischaemic stroke distributed
across the age spectrum in routine national practice in Germany, and how do
utilisation and in-hospital outcomes vary with age?

**Data.** Public aggregate counts from the InEK DatenBrowser
(datenbrowser.inek.org), which reports nationwide statutory (§21 KHEntgG) inpatient
billing data grouped to German Diagnosis Related Groups. Data years 2019–2024.
The unit is the discharge episode; there is no patient linkage. Cells with
fewer than four cases are suppressed at source.

**Cohort.** Discharge episodes with procedure code OPS 5-012.0 (cranial
decompression within the craniotomy/craniectomy category) and a primary
diagnosis of cerebral infarction (ICD-10-GM I63, nine leaf codes). This is a
broad coded proxy and cannot identify malignant middle cerebral artery
infarction.

**Main measures.**

- Episode volume, age distribution, in-hospital mortality (discharge reason 07),
  discharge disposition (discharge-reason codes), and I63 subcode composition.
- Age-specific utilisation ratio: cohort episodes per 1000 primary-I63
  inpatient episodes, by age band. The denominator is all primary-I63
  episodes and is an episode count, not a patient count or an eligibility
  denominator.

**Headline results (pooled 2019–2024).**

- 5,498 episodes over six years (mean 916/year; range 855–975).
- Episodes aged 60 or older were about half of the cohort (49.8%), whereas
  85.8% of the 1.49 million primary-I63 episodes were aged 60 or older.
- The utilisation ratio fell with age, from 19.1 per 1000 below 40 to 0.2 per
  1000 at 80 or older (12.99 per 1000 at <60 versus 2.14 at ≥60). The older
  patient share reflects the older age structure of the inpatient case mix
  rather than age-proportionate utilisation.
- Reconstructed in-hospital mortality rose across the age spectrum overall,
  from about 13% below 40 to about 42% at 80 or older; the largest between-band
  increase was from 65–74 to 75–79.
- Discharge disposition (pooled): transfer to another hospital 39.9%,
  in-hospital death 24.5%, rehabilitation 22.9%, a home/routine/other/
  suppressed-hospice residual 11.1%, nursing facility 1.5%.
- Cerebral-artery codes (I63.3–I63.5) accounted for 74.6% of the cohort;
  cerebral venous thrombosis (I63.6) for 0.2%.

**Boundaries.** Analyses are descriptive. The coded cohort cannot be equated
with malignant MCA infarction. The utilisation ratio is a relative age-pattern
measure, not a treatment rate among eligible patients. The unit is the discharge
episode, so transfers can produce more than one episode per patient. Age-band
mortality is reconstructed from grouped age distributions and is approximate;
grouped bands do not permit a test for a change at exact age 60. Functional
outcome (modified Rankin Scale) is not recorded.

## Repository layout

```
data/
  dc_data_base.json        cohort volume, sex, LOS, PCCL, age bands, mortality by year
  dc_data_v2_new.json      I63 subcode composition, disposition, and the primary-I63 denominator by year
  results_workbook.xlsx    multi-sheet summary workbook (built by src/build_workbook.py)
  csv/                     tidy CSV tables (built by src/export_tables.py):
                             annual_profile.csv, utilisation_by_age_pooled.csv,
                             mortality_by_age_pooled.csv, disposition_by_year.csv,
                             subtype_by_year.csv, denominator_by_year.csv
src/
  compute_statistics.py    prints all numeric results; writes results/summary_statistics.csv
  export_tables.py         writes the tidy CSV tables into data/csv/
  make_figures.py          generates all figures (PNG 600 dpi and PDF) into figures/
  build_workbook.py        rebuilds data/results_workbook.xlsx
figures/                   generated figures (main fig1–fig4, supplementary figS1–figS3)
results/                   created on run; holds summary_statistics.csv
requirements.txt
LICENSE
```

The JSON files are the primary source; the CSV tables in `data/csv/` are a
human-readable export of the same values for direct inspection. All labels are
in English. Age-band counts in the utilisation and mortality tables are
reconstructed from reported age-band percentages and annual totals and are
approximate; overall counts are exact.

## Data dictionary (brief)

- `dc_data_base.json`: for each year, `base_cohort` (episode_count, sex, length of
  stay, PCCL distribution, native age-band percentages, ≥60 overlay) and
  `mortality` (death count, in-hospital mortality, death age-band percentages).
- `dc_data_v2_new.json`: for each year, `subtype_composition` (I63 subcode
  counts and grouped totals), `disposition` (discharge-reason counts, with the
  residual and the raw suppressed hospice query result), and
  `denominator_all_I63` (all primary-I63 episodes and their age distribution).
  The `_meta` block documents the disposition residual and the extraction and
  reconstruction methods.

## Reproduce

```bash
pip install -r requirements.txt
python src/compute_statistics.py     # prints results, writes results/summary_statistics.csv
python src/export_tables.py          # writes tidy CSV tables into data/csv/
python src/make_figures.py           # writes figures/*.png and figures/*.pdf
python src/build_workbook.py         # rebuilds data/results_workbook.xlsx
```

Each year's cohort volume was rebuilt independently at the data source and
matched an earlier extraction exactly, as an integrity check
(2019, 941; 2020, 893; 2021, 975; 2022, 855; 2023, 937; 2024, 897).

## License

Code and derived data tables are released under the MIT License (see LICENSE).
The underlying counts are public aggregate figures from the InEK DatenBrowser.
