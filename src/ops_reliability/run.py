"""One-command reproducible example: audit, deliver, and backtest."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

from .generate import generate
from .qa import audit
from .analysis import daily_metrics, backtest


def run(root: Path, create_data: bool = False, count: int = 14000) -> dict:
    if create_data:
        generate(root, count=count)
    raw = root / "data" / "raw"
    tickets = pd.read_csv(raw / "tickets.csv", dtype=str, keep_default_na=False)
    agents = pd.read_csv(raw / "agents.csv", dtype=str)
    shifts = pd.read_csv(raw / "shifts.csv", dtype=str)
    result = audit(tickets, agents, shifts)
    metrics = daily_metrics(result.clean, shifts)
    forecasts, evaluation = backtest(metrics)
    out = root / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    result.clean.to_csv(out / "clean_tickets.csv", index=False)
    result.exceptions.to_csv(out / "qa_exceptions.csv", index=False)
    metrics.to_csv(out / "regional_daily_metrics.csv", index=False)
    forecasts.to_csv(out / "forecast_backtest.csv", index=False)
    summary = {"audit": result.summary, "forecast": evaluation,
               "source_files": ["tickets.csv", "agents.csv", "shifts.csv"]}
    (out / "validation_report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "validation_notes.md").write_text(
        "# Data release note (synthetic demonstration)\n\n"
        f"- Source ticket rows: **{result.summary['source_ticket_rows']:,}**\n"
        f"- Analysis-ready rows: **{result.summary['analysis_ready_rows']:,}**\n"
        f"- Excluded source rows: **{result.summary['excluded_ticket_rows']:,}**\n"
        f"- Ticket-level rule violations: **{result.summary['ticket_issues']}**\n"
        f"- Invalid shift records: **{result.summary['shift_issues']}**\n"
        f"- Column-level missing counts: `{json.dumps(result.summary['missing_by_column'])}`\n"
        "- Type checks: UTC timestamps parsed; SLA target converted to positive integer; duration checked.\n"
        "- Cross-source reconciliation: agent ID and home region checked; staffing hours joined by region/day.\n"
        "- Plausibility checks: negative or >30-day durations, invalid priority/channel/region, duplicates.\n"
        "- Row counts reconcile: source rows = clean rows + excluded rows.\n"
        f"- Held-out demand forecast: lag-7 WAPE **{evaluation['lag_7_wape']:.1%}**, "
        f"historical-mean WAPE **{evaluation['historical_mean_wape']:.1%}**.\n\n"
        "**Limitations:** Synthetic data, no deployment, no actual customer or clinical records. "
        "Anomaly rules are illustrative and must be calibrated to a real operational system.\n",
        encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--count", type=int, default=14000)
    args = parser.parse_args()
    print(json.dumps(run(args.root, create_data=args.generate, count=args.count), indent=2))

if __name__ == "__main__":
    main()
