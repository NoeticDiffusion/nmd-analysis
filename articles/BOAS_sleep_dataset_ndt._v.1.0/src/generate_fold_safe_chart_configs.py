"""Generate explicit fold-specific train/apply configs for the BOAS chart gate.

The measurement overlay, chart definition and support ledger are shared. Only
the frozen fold manifest, role, anchor-fit behavior, and role-specific anchor
reference differ. Existing config files are never overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ARTICLE_ROOT = Path(__file__).resolve().parents[1]
CHART_ROOT = ARTICLE_ROOT / "results" / "fold_safe_chart_qualification_20260930_v1"
CONFIG_DIR = CHART_ROOT / "configs"
V4_ROOT = ARTICLE_ROOT / "results" / "continuous_full_surface_support_audit_20260929_v4"
OVERLAY = Path(r"H:\SourceRepo2\NeuralManifoldDynamics\mndm\config\sources\openneuro\config_ingest_ds005555_continuous_c123_fold_safe_chart_qualification.yaml")
PROCESSED_ROOT = CHART_ROOT / "processed"
SIGNAL_LEDGER = V4_ROOT / "signal_support_ledger.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def yaml_quote(value: str) -> str:
    return json.dumps(value.replace("\\", "/"), ensure_ascii=False)


def render(fold: int, role: str, anchor_id: str) -> str:
    manifest = V4_ROOT / "fold_manifests" / f"fold_{fold}.json"
    common = (
        "version: 1.2\n"
        "imports:\n"
        f"  - {yaml_quote(str(OVERLAY))}\n\n"
        "paths:\n"
        f"  received_dir: {yaml_quote('K:/ExternalReceivedDatasets/openneuro/received')}\n"
        f"  processed_dir: {yaml_quote(str(PROCESSED_ROOT))}\n"
        "  dataset_received_dirs:\n"
        f"    ds005555: {yaml_quote('K:/ExternalReceivedDatasets/openneuro/received/ds005555')}\n\n"
        "mnps_projection:\n"
        "  fold_safe:\n"
        "    enabled: true\n"
        f"    manifest: {yaml_quote(str(manifest))}\n"
        f"    role: {role}\n"
        f"    signal_support_ledger: {yaml_quote(str(SIGNAL_LEDGER))}\n"
        "  anchor_auto_fit:\n"
        f"    enabled: {'true' if role == 'training' else 'false'}\n"
        "    scale_method: iqr\n"
        "    min_subjects: 20\n"
        f"    anchor_id: {anchor_id}\n"
        "  anchor:\n"
    )
    if role == "training":
        common += "    enabled: false\n    scale_method: iqr\n    min_subjects: 20\n"
    else:
        anchor_path = (
            PROCESSED_ROOT
            / "ds005555"
            / f"fold_{fold}_training_label_free_v1"
            / "anchors"
            / f"{anchor_id}.json"
        )
        common += (
            "    enabled: true\n"
            f"    path: {yaml_quote(str(anchor_path))}\n"
            "    scale_method: iqr\n"
            "    min_subjects: 20\n"
        )
    return common


def generate(folds: list[int]) -> list[dict[str, str | int]]:
    if not OVERLAY.is_file():
        raise FileNotFoundError(f"Generic MNDM chart overlay missing: {OVERLAY}")
    if not SIGNAL_LEDGER.is_file():
        raise FileNotFoundError(f"Frozen signal support ledger missing: {SIGNAL_LEDGER}")

    requests: list[tuple[int, str, str, Path, Path]] = []
    for fold in folds:
        manifest_path = V4_ROOT / "fold_manifests" / f"fold_{fold}.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Fold manifest missing: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != "mndm.fold_split.v1":
            raise ValueError(f"Unexpected fold manifest schema: {manifest_path}")
        if manifest.get("split_id") != f"ds005555-continuous-c123-ppg-fold-{fold}-20260929-v1":
            raise ValueError(f"Unexpected frozen split identity: {manifest_path}")
        if set(manifest.get("training_pids", [])) & set(manifest.get("apply_pids", [])):
            raise ValueError(f"Training/apply participant sets overlap: {manifest_path}")

        anchor_id = f"ds005555_continuous_c123_fold_{fold}_chart_label_free_v1"
        for role, run_role in (("training", "training"), ("apply", "apply")):
            config_name = f"fold_{fold}_{run_role}_label_free_v1.yaml"
            config_path = CONFIG_DIR / config_name
            requests.append((fold, role, anchor_id, config_path, manifest_path))

    collisions = [str(config_path) for _, _, _, config_path, _ in requests if config_path.exists()]
    if collisions:
        raise FileExistsError("Refusing to overwrite existing configs: " + ", ".join(collisions))

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, str | int]] = []
    for fold, role, anchor_id, config_path, manifest_path in requests:
        content = render(fold, role, anchor_id)
        config_path.write_text(content, encoding="utf-8", newline="\n")
        results.append(
            {
                "fold": fold,
                "role": role,
                "config": str(config_path),
                "config_sha256": sha256_file(config_path),
                "manifest_sha256": sha256_file(manifest_path),
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folds", nargs="+", type=int, default=[1, 2, 3, 4])
    args = parser.parse_args()
    if len(set(args.folds)) != len(args.folds) or any(fold not in range(1, 5) for fold in args.folds):
        parser.error("This extension accepts unique remaining fold IDs from 1 to 4; fold 0 is preserved.")
    for row in generate(args.folds):
        print(json.dumps(row, sort_keys=True))


if __name__ == "__main__":
    main()
