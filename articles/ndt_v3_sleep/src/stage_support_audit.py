"""Bounded audit of recorded sleep-stage runs and raw annotation alignment."""
from __future__ import annotations

import argparse
import hashlib
import json
import importlib.metadata
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yaml

KNOWN = {0: "Wake", 1: "N1", 2: "N2", 3: "N3", 4: "REM"}


def _pkg(name: str) -> bool:
    try:
        importlib.metadata.version(name); return True
    except importlib.metadata.PackageNotFoundError:
        return False


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _same_supported(a: pd.Series, b: pd.Series) -> bool:
    return (int(b.window_id) == int(a.window_id) + 1 and
            abs(float(b.window_start) - float(a.window_end)) <= 1e-9 and
            a.stage_label_status == "recorded" and b.stage_label_status == "recorded" and
            a.stage_label == b.stage_label)


def audit_bouts(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    start = 0
    for i in range(1, len(frame) + 1):
        split = i == len(frame)
        if not split:
            prev, cur = frame.iloc[i - 1], frame.iloc[i]
            split = not (int(cur.window_id) == int(prev.window_id) + 1 and
                         abs(float(cur.window_start) - float(prev.window_end)) <= 1e-9 and
                         int(cur.stage_code) == int(prev.stage_code) and
                         cur.stage_label_status == prev.stage_label_status)
        if split:
            part = frame.iloc[start:i]
            first, last = part.iloc[0], part.iloc[-1]
            code = int(first.stage_code)
            known = first.stage_label_status == "recorded" and code in KNOWN
            retained = 0
            for k in range(start, i):
                if k > 0 and k + 1 < len(frame) and _same_supported(frame.iloc[k - 1], frame.iloc[k]) and _same_supported(frame.iloc[k], frame.iloc[k + 1]):
                    retained += 1
            rows.append({"bout_id": len(rows), "start_window_id": int(first.window_id), "end_window_id": int(last.window_id),
                         "stage_code": code, "stage_label": first.stage_label if first.stage_label_status == "recorded" else None,
                         "stage_label_status": first.stage_label_status, "bout_kind": "known" if known else "unknown_or_unresolved", "n_windows": len(part),
                         "start_sec": float(first.window_start), "end_sec": float(last.window_end),
                         "duration_sec": float(part.window_end.iloc[-1] - part.window_start.iloc[0]),
                         "two_sided_retained_windows": retained,
                         "split_reason_after": "end" if i == len(frame) else "id_bound_or_label_change"})
            start = i
    bouts = pd.DataFrame(rows)
    summaries = []
    for code, label in KNOWN.items():
        part = bouts.loc[(bouts.stage_code == code) & (bouts.stage_label_status == "recorded")]
        lengths = part.n_windows.to_numpy(dtype=int)
        summaries.append({"stage_code": code, "stage_label": label, "n_bouts": len(part),
                          "n_windows": int(lengths.sum()) if len(lengths) else 0,
                          "total_duration_sec": float(part.duration_sec.sum()) if len(part) else 0.0,
                          "two_sided_retained_windows": int(part.two_sided_retained_windows.sum()) if len(part) else 0,
                          "min_bout_windows": int(lengths.min()) if len(lengths) else np.nan,
                          "max_bout_windows": int(lengths.max()) if len(lengths) else np.nan,
                          "bout_lengths_windows": ",".join(map(str, lengths.tolist()))})
    return bouts, pd.DataFrame(summaries)


def raw_alignment(frame: pd.DataFrame, raw: pd.DataFrame, sampling_frequency: float | None) -> pd.DataFrame:
    if len(frame) != len(raw):
        raise ValueError("epoch/raw annotation row count mismatch")
    rows = []
    for i in range(len(frame)):
        epoch, event = frame.iloc[i], raw.iloc[i]
        numeric = [event[c] for c in ("onset", "duration", "begsample", "endsample", "offset", "stage_hum")]
        if not all(np.isfinite(float(x)) for x in numeric) or any(float(x) != int(float(x)) for x in (event.stage_hum, event.begsample, event.endsample, event.offset)):
            raise ValueError("raw annotation contains nonfinite or noninteger required values")
        rows.append({"window_id": int(epoch.window_id), "epoch_stage_code": int(epoch.stage_code),
                     "raw_stage_hum": int(event.stage_hum), "raw_stage_ai": (int(event.stage_ai) if "stage_ai" in raw.columns else np.nan),
                     "stage_hum_match": int(epoch.stage_code) == int(event.stage_hum),
                     "onset_matches_window_start": abs(float(event.onset) - float(epoch.window_start)) <= 1e-6,
                     "duration_matches_bounds": abs(float(event.duration) - (float(epoch.window_end) - float(epoch.window_start))) <= 1e-6,
                     "begsample": int(event.begsample), "endsample": int(event.endsample), "offset": int(event.offset),
                     "sample_clock_ok": (sampling_frequency is not None and abs((float(event.endsample) - float(event.begsample) + 1.0) / sampling_frequency - float(event.duration)) <= 1e-6 and abs((float(event.begsample) - 1.0) / sampling_frequency - float(event.onset)) <= 1e-6 and int(event.offset) == 0)})
    return pd.DataFrame(rows)


def run(table: Path, raw_events: Path, output: Path, config: Path | None = None) -> dict:
    table, raw_events = table.resolve(), raw_events.resolve()
    config_hash = None; provenance_files = {}; epoch_manifest_ref = None; sampling_frequency = None; recording_duration = None; recording_duration_raw = None; duration_status = "not_assessed"; eeg_meta = None
    if config is not None:
        config = config.resolve(); cfg = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        if Path(str(cfg.get("epoch_table", ""))).resolve() != table or str(cfg.get("epoch_table_sha256", "")).lower() != sha256(table):
            raise ValueError("epoch table pin mismatch")
        if Path(str(cfg.get("raw_events", ""))).resolve() != raw_events or str(cfg.get("raw_events_sha256", "")).lower() != sha256(raw_events):
            raise ValueError("raw annotation pin mismatch")
        code = Path(__file__).resolve()
        if Path(str(cfg.get("analysis_code", ""))).resolve() != code or str(cfg.get("analysis_code_sha256", "")).lower() != sha256(code):
            raise ValueError("audit code pin mismatch")
        manifest = Path(str(cfg.get("epoch_manifest", ""))).resolve()
        epoch_manifest_ref = manifest
        if not manifest.is_file() or str(cfg.get("epoch_manifest_sha256", "")).lower() != sha256(manifest):
            raise ValueError("epoch manifest pin mismatch")
        if json.loads(manifest.read_text(encoding="utf-8")).get("output", {}).get("table_sha256") != sha256(table):
            raise ValueError("epoch manifest table hash mismatch")
        for name, spec in (cfg.get("provenance_files") or {}).items():
            path = Path(str(spec.get("path", ""))).resolve()
            if not path.is_file() or str(spec.get("sha256", "")).lower() != sha256(path):
                raise ValueError(f"provenance file pin mismatch: {name}")
            provenance_files[name] = {"path": str(path), "sha256": sha256(path)}
        if "eeg_json" in provenance_files:
            try:
                eeg_meta = json.loads(Path(provenance_files["eeg_json"]["path"]).read_text(encoding="utf-8"))
                sampling_frequency = float(eeg_meta.get("SamplingFrequency"))
                if not np.isfinite(sampling_frequency) or sampling_frequency <= 0: sampling_frequency = None
                raw_duration = float(eeg_meta.get("RecordingDuration")); recording_duration_raw = raw_duration
                if np.isfinite(raw_duration) and raw_duration >= 0:
                    recording_duration = raw_duration; duration_status = "recorded_valid"
                else:
                    duration_status = "invalid"
            except (TypeError, ValueError, json.JSONDecodeError):
                sampling_frequency = None; duration_status = "invalid"
        config_hash = sha256(config)
    input_before = {"epoch_table": sha256(table), "raw_events": sha256(raw_events), **{k: v["sha256"] for k, v in provenance_files.items()}}
    frame = pd.read_parquet(table).sort_values("window_id").reset_index(drop=True)
    raw = pd.read_csv(raw_events, sep="\t")
    required = {"window_id", "window_start", "window_end", "stage_code", "stage_label", "stage_label_status"}
    if not required.issubset(frame.columns): raise ValueError("epoch table missing required fields")
    if not {"onset", "duration", "begsample", "endsample", "offset", "stage_hum"}.issubset(raw.columns): raise ValueError("raw annotation columns missing")
    if len(frame) == 0: raise ValueError("empty epoch input")
    if frame.window_id.isna().any() or frame.window_id.duplicated().any() or not np.equal(frame.window_id.to_numpy(dtype=float), frame.window_id.to_numpy(dtype=int)).all(): raise ValueError("window IDs must be finite unique integers")
    if not np.isfinite(frame.stage_code.to_numpy(dtype=float)).all() or not np.equal(frame.stage_code.to_numpy(dtype=float), frame.stage_code.to_numpy(dtype=int)).all(): raise ValueError("stage codes must be finite integers")
    for code, label in KNOWN.items():
        part = frame.stage_code == code
        if (frame.loc[part, "stage_label_status"] != "recorded").any() or (frame.loc[part, "stage_label"] != label).any(): raise ValueError("known stage code/label/status mismatch")
    unknown = ~frame.stage_code.isin(list(KNOWN))
    if (frame.loc[unknown, "stage_label_status"] != "missing_or_unknown").any() or frame.loc[unknown, "stage_label"].notna().any(): raise ValueError("unresolved stage mapping is not explicit")
    if not np.isfinite(frame[["window_start", "window_end"]].to_numpy(dtype=float)).all() or (frame.window_end <= frame.window_start).any(): raise ValueError("window bounds must be finite with start < end")
    if len(frame) != len(raw): raise ValueError("epoch/raw annotation row count mismatch")
    output.mkdir(parents=True, exist_ok=False)
    bouts, summary = audit_bouts(frame); alignment = raw_alignment(frame, raw, sampling_frequency)
    input_after = {"epoch_table": sha256(table), "raw_events": sha256(raw_events), **{k: sha256(Path(v["path"])) for k, v in provenance_files.items()}}
    if input_after != input_before: raise ValueError("audited input changed during run")
    bouts.to_csv(output / "stage_bouts.csv", index=False); summary.to_csv(output / "stage_bout_summary.csv", index=False); alignment.to_csv(output / "raw_annotation_alignment.csv", index=False)
    source_semantics = {"code_8": "PSG_disconnection_retained_as_unknown", "stage_hum": "human_scored_stage_annotation", "stage_ai": "available_but_not_used"}
    observed_end = float(frame.window_end.max())
    if recording_duration is not None and recording_duration < observed_end:
        duration_status = "invalid_observed_end_exceeds_duration"; recording_duration = None
    tail = recording_duration - observed_end if recording_duration is not None and recording_duration >= observed_end else None
    duration_window_status = "within_recording_duration" if recording_duration is not None and observed_end <= recording_duration else ("mismatch" if recording_duration is not None else "not_assessed")
    alignment_ok = bool(alignment.stage_hum_match.all() and alignment.onset_matches_window_start.all() and alignment.duration_matches_bounds.all() and sampling_frequency is not None and alignment.sample_clock_ok.all() and duration_window_status == "within_recording_duration")
    output_hashes = {name: sha256(output / name) for name in ("stage_bouts.csv", "stage_bout_summary.csv", "raw_annotation_alignment.csv")}
    manifest = {"status": "descriptive_stage_support_audit" if alignment_ok else "mismatch", "claim_status": "no_biological_claim",
                "epoch_table": str(table), "epoch_table_sha256": sha256(table), "raw_events": str(raw_events), "raw_events_sha256": sha256(raw_events),
                "config": ({"path": str(config), "sha256": config_hash} if config is not None else None), "epoch_manifest": ({"path": str(epoch_manifest_ref), "sha256": sha256(epoch_manifest_ref)} if epoch_manifest_ref is not None else None), "provenance_files": provenance_files,
                "analysis_code": str(Path(__file__).resolve()), "analysis_code_sha256": sha256(Path(__file__).resolve()),
                "n_epochs": len(frame), "n_bouts": len(bouts), "raw_alignment_all_stage_hum": bool(alignment.stage_hum_match.all()),
                "raw_alignment_all_onset": bool(alignment.onset_matches_window_start.all()), "raw_alignment_all_duration": bool(alignment.duration_matches_bounds.all()),
                "raw_alignment_all_sample_clock": (bool(alignment.sample_clock_ok.all()) if sampling_frequency is not None else "not_assessed"),
                "known_stage_catalog": KNOWN, "unknown_stage_rows": int((frame.stage_label_status != "recorded").sum()),
                "code_8_handling": "retained_as_unknown_stage_code; no relabeling",
                "source_semantics": source_semantics, "recording_duration_raw_sec": recording_duration_raw, "recording_duration_sec": recording_duration, "recording_duration_status": duration_status, "observed_epoch_end_sec": observed_end, "recording_window_status": duration_window_status, "recording_tail_sec_not_in_epoch_table": tail,
                "sampling_frequency_hz": sampling_frequency, "alignment_checks": {"all_stage_hum": bool(alignment.stage_hum_match.all()), "all_onset": bool(alignment.onset_matches_window_start.all()), "all_duration": bool(alignment.duration_matches_bounds.all()), "all_sample_clock": (bool(alignment.sample_clock_ok.all()) if sampling_frequency is not None else "not_assessed")},
                "support_semantics": "recorded labels and immediate contiguous runs only; estimator/filter/neighborhood purity not assessed",
                "input_hashes_before": input_before, "input_hashes_after": input_after,
                "runtime": {"python": __import__("sys").version, "packages": {n: importlib.metadata.version(n) for n in ("numpy", "pandas", "pyarrow", "PyYAML") if _pkg(n)}},
                "outputs": ["stage_bouts.csv", "stage_bout_summary.csv", "raw_annotation_alignment.csv"], "output_sha256": output_hashes}
    (output / "audit_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output / "audit_manifest.sha256").write_text(sha256(output / "audit_manifest.json") + "  audit_manifest.json\n", encoding="utf-8")
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(); p.add_argument("--table", type=Path, required=True); p.add_argument("--raw-events", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--config", type=Path, required=True)
    a = p.parse_args(argv); run(a.table, a.raw_events, a.output, a.config); return 0


if __name__ == "__main__": raise SystemExit(main())
