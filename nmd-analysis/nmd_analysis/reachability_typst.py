from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .analysis_config import ContrastConfig, load_analysis_config


SECTION_ORDER = ["GLOBAL_TUBE", "GLOBAL_PER_H", "BLOCK_TUBE", "BLOCK_PER_H"]


@dataclass(frozen=True)
class ContrastDisplay:
    name: str
    label: str


def _format_num(value: object, digits: int) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "–"
    if not np.isfinite(numeric):
        return "–"
    return f"{numeric:.{digits}f}"


def _format_p(value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "–"
    if not np.isfinite(numeric):
        return "–"
    return f"{numeric:.2e}"


def _bh_fdr_qvals(pvals: np.ndarray) -> np.ndarray:
    p = np.asarray(pvals, dtype=float)
    out = np.full(p.shape, np.nan, dtype=float)
    mask = np.isfinite(p)
    if not np.any(mask):
        return out
    pv = p[mask]
    order = np.argsort(pv)
    ranked = pv[order]
    m = int(ranked.size)
    q = ranked * (m / np.arange(1, m + 1, dtype=float))
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.clip(q, 0.0, 1.0)
    unsorted = np.empty_like(q)
    unsorted[order] = q
    out[mask] = unsorted
    return out


def _expand_with_iqr(features: Iterable[str]) -> List[str]:
    out: List[str] = []
    for feature in features:
        out.append(feature)
        if feature.endswith("_median"):
            out.append(feature.replace("_median", "_iqr"))
    return out


def _display_feature_name(feature: str) -> str:
    if "cone_kappa_h" in feature:
        return feature
    if "cone_kappa_" in feature:
        return feature.replace("cone_kappa_", "cone_vol_ratio_")
    if "tube_rotation_" in feature:
        return feature.replace("tube_rotation_", "cone_rhoA_")
    return feature


def _sig_label(row: pd.Series, q_fallback: float) -> str:
    q_value = pd.to_numeric(pd.Series([row.get("q_value")]), errors="coerce").iloc[0]
    if np.isfinite(q_value):
        return "FDR" if float(q_value) <= 0.05 else "not-sig"
    return "BH(section)" if np.isfinite(q_fallback) and float(q_fallback) <= 0.05 else "not-sig"


def _ordered_selector_items(selector: Dict[str, object]) -> List[Tuple[str, str]]:
    order = ["group", "condition", "category", "task", "session", "run"]
    items: List[Tuple[str, str]] = []
    seen: set[str] = set()
    for key in order + list(selector.keys()):
        if key in seen or key not in selector:
            continue
        value = selector[key]
        if isinstance(value, list):
            continue
        text = str(value).strip()
        if not text:
            continue
        items.append((key, text))
        seen.add(key)
    return items


def _pretty_token(token: str) -> str:
    mapping = {
        "A": "AD",
        "F": "FTD",
        "C": "Healthy",
        "HC": "Healthy",
        "control": "Healthy",
        "nrem2": "NREM2",
        "nrem3": "NREM3",
        "rem": "REM",
        "awake": "Awake",
        "unresponsive": "Unresponsive",
        "recovery": "Recovery",
        "rest": "Rest",
    }
    cleaned = token.replace("_", " ").strip()
    return mapping.get(cleaned, mapping.get(cleaned.lower(), cleaned))


def _side_label(selector: Dict[str, object], drop_keys: Sequence[str]) -> str:
    tokens = [_pretty_token(value) for key, value in _ordered_selector_items(selector) if key not in drop_keys]
    return " ".join(token for token in tokens if token).strip()


def _fallback_contrast_label(name: str) -> str:
    if "_vs_" not in name:
        return _pretty_token(name)
    left_raw, right_raw = name.split("_vs_", 1)
    left_tokens = [_pretty_token(token) for token in left_raw.split("_") if token]
    right_tokens = [_pretty_token(token) for token in right_raw.split("_") if token]
    while left_tokens and right_tokens and left_tokens[0] == right_tokens[0]:
        left_tokens.pop(0)
        right_tokens.pop(0)
    left = " ".join(left_tokens).strip()
    right = " ".join(right_tokens).strip()
    if left and right:
        return f"{left} vs {right}"
    text = name.replace("_vs_", " vs ")
    return text.replace("_", " ")


def build_contrast_displays(config_path: str | Path) -> List[ContrastDisplay]:
    cfg = load_analysis_config(config_path)
    displays: List[ContrastDisplay] = []
    for contrast in cfg.contrasts:
        if not isinstance(contrast, ContrastConfig):
            continue
        label = _fallback_contrast_label(contrast.name)
        if not label or " vs " not in label:
            left_items = dict(_ordered_selector_items(contrast.left))
            right_items = dict(_ordered_selector_items(contrast.right))
            shared_keys = [key for key in left_items if key in right_items and left_items[key] == right_items[key]]
            label_left = _side_label(contrast.left, shared_keys)
            label_right = _side_label(contrast.right, shared_keys)
            label = f"{label_left} vs {label_right}".strip()
            if not label_left or not label_right:
                label = _fallback_contrast_label(contrast.name)
        displays.append(ContrastDisplay(name=contrast.name, label=label))
    return displays


def latest_analysis_file(analysis_dir: str | Path, dataset: str, analysis_type: str) -> Path:
    root = Path(analysis_dir)
    pattern = f"{dataset}_{analysis_type}_*.parquet"
    candidates = sorted(root.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No analysis file matching {pattern} under {root}")
    return candidates[0]


def load_latest_contrast_results(analysis_dir: str | Path, dataset: str) -> pd.DataFrame:
    root = Path(analysis_dir)
    candidates = sorted(
        root.glob(f"{dataset}_contrast_results_*.parquet"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No contrast_results parquet found for {dataset} under {root}")
    last_frame = pd.DataFrame()
    for path in candidates:
        frame = pd.read_parquet(path)
        if "analysis_type" in frame.columns:
            frame = frame[frame["analysis_type"] == "reachability_cones"].copy()
        if "metric" in frame.columns:
            frame["metric"] = frame["metric"].astype(str)
        if "contrast_name" in frame.columns:
            frame["contrast_name"] = frame["contrast_name"].astype(str)
        if not frame.empty:
            return frame
        last_frame = frame
    return last_frame


def _rows_for_features(
    frame: pd.DataFrame,
    contrast_name: str,
    label: str,
    features: Iterable[str],
    *,
    block: Optional[str] = None,
    p_threshold: Optional[float] = None,
) -> List[str]:
    contrast_frame = frame[frame["contrast_name"] == contrast_name].copy()
    rows: List[str] = []
    resolved: List[pd.Series] = []
    pvals: List[float] = []
    for feature in features:
        hit = contrast_frame[contrast_frame["metric"] == feature]
        if hit.empty:
            resolved.append(pd.Series(dtype=object))
            pvals.append(float("nan"))
            continue
        row = hit.iloc[0]
        resolved.append(row)
        pvals.append(float(pd.to_numeric(pd.Series([row.get("p_value")]), errors="coerce").iloc[0]))
    fallback_q = _bh_fdr_qvals(np.asarray(pvals, dtype=float))
    for feature, row, p_value, q_value in zip(features, resolved, pvals, fallback_q, strict=False):
        if row.empty:
            continue
        if p_threshold is not None and np.isfinite(p_value) and float(p_value) >= p_threshold:
            continue
        effect = pd.to_numeric(pd.Series([row.get("effect_size")]), errors="coerce").iloc[0]
        t_like = pd.to_numeric(pd.Series([row.get("effect_estimate")]), errors="coerce").iloc[0]
        sig = _sig_label(row, q_value)
        feature_label = _display_feature_name(feature)
        if block is None:
            rows.append(
                f"    [{label}], [`{feature_label}`], [{_format_num(effect, 3)}], "
                f"[{_format_num(t_like, 2)}], [{_format_p(p_value)}], [{sig}],"
            )
        else:
            rows.append(
                f"    [{label}], [{block}], [`{feature_label}`], [{_format_num(effect, 3)}], "
                f"[{_format_num(t_like, 2)}], [{_format_p(p_value)}], [{sig}],"
            )
    return rows


def build_reachability_typst_sections(
    frame: pd.DataFrame,
    displays: Sequence[ContrastDisplay],
    *,
    horizon: int = 4,
    p_threshold: Optional[float] = None,
) -> List[str]:
    lines: List[str] = [
        "// FDR policy: use q_value when present; otherwise BH(section) over resolved section rows.",
    ]
    for display in displays:
        global_tube = _expand_with_iqr(
            [
                "tube_log_det_median",
                "tube_kappa_median",
                "tube_log_eig_var_median",
                "tube_d_eff_median",
                "tube_dir_entropy_median",
                "tube_dir_entropy_norm_median",
                "cone_kappa_median",
                "tube_rotation_median",
                "persistence_log_det_median",
                "persistence_kappa_median",
                "persistence_log_eig_var_median",
                "persistence_d_eff_median",
                "persistence_tau_log_det_median",
                "persistence_tau_kappa_median",
                "persistence_tau_log_eig_var_median",
                "persistence_tau_d_eff_median",
                "persistence_hysteresis_log_det_median",
                "persistence_hysteresis_kappa_median",
                "persistence_hysteresis_log_eig_var_median",
                "persistence_hysteresis_d_eff_median",
            ]
        )
        lines.append("[GLOBAL_TUBE]")
        lines.extend(
            _rows_for_features(frame, display.name, display.label, global_tube, p_threshold=p_threshold)
        )

        per_h: List[str] = []
        for horizon_idx in range(1, horizon + 1):
            per_h.extend(
                _expand_with_iqr(
                    [
                        f"cone_log_det_h{horizon_idx}_median",
                        f"cone_kappa_h{horizon_idx}_median",
                        f"cone_log_eig_var_h{horizon_idx}_median",
                        f"cone_d_eff_h{horizon_idx}_median",
                        f"cone_dir_entropy_h{horizon_idx}_median",
                        f"cone_dir_entropy_norm_h{horizon_idx}_median",
                    ]
                )
            )
        lines.append("[GLOBAL_PER_H]")
        lines.extend(_rows_for_features(frame, display.name, display.label, per_h, p_threshold=p_threshold))

        lines.append("[BLOCK_TUBE]")
        for block in ["m", "d", "e"]:
            block_tube = _expand_with_iqr(
                [
                    f"block_{block}_tube_log_det_median",
                    f"block_{block}_tube_kappa_median",
                    f"block_{block}_tube_log_eig_var_median",
                    f"block_{block}_tube_d_eff_median",
                    f"block_{block}_tube_dir_entropy_median",
                    f"block_{block}_tube_dir_entropy_norm_median",
                    f"block_{block}_cone_kappa_median",
                    f"block_{block}_tube_rotation_median",
                    f"block_{block}_persistence_log_det_median",
                    f"block_{block}_persistence_kappa_median",
                    f"block_{block}_persistence_log_eig_var_median",
                    f"block_{block}_persistence_d_eff_median",
                    f"block_{block}_persistence_tau_log_det_median",
                    f"block_{block}_persistence_tau_kappa_median",
                    f"block_{block}_persistence_tau_log_eig_var_median",
                    f"block_{block}_persistence_tau_d_eff_median",
                    f"block_{block}_persistence_hysteresis_log_det_median",
                    f"block_{block}_persistence_hysteresis_kappa_median",
                    f"block_{block}_persistence_hysteresis_log_eig_var_median",
                    f"block_{block}_persistence_hysteresis_d_eff_median",
                ]
            )
            lines.extend(
                _rows_for_features(
                    frame,
                    display.name,
                    display.label,
                    block_tube,
                    block=block,
                    p_threshold=p_threshold,
                )
            )

        lines.append("[BLOCK_PER_H]")
        for block in ["m", "d", "e"]:
            block_per_h: List[str] = []
            for horizon_idx in range(1, horizon + 1):
                block_per_h.extend(
                    _expand_with_iqr(
                        [
                            f"block_{block}_cone_log_det_h{horizon_idx}_median",
                            f"block_{block}_cone_kappa_h{horizon_idx}_median",
                            f"block_{block}_cone_log_eig_var_h{horizon_idx}_median",
                            f"block_{block}_cone_d_eff_h{horizon_idx}_median",
                            f"block_{block}_cone_dir_entropy_h{horizon_idx}_median",
                            f"block_{block}_cone_dir_entropy_norm_h{horizon_idx}_median",
                        ]
                    )
                )
            lines.extend(
                _rows_for_features(
                    frame,
                    display.name,
                    display.label,
                    block_per_h,
                    block=block,
                    p_threshold=p_threshold,
                )
            )
    return lines
