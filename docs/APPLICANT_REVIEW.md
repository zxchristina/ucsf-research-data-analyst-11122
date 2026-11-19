# First-person interview preparation and review checklist

This codebase was prepared with AI assistance. Please review it before representing it as your own project work.

1. **Run end to end:** `python -m pytest -q` then `python -m src.ops_reliability.run --generate`.
2. **Inspect five rows** in each input, the issue audit, the clean output, and the staffing metric join. Explain why row counts reconcile despite multiple flags per record.
3. **Explore a defect:** change a synthetic ticket to an invalid `channel`, rerun, and check the issue appears. Add a test for that scenario.
4. **Understand forecast validation:** the 28-day backtest predicts ticket volume using lag-7 and expanding historical mean. Explain why both use only earlier observed values, and why the sample is not proof of real predictive ability.
5. **SQL/R verification:** run the PostgreSQL scripts and R/tidyverse summary in actual runtimes. Fix incompatibilities and commit tests or corrections before claiming these components work.
6. **Security:** no actual customer/employee/health data, no credentials. Be ready to explain why real-world private data needs authorization and additional governance.
7. **Keep your account's history meaningful:** make an independently reviewed and tested improvement on a branch, then merge it. Describe your own contributions rather than attributing the AI-generated starter to past employer work.
