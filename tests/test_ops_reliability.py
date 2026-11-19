from pathlib import Path

import pandas as pd
import pytest

from src.ops_reliability.generate import generate
from src.ops_reliability.qa import audit
from src.ops_reliability.analysis import backtest, daily_metrics
from src.ops_reliability.run import run


def inputs(tmp_path: Path, errors=True):
    generate(tmp_path, count=800, inject_errors=errors)
    raw = tmp_path / 'data' / 'raw'
    return tuple(pd.read_csv(raw / f, dtype=str, keep_default_na=False)
                 for f in ('tickets.csv', 'agents.csv', 'shifts.csv'))


def test_synthetic_data_has_no_names_or_customer_emails(tmp_path):
    tickets, agents, shifts = inputs(tmp_path)
    assert len(tickets) == 801
    assert agents['agent_id'].nunique() == 96
    assert shifts['region'].nunique() == 6
    assert not {'customer_name', 'customer_email', 'phone'}.intersection(tickets.columns)


def test_exceptions_are_excluded_and_reconciled(tmp_path):
    tickets, agents, shifts = inputs(tmp_path)
    result = audit(tickets, agents, shifts)
    assert result.summary['source_ticket_rows'] == 801
    assert result.summary['excluded_ticket_rows'] > 0
    assert len(result.clean) + result.summary['excluded_ticket_rows'] == len(tickets)
    assert result.clean['ticket_id'].is_unique
    assert {'duplicate_ticket_id', 'unknown_region', 'unknown_priority', 'agent_region_mismatch',
            'invalid_shift_hours', 'negative_resolution_duration'}.issubset(set(result.exceptions.issue))


def test_clean_data_has_no_exceptions(tmp_path):
    tickets, agents, shifts = inputs(tmp_path, errors=False)
    result = audit(tickets, agents, shifts)
    assert len(result.clean) == 800
    assert result.summary['ticket_issues'] == 0
    assert result.summary['shift_issues'] == 0


def test_unknown_agent_and_invalid_sla_are_detected(tmp_path):
    tickets, agents, shifts = inputs(tmp_path)
    result = audit(tickets, agents, shifts)
    assert 'unknown_agent' in set(result.exceptions.issue)
    assert 'invalid_sla_target' in set(result.exceptions.issue)


def test_metrics_are_joined_to_staffing(tmp_path):
    tickets, agents, shifts = inputs(tmp_path, errors=False)
    result = audit(tickets, agents, shifts)
    metrics = daily_metrics(result.clean, shifts)
    assert metrics['ticket_count'].gt(0).all()
    assert metrics['breach_rate'].between(0,1).all()
    assert metrics['_merge'].eq('both').all()


def test_forecast_uses_past_only(tmp_path):
    tickets, agents, shifts = inputs(tmp_path, errors=False)
    metrics = daily_metrics(audit(tickets, agents, shifts).clean, shifts)
    output, scores = backtest(metrics)
    assert len(output) > 0
    assert scores['holdout_days'] == 28
    assert scores['lag_7_wape'] >= 0
    assert scores['historical_mean_wape'] >= 0


def test_end_to_end_writes_release_note(tmp_path):
    report = run(tmp_path, create_data=True, count=800)
    assert report['audit']['row_reconciliation_passed']
    assert (tmp_path/'outputs'/'validation_notes.md').exists()
    assert (tmp_path/'outputs'/'qa_exceptions.csv').exists()
    assert (tmp_path/'outputs'/'forecast_backtest.csv').exists()


def test_insufficient_dataset_rejected(tmp_path):
    with pytest.raises(ValueError):
        generate(tmp_path, count=20)
