"""Demonstrate data QA for three linked, entirely synthetic research extracts."""
from __future__ import annotations
import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import pandas as pd

REQUIRED: dict[str, set[str]] = {
    'registry': {'case_id', 'site_id', 'recipient_age', 'transplant_date', 'graft_status'},
    'redcap': {'case_id', 'site_id', 'anesthesia_start', 'anesthesia_end', 'asa_class'},
    'anesthesia': {'case_id', 'site_id', 'ebl_ml', 'anesthesia_minutes'},
}
ALLOWED_ASA = {'I', 'II', 'III', 'IV', 'V'}
ALLOWED_GRAFT_STATUS = {'functioning', 'unknown'}
VALID_SITES = {f'SITE{i:02}' for i in range(1, 17)}


@dataclass(frozen=True)
class AuditFinding:
    site_id: str
    case_id: str
    source: str
    rule: str
    description: str


def load_inputs(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Do not silently accept missing source columns or missing files."""
    frames: dict[str, pd.DataFrame] = {}
    for name, required in REQUIRED.items():
        file = input_dir / f'{name}.csv'
        frame = pd.read_csv(file, dtype=str, keep_default_na=False)
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f'{name}: missing columns {sorted(missing)}')
        frames[name] = frame
    return frames


def _numeric(value: str) -> float | None:
    result = pd.to_numeric(value, errors='coerce')
    return None if pd.isna(result) else float(result)


def _timestamp(value: str):
    return pd.to_datetime(value, errors='coerce')


def validate(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Run illustrative rules and exclude every case with a blocking finding."""
    findings: list[AuditFinding] = []
    seen: set[tuple[str, str, str]] = set()
    registry = frames['registry']
    indexed: dict[str, pd.DataFrame] = {}

    def flag(site_id: str, case_id: str, source: str, rule: str, desc: str) -> None:
        key = (case_id, source, rule)
        if key not in seen:
            seen.add(key)
            findings.append(AuditFinding(site_id, case_id, source, rule, desc))

    for name, frame in frames.items():
        for _, row in frame.iterrows():
            if not row['case_id'] or not row['site_id']:
                flag(row['site_id'] or 'UNKNOWN', row['case_id'] or 'MISSING', name,
                     'REQUIRED_KEY', 'Missing case_id or site_id')
        duplicated = frame[frame.duplicated('case_id', keep=False)]
        for cid, group in duplicated.groupby('case_id'):
            flag(group.iloc[0]['site_id'], cid, name,
                 'DUPLICATE_CASE', f'Case key appears {len(group)} times in {name}')
        indexed[name] = frame.drop_duplicates('case_id').set_index('case_id', drop=False)

    registry_ids = set(indexed['registry'].index)
    for name in ('redcap', 'anesthesia'):
        ids = set(indexed[name].index)
        for cid in sorted(registry_ids - ids):
            row = indexed['registry'].loc[cid]
            flag(row['site_id'], cid, name, 'SOURCE_RECORD_MISSING',
                 'Registry case is absent from this source extract')
        for cid in sorted(ids - registry_ids):
            row = indexed[name].loc[cid]
            flag(row['site_id'], cid, name, 'UNMATCHED_CASE',
                 'Submitted case has no registry match')

    for cid, reg in indexed['registry'].iterrows():
        site = reg['site_id']
        if site not in VALID_SITES:
            flag(site, cid, 'registry', 'UNRECOGNIZED_SITE', 'Site not in demo site codebook')
        age = _numeric(reg['recipient_age'])
        if age is None or not (18 <= age <= 100):
            flag(site, cid, 'registry', 'AGE_PLAUSIBILITY',
                 'Missing, non-numeric, or outside illustrative 18–100 age range')
        if pd.isna(_timestamp(reg['transplant_date'])):
            flag(site, cid, 'registry', 'INVALID_DATE', 'Missing or invalid transplant date')
        if reg['graft_status'] not in ALLOWED_GRAFT_STATUS:
            flag(site, cid, 'registry', 'OUT_OF_CODEBOOK', 'Unknown graft status code')

        for name in ('redcap', 'anesthesia'):
            if cid not in indexed[name].index:
                continue
            other = indexed[name].loc[cid]
            if other['site_id'] != site:
                flag(site, cid, name, 'SITE_ID_MISMATCH',
                     f"Source site={other['site_id']}; registry site={site}")

        if cid in indexed['redcap'].index:
            row = indexed['redcap'].loc[cid]
            start = _timestamp(row['anesthesia_start'])
            stop = _timestamp(row['anesthesia_end'])
            if pd.isna(start) or pd.isna(stop):
                flag(site, cid, 'redcap', 'MISSING_DATETIME',
                     'Anesthesia start or stop is missing/unparseable')
            elif stop <= start:
                flag(site, cid, 'redcap', 'TIME_ORDER',
                     'Anesthesia stop must occur after start')
            if row['asa_class'] not in ALLOWED_ASA:
                flag(site, cid, 'redcap', 'OUT_OF_CODEBOOK',
                     f"Unrecognized ASA class {row['asa_class']!r}")

        if cid in indexed['anesthesia'].index:
            row = indexed['anesthesia'].loc[cid]
            loss = _numeric(row['ebl_ml'])
            duration = _numeric(row['anesthesia_minutes'])
            if loss is None or not 0 <= loss <= 15000:
                flag(site, cid, 'anesthesia', 'EBL_PLAUSIBILITY',
                     'Missing/non-numeric/outside illustrative 0–15000 range')
            if duration is None or not 1 <= duration <= 1440:
                flag(site, cid, 'anesthesia', 'DURATION_PLAUSIBILITY',
                     'Missing/non-numeric/outside illustrative 1–1440 minute range')

    audit = pd.DataFrame([asdict(x) for x in findings],
                         columns=['site_id', 'case_id', 'source', 'rule', 'description'])
    excluded = set(audit['case_id'])
    clean_ids = sorted(registry_ids - excluded)
    # Explicit one-to-one joins provide traceable row reconciliation.
    cohort = (frames['registry'][frames['registry']['case_id'].isin(clean_ids)]
              .merge(frames['redcap'][frames['redcap']['case_id'].isin(clean_ids)], on='case_id', how='inner',
                     suffixes=('_registry', '_redcap'), validate='one_to_one')
              .merge(frames['anesthesia'][frames['anesthesia']['case_id'].isin(clean_ids)], on='case_id', how='inner',
                     validate='one_to_one', suffixes=('', '_anesthesia')))
    if len(cohort) != len(clean_ids):
        raise AssertionError('Cohort row-count reconciliation failed')
    if (cohort['site_id_registry'] != cohort['site_id_redcap']).any() or \
       (cohort['site_id_registry'] != cohort['site_id']).any():
        raise AssertionError('Site reconciliation failed')
    cohort = cohort.drop(columns=['site_id_redcap']).rename(
        columns={'site_id_registry': 'site_id', 'site_id': 'anesthesia_site_id'})
    cohort = cohort.drop(columns=['anesthesia_site_id'])
    cohort['recipient_age'] = pd.to_numeric(cohort['recipient_age']).astype('int64')
    cohort['ebl_ml'] = pd.to_numeric(cohort['ebl_ml']).astype('int64')
    cohort['anesthesia_minutes'] = pd.to_numeric(cohort['anesthesia_minutes']).astype('int64')

    total = len(registry_ids)
    counts = {
        'registry_unique_cases': total,
        'redcap_rows': len(frames['redcap']),
        'anesthesia_rows': len(frames['anesthesia']),
        'cases_excluded': len(registry_ids - set(clean_ids)),
        'analysis_ready_rows': len(cohort),
        'audit_findings': len(audit),
        'count_reconciled': len(cohort) + len(registry_ids - set(clean_ids)) == total,
    }
    by_rule = audit['rule'].value_counts().sort_index().to_dict()
    report = {
        'dataset': '100% SYNTHETIC, NOT CLINICAL DATA',
        'status': 'completed_with_issues' if findings else 'passed',
        'counts': counts,
        'rule_counts': by_rule,
        'validation_checks': [
            'source file/required column presence',
            'case ID duplicates/missing keys',
            'case joins and 1:1 cardinality',
            'registry/site ID agreement',
            'required timestamps and ordering',
            'demo codebook allowed values',
            'illustrative numeric ranges',
            'final eligible rows + excluded rows = unique registry cases',
        ],
        'clinical_disclaimer': 'Illustrative rules only; never use for actual clinical data or decisions.',
    }
    return cohort.sort_values('case_id'), audit.sort_values(['site_id', 'case_id', 'rule']), report


def build_site_summary(frames: dict[str, pd.DataFrame], clean: pd.DataFrame,
                       audit: pd.DataFrame) -> pd.DataFrame:
    registry = frames['registry']
    counts = registry.groupby('site_id')['case_id'].nunique()
    approved = clean.groupby('site_id')['case_id'].nunique()
    flagged_cases = audit.groupby('site_id')['case_id'].nunique()
    return pd.DataFrame({
        'submitted_registry_cases': counts,
        'clean_cases': approved.reindex(counts.index, fill_value=0),
        'cases_with_audit_findings': flagged_cases.reindex(counts.index, fill_value=0),
    }).reset_index().sort_values('site_id')


def run_pipeline(input_dir: Path, output_dir: Path) -> dict:
    frames = load_inputs(input_dir)
    cohort, audit, report = validate(frames)
    output_dir.mkdir(parents=True, exist_ok=True)
    cohort.to_csv(output_dir / 'analysis_ready.csv', index=False)
    audit.to_csv(output_dir / 'site_audit.csv', index=False)
    build_site_summary(frames, cohort, audit).to_csv(output_dir / 'site_summary.csv', index=False)
    (output_dir / 'validation_report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path('data/raw'))
    parser.add_argument('--output', type=Path, default=Path('outputs'))
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.input, args.output), indent=2))


if __name__ == '__main__':
    main()
