# Synthetic Multicenter Transplant Outcomes Data QA

**Prepared as an independent portfolio demonstration for the UCSF Research Data Analyst application (Req 11122) | Entirely synthetic data | Not an official UCSF/SATA project**

A reproducible, small-scale demonstration of how a research data coordination center could ingest REDCap-style exports, registry records, and anesthesia extracts from **16 fictional participating sites**, run transparent data-quality rules, and publish an audited, analysis-ready cohort. Built as an **AI-assisted portfolio starter** for personal learning. It is not affiliated with UCSF, the SATA Liver Transplant Outcomes Database, SRTR, or any clinical provider.

**No actual patient information is included**. Field names, code lists, and plausibility thresholds are illustrative and **must not be used for clinical decisions or real protected health information (PHI)**.

## Relevance to research data analyst work

| Research data-center responsibility | Demonstration |
| --- | --- |
| Ingest heterogeneous submissions | Three CSV exports with site IDs and common case keys |
| Reconcile REDCap-style, registry, anesthesia data | `merge(..., validate='one_to_one')`, site/ID mismatch audit, row-count checks |
| Assess missingness and implausible values | Missing/duplicate keys, types, date ordering, illustrative age/blood-loss rules |
| Return site-specific audit sheets | `outputs/site_audit.csv` and `outputs/site_summary.csv` |
| Deliver reproducible analysis data | `outputs/analysis_ready.csv` with flagged cases excluded |
| Make validation transparent | `outputs/validation_report.json` with counts and check definitions |
| Prepare Postgres data model | `sql/001_schema.sql`, `sql/002_cohorts.sql` |
| Summarize data with tidyverse | `r/cohort_summary.R` (requires separate R installation) |
| Review AI-assisted changes | tests + human-review checklist; use Git branches and PRs when publishing |

## Quickstart

Requires Python 3.10+. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m src.sata_demo.generate --output data/raw
python -m src.sata_demo.pipeline --input data/raw --output outputs
pytest -q
```

Optional, if R and tidyverse are installed:

```bash
Rscript r/cohort_summary.R outputs/analysis_ready.csv outputs/r_site_summary.csv
```

Generated runtime outputs are intentionally not committed; representative output examples are checked in under `docs/examples/`. The synthetic input files **are committed** for repeatability, and can be regenerated deterministically. To visualize data, open `outputs/validation_report.json` and `outputs/site_audit.csv`.

## Controlled synthetic error cases

Generator intentionally inserts: a missing REDCap stop time, out-of-range blood loss, impossible registry age, wrong site label, duplicate REDCap case, unrecognized ASA code, and a registry case missing from the anesthesia extract. The QA pipeline reports each case with a rule code and a site-scoped audit message. Rules are **pedagogical approximations, not validated medical definitions**.

## Schema + security model

`docs/data_dictionary.md` lists source fields and controlled values. No names, MRNs, birth dates, clinical notes, or actual identifiers are used. `case_id` and `site_id` are fictional test identifiers only. Do **not** add real clinical files to this repo. `data/raw/*.csv` contains public synthetic examples; `.gitignore` excludes runtime outputs, local secrets, credentials, and non-synthetic work datasets by default.

Real clinical deployment would require approved institutional systems, IRB/DUA permissions, secure transfer, access controls, privacy training, encryption, audit logging, schema and codebook approval, and PI signoff. None is implemented here.

## What I would improve with a PI/team

- Replace illustrative QA thresholds with an approved clinical codebook and governance process.
- Add an R/Shiny review interface with authenticated, role-scoped access (not suitable for this public demo).
- Integrate secure REDCap API exports and registry mappings **only after** appropriate authorization.
- Add CI checks for R syntax and database migrations using an actual PostgreSQL service.

