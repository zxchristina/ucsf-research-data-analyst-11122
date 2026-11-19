"""Validation rules for independent support operations data.

Rows are excluded conservatively when any critical field or reference fails QA.
"""
from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from .generate import REGIONS, PRIORITIES, CHANNELS, CATEGORIES


@dataclass
class AuditResult:
    clean: pd.DataFrame
    exceptions: pd.DataFrame
    summary: dict


def audit(tickets: pd.DataFrame, agents: pd.DataFrame, shifts: pd.DataFrame) -> AuditResult:
    rows = tickets.copy()
    required = ["ticket_id", "region", "agent_id", "channel", "category", "priority", "opened_at_utc", "resolved_at_utc", "sla_target_minutes"]
    for column in required:
        if column not in rows:
            raise ValueError(f"Missing required column: {column}")
    problems: list[dict] = []
    def mark(mask: pd.Series, reason: str) -> None:
        for _, record in rows.loc[mask.fillna(False)].iterrows():
            problems.append({"ticket_id": str(record["ticket_id"]), "region": str(record["region"]), "issue": reason})

    rowcount = len(rows)
    missing_counts = {c: int((rows[c].isna() | rows[c].astype(str).str.strip().eq("" )).sum()) for c in required}
    for col in required:
        mark(rows[col].isna() | rows[col].astype(str).str.strip().eq(""), f"missing_{col}")
    mark(rows["ticket_id"].duplicated(keep=False), "duplicate_ticket_id")
    mark(~rows["region"].isin(REGIONS), "unknown_region")
    mark(~rows["priority"].isin(PRIORITIES), "unknown_priority")
    mark(~rows["channel"].isin(CHANNELS), "unknown_channel")
    mark(~rows["category"].isin(CATEGORIES), "unknown_category")
    start = pd.to_datetime(rows["opened_at_utc"], utc=True, errors="coerce")
    end = pd.to_datetime(rows["resolved_at_utc"], utc=True, errors="coerce")
    mark(start.isna(), "invalid_opened_at")
    mark(end.isna(), "invalid_resolved_at")
    minutes = (end - start).dt.total_seconds() / 60
    mark(minutes.lt(0), "negative_resolution_duration")
    mark(minutes.gt(30 * 24 * 60), "implausible_resolution_duration_over_30d")
    targets = pd.to_numeric(rows["sla_target_minutes"], errors="coerce")
    mark(targets.isna() | targets.le(0), "invalid_sla_target")
    known_agents = set(agents["agent_id"].astype(str))
    mark(~rows["agent_id"].isin(known_agents), "unknown_agent")
    owner_region = rows["agent_id"].map(agents.set_index("agent_id")["home_region"])
    mark(owner_region.notna() & owner_region.ne(rows["region"]), "agent_region_mismatch")

    # A separate source reconciliation: staffed region/days must have valid hours.
    shifts_copy = shifts.copy()
    shifts_copy["scheduled_agent_hours"] = pd.to_numeric(shifts_copy["scheduled_agent_hours"], errors="coerce")
    bad_shift = shifts_copy["scheduled_agent_hours"].isna() | shifts_copy["scheduled_agent_hours"].le(0)
    shift_audits = [{"ticket_id": "", "region": str(x["region"]), "issue": "invalid_shift_hours", "source_row": int(idx)}
                    for idx, x in shifts_copy.loc[bad_shift].iterrows()]
    exceptions = pd.DataFrame(problems, columns=["ticket_id", "region", "issue"])
    ticket_exceptions = exceptions.copy()
    if shift_audits:
        exceptions = pd.concat([exceptions, pd.DataFrame(shift_audits)], ignore_index=True)
    flagged_ids = set(ticket_exceptions["ticket_id"])
    good_mask = ~rows["ticket_id"].astype(str).isin(flagged_ids)
    clean = rows.loc[good_mask].copy()
    clean["opened_at_utc"] = start.loc[good_mask].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    clean["resolved_at_utc"] = end.loc[good_mask].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    clean["resolution_minutes"] = minutes.loc[good_mask].round(1)
    clean["sla_breached"] = clean["resolution_minutes"].gt(targets.loc[good_mask])
    clean["ticket_day"] = start.loc[good_mask].dt.strftime("%Y-%m-%d")
    clean = clean.reset_index(drop=True)
    clean["sla_target_minutes"] = targets.loc[good_mask].astype(int).to_numpy()
    # Explicit reconciliation, not silent drop.
    excluded_rows = rowcount - len(clean)
    assert rowcount == len(clean) + excluded_rows
    summary = {
        "source_ticket_rows": rowcount,
        "analysis_ready_rows": len(clean),
        "excluded_ticket_rows": excluded_rows,
        "ticket_issues": len(ticket_exceptions),
        "shift_issues": len(shift_audits),
        "missing_by_column": missing_counts,
        "row_reconciliation_passed": True,
        "unique_ticket_ids_in_clean": bool(clean["ticket_id"].is_unique),
        "invalid_shift_rows": int(bad_shift.sum()),
        "caution": "Synthetic dataset and illustrative QA rules only; no real customer or employee data",
    }
    return AuditResult(clean, exceptions, summary)
