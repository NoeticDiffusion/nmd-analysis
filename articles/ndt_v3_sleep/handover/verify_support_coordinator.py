"""Verify candidate artifact directly from HDF5; no analysis/producer imports."""
from pathlib import Path
import argparse
import hashlib
import json
import h5py
import numpy as np
import pandas as pd


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def verify(run):
    root = Path(__file__).resolve().parents[1]
    stage_run = root / 'results/stage_support_audit_20260907_r7'
    sm = json.loads((stage_run / 'audit_manifest.json').read_text())
    assert sha(sm['analysis_code']) == sm['analysis_code_sha256']
    assert sha(sm['raw_events']) == sm['raw_events_sha256']
    assert sha(sm['epoch_table']) == sm['epoch_table_sha256']
    for name, digest in sm['output_sha256'].items():
        assert sha(stage_run / name) == digest
    raw_events = pd.read_csv(sm['raw_events'], sep='\t')
    frame = pd.read_parquet(sm['epoch_table']).sort_values('window_id')
    np.testing.assert_array_equal(raw_events.stage_hum, frame.stage_code)
    np.testing.assert_array_equal(raw_events.onset, frame.window_start)
    np.testing.assert_array_equal(raw_events.duration, frame.window_end.to_numpy() - frame.window_start.to_numpy())
    np.testing.assert_array_equal((raw_events.begsample - 1) / 256, raw_events.onset)
    np.testing.assert_array_equal((raw_events.endsample - raw_events.begsample + 1) / 256, raw_events.duration)
    cuts = np.r_[0, np.flatnonzero(np.diff(raw_events.stage_hum) != 0) + 1, len(raw_events)]
    counts = []
    for code in range(5):
        lengths = [b - a for a, b in zip(cuts[:-1], cuts[1:]) if raw_events.stage_hum.iloc[a] == code]
        counts.append({'stage_code': code, 'bouts': len(lengths), 'epochs': int(sum(lengths)), 'two_sided': int(sum(max(0, n - 2) for n in lengths))})
    assert [r['two_sided'] for r in counts] == [249, 2, 581, 0, 103]
    assert len(cuts) - 1 == sm['n_bouts'] == 84
    m = json.loads((run / 'manifest.json').read_text())
    assert m['status'] == 'candidate_only_membership_exported'
    assert sha(m['input_h5']) == m['input_h5_sha256_before'] == m['input_h5_sha256_after']
    index = run / 'output_hashes.json'
    assert sha(index) == (run / 'output_hashes.sha256').read_text().split()[0]
    for name, digest in json.loads(index.read_text())['files'].items():
        assert sha(run / name) == digest, name
    with h5py.File(m['input_h5'], 'r') as f:
        x = f['coords_3d_subject_anchored/values'][:].astype(np.float64)
        t = f['time'][:]
        labels = f['labels/stage'][:]
        raw = f['row_source/raw_file'][:]
        tensor = f['dynamical_families/diffusion/v1/series/diffusion_tensor'][:]
        ids = f['epoch_id'][:]
    assert np.isfinite(x).all() and np.isfinite(t).all()
    sources = np.flatnonzero((np.diff(t) > 0) & (raw[:-1] == raw[1:]))
    dt = np.median(np.diff(t)[sources])
    neighbors = pd.read_csv(run / 'candidate_neighbors.csv')
    assert len(neighbors) == len(x) * 20
    all_same = []
    touched = []
    for q, rows in neighbors.groupby('query_index', sort=True):
        rows = rows.sort_values('selection_index')
        dist = np.sum((x[sources] - x[q]) ** 2, axis=1)
        picked = np.argpartition(dist, 19)[:20]
        src = sources[picked]
        np.testing.assert_array_equal(rows.source_index, src)
        np.testing.assert_array_equal(rows.target_index, src + 1)
        np.testing.assert_array_equal(rows.source_epoch_id, ids[src])
        np.testing.assert_array_equal(rows.target_epoch_id, ids[src + 1])
        np.testing.assert_array_equal(rows.source_stage_code, labels[src])
        np.testing.assert_array_equal(rows.target_stage_code, labels[src + 1])
        np.testing.assert_allclose(rows.distance_squared, dist[picked], rtol=1e-14, atol=1e-15)
        inc = x[src + 1] - x[src]
        covariance = np.cov(inc, rowvar=False, ddof=1) / dt
        values, vectors = np.linalg.eigh((covariance + covariance.T) * 0.5)
        projected = (vectors * np.maximum(values, 1e-8)) @ vectors.T
        np.testing.assert_array_equal(projected.astype(tensor.dtype), tensor[q])
        if labels[q] in range(5):
            all_same.append(bool(((labels[src] == labels[q]) & (labels[src + 1] == labels[q])).all()))
            touched.append(bool(((labels[src] == 8) | (labels[src + 1] == 8)).any()))
    result = {
        'status': 'PASS', 'run': str(run), 'manifest_sha256': sha(run / 'manifest.json'),
        'stage_run': str(stage_run), 'stage_counts_independent': counts,
        'independent_method': 'direct full distance/argpartition and numpy covariance/eigendecomposition; no producer imports',
        'verified_queries': len(x), 'verified_neighbor_rows': len(neighbors),
        'known_queries': len(all_same), 'known_queries_all_twenty_same_stage_endpoints': sum(all_same),
        'known_queries_with_disconnection_endpoint': sum(touched),
        'all_query_neighbor_rows_with_disconnection_endpoint': int(((neighbors.source_stage_code == 8) | (neighbors.target_stage_code == 8)).sum()),
        'historical_membership': 'not_claimed', 'full_support': 'not_assessed',
    }
    assert sha(m['input_h5']) == m['input_h5_sha256_before']
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.run.resolve())
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
