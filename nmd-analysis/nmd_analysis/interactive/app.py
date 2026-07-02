"""Interactive Dash app: MNPS 3D "time travel" trajectory explorer.

Run with:

    python app.py
    python app.py --root "J:/path/to/some/h5/folder" --port 8050

Then open the printed URL in a browser. Use the sidebar to point at any
folder containing NDT-contract H5 files (see `../ndt_analysis/h5_contract.py`
for the expected layout), pick a dataset/subject, and scrub or play through
its MNPS 3D trajectory (tab 1) or its local MNJ flow-field geometry (tab 2).

This covers Steps 1 and 3 (3D-only) of the interactive MNPS/MNJ explorer
(see `c:/Users/Robin/.cursor/plans/interactive_mnps_mnj_viewer_b21bb4d2.plan.md`):

1. MNPS 3D time-travel, subject-level - `figures.py`.
3. Interactive MNJ view (2D flow-field slice of the local Jacobian, data-driven
   version of `Jacobian_frobenius_norm.png`) - `figures_mnj.py`.

Step 2 (9D as three synced 3D boxes) and the reachability-cone part of Step 3
are not yet implemented.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, no_update
from dash.exceptions import PreventUpdate

from data_loader import discover_h5_files, group_by_dataset, load_subject_cached
from figures import build_trajectory_figure_3d
from figures_mnj import (
    PLANE_OPTIONS,
    build_mnj_flow_figure,
    build_mnj_timeseries_figure,
    nearest_window_index,
    resolve_plane_indices,
)

_APP_DIR = Path(__file__).resolve().parent
_NDT_ANALYSIS_ROOT = _APP_DIR.parent
_REPO_ROOT = _NDT_ANALYSIS_ROOT.parent
_DEFAULT_ROOT = _REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003474_20260609_044822"

_MIN_INTERVAL_MS = 1000 / 30
_MAX_INTERVAL_MS = 1000 / 1


def _speed_to_interval_ms(steps_per_sec: float) -> float:
    steps_per_sec = max(1.0, min(30.0, float(steps_per_sec)))
    return float(min(_MAX_INTERVAL_MS, max(_MIN_INTERVAL_MS, 1000.0 / steps_per_sec)))


def _dataset_options(groups: Dict[str, List[Path]]) -> List[Dict[str, Any]]:
    return [
        {"label": f"{name} ({len(paths)} files)", "value": name}
        for name, paths in sorted(groups.items())
    ]


def _subject_options(paths: List[Path]) -> List[Dict[str, Any]]:
    return [{"label": p.stem, "value": str(p)} for p in paths]


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


def _time_slider_marks(time_values: List[float], n_points: int) -> Dict[int, str]:
    if n_points <= 1:
        return {0: "0s"}
    marks_at = sorted({0, n_points // 4, n_points // 2, (3 * n_points) // 4, n_points - 1})
    return {int(i): f"{time_values[i]:.0f}s" for i in marks_at}


app = Dash(__name__, title="Noetic Atlas - Interactive MNPS Explorer")

app.layout = html.Div(
    style={"display": "flex", "fontFamily": "Segoe UI, Arial, sans-serif", "height": "100vh"},
    children=[
        dcc.Store(id="entries-store"),
        dcc.Store(id="subject-data-store"),
        html.Div(
            style={
                "width": "320px",
                "padding": "16px",
                "borderRight": "1px solid #ddd",
                "overflowY": "auto",
                "boxSizing": "border-box",
            },
            children=[
                html.H3("MNPS Explorer"),
                html.P(
                    "MNPS 3D time-travel trajectory + MNJ local flow-field viewer.",
                    style={"color": "#666", "fontSize": "13px"},
                ),
                html.Label("Data root folder", style={"fontWeight": "bold"}),
                dcc.Input(
                    id="root-path-input",
                    value=str(_DEFAULT_ROOT),
                    type="text",
                    style={"width": "100%", "marginBottom": "6px"},
                ),
                html.Button("Scan", id="scan-button", n_clicks=0, style={"width": "100%"}),
                html.Div(id="scan-status", style={"fontSize": "12px", "color": "#666", "marginTop": "6px"}),
                html.Hr(),
                html.Label("Dataset", style={"fontWeight": "bold"}),
                dcc.Dropdown(id="dataset-dropdown", options=[], value=None),
                html.Label("Subject / file", style={"fontWeight": "bold", "marginTop": "10px"}),
                dcc.Dropdown(id="subject-dropdown", options=[], value=None),
                html.Div(id="load-status", style={"fontSize": "12px", "color": "#a33", "marginTop": "6px"}),
                html.Hr(),
                html.Label("Color trail by", style={"fontWeight": "bold"}),
                dcc.RadioItems(
                    id="color-by-radio",
                    options=[
                        {"label": " Recency (time)", "value": "time"},
                        {"label": " Stage / event", "value": "stage"},
                    ],
                    value="time",
                    labelStyle={"display": "block"},
                ),
                html.Label("MNJ plane (2D slice)", style={"fontWeight": "bold", "marginTop": "10px"}),
                dcc.Dropdown(id="mnj-plane-dropdown", options=PLANE_OPTIONS, value="d-m", clearable=False),
                html.Label("Trail length (points)", style={"fontWeight": "bold", "marginTop": "10px"}),
                dcc.Slider(id="trail-len-slider", min=5, max=300, step=5, value=60, marks=None,
                           tooltip={"placement": "bottom", "always_visible": False}),
                html.Label("Playback speed (steps/sec)", style={"fontWeight": "bold", "marginTop": "10px"}),
                dcc.Slider(id="speed-slider", min=1, max=30, step=1, value=8, marks=None,
                           tooltip={"placement": "bottom", "always_visible": False}),
                html.Div(
                    style={"marginTop": "10px", "display": "flex", "gap": "8px"},
                    children=[
                        html.Button("Play", id="play-button", n_clicks=0, style={"flex": "1"}),
                    ],
                ),
                html.Hr(),
                html.Div(id="readout-div", style={"fontSize": "13px", "lineHeight": "1.6em"}),
            ],
        ),
        html.Div(
            style={"flex": "1", "padding": "16px", "boxSizing": "border-box", "display": "flex", "flexDirection": "column"},
            children=[
                dcc.Tabs(
                    id="main-tabs",
                    value="mnps",
                    children=[
                        dcc.Tab(
                            label="MNPS 3D trajectory",
                            value="mnps",
                            children=[
                                dcc.Graph(
                                    id="trajectory-graph",
                                    style={"height": "560px"},
                                    figure=_empty_figure("Scan a folder and pick a subject to begin."),
                                ),
                            ],
                        ),
                        dcc.Tab(
                            label="MNJ (local Jacobian)",
                            value="mnj",
                            children=[
                                html.Div(
                                    id="mnj-readout-div",
                                    style={"fontSize": "13px", "lineHeight": "1.6em", "margin": "10px 0"},
                                ),
                                dcc.Graph(
                                    id="mnj-flow-graph",
                                    style={"height": "380px"},
                                    figure=_empty_figure("Scan a folder and pick a subject to begin."),
                                ),
                                dcc.Graph(
                                    id="mnj-timeseries-graph",
                                    style={"height": "200px"},
                                    figure=_empty_figure(""),
                                ),
                            ],
                        ),
                    ],
                ),
                dcc.Slider(id="time-slider", min=0, max=0, step=1, value=0, marks={0: "0s"}),
                dcc.Interval(id="playback-interval", interval=_speed_to_interval_ms(8), n_intervals=0, disabled=True),
            ],
        ),
    ],
)


@app.callback(
    Output("entries-store", "data"),
    Output("dataset-dropdown", "options"),
    Output("dataset-dropdown", "value"),
    Output("scan-status", "children"),
    Input("scan-button", "n_clicks"),
    State("root-path-input", "value"),
)
def scan_root(_n_clicks: int, root_path: Optional[str]):
    if not root_path:
        raise PreventUpdate
    root = Path(root_path)
    files = discover_h5_files(root)
    if not files:
        return {}, [], None, f"No .h5 files found under: {root}"
    groups = group_by_dataset(root, files)
    entries_data = {name: [str(p) for p in paths] for name, paths in groups.items()}
    options = _dataset_options(groups)
    default_dataset = options[0]["value"] if options else None
    status = f"Found {len(files)} H5 file(s) across {len(groups)} dataset folder(s)."
    return entries_data, options, default_dataset, status


@app.callback(
    Output("subject-dropdown", "options"),
    Output("subject-dropdown", "value"),
    Input("dataset-dropdown", "value"),
    State("entries-store", "data"),
)
def update_subject_options(dataset_name: Optional[str], entries_data: Optional[Dict[str, List[str]]]):
    if not dataset_name or not entries_data:
        return [], None
    paths = [Path(p) for p in entries_data.get(dataset_name, [])]
    options = _subject_options(paths)
    default_value = options[0]["value"] if options else None
    return options, default_value


@app.callback(
    Output("subject-data-store", "data"),
    Output("time-slider", "min"),
    Output("time-slider", "max"),
    Output("time-slider", "value"),
    Output("time-slider", "marks"),
    Output("load-status", "children"),
    Input("subject-dropdown", "value"),
)
def load_subject_data(subject_path: Optional[str]):
    if not subject_path:
        return None, 0, 0, 0, {0: "0s"}, ""
    try:
        subject = load_subject_cached(Path(subject_path))
    except Exception as exc:  # noqa: BLE001
        return None, 0, 0, 0, {0: "0s"}, f"Failed to load {subject_path}: {exc}"
    store_dict = subject.to_store_dict()
    n_points = store_dict["n_points"]
    marks = _time_slider_marks(store_dict["time"], n_points)
    status = (
        f"Loaded {subject.subject_id} ({subject.dataset_id}), "
        f"{n_points} timepoints, contract={subject.coords_3d_contract}."
    )
    if not store_dict["stage_labels"] or set(store_dict["stage_labels"].keys()) == {"-1"}:
        status += " No stage/event labels available for coloring."
    return store_dict, 0, max(n_points - 1, 0), 0, marks, status


@app.callback(
    Output("trajectory-graph", "figure"),
    Output("readout-div", "children"),
    Input("time-slider", "value"),
    Input("trail-len-slider", "value"),
    Input("color-by-radio", "value"),
    Input("main-tabs", "value"),
    State("subject-data-store", "data"),
)
def update_graph(
    time_idx: Optional[int],
    trail_len: int,
    color_by: str,
    active_tab: str,
    subject_data: Optional[Dict[str, Any]],
):
    # Only rebuild the (heavier) figure that is actually visible right now -
    # the other tab's callback does the same in reverse. This keeps exactly
    # one server round-trip of real work per animation frame.
    if active_tab != "mnps":
        raise PreventUpdate
    if not subject_data:
        return _empty_figure("Scan a folder and pick a subject to begin."), ""
    time_idx = int(time_idx or 0)
    fig = build_trajectory_figure_3d(
        coords=subject_data["coords_3d"],
        axis_names=subject_data["coords_3d_names"],
        time=subject_data["time"],
        time_idx=time_idx,
        trail_len=trail_len,
        color_by=color_by,
        stage_codes=subject_data.get("stage_codes"),
        stage_labels=subject_data.get("stage_labels"),
    )
    names = subject_data["coords_3d_names"]
    coords = subject_data["coords_3d"]
    t_val = subject_data["time"][time_idx]
    point = coords[time_idx]
    readout_lines = [
        html.Div(f"Subject: {subject_data['subject_id']}  ({subject_data['dataset_id']})"),
        html.Div(f"t = {t_val:.2f} s   (index {time_idx}/{subject_data['n_points'] - 1})"),
        html.Div(f"{names[0]} = {point[0]:.3f}"),
        html.Div(f"{names[1]} = {point[1]:.3f}"),
        html.Div(f"{names[2]} = {point[2]:.3f}"),
    ]
    stage_labels = subject_data.get("stage_labels") or {}
    stage_codes = subject_data.get("stage_codes")
    if color_by == "stage" and stage_codes is not None:
        code = str(int(stage_codes[time_idx]))
        readout_lines.append(html.Div(f"stage = {stage_labels.get(code, code)}"))
    return fig, readout_lines


def _mnj_readout_lines(
    subject_data: Dict[str, Any],
    jacobian_3d: Optional[Dict[str, Any]],
    time_idx: int,
    plane: str,
) -> List[Any]:
    t_val = subject_data["time"][time_idx]
    lines: List[Any] = [
        html.Div(f"Subject: {subject_data['subject_id']}  ({subject_data['dataset_id']})"),
        html.Div(f"t = {t_val:.2f} s   (index {time_idx}/{subject_data['n_points'] - 1})"),
    ]
    if not jacobian_3d or not jacobian_3d.get("j_hat"):
        lines.append(html.Div("No 3D Jacobian (MNJ) data available for this subject.", style={"color": "#a33"}))
        return lines

    _, _, x_label, y_label = resolve_plane_indices(subject_data.get("coords_3d_names"), plane)
    centers = jacobian_3d.get("centers")
    centers_arr = None if centers is None else np.asarray(centers, dtype=int)
    win_idx = nearest_window_index(centers_arr, len(jacobian_3d["j_hat"]), time_idx)
    if win_idx is None:
        lines.append(html.Div("No 3D Jacobian (MNJ) window resolved for this frame.", style={"color": "#a33"}))
        return lines

    fro = jacobian_3d["fro_norm"][win_idx]
    stretch = jacobian_3d["stretch_norm"][win_idx]
    rotation = jacobian_3d["rotation_norm"][win_idx]
    divergence = jacobian_3d["divergence"][win_idx]
    eig_min = jacobian_3d["eig_real_min"][win_idx]
    eig_max = jacobian_3d["eig_real_max"][win_idx]
    eig_imag = jacobian_3d["eig_imag_abs_max"][win_idx]
    lines.extend(
        [
            html.Div(f"plane: {x_label} vs {y_label}"),
            html.Div(f"||J||_F = {fro:.3f}  (stretch ||S||_F = {stretch:.3f}, rotation ||\u03a9||_F = {rotation:.3f})"),
            html.Div(f"div(f) = tr(J) = {divergence:.3f}"),
            html.Div(f"eig(J) real range = [{eig_min:.3f}, {eig_max:.3f}]   max|imag| = {eig_imag:.3f}"),
        ]
    )
    return lines


@app.callback(
    Output("mnj-flow-graph", "figure"),
    Output("mnj-timeseries-graph", "figure"),
    Output("mnj-readout-div", "children"),
    Input("time-slider", "value"),
    Input("trail-len-slider", "value"),
    Input("mnj-plane-dropdown", "value"),
    Input("main-tabs", "value"),
    State("subject-data-store", "data"),
)
def update_mnj_view(
    time_idx: Optional[int],
    trail_len: int,
    plane: str,
    active_tab: str,
    subject_data: Optional[Dict[str, Any]],
):
    if active_tab != "mnj":
        raise PreventUpdate
    if not subject_data:
        placeholder = _empty_figure("Scan a folder and pick a subject to begin.")
        return placeholder, _empty_figure(""), ""
    time_idx = int(time_idx or 0)
    jacobian_3d = subject_data.get("jacobian_3d")
    flow_fig = build_mnj_flow_figure(
        coords=subject_data["coords_3d"],
        axis_names=subject_data["coords_3d_names"],
        time=subject_data["time"],
        time_idx=time_idx,
        trail_len=trail_len,
        jacobian_3d=jacobian_3d,
        plane=plane,
    )
    ts_fig = build_mnj_timeseries_figure(
        time=subject_data["time"],
        jacobian_3d=jacobian_3d,
        time_idx=time_idx,
    )
    readout = _mnj_readout_lines(subject_data, jacobian_3d, time_idx, plane)
    return flow_fig, ts_fig, readout


@app.callback(
    Output("playback-interval", "disabled", allow_duplicate=True),
    Output("play-button", "children", allow_duplicate=True),
    Output("time-slider", "value", allow_duplicate=True),
    Input("play-button", "n_clicks"),
    State("playback-interval", "disabled"),
    State("time-slider", "value"),
    State("subject-data-store", "data"),
    prevent_initial_call=True,
)
def toggle_playback(
    n_clicks: int,
    is_disabled: bool,
    current_value: Optional[int],
    subject_data: Optional[Dict[str, Any]],
):
    if not n_clicks:
        raise PreventUpdate
    now_disabled = not is_disabled
    # If (re)starting playback from the end of the trajectory, restart from
    # the beginning instead of doing nothing (advance_playback would
    # immediately stop again at the last index otherwise).
    if not now_disabled and subject_data:
        n_points = int(subject_data.get("n_points", 1))
        if int(current_value or 0) >= max(n_points - 1, 0):
            return now_disabled, "Pause", 0
    return now_disabled, ("Play" if now_disabled else "Pause"), no_update


@app.callback(
    Output("playback-interval", "interval"),
    Input("speed-slider", "value"),
)
def update_speed(steps_per_sec: float):
    return _speed_to_interval_ms(steps_per_sec)


# Advancing the time index on every `Interval` tick is done entirely in the
# browser (clientside), instead of a Python/server callback. Doing this
# server-side previously meant round-tripping the *entire* subject payload
# (coords, time, stage codes, ...) over HTTP on every single animation frame
# just to compute `+ 1`, on top of the (necessary) round-trip that rebuilds
# the figure. On the single-threaded dev server, those two round-trips per
# frame could queue up and fall behind at higher playback speeds, which is
# what caused the choppy/out-of-sync playback. The clientside version reuses
# the subject data already sitting in the browser's `dcc.Store` for free and
# leaves only the one round-trip that actually needs Python (rebuilding the
# 3D figure) per frame.
app.clientside_callback(
    """
    function(_n_intervals, current_value, subject_data) {
        if (!subject_data) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        var nPoints = subject_data.n_points || 1;
        var lastIndex = Math.max(nPoints - 1, 0);
        var nextValue = (current_value || 0) + 1;
        if (nextValue >= lastIndex) {
            // Reached the end of the trajectory: stop instead of looping back to 0.
            return [lastIndex, true, "Play"];
        }
        return [nextValue, window.dash_clientside.no_update, window.dash_clientside.no_update];
    }
    """,
    Output("time-slider", "value", allow_duplicate=True),
    Output("playback-interval", "disabled", allow_duplicate=True),
    Output("play-button", "children", allow_duplicate=True),
    Input("playback-interval", "n_intervals"),
    State("time-slider", "value"),
    State("subject-data-store", "data"),
    prevent_initial_call=True,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive MNPS 3D trajectory explorer.")
    parser.add_argument("--root", type=str, default=None, help="Default data root folder to prefill in the UI.")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.root:
        # layout.children = [entries-store, subject-data-store, sidebar, main panel]
        sidebar = app.layout.children[2]
        for component in sidebar.children:
            if getattr(component, "id", None) == "root-path-input":
                component.value = args.root
    # threaded=True lets the (dev) server handle overlapping requests, e.g. a
    # slider-driven figure rebuild while a scan/load request is still in
    # flight, instead of queueing them on a single thread - which is a major
    # source of choppy/out-of-sync playback at higher animation speeds.
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == "__main__":
    main()
