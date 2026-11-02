#!/usr/bin/env python3
"""Outcome analysis for SL-020 ds004148. Requires an intact full cohort."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import platform
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import scipy
import sklearn
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 20261019
BOOTSTRAPS = 10_000
NULL_SHUFFLES = 999
SESSIONS = ("ses-session1", "ses-session2", "ses-session3")
TASKS = ("eyesclosed", "eyesopen", "mathematic", "memory", "music")
CONTRASTS = ("mathematic", "memory", "music")
DURATIONS = (4, 20)
FAMILIES = ("PCV", "TP", "AR", "NIE", "RD", "OI", "SC", "ED")
SCALAR_FAMILIES = tuple(x for x in FAMILIES if x != "AR")
BASELINES = (
    "log10_median_channel_rms_uV", "relative_delta_1_4hz", "relative_theta_4_8hz",
    "relative_alpha_8_13hz", "relative_beta_13_30hz", "relative_gamma_30_45hz",
    "normalized_spectral_entropy_1_45hz", "median_channel_autocorrelation_lag_1s",
    "mean_absolute_zero_lag_channel_correlation",
)
PROTOCOL_ID = "SL-020-MNPS32-RETEST-001"
EXPECTED_FAMILY_STATUS_ROWS = 896 * 90 + 4 * 2
EXPECTED_BASELINE_STATUS_ROWS = 896 * 90


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def holm(pvalues: list[float]) -> list[float]:
    order = sorted(range(len(pvalues)), key=lambda i: (pvalues[i], i))
    out, running, n = [1.0] * len(pvalues), 0.0, len(pvalues)
    for rank, index in enumerate(order):
        running = max(running, (n - rank) * pvalues[index])
        out[index] = min(1.0, running)
    return out


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _ci_median(values: np.ndarray, rng: np.random.Generator) -> tuple[float | None, float | None]:
    if len(values) == 0:
        return None, None
    indices = rng.integers(0, len(values), size=(BOOTSTRAPS, len(values)))
    medians = np.median(values[indices], axis=1)
    return float(np.quantile(medians, .025)), float(np.quantile(medians, .975))


def icc_a1(x: np.ndarray) -> float:
    """Two-way random, absolute agreement, single-measure ICC(2,1), n x 2."""
    if x.ndim != 2 or x.shape[1] != 2 or x.shape[0] < 2 or not np.isfinite(x).all():
        return float("nan")
    n, k = x.shape
    grand, row, col = float(x.mean()), x.mean(axis=1), x.mean(axis=0)
    msr = k * np.sum((row - grand) ** 2) / (n - 1)
    msc = n * np.sum((col - grand) ** 2) / (k - 1)
    residual = x - row[:, None] - col[None, :] + grand
    mse = np.sum(residual ** 2) / ((n - 1) * (k - 1))
    den = msr + (k - 1) * mse + k * (msc - mse) / n
    return float((msr - mse) / den) if den != 0 else float("nan")


def _ci_icc(x: np.ndarray, rng: np.random.Generator) -> tuple[float | None, float | None]:
    if len(x) < 12:
        return None, None
    n = len(x)
    samples = x[rng.integers(0, n, size=(BOOTSTRAPS, n))]
    grand = samples.mean(axis=(1, 2))
    row, col = samples.mean(axis=2), samples.mean(axis=1)
    msr = 2 * np.sum((row - grand[:, None]) ** 2, axis=1) / (n - 1)
    msc = n * np.sum((col - grand[:, None]) ** 2, axis=1)
    resid = samples - row[:, :, None] - col[:, None, :] + grand[:, None, None]
    mse = np.sum(resid ** 2, axis=(1, 2)) / (n - 1)
    den = msr + mse + 2 * (msc - mse) / n
    with np.errstate(divide="ignore", invalid="ignore"):
        vals = (msr - mse) / den
    vals = vals[np.isfinite(vals)]
    if not len(vals):
        return None, None
    return float(np.quantile(vals, .025)), float(np.quantile(vals, .975))


def _verify_frozen_document(path: Path, expected_id: str) -> str:
    digest = file_sha(path)
    sidecar = path.with_suffix(path.suffix + ".sha256")
    if not sidecar.is_file():
        raise RuntimeError(f"frozen_document_hash_file_missing:{path.name}")
    recorded = sidecar.read_text(encoding="utf-8").split()[0]
    if recorded != digest:
        raise RuntimeError(f"frozen_document_hash_file_mismatch:{path.name}")
    if digest != expected_id:
        raise RuntimeError(f"frozen_document_hash_unexpected:{path.name}")
    return digest


def verify_cohort(root: Path, protocol: Path, amendment_001: Path,
                  amendment_002: Path) -> tuple[dict[str, Any], list[Path], dict[str, str]]:
    manifest_path = root / "run_manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("cohort_run_manifest_missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ident = manifest.get("frozen_identity", {})
    completed = manifest.get("completed_participants", {})
    participants = ident.get("selected_participants", [])
    if manifest.get("status") != "complete" or ident.get("mode") != "cohort":
        raise RuntimeError("analysis_requires_complete_cohort_mode")
    if len(participants) != 60 or set(participants) != set(completed):
        raise RuntimeError(f"cohort_participant_manifest_incomplete:{len(participants)}:{len(completed)}")
    if len(ident.get("selected_recording_keys", [])) != 900:
        raise RuntimeError("cohort_recording_manifest_incomplete")
    support = manifest.get("support_counts", {})
    for family in FAMILIES:
        requested = int(support.get(f"family:{family}:requested", 0))
        status_total = sum(int(v) for k, v in support.items() if k.startswith(f"family:{family}:status:"))
        if requested != EXPECTED_FAMILY_STATUS_ROWS or status_total != EXPECTED_FAMILY_STATUS_ROWS:
            raise RuntimeError(f"cohort_family_status_coverage_failed:{family}:{requested}:{status_total}")
    for baseline in BASELINES:
        status_total = sum(int(v) for k, v in support.items() if k.startswith(f"baseline:{baseline}:status:"))
        if status_total != EXPECTED_BASELINE_STATUS_ROWS:
            raise RuntimeError(f"cohort_baseline_status_coverage_failed:{baseline}:{status_total}")
    protocol_hash = _verify_frozen_document(
        protocol, "67bc3c6cace35f5341250c1cf25990a47b2114ac9fac426a8ea2e988cf60ebb2")
    amendment_001_hash = _verify_frozen_document(
        amendment_001, "16a3db93c847b0594f6c639461b477343df730289213698bc1a5b499becb1b5d")
    amendment_002_hash = _verify_frozen_document(
        amendment_002, "4d41d5d8ae0c6061d0a2a0e11fe21d06195d8dfadf4be75e256cc6f97c8a9243")
    if ident.get("protocol_sha256") != protocol_hash:
        raise RuntimeError("cohort_protocol_hash_mismatch")
    if ident.get("amendment_sha256") != amendment_001_hash:
        raise RuntimeError("cohort_amendment_001_hash_mismatch")
    shards = []
    for participant in participants:
        info = completed[participant]
        shard = root / info["relative_path"]
        if not shard.is_file() or file_sha(shard) != info.get("sha256"):
            raise RuntimeError(f"participant_shard_integrity_failure:{participant}")
        shards.append(shard)
    return manifest, shards, {
        "protocol_sha256": protocol_hash,
        "amendment_001_sha256": amendment_001_hash,
        "amendment_002_sha256": amendment_002_hash,
    }


def load_summaries(shards: list[Path]) -> tuple[dict, dict, dict, list[str]]:
    """Stream window exports into participant/session/condition medians."""
    window_vals: dict[tuple, list[float]] = defaultdict(list)
    reasons: dict[tuple, Counter] = defaultdict(Counter)
    file_reasons: dict[tuple, str] = {}
    aliases: dict[tuple, bool] = {}
    source_ok: dict[tuple, bool] = {}
    ar_names: dict[int, list[str]] = {4: [], 20: []}
    record_count = 0
    for shard in shards:
        with gzip.open(shard, "rt", encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                record_count += 1
                kind = row.get("record_type")
                if kind == "recording_manifest":
                    key = (row["participant_id"], row["session_id"], row["task_id"])
                    aliases[key] = bool(row.get("explicit_casefold_aliases") or [])
                    source_ok[key] = bool(row.get("payload_matches_declared_support") and row.get("payload_is_whole_frame"))
                    continue
                if kind not in ("measurement", "qEEG_baseline"):
                    raise RuntimeError(f"unknown_record_type:{kind}")
                pid, session, task = row.get("participant_id"), row.get("session_id"), row.get("condition")
                duration = int(row.get("duration_seconds") or 0)
                if session not in SESSIONS or task not in TASKS or duration not in DURATIONS:
                    raise RuntimeError("record_coordinate_outside_frozen_grid")
                rec = (pid, session, task)
                if kind == "measurement":
                    family = row.get("family_id")
                    if family not in FAMILIES:
                        raise RuntimeError(f"unknown_family:{family}")
                    entries = []
                    if family == "AR":
                        names, vals = row.get("component_names") or [], row.get("component_values") or []
                        statuses, why = row.get("component_status") or [], row.get("component_reasons") or []
                        if len(names) != len(vals):
                            raise RuntimeError("AR_component_schema_length_mismatch")
                        current_names = [str(name) for name in names]
                        if current_names:
                            if ar_names[duration] and current_names != ar_names[duration]:
                                raise RuntimeError(f"AR_component_order_or_roster_mismatch:{duration}s")
                            if not ar_names[duration]:
                                ar_names[duration] = current_names
                        for i, name in enumerate(names):
                            entries.append((f"MNPS:AR::{name}", _number(vals[i]),
                                            statuses[i] if i < len(statuses) else row.get("status"),
                                            why[i] if i < len(why) else row.get("reason")))
                        if not entries and not row.get("window_id"):
                            reason = row.get("reason") or row.get("status") or "unsupported_file_source"
                            file_reasons[(pid, session, task, duration)] = reason
                    else:
                        entries.append((f"MNPS:{family}", _number(row.get("value")), row.get("status"),
                                        row.get("reason"), row.get("valid")))
                else:
                    name = row.get("baseline_feature_id")
                    if name not in BASELINES:
                        raise RuntimeError(f"unknown_baseline_feature:{name}")
                    entries = [(f"qEEG:{name}", _number(row.get("value")), row.get("status"),
                                row.get("reason"), row.get("valid"))]
                window_id = row.get("window_id")
                if rec not in aliases:
                    raise RuntimeError("recording_manifest_must_precede_measurement_rows")
                start, end = row.get("start_seconds"), row.get("end_seconds")
                row_variants = ["primary"]
                if not window_id or (start is not None and end is not None and float(start) >= 20.0 and float(end) <= 280.0):
                    row_variants.append("trimmed_endpoints")
                if not aliases[rec]:
                    row_variants.append("strict_labels")
                for entry in entries:
                    feature, value, status, why = entry[:4]
                    row_valid = entry[4] if len(entry) > 4 else None
                    status_computed = isinstance(status, str) and status.startswith("computed")
                    is_ar_component = feature.startswith("MNPS:AR::")
                    accepted = status_computed and value is not None and (is_ar_component or row_valid is True)
                    if not window_id or not accepted:
                        reason = why or status or "unsupported_file_source"
                        if window_id and value is not None and not accepted:
                            reason = "value_status_validity_inconsistent"
                        if not window_id and why:
                            file_reasons[(pid, session, task, duration)] = str(why)
                        for variant in row_variants:
                            reasons[(variant, pid, session, task, duration, feature)].update([reason])
                        continue
                    for variant in row_variants:
                        window_vals[(variant, pid, session, task, duration, feature, window_id)].append(value)
    # File-level source failures have no window rows for the qEEG baselines and
    # no AR component records. Keep their known local reason beside each planned
    # feature summary instead of turning missing rows into values.
    for (pid, session, task), supported in source_ok.items():
        if supported:
            continue
        for duration in DURATIONS:
            reason = file_reasons.get((pid, session, task, duration), "unsupported_file_source")
            planned = [f"MNPS:{fam}" for fam in SCALAR_FAMILIES]
            planned.extend(f"MNPS:AR::{name}" for name in ar_names[duration])
            planned.extend(f"qEEG:{name}" for name in BASELINES)
            for feature in planned:
                use_variants = ["primary", "trimmed_endpoints"]
                if not aliases[(pid, session, task)]:
                    use_variants.append("strict_labels")
                for variant in use_variants:
                    reasons[(variant, pid, session, task, duration, feature)].update([reason])
    # There is one measurement per feature/window; median is defensive for duplicates.
    by_session: dict[tuple, list[float]] = defaultdict(list)
    window_ids: dict[tuple, set[str]] = defaultdict(set)
    for (variant, pid, session, task, duration, feature, wid), vals in window_vals.items():
        key = (variant, pid, session, task, duration, feature)
        by_session[key].append(float(np.median(vals)))
        window_ids[key].add(wid)
    summaries, counts, summary_rows = {}, {}, []
    features = sorted({k[-1] for k in by_session} | {k[-1] for k in reasons})
    participants = sorted({k[1] for k in by_session})
    for variant in ("primary", "trimmed_endpoints", "strict_labels"):
        for pid in participants:
            for session in SESSIONS:
                for task in TASKS:
                    for duration in DURATIONS:
                        source_supported = source_ok.get((pid, session, task), False)
                        duration_features = [f for f in features if not f.startswith("MNPS:AR::") or
                                             f.split("::", 1)[1] in ar_names[duration]]
                        for feature in duration_features:
                            key = (variant, pid, session, task, duration, feature)
                            vals = by_session.get(key, [])
                            if vals:
                                summaries[key] = float(np.median(vals))
                            counts[key] = len(window_ids.get(key, set()))
                            wanted = (300 // duration) - (2 if variant == "trimmed_endpoints" else 0)
                            why = dict(reasons.get((variant, pid, session, task, duration, feature), Counter()))
                            if variant == "strict_labels" and aliases.get((pid, session, task), False):
                                wanted = 0
                                why = {"excluded_source_header_capitalization_alias": 1}
                            if not source_supported and not why:
                                why = {"unsupported_file_source": wanted}
                            summary_rows.append({
                                "analysis_variant": variant, "participant_id": pid, "session_id": session,
                                "condition": task, "duration_seconds": duration, "feature_id": feature,
                                "session_median": summaries.get(key), "valid_window_count": counts[key],
                                "requested_window_count": wanted, "support_reasons": why, "qualified": False,
                            })
    meta = {"aliases": aliases, "source_supported": source_ok, "summary_rows": summary_rows,
            "records_read": record_count, "ar_names": ar_names}
    return summaries, counts, meta, features


def _participant_deltas(summaries: dict, variant: str, task: str, duration: int, feature: str):
    result = {}
    pids = sorted({k[1] for k in summaries if k[0] == variant})
    for pid in pids:
        session_deltas = []
        for session in SESSIONS:
            ec = summaries.get((variant, pid, session, "eyesclosed", duration, feature))
            val = summaries.get((variant, pid, session, task, duration, feature))
            if ec is not None and val is not None:
                session_deltas.append(val - ec)
        if len(session_deltas) >= 2:
            result[pid] = float(np.mean(session_deltas))
    return result


def task_sensitivity(summaries: dict, ar_names: dict[int, list[str]]) -> list[dict[str, Any]]:
    rng = np.random.default_rng(SEED)
    rows = []
    for variant in ("primary", "trimmed_endpoints", "strict_labels"):
        tests = []
        for duration in DURATIONS:
            features = [f"MNPS:{fam}" for fam in SCALAR_FAMILIES]
            features.extend(f"MNPS:AR::{name}" for name in ar_names[duration])
            for task in CONTRASTS:
                for feature in features:
                    delta = _participant_deltas(summaries, variant, task, duration, feature)
                    vals = np.asarray(list(delta.values()), dtype=float)
                    reason, statistic, p = None, None, 1.0
                    if len(vals) < 12:
                        reason = "fewer_than_12_participants_with_at_least_2_paired_sessions"
                    elif np.all(vals == 0):
                        statistic, p = 0.0, 1.0
                    else:
                        try:
                            test = stats.wilcoxon(vals, zero_method="wilcox", alternative="two-sided", method="auto")
                            statistic, p = float(test.statistic), float(test.pvalue)
                        except Exception as exc:
                            reason = f"wilcoxon_not_estimable:{type(exc).__name__}"
                    lo, hi = _ci_median(vals, rng) if len(vals) else (None, None)
                    tests.append({
                        "analysis_variant": variant, "task_minus_eyesclosed": task,
                        "duration_seconds": duration, "feature_id": feature, "participant_count": len(vals),
                        "participant_ids": sorted(delta), "median_participant_delta": float(np.median(vals)) if len(vals) else None,
                        "bootstrap_ci95_low": lo, "bootstrap_ci95_high": hi, "wilcoxon_statistic": statistic,
                        "p_raw": p, "not_estimable_reason": reason,
                    })
        if variant == "primary":
            if len(tests) != 72:
                raise RuntimeError(f"primary_holm_family_expected_72_got_{len(tests)}")
            for row, adj in zip(tests, holm([x["p_raw"] for x in tests]), strict=True):
                row["p_holm_72"] = adj
                row["reject_holm_05"] = bool(adj < .05)
        else:
            for row in tests:
                row["p_holm_72"] = None
                row["reject_holm_05"] = None
        rows.extend(tests)
    return rows


def reliability(summaries: dict, features: list[str], ar_names: dict[int, list[str]]) -> list[dict[str, Any]]:
    rng = np.random.default_rng(SEED)
    rows = []
    mnps = [f for f in features if f.startswith("MNPS:")]
    for variant in ("primary", "trimmed_endpoints", "strict_labels"):
        pids = sorted({k[1] for k in summaries if k[0] == variant})
        for duration in DURATIONS:
            fs = [f for f in mnps if not f.startswith("MNPS:AR::") or f.split("::", 1)[1] in ar_names[duration]]
            for feature in fs:
                for target, task in [("condition", t) for t in TASKS] + [("delta", t) for t in CONTRASTS]:
                    for pair, session2 in (("S1-S2", "ses-session2"), ("S1-S3", "ses-session3")):
                        paired = []
                        for pid in pids:
                            a = summaries.get((variant, pid, "ses-session1", task, duration, feature))
                            b = summaries.get((variant, pid, session2, task, duration, feature))
                            if target == "delta":
                                ec1 = summaries.get((variant, pid, "ses-session1", "eyesclosed", duration, feature))
                                ec2 = summaries.get((variant, pid, session2, "eyesclosed", duration, feature))
                                a_task = summaries.get((variant, pid, "ses-session1", task, duration, feature))
                                b_task = summaries.get((variant, pid, session2, task, duration, feature))
                                a = a_task - ec1 if a_task is not None and ec1 is not None else None
                                b = b_task - ec2 if b_task is not None and ec2 is not None else None
                            if a is not None and b is not None:
                                paired.append((pid, a, b))
                        x = np.asarray([[a, b] for _, a, b in paired], dtype=float)
                        n = len(x)
                        value = icc_a1(x) if n >= 12 else float("nan")
                        lo, hi = _ci_icc(x, rng) if n >= 12 else (None, None)
                        rows.append({
                            "analysis_variant": variant, "reliability_target": f"{target}:{task}",
                            "duration_seconds": duration, "feature_id": feature, "session_pair": pair,
                            "paired_participants": n, "icc_a1": value if math.isfinite(value) else None,
                            "bootstrap_ci95_low": lo, "bootstrap_ci95_high": hi,
                            "not_estimable_reason": None if n >= 12 else "fewer_than_12_paired_participants",
                        })
    return rows


def _model(c: float):
    return make_pipeline(StandardScaler(), LogisticRegression(C=c, penalty="l2", solver="liblinear", max_iter=2000))


def _choose_c(x: np.ndarray, y: np.ndarray, groups: np.ndarray) -> float:
    nfold = min(4, len(np.unique(groups)))
    if nfold < 2:
        return 1.0
    splitter = GroupKFold(n_splits=nfold)
    scored = []
    for c in (.01, .1, 1.0, 10.0):
        fold_scores = []
        for tr, va in splitter.split(x, y, groups):
            if len(np.unique(y[tr])) < 2 or len(np.unique(y[va])) < 2:
                continue
            fit = _model(c).fit(x[tr], y[tr])
            fold_scores.append(balanced_accuracy_score(y[va], fit.predict(x[va])))
        scored.append((float(np.mean(fold_scores)) if fold_scores else -1.0, -c, c))
    return max(scored)[2]


def _predict_outer(x: np.ndarray, y: np.ndarray, subject: np.ndarray, session: np.ndarray,
                   transfer: str, roster: list[str]):
    pred, prob = np.full(len(y), np.nan), np.full(len(y), np.nan)
    tr_all = np.where(session == "ses-session1")[0]
    te_all = np.where(session == transfer)[0]
    split = GroupKFold(n_splits=5)
    fold_for = {}
    dummy, grp = np.arange(len(roster))[:, None], np.asarray(roster)
    for fold, (_, held_idx) in enumerate(split.split(dummy, groups=grp)):
        for i in held_idx:
            fold_for[roster[i]] = fold
    for fold in range(5):
        held = {p for p in roster if fold_for[p] == fold}
        tr = tr_all[np.asarray([subject[i] not in held for i in tr_all])]
        te = te_all[np.asarray([subject[i] in held for i in te_all])]
        if not len(tr) or not len(te) or len(np.unique(y[tr])) < 2:
            continue
        c = _choose_c(x[tr], y[tr], subject[tr])
        fit = _model(c).fit(x[tr], y[tr])
        pred[te] = fit.predict(x[te])
        prob[te] = fit.predict_proba(x[te])[:, 1]
    return pred, prob


def _metrics(y: np.ndarray, pred: np.ndarray, prob: np.ndarray, subject: np.ndarray,
             rng: np.random.Generator) -> dict[str, Any]:
    good = np.isfinite(pred) & np.isfinite(prob)
    y, pred, prob, subject = y[good], pred[good].astype(int), prob[good], subject[good]
    if len(np.unique(y)) != 2:
        return {"balanced_accuracy": None, "roc_auc": None, "participants": len(np.unique(subject)),
                "bacc_ci95": [None, None], "auc_ci95": [None, None]}
    bacc, auc = float(balanced_accuracy_score(y, pred)), float(roc_auc_score(y, prob))
    unique = np.unique(subject)
    by = {s: np.where(subject == s)[0] for s in unique}
    bboots, aboots = [], []
    for _ in range(BOOTSTRAPS):
        draw = rng.choice(unique, size=len(unique), replace=True)
        ix = np.concatenate([by[s] for s in draw])
        if len(np.unique(y[ix])) == 2:
            bboots.append(balanced_accuracy_score(y[ix], pred[ix]))
            aboots.append(roc_auc_score(y[ix], prob[ix]))
    ci = lambda z: [float(np.quantile(z, .025)), float(np.quantile(z, .975))] if z else [None, None]
    return {"balanced_accuracy": bacc, "roc_auc": auc, "participants": len(unique),
            "bacc_ci95": ci(bboots), "auc_ci95": ci(aboots)}


def classification(summaries: dict, features: list[str], ar_names: dict[int, list[str]]) -> list[dict[str, Any]]:
    base = [f"qEEG:{n}" for n in BASELINES]
    mnps_all = [f for f in features if f.startswith("MNPS:")]
    rows, test_indices, pvalues = [], [], []
    for duration in DURATIONS:
        mnps = [f for f in mnps_all if not f.startswith("MNPS:AR::") or f.split("::", 1)[1] in ar_names[duration]]
        for task in CONTRASTS:
            for transfer in ("ses-session2", "ses-session3"):
                roster = []
                pids = sorted({k[1] for k in summaries if k[0] == "primary"})
                for pid in pids:
                    complete = all(summaries.get(("primary", pid, ses, cond, duration, f)) is not None
                                   for ses in ("ses-session1", transfer)
                                   for cond in ("eyesclosed", task) for f in base + mnps)
                    if complete:
                        roster.append(pid)
                if len(roster) < 12:
                    rows.extend([
                        {"duration_seconds": duration, "task_minus_eyesclosed": task, "transfer_session": transfer,
                         "feature_arm": arm, "participant_count": len(roster), "not_estimable_reason": "fewer_than_12_complete_paired_participants"}
                        for arm in ("qEEG", "qEEG+MNPS")
                    ])
                    rows.append({"duration_seconds": duration, "task_minus_eyesclosed": task,
                                 "transfer_session": transfer, "feature_arm": "incremental", "participant_count": len(roster),
                                 "delta_balanced_accuracy": None, "p_raw_one_sided": 1.0,
                                 "not_estimable_reason": "fewer_than_12_complete_paired_participants"})
                    test_indices.append(len(rows)-1); pvalues.append(1.0)
                    continue
                subjects, sessions, y, xq, xm = [], [], [], [], []
                for pid in roster:
                    for ses in ("ses-session1", transfer):
                        for label, cond in ((0, "eyesclosed"), (1, task)):
                            key = ("primary", pid, ses, cond, duration)
                            subjects.append(pid); sessions.append(ses); y.append(label)
                            xq.append([summaries[(*key, f)] for f in base])
                            xm.append([summaries[(*key, f)] for f in base + mnps])
                subject, session, y = np.asarray(subjects), np.asarray(sessions), np.asarray(y, dtype=int)
                xq, xm = np.asarray(xq, dtype=float), np.asarray(xm, dtype=float)
                predq, probq = _predict_outer(xq, y, subject, session, transfer, roster)
                predm, probm = _predict_outer(xm, y, subject, session, transfer, roster)
                tm = session == transfer
                rng = np.random.default_rng(np.random.SeedSequence([SEED, duration, CONTRASTS.index(task), int(transfer[-1])]))
                mq = _metrics(y[tm], predq[tm], probq[tm], subject[tm], rng)
                mm = _metrics(y[tm], predm[tm], probm[tm], subject[tm], rng)
                delta = mm["balanced_accuracy"] - mq["balanced_accuracy"] if mq["balanced_accuracy"] is not None and mm["balanced_accuracy"] is not None else None
                delta_auc = mm["roc_auc"] - mq["roc_auc"] if mq["roc_auc"] is not None and mm["roc_auc"] is not None else None
                rows.append({"duration_seconds": duration, "task_minus_eyesclosed": task, "transfer_session": transfer,
                             "feature_arm": "qEEG", **mq})
                rows.append({"duration_seconds": duration, "task_minus_eyesclosed": task, "transfer_session": transfer,
                             "feature_arm": "qEEG+MNPS", **mm})
                valid = tm & np.isfinite(predq) & np.isfinite(predm)
                held = np.unique(subject[valid])
                by = {p: np.where(valid & (subject == p))[0] for p in held}
                delta_boot, delta_auc_boot = [], []
                for _ in range(BOOTSTRAPS):
                    draw = rng.choice(held, size=len(held), replace=True)
                    ix = np.concatenate([by[p] for p in draw])
                    if len(np.unique(y[ix])) == 2:
                        delta_boot.append(balanced_accuracy_score(y[ix], predm[ix]) - balanced_accuracy_score(y[ix], predq[ix]))
                        delta_auc_boot.append(roc_auc_score(y[ix], probm[ix]) - roc_auc_score(y[ix], probq[ix]))
                ci = [float(np.quantile(delta_boot, .025)), float(np.quantile(delta_boot, .975))] if delta_boot else [None, None]
                auc_ci = [float(np.quantile(delta_auc_boot, .025)), float(np.quantile(delta_auc_boot, .975))] if delta_auc_boot else [None, None]
                rows.append({"duration_seconds": duration, "task_minus_eyesclosed": task, "transfer_session": transfer,
                             "feature_arm": "incremental", "participant_count": len(held),
                             "delta_balanced_accuracy": delta, "delta_bacc_ci95": ci,
                             "delta_roc_auc": delta_auc, "delta_auc_ci95": auc_ci, "p_raw_one_sided": None})
                test_indices.append(len(rows)-1)
                if delta is None:
                    pvalues.append(1.0)
                    continue
                rng_null = np.random.default_rng(np.random.SeedSequence([SEED, duration, CONTRASTS.index(task), int(transfer[-1]), 77]))
                null = []
                for shuffle_index in range(NULL_SHUFFLES):
                    flips = {p: int(rng_null.integers(0, 2)) for p in roster}
                    y_perm = np.asarray([int(label) ^ flips[pid] for label, pid in zip(y, subject, strict=True)])
                    pq, _ = _predict_outer(xq, y_perm, subject, session, transfer, roster)
                    pm, _ = _predict_outer(xm, y_perm, subject, session, transfer, roster)
                    usable = tm & np.isfinite(pq) & np.isfinite(pm)
                    null.append(balanced_accuracy_score(y_perm[usable], pm[usable]) -
                                balanced_accuracy_score(y_perm[usable], pq[usable]))
                    if (shuffle_index + 1) % 100 == 0:
                        print(f"SL020 R3 null: {duration}s {task} {transfer}; {shuffle_index + 1}/{NULL_SHUFFLES}", flush=True)
                if len(null) != NULL_SHUFFLES:
                    raise RuntimeError("classifier_null_did_not_complete_999_swaps")
                p = (1 + int(np.sum(np.asarray(null) >= delta))) / 1000
                rows[test_indices[-1]]["p_raw_one_sided"] = p
                rows[test_indices[-1]]["null_delta_count"] = len(null)
                pvalues.append(p)
    if len(test_indices) != 12:
        raise RuntimeError(f"incremental_classifier_holm_family_expected_12_got_{len(test_indices)}")
    for idx, adj in zip(test_indices, holm(pvalues), strict=True):
        rows[idx]["p_holm_12"] = adj
        rows[idx]["reject_holm_05"] = bool(adj < .05)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list, tuple)) else v
                             for k, v in row.items()})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--amendment-001", type=Path, required=True)
    parser.add_argument("--amendment-002", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    cohort, protocol = args.cohort_root.resolve(strict=True), args.protocol.resolve(strict=True)
    amendment_001 = args.amendment_001.resolve(strict=True)
    amendment_002 = args.amendment_002.resolve(strict=True)
    output = args.output_root.resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError("refusing_nonempty_analysis_output_root")
    cohort_manifest, shards, frozen_hashes = verify_cohort(cohort, protocol, amendment_001, amendment_002)
    summaries, counts, meta, features = load_summaries(shards)
    if len(meta["ar_names"][4]) != 1 or len(meta["ar_names"][20]) != 9:
        raise RuntimeError(f"unexpected_AR_component_roster:{meta['ar_names']}")
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "session_summaries.csv", meta["summary_rows"])
    sensitivity = task_sensitivity(summaries, meta["ar_names"])
    write_csv(output / "primary_task_sensitivity.csv", sensitivity)
    reliability_rows = reliability(summaries, features, meta["ar_names"])
    write_csv(output / "reliability_icc.csv", reliability_rows)
    classifier_rows = classification(summaries, features, meta["ar_names"])
    write_csv(output / "incremental_classifier.csv", classifier_rows)
    analysis_manifest = {
        "protocol_id": PROTOCOL_ID, "analysis_status": "complete", "cohort_root": str(cohort),
        "cohort_run_manifest_sha256": file_sha(cohort / "run_manifest.json"),
        "cohort_participant_count": len(shards), "participant_shards_sha256_verified": True,
        "records_streamed": meta["records_read"], "summary_feature_count": len(features),
        "AR_component_names": {str(k): v for k, v in meta["ar_names"].items()},
        **frozen_hashes, "analysis_script_sha256": file_sha(Path(__file__).resolve()),
        "participant_bootstrap_resamples": BOOTSTRAPS, "master_seed": SEED,
        "classifier_label_swaps": NULL_SHUFFLES, "qualified": False,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__,
                    "scipy": scipy.__version__, "scikit_learn": sklearn.__version__},
    }
    (output / "analysis_manifest.json").write_text(json.dumps(analysis_manifest, indent=2), encoding="utf-8")
    print(json.dumps({"analysis_status": "complete", "participants": len(shards),
                      "records_streamed": meta["records_read"], "session_summary_rows": len(meta["summary_rows"]),
                      "primary_tests": len(sensitivity), "reliability_rows": len(reliability_rows),
                      "classifier_rows": len(classifier_rows), "qualified": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
