"""Read-only ds004100 coverage audit. Never compute condition endpoint effects."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

GROUPS = [
    'mnps_3d', 'coords_3d_cohort_anchored', 'coords_9d/values',
    'jacobian/J_hat', 'jacobian_9D/J_hat',
    'jacobian/derived_metrics/v1', 'jacobian_9D/derived_metrics/v1',
    'finite_time_response/v1/primary', 'finite_time_response/v1/stratified_9d',
    'transition_residuals/v1/primary', 'transition_residual_covariance_proxy/v1/primary',
    'stochastic_reachability', 'dynamical_families', 'events', 'labels',
    'support_signature', 'extensions/signal_support', 'features_raw',
]
ATTRS = ['subject_id', 'task', 'session', 'run', 'acq', 'primary_coordinate_layer',
         'anchor_hash', 'anchor_id', 'mndm_version', 'schema_version', 'window_sec',
         'fs_out', 'geometry_contract_status', 'normalize_mode', 'e_e_backend',
         'e_e_construct', 'e_e_degraded_mode', 'time_reference_status']
FEATURES = ['eeg_delta', 'eeg_theta', 'eeg_alpha', 'eeg_beta', 'eeg_gamma',
            'eeg_sample_entropy', 'eeg_hjorth_complexity']


def plain(v):
    if isinstance(v, bytes):
        return v.decode('utf-8')
    if isinstance(v, np.ndarray):
        return [plain(x) for x in v.tolist()]
    if isinstance(v, np.generic):
        return plain(v.item())
    return v


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def inspect(p, root):
    row = {'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size,
           'sha256': digest(p)}
    with h5py.File(p, 'r') as f:
        row['attrs'] = {k: plain(f.attrs.get(k, 'not_recorded')) for k in ATTRS}
        row['presence'] = {k: k in f for k in GROUPS}
        t = np.asarray(f['time'][:], dtype=float)
        dt = np.diff(t)
        row['time'] = {'rows': len(t), 'nonfinite': int((~np.isfinite(t)).sum()),
                       'nonpositive_steps': int((dt <= 0).sum()),
                       'non4sec_steps': int((np.abs(dt - 4) > 1e-6).sum()),
                       'nominal_window_seconds': plain(f.attrs.get('window_sec', None))}
        row['arrays'] = {}
        for key in ['mnps_3d', 'coords_3d_cohort_anchored', 'coords_9d/values',
                    'jacobian/J_hat', 'jacobian_9D/J_hat']:
            if key in f:
                node = f[key]
                if isinstance(node, h5py.Group):
                    node = node['values']
                a = np.asarray(node[:])
                row['arrays'][key] = {'shape': list(a.shape),
                    'finite_rows': int(np.isfinite(a).reshape(len(a), -1).all(axis=1).sum()) if len(a) else 0}
        row['certificates'] = {}
        for key in GROUPS:
            if key in f and isinstance(f[key], h5py.Group) and '/v1' in key:
                g = f[key]
                row['certificates'][key] = {
                    name: plain(g[name][()]) if name in g and g[name].shape == () else 'not_recorded'
                    for name in ['computation_status', 'measurement_validity', 'claim_status', 'validation_level']}
        row['required_features'] = {}
        if 'features_raw/names' in f and 'features_raw/values' in f:
            names = [str(plain(x)) for x in f['features_raw/names'][:]]
            a = f['features_raw/values'][:]
            for name in FEATURES:
                if name in names:
                    v = a[:, names.index(name)]
                    row['required_features'][name] = {'present': True,
                        'rows': len(v), 'finite': int(np.isfinite(v).sum())}
                else:
                    row['required_features'][name] = {'present': False}
        row['ftr_h2'] = {}
        prefix = 'finite_time_response/v1/primary/horizons/h2/series/'
        for name in ['actual_horizon_sec', 'g_max', 'd_resp']:
            key = prefix + name
            if key in f:
                v = f[key][:]
                info = {'shape': list(v.shape), 'finite': int(np.isfinite(v).sum())}
                if name == 'actual_horizon_sec':
                    info['not_8_sec'] = int((np.isfinite(v) & (np.abs(v - 8) > 1e-6)).sum())
                row['ftr_h2'][name] = info
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_ds004100_20260812_054004'))
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    if root == out or root in out.parents:
        raise ValueError('Audit outputs must be outside the source-data root')
    out.mkdir(parents=True, exist_ok=True)
    paths = sorted(root.rglob('*.h5'))
    if not paths:
        raise ValueError('No H5 files found')
    rows, errors = [], []
    for p in paths:
        try:
            rows.append(inspect(p, root))
        except Exception as exc:
            errors.append({'path': str(p), 'error': repr(exc)})
    if not rows:
        (out / 'coverage_errors.json').write_text(json.dumps(errors, indent=2), encoding='utf-8')
        raise RuntimeError('No H5 files successfully inspected; see coverage_errors.json')
    people = defaultdict(Counter)
    for r in rows:
        people[str(r['attrs']['subject_id'])][str(r['attrs']['task'])] += 1
    summary = {
        'audit_scope': 'All files: SHA256, selected schema/attrs, all time/coordinate/Jacobian finite rows, selected status fields and required-feature finite counts. No endpoint means, condition effects or models.',
        'root': str(root), 'created_utc': datetime.now(timezone.utc).isoformat(),
        'runtime': {'python': platform.python_version(), 'h5py': h5py.__version__, 'numpy': np.__version__},
        'script_sha256': digest(Path(__file__)),
        'files_found': len(paths), 'files_read': len(rows), 'errors': errors,
        'bytes': sum(r['bytes'] for r in rows), 'subjects': len(people),
        'paired_subjects': sum(c['ictal'] > 0 and c['interictal'] > 0 for c in people.values()),
        'two_files_each': sum(c['ictal'] >= 2 and c['interictal'] >= 2 for c in people.values()),
        'subject_file_counts': dict(people),
        'attribute_counts': {k: dict(Counter(str(r['attrs'][k]) for r in rows)) for k in ATTRS if k not in ['run', 'subject_id']},
        'presence_counts': {k: sum(r['presence'][k] for r in rows) for k in GROUPS},
        'total_time_rows': sum(r['time']['rows'] for r in rows),
        'time_rows_range': [min(r['time']['rows'] for r in rows), max(r['time']['rows'] for r in rows)],
        'irregular_time_files': [r['path'] for r in rows if r['time']['non4sec_steps'] or r['time']['nonpositive_steps'] or r['time']['nonfinite']],
        'certificate_counts': {key: {name: dict(Counter(str(r['certificates'][key][name]) for r in rows if key in r['certificates'])) for name in ['computation_status','measurement_validity','claim_status','validation_level']} for key in GROUPS if '/v1' in key},
        'root_sidecar_hashes': {p.name: digest(p) for p in sorted(root.iterdir()) if p.is_file() and p.suffix in ['.json', '.yaml', '.txt']},
        'limitations': ['No source-event or raw-filter verification', 'No channel-contact identity audit', 'No scientific qualification inferred', 'No seizure-interior durations inferred', 'No historical or new condition endpoints summarized'],
    }
    (out / 'coverage_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (out / 'coverage_details.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    with (out / 'h5_manifest.csv').open('w', newline='', encoding='utf-8') as stream:
        fields = ['path','bytes','sha256','subject_id','task','session','run','acq','n_time']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({**{k:r[k] for k in ['path','bytes','sha256']},
                **{k:r['attrs'][k] for k in ['subject_id','task','session','run','acq']}, 'n_time':r['time']['rows']})
    print(json.dumps({k: summary[k] for k in ['files_found','files_read','subjects','paired_subjects','two_files_each','total_time_rows','errors']}))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
