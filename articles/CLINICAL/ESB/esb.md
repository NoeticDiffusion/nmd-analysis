Implemented the architect’s recommendation as a Darwin auditability/control branch in the current scaffold, with no UI/corpus/offline-learning expansion and no runtime-shape mutation.

## Implemented

- Added an **audit trace layer** with retrieval-vs-authority diagnostics:
  - `src/spiralbase/demo/darwin/audit.py` (new)
  - `src/spiralbase/demo/darwin/schemas.py` (`DarwinRunTrace.audit`)
  - `src/spiralbase/demo/darwin/runtime.py` now records audit payload per run
- Extended authority control toggles for counterfactuals (defaults preserve current behavior):
  - `src/spiralbase/demo/darwin/authority.py`
  - supports retrieval-only path, weak-provenance relaxation, authority/year neutralization
- Added a **counterfactual runner**:
  - `scripts/run_darwin_demo_audit.py` (new)
  - arms: `retrieval_only`, `authority_enabled`, `allow_abstain_false`, `weak_provenance_allowed`, `authority_neutralized`, `year_neutralized`
- Added a broader **behavior pack** (18 questions) as audit sweep driver:
  - `src/spiralbase/demo/darwin/evaluation.py`
  - categories include direct answer, temporal authority, qualification, abstention/anachronism, source-type conflict, change-over-time
  - checks: behavior + expected source family + expected year window + legibility
- Updated exports:
  - `src/spiralbase/demo/darwin/__init__.py`
- Added diary note:
  - `Project/Diary/369_20260529_darwin_demo_auditability_sweep_branch.md`

Key runtime change:

```58:69:src/spiralbase/demo/darwin/runtime.py
    def answer_question(
        self,
        question: str,
        *,
        mode: str = "extractive",
        top_k: int | None = None,
        allow_abstain: bool = True,
        arbitration_mode: str = "authority",
        require_strong_provenance: bool = True,
        neutralize_authority: bool = False,
        neutralize_year: bool = False,
```

Audit payload shape now includes rankings, margins, pool composition, winner transition, and warning flags:

```132:177:src/spiralbase/demo/darwin/audit.py
    return {
        "control_mode": {
            "arbitration_mode": arbitration_mode,
            "allow_abstain": allow_abstain,
            "require_strong_provenance": require_strong_provenance,
            "neutralize_authority": neutralize_authority,
            "neutralize_year": neutralize_year,
        },
        "attribution": {
            "focus_operator": "lexical_retrieval",
            "route_operator": arbitration_mode,
            "bridge_operator": (
                "provenance_strength_filter"
                if require_strong_provenance
                else "provenance_filter_relaxed"
            ),
        },
        "retrieval_ranking": retrieval_rows,
        "authority_ranking": authority_rows,
        "winner_transition": {
            "retrieval_top_chunk_id": retrieval_top.get("chunk_id") if retrieval_top else None,
            ...
        },
        ...
        "warning_flags": warning_flags,
    }
```

Counterfactual runner entrypoint:

```34:41:scripts/run_darwin_demo_audit.py
    parser = argparse.ArgumentParser(description="Run Darwin demo auditability sweeps and counterfactual arms.")
    parser.add_argument(
        "--index-manifest",
        type=Path,
        default=ROOT / "experiments" / "outputs" / "darwin_demo" / "retrieval_index_manifest.json",
        help="Retrieval index manifest path.",
```

## Validation

Executed:

- `python scripts/run_darwin_demo_audit.py --run-pack`
- `python scripts/run_darwin_demo_audit.py --question-id darwin_pack_004_abstain_crispr --arms retrieval_only,authority_enabled,allow_abstain_false,weak_provenance_allowed,authority_neutralized,year_neutralized`
- `python scripts/run_darwin_demo_smoke.py`

Results:

- Behavior pack: `18 total`, `11 passed`, `7 failed`
  - behavior pass: `12`
  - source-family pass: `16`
  - year-window pass: `18`
  - output: `experiments/outputs/darwin_demo/audit_behavior_pack_results.json`
- Counterfactual output:
  - `experiments/outputs/darwin_demo/audit_counterfactual_results.json`
- Existing smoke remained stable: `4/4` pass

## Readout (branch-level)

- This now acts as a **causally legible audit rig** for commit-change analysis.
- Early signal from the behavior pack:
  - candidate inclusion looks relatively healthy (`16/18` source-family pass),
  - more failures are in **qualification/abstention behavior**, not year-window coverage.
- That suggests the next failure-focused branch is likely **authority/posterior control** rather than immediate candidate-construction expansion (unless you want to target the specific 2 source-family misses first).

If you want, I can take the 7 failing pack items and generate a strict file-by-file **next-branch DoD** split into:
1) candidate-construction fixes vs  
2) authority/posterior fixes, with expected trace deltas per fix.