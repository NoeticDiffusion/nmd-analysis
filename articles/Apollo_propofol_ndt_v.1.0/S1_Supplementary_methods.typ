// S1 Supplementary Methods — Apollo propofol occupancy secondary analysis.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - Apollo propofol occupancy",
  subtitle: "Measurement contract, occupancy scalar, matching rule, LOR labels, and statistical design",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.0 Dataset and measurement contract

Cambridge propofol sedation resting-state EEG, 20 healthy adults, four protocol phases each
@chennu2016propofol @chennu2016data. Source data DOI 10.17863/cam.68959. This article consumes a
frozen NeuralManifoldDynamics HDF5 export,
`neuralmanifolddynamics_Sedation-RestingState_20260918_075713` (80 files; pinned example
`sub-002_sedation_rest_run-003_acq-135.h5`, SHA-256
`1635513f690ae01807a9495d920052ddc2a2c9a568d3b8a76bb04139bca993ba`). Article `datainfo.mat` pin:
SHA-256 `ea8824f3ca9bd2eef0cdee3a7e1402dcc9e599f9688290cc382ae8e1a21f5608`. The article-local
`reproducibility_manifest.json` records repository base commit
`d1c7fcedfb92c34162437fe11cdb35aa64620018`, result-manifest hashes, and the limitation that the
collection manifest does not hash every raw H5 file; the current revision remains uncommitted.

Analyses should be read against the export's measurement contract, not as direct computations on
raw voltage traces. Exported `coords_3d_subject_anchored` uses local fit populations with ComBat
disabled; confirmatory amplitude claims on that chart remain gated. Occupancy does not use that
coordinate. It uses eight MNPS-used `features_raw` columns in a baseline-only robust-$z$ frame
constructed article-side.

Protocol phases come from `datainfo.mat` column 2 and are not inferred from `run`/`acq` order or
from H5 `condition=sedation`. Column 3 is plasma concentration ($mu$g/L), column 4 mean reaction
time (ms), column 5 $k$ correct / 40. The package alias `unresponsive` for protocol order 3 is
retained only as `datainfo_legacy_condition` and is not an LOR label.

= S1.1 Epoch structure and features

Feature windows are nominally 8 s with a 4 s step (`observed_dt` typically 4 s; occupancy
increments require $Delta t in [3.8, 4.2]$ s). Occupancy features:

`eeg_delta`, `eeg_theta`, `eeg_alpha`, `eeg_beta`, `eeg_gamma`, `eeg_alpha_theta`,
`eeg_beta_alpha`, `eeg_sample_entropy`.

These are the eight spectral/complexity columns used by the MNPS feature contract in this
export. Occupancy is median $norm(z)_2$ after baseline-only robust standardisation, not a
three-dimensional MNPS radius.

The article-side reanalysis consumes these frozen feature values and does not re-run EEG
preprocessing or estimate PSDs. Channel handling, reference, artefact treatment, band edges,
PSD estimator, sample-entropy parameters, and any gamma-EMG safeguards are therefore properties
of the pinned export, not newly estimated methods in this article. They must be audited from the
export-producing pipeline before any claim beyond this frozen feature contract; in particular,
the gamma contribution reported here is descriptive rather than an EMG-robust physiological claim.

= S1.2 Occupancy and matching

For participant $i$, all baseline rows with finite values in all eight features define

$ m_j = op("median")(x^"base"_(dot,j)), quad
  s_j = 1.4826 thin op("MAD")(x^"base"_(dot,j)), $

Scales that are non-finite or $<=10^(-8)$ are set to invalid (`NaN`); no floor value is
substituted or clamped. This scaling step is separate from one-step eligibility. Later-phase rows
are mapped $z_(t,j)=(x_(t,j)-m_j)\/s_j$. Occupancy is the median Euclidean radius of eligible
one-step sources (finite features and valid $Delta t$).
This is the unmatched occupancy scalar copied from the baseline-anchor matching pipeline; it is
not recomputed under a new distance.

Matching is greedy one-to-one Euclidean in $z$, caliper = median baseline leave-one-out
nearest-neighbour distance, minimum 20 pairs per participant, minimum 10 included participants
for a cohort test. Increment speed and spread are summaries of $Delta z \/ Delta t$ on matched
or unmatched eligible sources (S2). Matching is outcome-blind.

Recording-local `features_robust_z` is centred at 0 in every recording, so occupancy is
invisible in that chart. Local-chart MNPS matching therefore cannot be read as a
cross-phase physical-state match.

= S1.3 LOR/ROR

Exact binomial 95% Clopper–Pearson intervals @clopper1934binomial on $k$ out of 40 at baseline
versus later protocol sedation. LOR-impaired if the later interval lies entirely below baseline;
otherwise responsive @chennu2016propofol. Among impaired participants, ROR returned if the
recovery interval overlaps baseline. Labels are assigned from $k$ only, then joined to frozen
occupancy.

= S1.4 Statistical design

Unit of analysis: participant. The initially selected first-sedation-minus-baseline contrast is an
ordered reporting contrast, not a confirmatory primary endpoint. Its exact two-sided sign test on
non-zero differences, Wilcoxon signed-rank $p$, paired $d_z$, and percentile bootstrap 95% CI
(10 000 participant resamples, seed 20260920) are descriptive. Later sedation and recovery are
ordered descriptive contrasts. LOR group tests use two-sided Mann–Whitney and two-sample $d$,
with a gate $>=10$ per arm. Association: Spearman $rho$ occupancy versus $k$ at later sedation.
Discovery local-chart
screens: Holm on original H1/H2 sign tests; Benjamini–Hochberg FDR on a frozen Wilcoxon family
(S2). No FDR survivor is promoted.

= S1.5 Exploratory status and gates

Dated preregistration draft 2026-09-20 specified G0–G4 before confirmatory contrasts. G0
inventory, G1 labels, and G2 support were closed on this export. G3 independent code review and
G4 lock were not completed. Occupancy promotion is post-hoc relative to that draft for
first-sedation and recovery values. All $p$-values in the article are descriptive and exploratory.

= S1.6 What was not done

No new occupancy definition, no lowering of the $n=10$ matched-subject gate, no treating protocol
3 as LOR, and no confirmatory H1/H2 amplitude claim on `subject_anchored` MNPS were made. A
separate post-hoc robustness branch (`results/v1_occupancy_robustness_20260922_reviewfix/`) did decompose
the frozen radius and tested leave-one-feature-out, baseline-only sample-SD, and normalised-IQR
scales. It reused the original full-feature eligibility mask, participant unit, and missingness;
it therefore quantifies computational sensitivity for these choices but does not establish
biological robustness, independence, or confirmatory validity. No consciousness inference.

The robustness branch is computationally locked by its hash manifest, while G3 independent review
and G4 confirmatory locking remain open.

#bibliography("references.bib", style: "apa")
