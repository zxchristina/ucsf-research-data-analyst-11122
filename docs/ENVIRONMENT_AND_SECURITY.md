# Environment setup and data handling

## Reproduce on a clean machine
1. Clone the repository using HTTPS or configure GitHub SSH keys independently. Do not commit private SSH keys.
2. Install Python 3.10+ and create a virtual environment: `python -m venv .venv`.
3. Activate it (`source .venv/bin/activate`) and install packages with `pip install -r requirements.txt`.
4. Run `python -m pytest -q` and `python -m src.ops_reliability.run --generate`.
5. Optionally install R + `tidyverse` and run `Rscript r/operations_summary.R`.
6. Optionally create a disposable PostgreSQL database, execute `sql/001_schema.sql`, import the generated CSVs using the `\\copy` commands shown in that file, and run `sql/002_queries.sql`.

No credentials, API tokens, production SSH keys, environment variables, or private patient/customer data are required. `.env` is intentionally ignored by Git and should never be added to this project.

## Privacy and compliance
This project uses randomly generated ticket/agent IDs only. It does not contain PHI, PII, or records from an employer, hospital, customer, or collaborator. Healthcare datasets require separate institutional authorization, IRB/DUA assessment as appropriate, appropriate access controls, and privacy training; this demonstration does **not** substitute for those approvals or qualify as prior clinical-data experience.
