# ServiceOps Reliability Lab


A reproducible analytics system for a practical business question: **Can a distributed customer support team trust its daily demand, SLA and staffing metrics enough to make scheduling decisions?**

The project combines three fictional exports — service interactions, agent directory, and workforce schedules — across **six global regions and six months**. It detects data defects, documents reconciled counts, builds daily operational metrics, and evaluates two simple demand-forecasting baselines on a held-out time window.

The choice of domain reflects applied service operations analytics work and is deliberately independent of any medical or transplant job description.

## Why this is useful

Analytics fails when rows vanish silently, identifiers disagree across systems, or a forecast accidentally sees future data. This project treats **data quality as part of analytical delivery**: a metric should ship with a clear description of source inputs, exclusions, validation checks, and unresolved anomalies.

### Evidence from a deterministic demo run

- **14,001** fictional ticket rows generated, with **96** fictional agent records and **1,086** regional shift records.
- **10 ticket rows excluded** by explicit QA rules; **13,991** clean rows retained; source and output counts reconcile.
- **12** ticket rule violations and **1** staffing-feed violation detected (multiple problems can apply to one ticket).
- **8/8 Python tests passing locally**. The actual Python tests and pipeline can be rerun with the commands below.
- Backtesting compares previous-week same-weekday demand against an expanding historical mean on a **28-day holdout**, without future-data leakage.

Numbers above reflect an entirely synthetic, fixed-seed run and are not research findings about real customers. The data and large output CSVs are regenerated locally by the quickstart command; no private records or external downloads are needed.

## Architecture

```text
data/raw/{tickets,agents,shifts}.csv [generated; synthetic]
                |
                v
       Python type & reference audits  ---> outputs/qa_exceptions.csv
                |                        ---> outputs/validation_notes.md
                v
       outputs/clean_tickets.csv
                |
                +----> SQL/PostgreSQL analytical views (examples)
                +----> R/tidyverse monthly summaries (example)
                +----> daily regional SLA/staffing metrics
                                  |
                                  v
                         28-day forecast backtest
```

## Run it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python -m src.ops_reliability.run --generate
```

Key files: `src/ops_reliability/qa.py` (cross-source validation), `analysis.py` (metrics/forecasts), `sql/` (PostgreSQL schema and queries), `r/operations_summary.R` (tidyverse transformation), `tests/` (edge cases and assertions), `outputs/validation_notes.md` (plain-English evidence of checks).

See `docs/ENVIRONMENT_AND_SECURITY.md` for optional R/PostgreSQL setup, `docs/DATA_DICTIONARY.md` for types and lineage, and `docs/AI_ASSISTANCE_AND_VERIFICATION.md` for the AI-assisted development disclosure and review checklist.

## Data safety and honesty

All data is algorithmically generated, using arbitrary ticket and agent IDs; there are **no actual customers, employees, patients, employers, or private business records**. The illustrative SLA targets and validation thresholds cannot be used to make real production decisions. This is a learning and demonstration portfolio, not a finished deployed service or a previously performed employer project.

**Verification status:** Python tests and end-to-end generation were executed locally. R and PostgreSQL examples still require runtime validation in their respective environments. GitHub Actions is configured for Python tests, but a successful hosted CI run must be confirmed separately.
