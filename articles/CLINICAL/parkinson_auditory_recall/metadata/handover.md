Du analyserar en färdig H5-bundle för OpenNeuro-datasetet `ds004574` (Parkinson oddball EEG), producerad av MNDM.

## Bundle och provenance

Primär run:
- `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_ds004574_20260602_062756`

Viktiga sidecars i samma run-dir:
- `run_manifest.json`
- `stage_mapping_qc.json`
- `features_snapshot.json`
- `normalization_report.json`

Aktiv ingest-config för denna run:
- `H:/SourceRepo2/NeuralManifoldDynamics/mndm/config/config_ingest_ds004574.yaml`

Datasetroten för denna run är INTE rå-OpenNeuro-rooten utan en extern behavior-enriched staging:
- `M:/datasets/received/openneuro/ds004574_behavior_enriched`

Den staged roten skapades för att join:a in trial-subtyp från `beh.tsv` in i `*_events.tsv` utan att ändra MNDM-kod.

## Kohort

Dataset:
- `146` subjects totalt
- `98` Parkinson
- `48` Control

Full run-status:
- full `features` klar
- full `summarize` klar
- `146` H5-filer
- `146` summary-json
- `146` qc-summary-json
- `146` qc-reliability-json

Feature coverage:
- `27,715` epochs totalt
- `146` unika källfiler

Metadata som kan antas:
- `task = oddball`
- `condition = not_applicable`
- `group in {Parkinson, Control}`

## Vad som finns i H5

Per subject-H5 finns bland annat:
- `coords_9d/values`
- `coords_9d/names`
- `jacobian/J_hat`          -> vanlig 3D MNJ
- `jacobian_9D/J_hat`       -> 9D-Jacobian
- `features_raw/*`
- `features_robust_z/*`
- `labels/*`

Koordinatordning i `coords_9d/names` är konsekvent:
- `m_a`, `m_e`, `m_o`, `d_n`, `d_l`, `d_s`, `e_e`, `e_s`, `e_m`

Former som observerats:
- `coords_9d/values`: `[T, 9]`
- `jacobian/J_hat`: `[W, 3, 3]`
- `jacobian_9D/J_hat`: `[W, 9, 9]`

Alla stickprov och kohortkontroller visade:
- inga NaN/Inf i `coords_9d`
- inga NaN/Inf i `jacobian/J_hat`
- inga NaN/Inf i `jacobian_9D/J_hat`

## Viktig semantik för events / labels

Den här bundle:n använder behavior-enriched event provenance.

Centrala `labels/*`-keys som nu finns i fullrunnen:
- `raw_boundary_onset_sec`
- `raw_standard_precue_onset_sec`
- `raw_standard_arrowcue_onset_sec`
- `raw_standard_response_onset_sec`
- `raw_oddball_auditory_precue_onset_sec`
- `raw_oddball_auditory_arrowcue_onset_sec`
- `raw_oddball_auditory_response_onset_sec`
- `raw_oddball_visual_precue_onset_sec`
- `raw_oddball_visual_arrowcue_onset_sec`
- `raw_oddball_visual_response_onset_sec`

VIKTIGT:
- dessa rå labels är den meningsfulla event-ytan för oddball-subtyper
- `labels/stage` ska INTE tolkas som användbar trial/stage-annotation här
- stage är medvetet inte promenerad från punkt-events till en kanonisk per-window-stage
- i praktiken är `labels/stage` i detta dataset i huvudsak `-1` över fönster

Så:
- använd `raw_*` subtype-labelsen för eventrelaterade analyser
- använd inte `stage` som klinisk eller experimentell tillståndsyta för detta dataset

## Behavior-join och residual caveat

En extern join mellan EEG-events och `beh.tsv` användes för att skapa subtype-labels.

Alignmentkvalitet i staged data:
- `140` subjects = `good`
- `5` subjects = `usable`
- `1` subject = `partial`

