from pathlib import Path
import pandas as pd
import pytest
from src.sata_demo.generate import make_synthetic
from src.sata_demo.pipeline import load_inputs, validate, run_pipeline


def test_fixtures_are_fictional_and_multisite(tmp_path: Path):
    frames = make_synthetic(tmp_path)
    assert frames['registry']['site_id'].nunique() == 16
    assert len(frames['registry']) == 320
    assert frames['registry']['case_id'].str.startswith('CASE').all()
    assert 'patient_name' not in frames['registry']


def test_audit_catches_expected_bad_cases(tmp_path: Path):
    frames = make_synthetic(tmp_path)
    clean, audit, report = validate(frames)
    codes = set(audit['rule'])
    assert {'MISSING_DATETIME', 'EBL_PLAUSIBILITY', 'AGE_PLAUSIBILITY',
            'SITE_ID_MISMATCH', 'DUPLICATE_CASE', 'OUT_OF_CODEBOOK',
            'SOURCE_RECORD_MISSING', 'TIME_ORDER'} <= codes
    assert not set(clean['case_id']) & set(audit['case_id'])
    assert report['counts']['count_reconciled'] is True


def test_output_files_and_validation_note(tmp_path: Path):
    source, out = tmp_path / 'raw', tmp_path / 'out'
    make_synthetic(source)
    report = run_pipeline(source, out)
    assert report['status'] == 'completed_with_issues'
    assert len(pd.read_csv(out / 'analysis_ready.csv')) == report['counts']['analysis_ready_rows']
    assert 'clinical_disclaimer' in (out / 'validation_report.json').read_text()
    assert (out / 'site_audit.csv').exists()
    assert (out / 'site_summary.csv').exists()


def test_reject_unexpected_missing_column(tmp_path: Path):
    make_synthetic(tmp_path)
    path = tmp_path / 'redcap.csv'
    df = pd.read_csv(path).drop(columns=['asa_class'])
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match='missing columns'):
        load_inputs(tmp_path)


def test_valid_no_exclusion_after_cleaning(tmp_path: Path):
    frames = make_synthetic(tmp_path)
    # Start from a small, fully clean subset to demonstrate success state.
    keep = {'CASE0001', 'CASE0002', 'CASE0003'}
    reduced = {name: df[df['case_id'].isin(keep)].copy()
               for name, df in frames.items()}
    clean, audit, report = validate(reduced)
    assert len(clean) == 3
    assert len(audit) == 0
    assert report['status'] == 'passed'
