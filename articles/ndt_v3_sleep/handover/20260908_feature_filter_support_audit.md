# Feature- och filterstöd för sub-99 (H5)

Status: **METHOD_LIMITED / provenance incomplete**. Detta är en read-only audit av den accepterade continuous-fullnight-körningen, inte en ny analys och inte en biologisk slutsats.

## Vad som faktiskt är mätt/exporterat

H5 innehåller 1 068 rader med 30 s epoch-längd och 30 s steg; den exporterade täckningen är 32 040 s. Alla exporterade `coverage_ok`, `retained_after_qc`, `geometry_valid`, 3D- och 9D-masker är sanna i H5. Rå- och robust-z-featurematriserna är ändliga för de exporterade kärnfeatures. Rå EDF-metadata anger 32 064 s, alltså 24 s i slutet utanför 1 068 kompletta 30 s-epocher. Detta är epoch-/ingeststöd, inte ett mått på filterstöd.

H5-attributen `window_sec=8.0` och `fs_out=4.0` kommer från det generiska MNPS-kontraktet. Den inbäddade resolved time-grid/epoch-konfigurationen och continuous-pilot-konfigurationen anger 30 s/30 s. `fs_out` är en downstream-hint; den får inte användas för att tolka råfeature-epochen som 8 s eller för att påstå 4 Hz mätning.

3D- och 9D-lagren är subject-anchored. H5-konfigurationen och `/support_signature/v1` anger featurekällorna; denna audit enumererar inte varje projektionkoefficient. I just denna körning föll `e_m` tillbaka till `ppg_rate_bpm`, med `semantic_equivalence=false`. Det finns ingen exporterad cohort/external anchor. Stagepåståenden måste därför behålla skillnaden mellan deskriptiva gemensamma koordinater och en stage-konditionerad estimator.

## Temporalt beroende per lager

* **EEG/PPG feature-row:** koden skär varje rad från en sammanhängande epoch med `length_s=30` och `step_s=30`. EEG bandpower, ratios, Hjorth och entropi beräknas därefter på den epochens signal. PPG-fallbacken filtrerar PPG-signalen och räknar pulsattribut per samma epoch-index. Detta fastställer den avsedda input-epochen; det fastställer inte effektivt FIR/IIR-stöd, edge-padding eller hur en signal nära en disconnection påverkas.
* **Resampling, notch, EEG-bandpass och CSD:** koden kan resampla, notch-filtrera, bandpass-filtrera och göra CSD på den kontinuerliga råsignalen före epochering. De aktiva YAML-filerna anger bland annat notch 50 Hz, EEG-bandpass 1–45 Hz och CSD-parametrar, men run-manifestets excerpt saknar den fullständiga resolved preprocessing-profilen. H5 saknar filterlängd, MNE-metod/padding, faktisk branch-status och en körd filterlogg. Därför kan den effektiva temporala supporten inte reduceras till ett påhittat antal sekunder.
* **Feature-normalisering:** robust-z-centra och skalor har `finite_count=1068` i H5 och `anchor_applied=local`. De är alltså fit:ade över hela recordingens feature-rader. Detta är en känd, recording-global algoritmisk dependency: varje standardiserad rad kan bero på andra tidpunkter. Det är inte i sig bevis på biologisk läckage, men det utesluter en stark formulering om att stagevärdena är oberoende av övriga stages eller att stage-konditionerad validitet redan är certifierad.
* **Projection/anchors:** H5 visar subject-anchored coordinates och inga exporterade feature/cohort anchors. Den globala robust-z-fit:en kvarstår som dependency; external/cohort calibration ska inte antas.
* **Downstream dynamik:** transition-residualer, diffusion och FTR har egna horizon-, neighbor- och embargo-kontrakt. De är inte feature-filter-support och ska rapporteras separat. FTR är modell-derived och measurement-validity är not assessed. Detta dokument återöppnar inte downstream-gate-beslut.

## Disconnection och stage-gränser

H5 har nio stage-kod-8-fönster; deras första start är 20 970 s och sista start 21 210 s. Med 30 s window bounds täcker de 20 970–21 240 s, och alla retention-/geometry-masker är ändå sanna. Koden 8 är en PSG-disconnection-status i annoteringen; den har inte relabelats till en sleep stage. H5 visar inte någon separat signalmask som exkluderar dessa rader, och den körda preprocessingens filterstöd/padding är inte pinad. Därför är det inte visat att en epoch eller ett filterfönster nära disconnectionen är isolerat från signal före/efter intervallet. Det är en stöd-/provenance-risk, inte ett påstående att kontamination faktiskt inträffade. Stage-purity och full temporal support förblir `not_assessed`.

## Provenance-gap

Konfigurationskedjan och dess SHA-256 finns nedan i JSON-filen. Den visar den avsedda 30 s continuous-pilot-konfigurationen och de deklarerade preprocess-värdena. Den visar inte ensam exakt vilken preprocessinggren som exekverades: run-manifestets config excerpt tar inte med top-level preprocess, H5 saknar filter-/resamplinglogg, och rå EDF-hash/faktisk filterparameterisering är inte länkad från H5. `source_window_id`/row alignment och epochbounds är däremot exporterade och verifierade i de föregående support-audit-artifakterna.

## Minsta nästa implementation

1. Lägg in ett resolved preprocessing-record i run manifest/H5: input sampling frequency, resample events, notch/bandpass design och MNE method, filter length, padding/edge policy, CSD status/parameters, PPG filter parameters och fallback source per row.
2. Exportera en per-epoch `raw_support_start/end` eller ett konservativt `support_status` som skiljer exact epoch bounds från effective filter support. Om biblioteket inte kan ge en verifierad finite support ska status vara `unknown`, inte ett numeriskt antagande.
3. Koppla disconnection/bad-annotation intervals till samma timebase och låt supportmasken exkludera eller markera epoch/fönster vars verifierade support korsar intervallet. Bridging över code 8 ska vara förbjudet i stage-konditionerad analys.
4. Registrera robust-z fit population och anchor scope explicit i analysmanifestet. För en framtida stage-konditionerad estimator krävs en i förväg dokumenterad extern tränings-/kalibreringspolicy som bevarar gemensamma koordinater; within-stage fit ska inte införas som standard och nuvarande deskriptiva koordinater ska inte retrofittas.

Det minsta säkra resultatet från nuvarande artefakt är därför: **global deskriptiv koordinatprodukt med 30 s epoch-input, men effektiv filter-/nonlocal support och stage-konditionerad temporal renhet är inte fullständigt reproducerbara eller certifierade.**

Se [`20260908_feature_filter_support_audit.json`](20260908_feature_filter_support_audit.json) för maskinläsbara paths, SHA-256 och line references.

