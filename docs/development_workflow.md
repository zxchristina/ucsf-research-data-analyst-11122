# Environment, AI code review, and publishing checklist

## Prepare the environment (local, synthetic data only)

1. Check `python --version` (3.10+) and `git --version`.
2. Create a venv and install `requirements.txt` exactly as in the README.
3. Regenerate CSVs, run `python -m src.sata_demo.pipeline`, and inspect the audit report.
4. Run `python -m pytest -q` and check the reconciliation counts.
5. If needed, set up a local PostgreSQL sandbox with **synthetic examples only**; `sql/` contains an illustrative schema and cohort queries, not migrations tested against a live DB.
6. R/tidyverse output must be validated in an R-enabled environment; it was not executable in the construction environment.

## Git branch / commit / merge example

The initial archive contains assistant-attributed Git history including a real feature branch merge. To contribute your own work after review:

```bash
git checkout -b feature/my-review
# edit the code and add/review a unit test
git add src tests README.md
git commit -m "test: add reviewed boundary cases"
git checkout main
git merge --no-ff feature/my-review
```

## Before accepting AI-assisted code

- [ ] Inspect the diff; explain the rule being modified.
- [ ] Run unit tests, including negative and boundary cases.
- [ ] Reconcile before/after record counts and sample exception sheets.
- [ ] Identify any false exclusions and review with appropriate domain experts.
- [ ] Keep actual clinical data out of all public repositories and unapproved AI services.
- [ ] Document approvals, changes, tests, and versioned releases.

## Publish to your GitHub account

Create a **blank** GitHub repository, e.g. `synthetic-multicenter-research-data-qa`, without adding a README (this repository already has one). Then from the unzipped folder:

```bash
git remote add origin https://github.com/YOUR_USERNAME/synthetic-multicenter-research-data-qa.git
git push -u origin main
```

GitHub will require authentication or a credential helper. The initial commits are by **AI Portfolio Assistant** because those are the actual starter-code creation commits. Review, test, and make your own improvements/commits under your true Git identity before using the link as evidence of personal coding proficiency. Never change commit author metadata to misrepresent who wrote the original code.

A local zip file path is **not** a shareable GitHub URL. Add the actual public GitHub HTTPS URL to the fourth paragraph of the UCSF cover letter only after publishing.
