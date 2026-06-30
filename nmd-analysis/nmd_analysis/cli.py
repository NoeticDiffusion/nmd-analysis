from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .analysis_pipeline import run_cleaned_analysis_pipeline
from .pipeline import run_dataset_pipeline
from .spindle_event_locked import (
    SpindleEventConfig,
    run_spindle_event_locked,
    write_spindle_outputs,
)

app = typer.Typer(help="NDT analysis pipeline (Parquet-first).")


@app.command("run")
def run(
    config: Path = typer.Option(..., "--config", exists=True, file_okay=True, dir_okay=False),
    input_root: Optional[Path] = typer.Option(None, "--input-root"),
    output_root: Optional[Path] = typer.Option(None, "--output-root"),
    workers: Optional[int] = typer.Option(
        None,
        "--workers",
        min=1,
        help="Number of worker processes (default: config.runtime.workers or cpu_count-1).",
    ),
    analyses: Optional[str] = typer.Option(
        None,
        "--analyses",
        help="Comma-separated analysis types to run (default: all enabled in YAML).",
    ),
) -> None:
    """Run dataset analysis pipeline from YAML config."""
    selected = None
    if analyses:
        selected = [part.strip() for part in analyses.split(",") if part.strip()]
    result = run_dataset_pipeline(
        config_path=config,
        input_root=input_root,
        output_root=output_root,
        analyses_filter=selected,
        workers=workers,
    )
    typer.echo(json.dumps(result, indent=2))


@app.command("analyze")
def analyze(
    config: Path = typer.Option(..., "--config", exists=True, file_okay=True, dir_okay=False),
    cleaned_root: Optional[Path] = typer.Option(None, "--cleaned-root"),
    output_root: Optional[Path] = typer.Option(None, "--output-root"),
    analyses: Optional[str] = typer.Option(
        None,
        "--analyses",
        help="Comma-separated analysis blocks to include from cleaned parquet files.",
    ),
    contrasts: Optional[str] = typer.Option(
        None,
        "--contrasts",
        help="Comma-separated contrast names to run from the analysis YAML.",
    ),
) -> None:
    """Run cleaned -> analysis MVP pipeline from YAML config."""
    selected_analyses = None
    if analyses:
        selected_analyses = [part.strip() for part in analyses.split(",") if part.strip()]
    selected_contrasts = None
    if contrasts:
        selected_contrasts = [part.strip() for part in contrasts.split(",") if part.strip()]
    result = run_cleaned_analysis_pipeline(
        config_path=config,
        cleaned_root=cleaned_root,
        output_root=output_root,
        blocks_filter=selected_analyses,
        contrasts_filter=selected_contrasts,
    )
    typer.echo(json.dumps(result, indent=2))


@app.command("spindle-events")
def spindle_events(
    event_root: Path = typer.Option(..., "--event-root", exists=True, file_okay=False, dir_okay=True),
    output_root: Path = typer.Option(..., "--output-root", file_okay=False, dir_okay=True),
    channel: str = typer.Option("psg_c3", "--channel", help="Event parquet channel suffix, e.g. psg_c3."),
    condition: str = typer.Option("spindle_event", "--condition"),
    baseline_bin: str = typer.Option("pre_far", "--baseline-bin"),
    min_subjects: int = typer.Option(3, "--min-subjects", min=2),
) -> None:
    """Run spindle event-locked baseline-delta analysis from event parquet exports."""
    cfg = SpindleEventConfig(
        event_root=event_root,
        channel=channel,
        condition=condition,
        baseline_bin=baseline_bin,
        min_subjects=min_subjects,
    )
    outputs = run_spindle_event_locked(cfg)
    written = write_spindle_outputs(outputs, output_root, channel=channel)
    result = {
        "channel": channel,
        "condition": condition,
        "baseline_bin": baseline_bin,
        "n_event_windows": int(len(outputs["event_windows"])),
        "n_subject_delta_rows": int(len(outputs["subject_deltas"])),
        "written_files": written,
    }
    typer.echo(json.dumps(result, indent=2))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
