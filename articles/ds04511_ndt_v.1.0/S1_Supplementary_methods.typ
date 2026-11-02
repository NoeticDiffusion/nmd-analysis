#import "template_eLife.typ": *
#show: netn-template.with(title: "S1 Supplementary Methods", short-title: "S1 Methods ds004511", subtitle: "Pinned measurement contract and analysis design", authors: ((name: "Robin Langell", affil: 1),), affiliations: ("Langell Konsult AB, Vallentuna, Sweden",), corresponding-author: "Robin Langell, hello@noeticdiffusion.com", article-type: "Supplement")

= S1.1 Dataset and contract

The analysed export is `neuralmanifolddynamics_ds004511_20260921_050009`: 134 H5 recordings from 45 people (Rest 45, CC 45, GG 44) from OpenNeuro ds004511 @makowski2026_ds004511. The canonical MNPS `[m,d,e]` and stratified 9D definitions are fixed. Coordinates are `subject_anchored`; values are not re-centred or re-tuned against task contrasts. Task labels come from the BIDS-style filename stem, not within-subject order.

= S1.2 Estimator separation and mathematical bridge

Occupancy is a chart-location summary. Chart-Jacobian alpha is the spectral abscissa of the local chart Jacobian. L2/L3 quantities derive from an identified lag-1 one-step map, only where support permits. The map has the exported affine form $x_(t + Delta t) approx Phi (x_t - bar x) + c$; L3 alpha is the spectral abscissa of the matrix-log generator proxy `log(Phi)/dt`, not of `Phi` itself and not an Itô generator. The exporter writes L3 leaves only when the map passes the frozen two-fold out-of-fold identification gate and the matrix-log proxy is real; unsupported or non-real cases remain missing. This is a qualification rule, not a numerical repair rule. L4 amplitude summaries are finite-horizon certificate-derived summaries. These objects are reported in separate panels and never substituted for each other. Lag-2 was attempted but yielded only 13 direct L2 maps and 10 L3 proxies, too sparse and task-imbalanced for inference. `reach_d_eff` is excluded from dimensional interpretation after the degeneracy audit.

The conceptual bridge is an estimated local flow $hat b_x$ with local Jacobian $hat J_x(x) = partial hat b_x(x) / partial x$ versus a finite-step affine map and its matrix-log proxy. Agreement would require, among other things, comparable state representation, local linearity, approximate time homogeneity, adequate sampling, and comparable conditioning/support. No identity equates a median of window-level Jacobian spectral abscissae with the spectral abscissa of a fitted matrix-log proxy.

= S1.3 Aggregation and inference

Each finite recording-level included median is reduced to a subject-by-task median. Pairwise contrasts are complete-case later-minus-earlier Wilcoxon signed-rank tests @wilcoxon1945 with paired $d_z$; omnibus results use complete-triplet Friedman tests. BH correction @benjamini1995 is applied across finite Wilcoxon tests separately for (i) occupancy/MNJ/L1/L4 and (ii) chart-Jacobian alpha/L2/L3. The degenerate `reach_d_eff` QC readout is not a substantive endpoint and is excluded from the corrected task-effect family. Bootstrap uses 10,000 replicates and seed 20260921. No missing value is represented as zero.

= S1.4 Fixed-duration sensitivities

The task recordings have non-overlapping duration ranges. Bounded sensitivity analyses therefore re-aggregate the exported chart-Jacobian spectral-abscissa series and all four L1 series over the deterministic first 100 windows (400 s) in every recording. The coordinate chart, per-window measurements, exported validity masks, missingness handling, and production support thresholds remain unchanged; no estimator is re-fit. The three chart-alpha contrasts form one sensitivity family; the 12 L1 metric-by-contrast rows form a separate L1 sensitivity family, with four L1 Friedman tests corrected separately. L4 cannot be subjected to the same truncation from this export because only one certificate-derived scalar per recording is available.

= S1.5 Status and prohibited claims

This is `exploratory_discovery_20260921_g4_not_locked`, internally checked on one export. It is neither a mechanistic experiment nor a confirmatory test. Subject anchoring precludes interpreting amplitudes as between-subject levels; partial lag-1 identification defines the eligible sample rather than a recoverable nuisance.

Rest is retained as the exported resting-state task label. The current HDF5 task metadata does not encode eye state, so comparisons are not relabelled as eyes-closed versus eyes-open; eye-state sensitivity is a design limitation supported by independent EEG work @barry2007eeg. The GG--CC contrast is retained as an important active-task comparison, but no task contrast is interpreted as a mechanism of gambling, deception, or cognitive control.

#bibliography("references.bib", style: "apa")