Alignmentaudit finns här:
- `M:/datasets/received/openneuro/ds004574_behavior_enriched/behavior_event_alignment.tsv`

Residual caveat:
- `raw_nan_onset_sec` förekommer fortfarande i fullrunnen
- detta gäller `27` subjects
- det betyder inte att runnen misslyckats
- det betyder att vissa enrichade eventrader inte fick ett rent subtype-namn efter join/matchning

Praktisk tolkning:
- behandla `raw_nan_onset_sec` som residual unmatched event provenance
- använd det inte som ett meningsfullt experimentellt event
- om du behöver strikt ren label-namespace kan du exkludera dessa events eller mappa dem till `unmatched`

Särskilt:
- `sub-025` var värst i alignment-residualerna och hade många `nan`-eventrader
- full summarize lyckades ändå för alla 146 subjects

## Numerisk QC från stickprov

Kohortstickprov på `coords_9d` och MNJ visade:
- `coords_9d` ser inte kollapsad eller degenererad ut
- 9D-axlarna har rimlig spridning över subjects
- 3D-Jacobian/MNJ är generellt lugn
- 9D-Jacobian är mer dynamisk men överlag rimlig

Observerad outlier:
- `sub-112` hade högst `jacobian_9D`-spik (`abs max ~ 8.79`)
- detta såg ut som enstaka toppar, inte total numerisk korruption
- samma subject hade fortfarande ändliga värden och rimliga percentiler i övrigt

Så:
- bundle:n verkar användbar för analys
- men om du gör gruppjämförelser på extrema Jacobian-mått bör du robustifiera mot outliers

## Vad som INTE finns i denna bundle

Denna run är inte:
- cohort-anchored
- ComBat-normaliserad
- regional-MNPS-utökad
- time-reference-utökad

Det som finns:
- subject-anchored koordinatlager
- raw features
- robust-z feature exports
- 3D MNPS / MNJ
- 9D coords / 9D Jacobian
- enriched raw event provenance

## Rekommenderad analysstrategi

Om du ska analysera bundle:n:

1. Läs `run_manifest.json` först för schema/capabilities.
2. Använd `coords_9d/names` för att säkra korrekt dimensionsordning.
3. För oddball-jämförelser:
   - använd `raw_standard_*`
   - använd `raw_oddball_auditory_*`
   - använd `raw_oddball_visual_*`
4. Använd inte `labels/stage` som semantisk stage-variabel här.
5. Hantera `raw_nan_onset_sec` som residual/brus.
6. Vid gruppjämförelser på MNJ:
   - använd robusta sammanfattningar
   - kontrollera outliers som `sub-112`
   - rapportera gärna både median/IQR och trimmed/winsorized varianter

## Bra första frågor att besvara i analysrepot

- Skiljer sig Parkinson vs Control i 9D-koordinaternas spridning eller occupancy?
- Skiljer sig Parkinson vs Control i 3D-MNJ eller 9D-Jacobian-normer?
- Skiljer sig standard vs auditory oddball vs visual oddball i lokal dynamik?
- Är event-låsta förändringar runt `precue`, `arrowcue` eller `response` tydligare i vissa 9D-axlar?
- Är resultaten robusta om `raw_nan_onset_sec` exkluderas?
- Är resultaten robusta om subjects med extrem `jacobian_9D`-amplitud winsoriseras eller flaggas?

## Kort sammanfattning

Detta är en full, lyckad H5-bundle för `ds004574` där det viktigaste nya är subtype-aware oddball event provenance från behavior-join:
- standard
- oddball_auditory
- oddball_visual

Använd raw subtype-labelsen som experimentell event-yta.
Använd inte `stage` som huvudsaklig tillståndslabel i detta dataset.
Var uppmärksam på residual `raw_nan_onset_sec` och några få 9D-Jacobian-outliers, men betrakta bundle:n som överlag numeriskt frisk och analysbar.