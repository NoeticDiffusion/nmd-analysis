from __future__ import annotations

from typing import Dict

import numpy as np


def compute_phase_volume_expansion(J: np.ndarray, flow: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Ported from legacy toolkit: local phase-volume expansion metrics.
    """
    if J.ndim != 3:
        raise ValueError(f"J must have shape (n_windows, n_dims, n_dims); got {J.shape}")
    if flow.ndim != 2:
        raise ValueError(f"flow must have shape (n_windows, n_dims); got {flow.shape}")
    if J.shape[0] != flow.shape[0]:
        raise ValueError(f"Window mismatch: J has {J.shape[0]} windows, flow has {flow.shape[0]} windows")
    if J.shape[1] != J.shape[2]:
        raise ValueError(f"J must be square per window; got {J.shape}")
    if J.shape[1] != flow.shape[1]:
        raise ValueError(f"Dim mismatch: J is {J.shape[1]}D, flow is {flow.shape[1]}D")

    n_windows, n_dims = flow.shape
    total_div = np.trace(J, axis1=1, axis2=2)
    long_exp = np.zeros(n_windows)
    trans_div = np.zeros(n_windows)
    max_ortho_exp = np.zeros(n_windows)
    ortho_pos_sum = np.zeros(n_windows)

    for i in range(n_windows):
        Ji = J[i]
        fi = flow[i]

        if np.any(np.isnan(Ji)) or np.any(np.isnan(fi)):
            long_exp[i] = np.nan
            trans_div[i] = np.nan
            max_ortho_exp[i] = np.nan
            ortho_pos_sum[i] = np.nan
            continue

        speed = np.linalg.norm(fi)
        if speed < 1e-10:
            S = 0.5 * (Ji + Ji.T)
            evals = np.linalg.eigvalsh(S)
            long_exp[i] = np.nan
            trans_div[i] = total_div[i]
            max_ortho_exp[i] = evals[-1]
            ortho_pos_sum[i] = float(np.sum(np.maximum(evals, 0.0)))
            continue

        v = fi / speed
        S = 0.5 * (Ji + Ji.T)
        le = v @ S @ v
        long_exp[i] = le
        trans_div[i] = total_div[i] - le

        P = np.eye(n_dims) - np.outer(v, v)
        w, U = np.linalg.eigh(P)
        Q = U[:, w > 0.5]
        if Q.shape[1] == 0:
            max_ortho_exp[i] = np.nan
            ortho_pos_sum[i] = np.nan
        else:
            S_perp = Q.T @ S @ Q
            evals_perp = np.linalg.eigvalsh(S_perp)
            max_ortho_exp[i] = evals_perp[-1]
            ortho_pos_sum[i] = float(np.sum(np.maximum(evals_perp, 0.0)))

    return {
        "total_divergence": total_div,
        "longitudinal_expansion": long_exp,
        "transverse_divergence": trans_div,
        "max_orthogonal_expansion": max_ortho_exp,
        "orthogonal_positive_expansion_sum": ortho_pos_sum,
    }
