"""Reproducible service demand, staffing metrics, and simple forecasting benchmark."""
from __future__ import annotations
import numpy as np
import pandas as pd


def daily_metrics(clean: pd.DataFrame, shifts: pd.DataFrame) -> pd.DataFrame:
    groups = clean.groupby(["region", "ticket_day"], as_index=False).agg(
        ticket_count=("ticket_id", "nunique"),
        breached=("sla_breached", "sum"),
        median_resolution_minutes=("resolution_minutes", "median"),
    )
    groups["breach_rate"] = groups["breached"] / groups["ticket_count"]
    schedules = shifts.rename(columns={"shift_date": "ticket_day"}).copy()
    schedules["scheduled_agent_hours"] = pd.to_numeric(schedules["scheduled_agent_hours"], errors="coerce")
    schedules.loc[schedules["scheduled_agent_hours"].le(0), "scheduled_agent_hours"] = np.nan
    combined = groups.merge(schedules[["region", "ticket_day", "scheduled_agent_hours"]],
                            on=["region", "ticket_day"], how="left", validate="one_to_one", indicator=True)
    combined["hours_per_ticket"] = combined["scheduled_agent_hours"] / combined["ticket_count"]
    return combined.sort_values(["region", "ticket_day"]).reset_index(drop=True)


def backtest(metrics: pd.DataFrame, holdout_days: int = 28) -> tuple[pd.DataFrame, dict]:
    """Forecast daily counts with a prior-week same-day baseline; no future leakage.

    A same-weekday lag 7 forecast is compared with expanding historical mean.
    Both use previous observations only, and are evaluated on last 28 days.
    """
    values = metrics[["region", "ticket_day", "ticket_count"]].copy()
    values["ticket_day"] = pd.to_datetime(values["ticket_day"])
    values = values.sort_values(["region", "ticket_day"])
    values["lag_7"] = values.groupby("region")["ticket_count"].shift(7)
    values["historical_mean"] = values.groupby("region")["ticket_count"].transform(
        lambda x: x.shift(1).expanding(min_periods=7).mean()
    )
    boundary = values["ticket_day"].max() - pd.Timedelta(days=holdout_days-1)
    test = values.loc[(values["ticket_day"] >= boundary) & values["lag_7"].notna()].copy()
    if test.empty:
        raise ValueError("Insufficient history for the requested backtest horizon")
    actual = test["ticket_count"].to_numpy()
    results: dict = {"holdout_start": boundary.strftime("%Y-%m-%d"), "holdout_days": holdout_days,
                     "evaluated_region_days": len(test)}
    for name in ("lag_7", "historical_mean"):
        pred = test[name].to_numpy()
        results[f"{name}_mae"] = round(float(np.mean(np.abs(actual - pred))), 3)
        results[f"{name}_wape"] = round(float(np.sum(np.abs(actual - pred)) / np.sum(actual)), 4)
    test["ticket_day"] = test["ticket_day"].dt.strftime("%Y-%m-%d")
    return test.reset_index(drop=True), results
