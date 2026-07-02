"""Plotly figure builders for the interactive MNPS explorer.

All functions here take plain numpy arrays / lists (not the `SubjectData`
dataclass) so they can be called directly from Dash callbacks, whose inputs
come back from `dcc.Store` as JSON-decoded lists.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

MAX_TRAIL_SEGMENTS = 60
CURRENT_POINT_COLOR = "#e6194B"
CONTEXT_COLOR = "rgba(120,120,120,0.25)"
TRAIL_COLORSCALE = "Plasma"
STAGE_PALETTE = [
    "#4363d8", "#3cb44b", "#ffe119", "#f58231", "#911eb4",
    "#42d4f4", "#f032e6", "#bfef45", "#469990", "#9A6324",
    "#800000", "#808000", "#000075", "#e6194B",
]
UNLABELED_STAGE_COLOR = "#a9a9a9"

# Desired plot axis assignment: x=d, y=m, z=e (independent of the H5
# contract's canonical column order, which is [m, d, e]).
_DESIRED_PLOT_AXES = ("d", "m", "e")


def _axis_labels(axis_names: Optional[Sequence[str]]) -> List[str]:
    if axis_names and len(axis_names) >= 3:
        return list(axis_names[:3])
    return ["m", "d", "e"]


def _resolve_plot_axis_order(axis_names: Optional[Sequence[str]]) -> List[int]:
    """Map (x, y, z) plot axes to columns of `coords`, per `_DESIRED_PLOT_AXES`.

    Falls back to positional order [0, 1, 2] if the axis names don't contain
    the expected m/d/e labels (e.g. an unrecognized coordinate contract).
    """
    names_lower = [str(n).lower() for n in _axis_labels(axis_names)]
    order = []
    for desired in _DESIRED_PLOT_AXES:
        if desired in names_lower:
            order.append(names_lower.index(desired))
        else:
            return [0, 1, 2]
    return order


def _trail_index_range(time_idx: int, trail_len: int, n_points: int) -> np.ndarray:
    time_idx = int(np.clip(time_idx, 0, max(n_points - 1, 0)))
    trail_len = max(2, int(trail_len))
    start = max(0, time_idx - trail_len + 1)
    return np.arange(start, time_idx + 1)


def _bucket_segments(idxs: np.ndarray, max_segments: int = MAX_TRAIL_SEGMENTS) -> List[np.ndarray]:
    n = len(idxs)
    if n < 2:
        return []
    n_segments = int(min(max_segments, n - 1))
    edges = np.unique(np.round(np.linspace(0, n - 1, n_segments + 1)).astype(int))
    segments = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if hi > lo:
            segments.append(idxs[lo : hi + 1])
    return segments


def _stage_color_map(stage_labels: Optional[Dict[str, str]]) -> Dict[int, str]:
    if not stage_labels:
        return {}
    codes = sorted(int(c) for c in stage_labels.keys() if int(c) != -1)
    return {code: STAGE_PALETTE[i % len(STAGE_PALETTE)] for i, code in enumerate(codes)}


def _axis_range(values: np.ndarray, pad_frac: float = 0.08) -> List[float]:
    lo, hi = float(np.nanmin(values)), float(np.nanmax(values))
    if not np.isfinite(lo) or not np.isfinite(hi):
        return [-1.0, 1.0]
    span = hi - lo
    if span <= 1e-9:
        span = max(abs(hi), 1.0)
    pad = span * pad_frac
    return [lo - pad, hi + pad]


def build_trajectory_figure_3d(
    coords: Sequence[Sequence[float]],
    axis_names: Optional[Sequence[str]],
    time: Sequence[float],
    time_idx: int,
    trail_len: int,
    color_by: str = "time",
    stage_codes: Optional[Sequence[int]] = None,
    stage_labels: Optional[Dict[str, str]] = None,
) -> go.Figure:
    """Build the 3D "time travel" MNPS trajectory figure for one frame.

    - Full-session trajectory is drawn faint/translucent for spatial context.
    - The trailing window (last `trail_len` points up to `time_idx`) is drawn
      as a fading "comet trail", colored either by recency (`color_by="time"`)
      or by stage/event label (`color_by="stage"`).
    - The current point is highlighted with a larger marker.
    """
    coords_arr = np.asarray(coords, dtype=float)
    time_arr = np.asarray(time, dtype=float)
    n_points = coords_arr.shape[0]
    labels = _axis_labels(axis_names)
    time_idx = int(np.clip(time_idx, 0, max(n_points - 1, 0)))

    plot_order = _resolve_plot_axis_order(axis_names)
    plot_coords = coords_arr[:, plot_order]
    plot_labels = [labels[i] for i in plot_order]

    stage_arr = np.asarray(stage_codes, dtype=int) if stage_codes is not None else None
    use_stage_color = bool(color_by == "stage" and stage_arr is not None and stage_labels)
    stage_colors = _stage_color_map(stage_labels) if use_stage_color else {}

    fig = go.Figure()

    fig.add_trace(
        go.Scatter3d(
            x=plot_coords[:, 0],
            y=plot_coords[:, 1],
            z=plot_coords[:, 2],
            mode="lines",
            line=dict(color=CONTEXT_COLOR, width=2),
            hoverinfo="skip",
            showlegend=False,
            name="full session",
        )
    )

    trail_idxs = _trail_index_range(time_idx, trail_len, n_points)
    segments = _bucket_segments(trail_idxs)
    n_segments = max(len(segments), 1)
    seen_stage_legend: set[int] = set()

    for seg_i, seg in enumerate(segments):
        recency = (seg_i + 1) / n_segments  # 0 (oldest) -> 1 (newest)
        opacity = 0.12 + 0.85 * recency

        if use_stage_color:
            end_code = int(stage_arr[seg[-1]])
            color = stage_colors.get(end_code, UNLABELED_STAGE_COLOR)
            label = (stage_labels or {}).get(str(end_code), f"code_{end_code}")
            show_legend = end_code not in seen_stage_legend
            seen_stage_legend.add(end_code)
        else:
            color = sample_colorscale(TRAIL_COLORSCALE, [recency])[0]
            label = "trail"
            show_legend = False

        fig.add_trace(
            go.Scatter3d(
                x=plot_coords[seg, 0],
                y=plot_coords[seg, 1],
                z=plot_coords[seg, 2],
                mode="lines+markers",
                line=dict(color=color, width=6),
                marker=dict(color=color, size=2.5),
                opacity=float(np.clip(opacity, 0.05, 1.0)),
                name=label,
                showlegend=show_legend,
                legendgroup=f"stage-{label}",
                hoverinfo="skip",
            )
        )

    current_hover = f"t={time_arr[time_idx]:.2f}s<br>{labels[0]}={coords_arr[time_idx,0]:.3f}<br>{labels[1]}={coords_arr[time_idx,1]:.3f}<br>{labels[2]}={coords_arr[time_idx,2]:.3f}"
    if use_stage_color:
        end_code = int(stage_arr[time_idx])
        current_hover += f"<br>stage={(stage_labels or {}).get(str(end_code), f'code_{end_code}')}"

    fig.add_trace(
        go.Scatter3d(
            x=[plot_coords[time_idx, 0]],
            y=[plot_coords[time_idx, 1]],
            z=[plot_coords[time_idx, 2]],
            mode="markers",
            marker=dict(color=CURRENT_POINT_COLOR, size=8, line=dict(color="white", width=1)),
            name="current",
            showlegend=False,
            hovertemplate=current_hover + "<extra></extra>",
        )
    )

    fig.update_layout(
        template="plotly_white",
        scene=dict(
            xaxis=dict(title=plot_labels[0], range=_axis_range(plot_coords[:, 0])),
            yaxis=dict(title=plot_labels[1], range=_axis_range(plot_coords[:, 1])),
            zaxis=dict(title=plot_labels[2], range=_axis_range(plot_coords[:, 2])),
            aspectmode="cube",
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        uirevision="mnps-trajectory-3d",
        legend=dict(itemsizing="constant"),
        showlegend=use_stage_color,
    )
    return fig
