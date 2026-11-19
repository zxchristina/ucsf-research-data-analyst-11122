"""Deterministically generate fake multi-site research exports: NO PHI."""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

SITES = [f'SITE{i:02}' for i in range(1, 17)]


def make_synthetic(output: Path, n_per_site: int = 20) -> dict[str, pd.DataFrame]:
    """Create linked fake registry, REDCap-style, and anesthesia CSV exports."""
    output.mkdir(parents=True, exist_ok=True)
    registry, redcap, anesthesia = [], [], []
    counter = 0
    base = datetime(2025, 1, 6, 7, 30)
    for site in SITES:
        for _ in range(n_per_site):
            counter += 1
            cid = f'CASE{counter:04}'
            start = base + timedelta(days=counter, hours=(counter % 4))
            duration = 115 + (counter % 25) * 9
            registry.append({
                'case_id': cid, 'site_id': site,
                'recipient_age': 21 + (counter % 65),
                'transplant_date': start.strftime('%Y-%m-%d'),
                'graft_status': 'functioning' if counter % 7 else 'unknown',
            })
            redcap.append({
                'case_id': cid, 'site_id': site,
                'anesthesia_start': start.isoformat(timespec='minutes'),
                'anesthesia_end': (start + timedelta(minutes=duration)).isoformat(timespec='minutes'),
                'asa_class': ['II', 'III', 'IV'][counter % 3],
            })
            anesthesia.append({
                'case_id': cid, 'site_id': site,
                'ebl_ml': 200 + (counter * 97) % 2600,
                'anesthesia_minutes': duration,
            })
    # Known synthetic errors ensure the audit can be demonstrated.
    redcap[4]['anesthesia_end'] = ''                 # Missing required value
    anesthesia[30]['ebl_ml'] = 18500                # Illustrative outlier
    registry[50]['recipient_age'] = 145             # Invalid age
    redcap[69]['site_id'] = 'SITE99'                 # Site-code mismatch
    redcap.append(dict(redcap[83]))                # Duplicate submission
    redcap[99]['asa_class'] = 'X'                    # Not in codebook
    anesthesia.pop(120)                            # Registry/anesthesia missingness
    redcap[130]['anesthesia_end'] = redcap[130]['anesthesia_start']  # Invalid duration
    dfs = {
        'registry': pd.DataFrame(registry),
        'redcap': pd.DataFrame(redcap),
        'anesthesia': pd.DataFrame(anesthesia),
    }
    for key, df in dfs.items():
        df.to_csv(output / f'{key}.csv', index=False)
    return dfs


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, default=Path('data/raw'))
    args = p.parse_args()
    dfs = make_synthetic(args.output)
    print('Generated entirely fictional CSVs: ' + ', '.join(f'{k}={len(v)}' for k, v in dfs.items()))


if __name__ == '__main__':
    main()
