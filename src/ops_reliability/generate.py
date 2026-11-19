"""Generate fully fictional, reproducible, multi-source service operations data.

No actual customer, employee, provider, or operational records are used.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REGIONS = ("NA-WEST", "NA-EAST", "EMEA", "APAC", "LATAM", "ANZ")
CATEGORIES = ("account", "billing", "technical", "product", "delivery")
PRIORITIES = ("low", "normal", "high", "critical")
CHANNELS = ("chat", "email", "phone")


def generate(root: Path, seed: int = 34, count: int = 14000, inject_errors: bool = True) -> dict[str, int]:
    """Create synthetic ticket, agent and shift exports with explicit QA faults."""
    if count < 200:
        raise ValueError("Count must be at least 200 for the demonstration")
    rng = np.random.default_rng(seed)
    raw = root / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    agents = pd.DataFrame([
        {"agent_id": f"AG{region_idx:02d}{n:02d}",
         "home_region": region, "primary_channel": CHANNELS[n % 3],
         "active": True}
        for region_idx, region in enumerate(REGIONS, start=1)
        for n in range(1, 17)
    ])
    agents.to_csv(raw / "agents.csv", index=False)

    days = pd.date_range("2026-01-01", "2026-06-30", freq="D", tz="UTC")
    shifts = pd.DataFrame([
        {"shift_date": day.date().isoformat(), "region": region,
         "scheduled_agent_hours": int(40 + rng.integers(0, 35)) +
             (0 if day.dayofweek < 5 else -12),
         "shift_source": "workforce_export"}
        for day in days for region in REGIONS
    ])

    # One record per support interaction. Ticket ownership is region-consistent.
    day_idx = rng.integers(0, len(days), size=count)
    weights = np.array([0.29, 0.22, 0.15, 0.22, 0.07, 0.05])
    r_idx = rng.choice(len(REGIONS), size=count, p=weights)
    opened = days[day_idx] + pd.to_timedelta(rng.integers(0, 24*60, count), unit="m")
    priorities = rng.choice(PRIORITIES, size=count, p=[0.18, 0.56, 0.21, 0.05])
    priority_minutes = {"low": 1440, "normal": 480, "high": 240, "critical": 60}
    target = np.array([priority_minutes[p] for p in priorities])
    # Some tickets miss SLA; this is legitimate operational variance, not a QA error.
    duration = np.maximum(4, rng.lognormal(mean=5.15, sigma=0.85, size=count)).astype(int)
    resolved = opened + pd.to_timedelta(duration, unit="m")
    regions = np.array(REGIONS)[r_idx]
    agent_ids = [f"AG{idx+1:02d}{int(rng.integers(1,17)):02d}" for idx in r_idx]
    tickets = pd.DataFrame({
        "ticket_id": [f"TKT{i:07d}" for i in range(1, count+1)],
        "region": regions,
        "agent_id": agent_ids,
        "channel": rng.choice(CHANNELS, size=count, p=[0.44, 0.35, 0.21]),
        "category": rng.choice(CATEGORIES, size=count),
        "priority": priorities,
        "opened_at_utc": opened.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resolved_at_utc": resolved.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sla_target_minutes": target,
    })
    if inject_errors:
        tickets.loc[8, "opened_at_utc"] = ""
        tickets.loc[24, "region"] = "MARS"
        tickets.loc[39, "agent_id"] = "AG9999"
        tickets.loc[52, "priority"] = "urgent-ish"
        tickets.loc[67, "sla_target_minutes"] = -10
        tickets.loc[81, "resolved_at_utc"] = "2025-12-01T00:00:00Z"
        tickets.loc[94, "resolved_at_utc"] = "2036-01-01T00:00:00Z"
        tickets.loc[103, "agent_id"] = f"AG{(r_idx[103]+1) % 6 + 1:02d}01"
        tickets = pd.concat([tickets, tickets.iloc[[5]]], ignore_index=True)
        shifts.loc[3, "scheduled_agent_hours"] = -4
    shifts.to_csv(raw / "shifts.csv", index=False)
    tickets.to_csv(raw / "tickets.csv", index=False)
    return {"tickets": len(tickets), "agents": len(agents), "shifts": len(shifts)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--seed", type=int, default=34)
    parser.add_argument("--count", type=int, default=14000)
    parser.add_argument("--no-errors", action="store_true")
    args = parser.parse_args()
    print(generate(args.root, args.seed, args.count, not args.no_errors))

if __name__ == "__main__":
    main()
