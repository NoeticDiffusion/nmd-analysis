"""Verify September audit hashes and document links without scoring neural effects."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

BASE = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = json.loads((BASE / 'coverage_september/ds004100_h5_manifest_september.json').read_text(encoding='utf-8'))
    support = json.loads((BASE / 'validation/endpoint_support_checks.json').read_text(encoding='utf-8'))
    source = json.loads((BASE / 'source_metadata/source_metadata_audit.json').read_text(encoding='utf-8'))
    root = Path(manifest['summary']['root'])
    mismatches = []
    for row in manifest['rows']:
        expected = row['sha256']
        if not re.fullmatch('[0-9a-f]{64}', expected) or digest(root / row['relative_path']) != expected:
            mismatches.append(row['relative_path'])
    for relative, record in manifest['summary']['root_sidecars'].items():
        if digest(root / relative) != record['sha256']:
            mismatches.append(relative)
    source_root = Path(source['summary']['source'])
    for relative, expected in source['source_sidecar_sha256'].items():
        if digest(source_root / relative) != expected:
            mismatches.append('SOURCE:' + relative)
    script_checks = {
        'coverage': digest(BASE / 'coverage_september/audit_ds004100_september_coverage.py') == manifest['summary']['script_sha256'],
        'source': digest(BASE / 'source_metadata/audit_source_metadata.py') == source['summary']['script_sha256'],
        'support': digest(BASE / 'validation/check_endpoint_support.py') == support['summary']['script_sha256'],
    }
    by_file = {row['relative_path'].replace('\\', '/'): row for row in manifest['rows']}
    support_mismatches = []
    for row in support['rows']:
        counterpart = by_file[row['file'].replace('\\', '/')]
        for endpoint in ('H1', 'H2'):
            if row[endpoint + '_valid_centers'] != counterpart[endpoint + '_native_supported_count']:
                support_mismatches.append([row['file'], endpoint])
    files = [BASE / 'README.md', BASE / 'preregistration/preregistration_ds004100_ndt_v1_1_20260922.md',
             BASE / 'peer_review/review_02_september.md', BASE / 'peer_review/september_revision_record.md']
    for directory in ('coverage_september', 'source_metadata', 'validation'):
        files.extend(p for p in (BASE / directory).rglob('*') if p.is_file() and p.suffix in {'.md', '.py', '.json', '.csv'})
    missing_links, encoding_errors = [], []
    for path in files:
        if path.suffix != '.md':
            continue
        content = path.read_text(encoding='utf-8')
        if '\ufffd' in content:
            encoding_errors.append(str(path.relative_to(BASE)))
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
            target = target.strip('<>').split('#')[0]
            if not target or re.match(r'^[A-Za-z]+://', target):
                continue
            if not (path.parent / target).exists():
                missing_links.append([str(path.relative_to(BASE)), target])
    result = {
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'data_root': str(root),
        'n_inputs': len(manifest['rows']),
        'input_manifest_hash_agreement': not mismatches,
        'hash_mismatches': mismatches,
        'source_sidecars_rehashed': len(source['source_sidecar_sha256']),
        'audit_read_errors': manifest['summary']['files_with_errors'],
        'script_hash_agreement': script_checks,
        'independent_primary_support_count_mismatches': support_mismatches,
        'structural_paired_subjects': support['summary']['structural_paired_subjects'],
        'missing_markdown_targets': missing_links,
        'encoding_errors': encoding_errors,
        'artifact_sha256': {str(path.relative_to(BASE)): digest(path) for path in sorted(set(files))},
        'primary_empirical_analysis': 'not_run',
        'full_inferential_extractor_qualification': 'not_run',
        'null_calibration': 'not_run',
        'registration': 'not_submitted',
        'review': 'Independent review 02 plus documented coordinator revisions; no second final approval claimed',
    }
    (BASE / 'artifact_checks.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'artifact_sha256'}, indent=2))
    assert len(manifest['rows']) == 319
    assert not (mismatches or support_mismatches or missing_links or encoding_errors or manifest['summary']['files_with_errors'])
    assert all(script_checks.values())


if __name__ == '__main__':
    main()
