# Data dictionary and lineage

The three source tables are **fictional**. Identifiers are synthetic and are never derived from human names or emails.

| Source | Grain / key | Main variables | Purpose |
|---|---|---|---|
| `tickets.csv` | one support interaction / `ticket_id` | region, agent_id, channel, category, priority, UTC opened/resolved, SLA target | Operational demand and outcomes |
| `agents.csv` | one fictional agent / `agent_id` | home_region, primary_channel, active | Dimension used to catch invalid ticket ownership |
| `shifts.csv` | one region-day / (`region`, `shift_date`) | scheduled_agent_hours | Separate staffing feed, intentionally includes one invalid record |

**Downstream lineage:** source exports -> `qa.audit` -> `clean_tickets.csv` / `qa_exceptions.csv` -> `analysis.daily_metrics` -> `regional_daily_metrics.csv` and `forecast_backtest.csv`. A summary JSON and human-readable validation note accompany each output.

**Codebook:** `region` is one of `NA-WEST`, `NA-EAST`, `EMEA`, `APAC`, `LATAM`, `ANZ`; `channel` is `chat`, `email`, `phone`; `priority` is `low`, `normal`, `high`, `critical`; durations are measured in minutes, and timestamp fields use UTC. Expected ticket IDs are globally unique; duplicate source rows are excluded for review rather than arbitrarily chosen.

**Operational caution:** `sla_target_minutes` is an illustrative ticket-level rule and should never be considered a contractual SLA. Bad staffing rows are flagged and surfaced as missing in metrics. Forecasts are retrospective benchmarks, not production staffing guidance.
