"""Plotly figure builders for the interactive MNJ (local Jacobian) view.

Mirrors the "intuitive visualization" conceptual figures under
`articles/CLINICAL/comatose_ndt/figures/conceptual_figures/` (vector field +
example trajectories), but data-driven: the flow field is the local linear
approximation `f(x) ~= J_hat @ (x - anchor) + v_anchor` built from the real,
per-window MNJ estimate (`jacobian_3d.j_hat`) resolved for the current
subject/time, restricted to a chosen 2D coordinate plane for display.

All functions here take plain numpy-friendly arrays/lists (as decoded from a
Dash `dcc.Store`), like `figures.py`.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
from plotly.figure_factory import create_quiver

MAX_TRAIL_SEGMENTS = 40
CURRENT_POINT_COLOR = "#e6194B"
TRAIL_COLORSCALE = "Plasma"
QUIVER_COLOR = "rgba(120,120,120,0.55)"
GRID_SIZE = 13

_AXIS_NAME_FALLBACK = ["m", "d", "e"]

PLANE_OPTIONS: List[Dict[str, str]] = [
    {"label": "d vs m", "value": "d-m"},
    {"label": "d vs e", "value": "d-e"},
    {"label": "m vs e", "value": "m-e"},
]


def _axis_labels(axis_names: Optional[Sequence[str]]) -> List[str]:
    if axis_names and len(axis_names) >= 3:
        return list(axis_names[:3])
    return list(_AXIS_NAME_FALLBACK)


def resolve_plane_indices(axis_names: Optional[Sequence[str]], plane: str) -> Tuple[int, int, str, str]:
    """Map a plane spec like "d-m" to (x_idx, y_idx, x_label, y_label)."""
    labels = _axis_labels(axis_names)
    lower = [str(n).lower() for n in labels]
    parts = [p.strip().lower() for p in (plane or "d-m").split("-")]
    if len(parts) != 2 or parts[0] not in lower or parts[1] not in lower or parts[0] == parts[1]:
        parts = ["d", "m"] if "d" in lower and "m" in lower else [lower[0], lower[1]]
    x_idx, y_idx = lower.index(parts[0]), lower.index(parts[1])
    return x_idx, y_idx, labels[x_idx], labels[y_idx]


def _axis_range(values: np.ndarray, pad_frac: float = 0.15) -> Tuple[float, float]:
    lo, hi = float(np.nanmin(values)), float(np.nanmax(values))
    if not np.isfinite(lo) or not np.isfinite(hi):
        return (-1.0, 1.0)
    span = hi - lo
    if span <= 1e-9:
        span = max(abs(hi), 1.0)
    pad = span * pad_frac
    return (lo - pad, hi + pad)


def nearest_window_index(centers: Optional[np.ndarray], n_windows: int, time_idx: int) -> Optional[int]:
    if n_windows <= 0:
        return None
    if centers is None or len(centers) != n_windows:
        # No explicit centers: assume windows are indexed 1:1 with timepoints
        # (common near-dense case, see data_loader/README caveats).
        return int(np.clip(time_idx, 0, n_windows - 1))
    centers_arr = np.asarray(centers)
    pos = int(np.searchsorted(centers_arr, time_idx))
    candidates = [c for c in (pos - 1, pos, pos + 1) if 0 <= c < n_windows]
    if not candidates:
        return None
    best = min(candidates, key=lambda c: abs(int(centers_arr[c]) - time_idx))
    return best


def _local_velocity(coords_arr: np.ndarray, time_arr: np.ndarray, time_idx: int, axes: Tuple[int, int]) -> np.ndarray:
    """Central (or one-sided at the boundary) finite-difference velocity estimate."""
    n = coords_arr.shape[0]
    a, b = axes
    lo = max(time_idx - 1, 0)
    hi = min(time_idx + 1, n - 1)
    dt = time_arr[hi] - time_arr[lo]
    if not np.isfinite(dt) or abs(dt) < 1e-12:
        return np.zeros(2)
    delta = coords_arr[hi, [a, b]] - coords_arr[lo, [a, b]]
    return delta / dt


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="#666"),
    )
    fig.update_layout(
        template="plotly_white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig


def build_mnj_flow_figure(
    coords: Sequence[Sequence[float]],
    axis_names: Optional[Sequence[str]],
    time: Sequence[float],
    time_idx: int,
    trail_len: int,
    jacobian_3d: Optional[Dict],
    plane: str = "d-m",
) -> go.Figure:
    """Build the 2D "local flow field" MNJ figure for one frame.

    The background quiver is the local linearization of the flow around the
    current point, restricted to the 2x2 sub-block of the full 3x3 Jacobian
    for the chosen coordinate plane (off-plane coupling to the third axis is
    not shown - an intentional simplification for a 2D "intuitive
    visualization" slice, not a claim that the third axis is decoupled).
    """
    if not jacobian_3d or not jacobian_3d.get("j_hat"):
        return _empty_figure("No 3D Jacobian (MNJ) data available for this subject.")

    coords_arr = np.asarray(coords, dtype=float)
    time_arr = np.asarray(time, dtype=float)
    n_points = coords_arr.shape[0]
    time_idx = int(np.clip(time_idx, 0, max(n_points - 1, 0)))

    x_idx, y_idx, x_label, y_label = resolve_plane_indices(axis_names, plane)

    j_hat = np.asarray(jacobian_3d["j_hat"], dtype=float)  # (W, 3, 3)
    centers = jacobian_3d.get("centers")
    centers_arr = np.asarray(centers, dtype=int) if centers is not None else None
    win_idx = nearest_window_index(centers_arr, j_hat.shape[0], time_idx)
    if win_idx is None:
        return _empty_figure("No 3D Jacobian (MNJ) window resolved for this frame.")

    j_full = j_hat[win_idx]
    j_sub = j_full[np.ix_([x_idx, y_idx], [x_idx, y_idx])]

    anchor = coords_arr[time_idx, [x_idx, y_idx]]
    velocity = _local_velocity(coords_arr, time_arr, time_idx, (x_idx, y_idx))

    x_range = _axis_range(coords_arr[:, x_idx])
    y_range = _axis_range(coords_arr[:, y_idx])
    grid_x, grid_y = np.meshgrid(
        np.linspace(x_range[0], x_range[1], GRID_SIZE),
        np.linspace(y_range[0], y_range[1], GRID_SIZE),
    )
    offsets = np.stack([grid_x.ravel() - anchor[0], grid_y.ravel() - anchor[1]], axis=-1)
    flow = offsets @ j_sub.T + velocity  # f(x) = J_sub (x - anchor) + v_anchor

    fig = create_quiver(
        grid_x.ravel(),
        grid_y.ravel(),
        flow[:, 0],
        flow[:, 1],
        scale=0.22,
        arrow_scale=0.35,
        line=dict(color=QUIVER_COLOR, width=1.5),
        name="local flow field",
    )
    fig.data[0].hoverinfo = "skip"
    fig.data[0].showlegend = False

    fig.add_trace(
        go.Scatter(
            x=coords_arr[:, x_idx],
            y=coords_arr[:, y_idx],
            mode="lines",
            line=dict(color="rgba(120,120,120,0.2)", width=1.5),
            hoverinfo="skip",
            showlegend=False,
            name="full session",
        )
    )

    trail_len = max(2, int(trail_len))
    start = max(0, time_idx - trail_len + 1)
    trail_idxs = np.arange(start, time_idx + 1)
    n_trail = len(trail_idxs)
    n_segments = int(min(MAX_TRAIL_SEGMENTS, max(n_trail - 1, 1)))
    if n_trail >= 2:
        edges = np.unique(np.round(np.linspace(0, n_trail - 1, n_segments + 1)).astype(int))
        for seg_i in range(len(edges) - 1):
            lo, hi = edges[seg_i], edges[seg_i + 1]
            if hi <= lo:
                continue
            seg = trail_idxs[lo : hi + 1]
            recency = (seg_i + 1) / max(len(edges) - 1, 1)
            color = sample_colorscale(TRAIL_COLORSCALE, [recency])[0]
            fig.add_trace(
                go.Scatter(
                    x=coords_arr[seg, x_idx],
                    y=coords_arr[seg, y_idx],
                    mode="lines+markers",
                    line=dict(color=color, width=4),
                    marker=dict(color=color, size=4),
                    opacity=float(np.clip(0.15 + 0.8 * recency, 0.05, 1.0)),
                    hoverinfo="skip",
                    showlegend=False,
                    name="trail",
                )
            )

    fig.add_trace(
        go.Scatter(
            x=[coords_arr[time_idx, x_idx]],
            y=[coords_arr[time_idx, y_idx]],
            mode="markers",
            marker=dict(color=CURRENT_POINT_COLOR, size=11, line=dict(color="white", width=1)),
            name="current",
            showlegend=False,
            hovertemplate=(
                f"t={time_arr[time_idx]:.2f}s<br>{x_label}={anchor[0]:.3f}<br>{y_label}={anchor[1]:.3f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        template="plotly_white",
        xaxis=dict(title=x_label, range=list(x_range), constrain="domain"),
        # `constrain="domain"` (rather than the default "range") keeps our
        # explicit data ranges intact and instead letterboxes the plotting
        # area to preserve a 1:1 aspect ratio. Without it, Plotly silently
        # *expands* whichever axis's range is needed to match the graph
        # container's pixel aspect ratio, which - for a wide/short container -
        # blew the x-range out from ~[-1, 5] to ~[-5, 10], squeezing the
        # entire trajectory/flow field into a thin sliver (looked like "just
        # a gray scribble, nothing else visible").
        yaxis=dict(title=y_label, range=list(y_range), scaleanchor="x", scaleratio=1, constrain="domain"),
        margin=dict(l=0, r=0, t=30, b=0),
        uirevision=f"mnj-flow-{plane}",
        showlegend=False,
    )
    return fig


def build_mnj_timeseries_figure(
    time: Sequence[float],
    jacobian_3d: Optional[Dict],
    time_idx: int,
) -> go.Figure:
    """Small session-long time series of ||J||_F, ||S||_F, ||Omega||_F.

    Lets the user see whether "now" is a locally high- or low-deformation /
    rotation-dominated moment relative to the rest of the session.
    """
    if not jacobian_3d or not jacobian_3d.get("j_hat"):
        return _empty_figure("No 3D Jacobian (MNJ) data available for this subject.")

    time_arr = np.asarray(time, dtype=float)
    n_points = time_arr.shape[0]
    time_idx = int(np.clip(time_idx, 0, max(n_points - 1, 0)))

    centers = jacobian_3d.get("centers")
    j_hat = jacobian_3d.get("j_hat") or []
    n_windows = len(j_hat)
    if centers is not None and len(centers) == n_windows:
        jac_time = time_arr[np.clip(np.asarray(centers, dtype=int), 0, n_points - 1)]
    else:
        jac_time = time_arr[:n_windows]

    fro_norm = np.asarray(jacobian_3d.get("fro_norm") or [])
    stretch_norm = np.asarray(jacobian_3d.get("stretch_norm") or [])
    rotation_norm = np.asarray(jacobian_3d.get("rotation_norm") or [])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=jac_time, y=fro_norm, mode="lines", name="||J||_F", line=dict(color="#333333", width=2)))
    fig.add_trace(
        go.Scatter(x=jac_time, y=stretch_norm, mode="lines", name="||S||_F (stretch)", line=dict(color="#4363d8", width=1.5))
    )
    fig.add_trace(
        go.Scatter(x=jac_time, y=rotation_norm, mode="lines", name="||Omega||_F (rotation)", line=dict(color="#f58231", width=1.5))
    )
    fig.add_vline(x=float(time_arr[time_idx]), line=dict(color=CURRENT_POINT_COLOR, width=2, dash="dash"))

    fig.update_layout(
        template="plotly_white",
        xaxis=dict(title="time (s)"),
        yaxis=dict(title="Frobenius norm"),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        uirevision="mnj-timeseries",
        height=200,
    )
    return fig
