# Interactive MNPS / MNJ Explorer

A Plotly/Dash app for "time-traveling" through a single subject's H5 file:

- **MNPS 3D trajectory tab**: scrub/play through the Meta-Noetic Phase Space
  (MNPS) trajectory in 3D, colored by recency or by stage/event label.
- **MNJ (local Jacobian) tab**: a 2D "local flow field" slice (data-driven
  version of `Jacobian_frobenius_norm.png`) built from the real per-window
  Meta-Noetic Jacobian (`jacobian_3d.j_hat`), plus a session-long time series
  of `||J||_F` / stretch / rotation norms and a numeric readout of the
  canonical decomposition (`S`, `Omega`) and invariants (`tr(J)`, eigenvalues)
  at the current time.

Both tabs share the same time slider / play controls, so scrubbing or playing
moves both views together.

This is **Steps 1 and 3 (3D-only)** of a larger plan (see
`c:/Users/Robin/.cursor/plans/interactive_mnps_mnj_viewer_b21bb4d2.plan.md`):

1. **MNPS 3D time-travel, subject-level** - implemented here (`figures.py`).
2. MNPS 9D as three synced 3D boxes (`m_a/m_e/m_o`, `d_n/d_l/d_s`, `e_e/e_s/e_m`) - not yet implemented.
3. Interactive MNJ / reachability views (data-driven versions of the
   conceptual figures in `articles/CLINICAL/comatose_ndt/figures/conceptual_figures/`).
   The **MNJ flow-field part is implemented here** (`figures_mnj.py`); the
   reachability-cone part is not yet implemented.
4. Cohort/group-level overlays (later, more code).

No code outside this folder is modified. The H5 contract and reachability
math are reused read-only from `ndt_analysis.h5_contract` /
`ndt_analysis.reachability_core` via `_vendor_path.py`, which just adds the
`ndt-analysis/` package root to `sys.path` at runtime.

## Setup

From this folder (`ndt-analysis/interactive/`), using the repo's existing
Python environment (which already has `numpy`, `h5py`, `pandas` etc. from
`ndt-analysis/pyproject.toml`):

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
# or, to prefill a different default data folder:
python app.py --root "J:/path/to/some/h5/folder" --port 8050
```

Then open the printed URL (default `http://127.0.0.1:8050`) in a browser.

Run `app.py` directly (not via `python -m ...`) - the lightweight sibling
imports (`data_loader`, `figures`, `_vendor_path`) rely on Python
automatically putting this folder on `sys.path` when the script is launched
directly.

## Using the app

1. Type/edit the **data root folder** in the sidebar and click **Scan**.
   This does a plain recursive filesystem walk for `*.h5` files (no files
   are opened yet), grouped by their top-level subfolder as "dataset".
   Pointing at a very large folder (e.g. a broad `data/raw/`) may take a
   while to walk; pointing at a single dataset export folder is fast.
2. Pick a **dataset** and then a **subject / file**. Only the chosen file is
   actually opened and read.
3. Use the **time slider** to scrub, or **Play** to animate. **Playback
   speed** controls steps/second; **trail length** controls how many past
   points remain visible (fading out with distance from "now").
4. **Color trail by** switches between coloring by recency (a Plasma
   gradient along the fading trail) and coloring by stage/event label (built
   from `event_windows` + `codebooks/stage` when present in the file; falls
   back gracefully with a status note when absent).
5. Switch to the **MNJ (local Jacobian)** tab to see the local flow-field
   slice around the current point. **MNJ plane (2D slice)** picks which two
   of the three MNPS axes (`m`, `d`, `e`) are shown; the background arrows
   are the local linearization `f(x) ~= J_sub (x - anchor) + v_anchor` of the
   real, per-window MNJ estimate restricted to that plane (off-plane
   coupling to the third axis is not shown - an intentional simplification,
   see caveat below). The small time series below it shows `||J||_F`
   (deformation), `||S||_F` (stretch) and `||Omega||_F` (rotation) for the
   whole session, with a dashed marker at "now".

## Files

- `_vendor_path.py` - adds `ndt-analysis/` to `sys.path` (read-only reuse of `ndt_analysis`).
- `data_loader.py` - H5 discovery (`discover_h5_files`, `group_by_dataset`) and
  loading (`SubjectData`, `load_subject`, `load_subject_cached`). Already
  resolves `coords_9d`, `jacobian_3d`, `jacobian_9d` and the 9D geometry-gate
  status for reuse in Steps 2-3, even though the current UI only drives the
  3D trajectory view.
- `figures.py` - `build_trajectory_figure_3d(...)`, a pure-array Plotly figure
  builder (safe to call with plain lists decoded from a Dash `dcc.Store`).
- `figures_mnj.py` - `build_mnj_flow_figure(...)` / `build_mnj_timeseries_figure(...)`,
  the MNJ tab's figure builders, plus small helpers (`resolve_plane_indices`,
  `nearest_window_index`) shared with `app.py`'s readout text.
- `app.py` - the Dash layout (with `dcc.Tabs` for the two views) and callbacks.

## Known data caveats

- `jacobian_9D_*` layers are frequently heavily "gated" (most windows marked
  invalid due to ill-conditioning) - e.g. in the bundled `ds003474` test file,
  only 2 of 175 windows are valid. `SubjectData` surfaces
  `jacobian_9d_status` / `jacobian_9d_windows_retained` /
  `jacobian_9d_invalid_windows` for a future 9D view to show an honest
  "insufficient data" state per file instead of a misleading sparse plot.
  The current MNJ tab only uses `jacobian_3d`, which is dense in the bundled
  test file (175/177 windows).
- The MNJ flow-field plot linearizes around the *current point* using only
  the 2x2 sub-block of the full 3x3 Jacobian for the selected plane; this
  ignores coupling to the third (hidden) axis. It is an intentional 2D
  "intuitive visualization" simplification (matching the conceptual PNGs),
  not a claim that the third axis is dynamically decoupled - treat it as a
  plausible-interpretation visual aid, not a rigorous reduced-order model.
