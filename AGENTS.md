# nmd-analysis agent guidance

This repository develops downstream analysis and empirical tests of NDT using
versioned neural measurements. Work from the actual checkout. The older
`.cursor/rules/role.mdc` and `.vscode/rules/role.mdc` are background, not extra
gate or reporting checklists; current user instructions take precedence.

## Scientific boundary

NeuralManifoldDynamics ingest defines the measurement contract. This repository
selects scientific estimands and statistical methods, tests contrasts and nulls,
and evaluates interpretation. Do not change an ingest definition, validity rule,
window, or estimator because a condition contrast improves. Develop alternative
methods explicitly and compare them as methods before using them for inference.

Treat MNPS coordinates, local Jacobians, regional outputs, and reachability as
operational measurements. They do not directly identify latent neural variables,
biophysical Jacobians, anatomical networks, controllability, or experience.
Preserve input versions, coordinate order, time base, gap and support flags,
missingness, and provenance. Exclude or label unsupported observations; never
convert them silently to zeros or count them as valid evidence.

## Development loop

1. Check `git status`, then inspect the relevant code, configs, tests, input
   schema, and downstream use. Preserve unrelated edits and existing results.
2. State the analysis question and unit of inference. Separate a code fix, a
   numerical method change, and a change to the scientific estimand. Implement
   the smallest coherent step and iterate in code.
3. Run focused tests. For an analysis claim, check input eligibility, leakage,
   a credible simpler baseline or null, uncertainty, and relevant sensitivity
   to support, gaps, subjects, and datasets. Use a bounded real-data check when
   it resolves a concrete uncertainty; a passing unit test does not validate a
   biological claim.
4. For paper-facing results, keep the input version, config, command, statistical
   unit, exclusions, and output tables reproducible. Check that the claim follows
   the effect size and uncertainty, including negative and inconclusive results.

Choose controls and validation depth for the claim at hand. Distinguish
exploratory from confirmatory results, and avoid promoting a selected endpoint
or nominal significance to a replicated finding. New analysis families can be
built experimentally without a fixed stage sequence.

Use an independent reviewer for broad or claim-changing work when a separate
check would catch meaningful risk, or when the user asks. Review is not required
after every iteration. Delegate non-overlapping work when useful.

## Reporting

For routine work, report the change, tests or analysis run, result, and remaining
limits in the final response. Record consequential method decisions and negative
evidence in the relevant code, docs, or a concise `project/diary/` entry. There
is no mandatory diary, gate sequence, or verdict template per iteration.
