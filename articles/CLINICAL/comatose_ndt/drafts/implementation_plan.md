# Implementation Plan: Comatose NDT / I-CARE

## Syfte

Detta dokument beskriver vilka analyser som bör genomföras för
`articles/comatose_ndt`, i vilken ordning de bör göras, och vilka delar som kan
göras redan nu respektive efter nästa ingest-runda med bättre tidsstöd i H5.

Huvudfrågan är inte en enkel kontrollgrupp-vs-fokusgrupp-jämförelse, utan om
tidig neural geometri efter hjärtstopp skiljer patienter med bättre senare
återhämtning från patienter med sämre utfall. Den centrala arbetsmodellen är en
prognostisk och longitudinell variant av C/TI/P-ramen:

- `C` = capacity collapse / kvarvarande eller återkommande lokal dynamisk kapacitet
- `TI` = transport-innovation balance / innovation-dominerad kontra transport-fångad geometri
- `P` = pathological lock-in / rigid, kanaliserad, asymmetrisk deformation

Denna plan inkluderar:

- klassiska MNPS-analyser (`3D`, `9D`, Jacobian, reachability),
- en första `C/TI/P-light`,
- en senare `C/TI/P v2`,
- samt en separat men kopplad sleep spindle / sleep-like microstructure-gren.

## Övergripande analyslogik

Analysprogrammet bör byggas i fyra lager:

1. *Data- och tidslager:* säker metadata, outcome-mappning, run-tider,
   patient-tidsbin, sjukhus- och confound-kovariater.
2. *Klassiskt MNPS-lager:* patientnivå-sammanfattningar från `mnps_3d`,
   `coords_9d`, `jacobian`, senare även reachability.
3. *C/TI/P-light:* en första pappersnära 3D-ram med robusta proxy-mått som redan
   finns eller nästan finns.
4. *C/TI/P v2:* fullare version när ingest exporterar bättre tidsstöd,
   reachability-panel och eventuellt fler block-/regionala geometriobjekt.

## Återanvändning från `ndt-analysis/ndt_analysis`

Innan nya artikel-specifika analyser byggs bör vi utgå från vad som redan finns
i `ndt-analysis/ndt_analysis`. Målet är att undvika ett parallellt analyslager
för sådant som paketet redan kan beräkna.

### Rekommenderad princip

- återanvänd `ndt_analysis` för generiska H5-, reachability-, spindle- och
  adaptive-collapse-beräkningar,
- lägg endast ett tunt I-CARE-/coma-lager ovanpå för:
  - outcome-mappning,
  - tidsaxel,
  - patient/tidsbin-aggregering,
  - prognostiska kontraster,
  - paper-facing coma-figurer.

### Delar som redan finns

#### `legacy_adapters.py`

Detta är den naturliga H5-ingången för run-nivå-sammanfattning. Filen har redan
adapters för:

- `global_mnps_3d`
- `global_mnps_jacobian_3d`
- `global_mnps_9d`
- `global_mnps_jacobian_9d`
- `global_mnps_jacobian_9d_block_jacobian`
- `regional_3d`
- `regional_9d`
- `reachability_cones`
- `regional_reachability_cones_3d`

Den räknar också redan ut flera mått som är direkt relevanta för `C/TI/P-light`,
bland annat:

- rotation norm
- Frobenius norm
- operator norm
- `ACI`
- spectral radius
- anisotropy from absolute eigenvalues
- Jacobian condition number
- `MDR` när `J_dot` finns

#### `reachability_cones.py`

Detta är redan den generiska vägen för reachability-sammanfattning från H5.
Den returnerar flat summaries med bland annat:

- `tube_*`
- `q_ratio_h*`
- cone-mått per horizon
- validity diagnostics

Detta bör vara huvudvägen för reachability i coma-spåret snarare än att skriva
en separat reachability-beräkning i `articles/comatose_ndt/src`.

#### `analysis_pipeline.py`

Denna fil innehåller redan derived logic för `adaptive_collapse`, inklusive:

- aliasing mellan reachability-mått och paper-facing metric names,
- `ati_reduced`,
- `ati_full`,
- `capture_gate`,
- `q_ratio_h4`,
- `cfca` från 9D block-Jacobians.

Det betyder att en stor del av den tänkta `C/TI/P-light`-ramen redan finns som
byggstenar i pipeline-lagret.

#### `spindle_event_locked.py`

Detta är redan en återanvändbar event-locked motor för:

- discovery av event parquets,
- bin-descriptives,
- subject-level deltas,
- paired tests,
- CSV outputs.

Sleep spindle / spindle-like coma-analyser bör så långt som möjligt använda
detta i stället för att duplicera logik i artikelmappen.

### Delar som fortfarande saknas för coma

Det som *inte* verkar finnas fullt ut i `ndt_analysis` ännu är:

- explicit I-CARE outcome-aware analys,
- patientrelativ eller ROSC-relativ tidsaggregering,
- patient/tidsbin-sammanfattning för prognos,
- coma-specifik C/TI/P-trajectory-visualisering,
- coma-specifik incremental validity mot outcome.

Detta är därför rätt plats för artikel- eller dataset-specifika skript.

### Praktisk konsekvens

När nya coma-skript skapas bör de i första hand:

1. importera eller återanvända outputs från `legacy_adapters.py`,
2. importera eller återanvända outputs från `reachability_cones.py`,
3. återanvända `spindle_event_locked.py` för event-locked spåret,
4. bara lägga till det I-CARE-specifika prognoslagret ovanpå.

## Arbetsordning

### Fas 0. Metadata, kohort och tid

Detta är fundamentet och måste vara klart innan paper-facing statistik blir
trovärdig.

#### Mål

- Mappa patientnivå-utfall (`outcome`, `cpc`, eventuellt andra kliniska labels).
- Mappa run-nivå tid på ett sätt som gör longitudinell analys möjlig.
- Definiera patientnivå-tidsbin för tidig post-ROSC-period.
- Inventera confounds som faktiskt finns tillgängliga.

#### Status

Delvis klart.

Redan verifierat:

- `participant/row_json` innehåller användbara fält som `outcome`, `cpc`,
  `rosc`, `hospital`, `ttm`, `age`, `sex`, `shockable_rhythm`.
- H5 innehåller relativ tid inom recording (`time`, `window_start`,
  `window_end`).
- Rå `*.hea` innehåller run-start och run-end som kan användas till en
  sammanhängande elapsed timeline.

Redan implementerat:

- `articles/comatose_ndt/src/icare_patient_timeline_analysis.py`

#### Kvar att göra

- När ingest uppdaterats: flytta run-start/run-end och helst mer explicit
  patientrelaterad tidsinformation direkt in i H5/manifest.
- Kontrollera om tidsaxeln kan knytas säkrare till `time since ROSC`, inte bara
  `time since first recording`.
- Bygg en sammanhängande kohorttabell med:
  - `subject`
  - `hospital`
  - `age`
  - `sex`
  - `rosc`
  - `ttm`
  - `shockable_rhythm`
  - `outcome`
  - `cpc`
  - antal runs
  - total användbar täckning
  - vilka tidsbin som faktiskt finns

#### Paper-facing outputs

- `subject_outcome_index.csv`
- `run_timing_metadata.csv`
- `patient_timebin_summaries.csv`
- en enkel figur över run-start över tid per patient
- en kohort-/coverage-tabell till manus

## Fas 1. Klassiska MNPS-analyser

Detta är den första fulla analysnivån och bör göras innan vi försöker sälja
C/TI/P starkt.

### 1A. MNPS 3D

#### Frågor

- Skiljer sig `m`, `d`, `e` mellan bättre och sämre outcome?
- Finns tidig divergens i `0-24 h`, `24-48 h`, `48-72 h`?
- Finns tecken på återexpansion eller återcentrering över tid?

#### Primära mått

- median och IQR av `m`, `d`, `e`
- path length
- displacement
- step norm / speed
- inom-patient-slope över tid

#### Första analyser

- patientnivå-sammanfattning per tidsbin
- `Good` vs `Poor` outcome per tidsbin
- mixed eller robust regression med tid + outcome + interaktion
- stratifiering eller kovariat för sjukhus om möjligt

#### Figurer

- per-axis violin/box för `m`, `d`, `e` per outcome och tidsbin
- trajectories i 3D för enskilda patienter eller gruppmedel
- patientmedel som punkter i 3D med färg för outcome

### 1B. Stratified 9D

#### Frågor

- Finns redistributionsmönster i `9D` som inte syns tydligt i `3D`?
- Är vissa subkoordinater särskilt associerade med återhämtning?

#### Primära mått

- median per subkoordinat
- spridning per subkoordinat
- 9D global variance / mean std
- eventuellt reducerade familjesummor:
  - `m-family`
  - `d-family`
  - `e-family`

#### Första analyser

- outcome-separation per subkoordinat
- PCA/UMAP endast som explorativ visualisering, inte huvudbevis
- robust feature-ranking för vilka 9D-dimensioner som bäst skiljer grupperna

#### Figurer

- heatmap över subkoordinatmedel per tidsbin och outcome
- spider/radar eller small-multiple bars för family-level shifts
- 9D summary projection för gruppöversikt

### 1C. Jacobian / MNJ

#### Frågor

- Är bättre outcome associerat med mindre rigid eller mindre ill-conditioned lokal geometri?
- Finns skillnader i deformation snarare än bara position?

#### Primära mått

- Jacobian Frobenius norm
- trace
- spectral radius
- condition number
- anisotropy-liknande proxy om enkel att beräkna robust
- eventuell `J_dot`-baserad stabilitet om exporten stödjer det

#### Första analyser

- patientnivå-medianer per tidsbin
- outcome-kontraster
- tid x outcome-interaktion

#### Figurer

- panel med Jacobian-summary distributions
- eventuell phase portrait-skiss för exempelpatienter

### 1D. Reachability

Detta bör ingå i den klassiska MNPS-planen, men kan behöva vänta på ingest om
exporten ännu inte är stabil eller komplett för I-CARE.

#### Frågor

- Har bättre-outcome-patienter större eller mer återhämtad lokal forward availability?
- Är dålig prognosis kopplad till kontraherad eller lägre-dimensionell
  reachability-geometri?

#### Primära mått

- tube log-determinant
- tube effective dimensionality
- cone anisotropy
- cone rotational structure
- `Q-ratio` vid kort horisont
- eventuell `CaptureGate` om det finns robust

#### Första analyser

- samma patient/tidsbin-upplägg som för `3D` och `9D`
- baseline mot enklare spektrala modeller

#### Figurer

- outcome-separation per reachability-mått
- trajectories av reachability över tid
- om möjligt 3D C/TI/P-proxy-plot med reachability-baserad kapacitetsaxel

## Fas 2. C/TI/P-light

Detta är den första paper-nära geometriska syntesen. Målet är att få en
tolkningsbar 3D-ram även innan hela version 2 finns.

### Designprincip

`C/TI/P-light` ska använda mått som redan finns eller kan beräknas robust från
nuvarande export, utan att kräva full perfekt reachability-stack.

### Föreslagen konstruktion

#### `C`-axel (capacity)

Målet är att sammanfatta hur mycket lokal kapacitet eller rörelseutrymme som
finns kvar.

Kandidater:

- `mnps_path_length`
- `mnps_step_norm_median`
- `mnps_displacement`
- `coords_9d_global_std_mean`
- senare gärna `tube_log_det` och `tube_d_eff`

Första version:

- robust z-scorad komposit av movement + spread

#### `TI`-axel (transport-innovation)

Målet är att skilja innovation-dominerad låg kapacitet från mer
transport-fångad geometri.

Kandidater:

- `J_dot / J`-proxy om tillgängligt
- relation mellan operatorstyrka och variation över tid
- eventuell enkel stabilitets-/rigiditetsproxy från `jacobian`
- senare riktiga `Q-ratio_H4` och `CaptureGate`

Första version:

- en försiktig proxy-axel med tydlig märkning som preliminär

#### `P`-axel (pathological lock-in)

Målet är att fånga rigiditet, kanalisation och asymmetrisk deformation.

Kandidater:

- Jacobian condition number
- anisotropy-liknande mått
- spectral radius eller dominant singular value
- block-asymmetri när block-Jacobians finns

Första version:

- robust komposit av condition + anisotropy-liknande proxy

### Analyser

- patientnivåpunkt i `C/TI/P-light` per tidsbin
- gruppcentroid för `Good` vs `Poor`
- individuella trajectories över tid
- enkel klassifikation/regression:
  - spektral baseline
  - spectral + `3D`
  - spectral + `3D` + `9D`
  - spectral + `C/TI/P-light`

### Figurer

- 3D scatter eller 2D-projektioner av `C/TI/P-light`
- trajectories över tid i C/TI/P-rummet
- occupancy shells eller density regions när n blir tillräckligt stort

### Viktig tolkningsregel

`C/TI/P-light` får inte presenteras som färdig teori-validering. Det är en
första paper-facing sammanfattning av den kliniska geometrin, inte slutversionen
av ramverket.

## Fas 3. C/TI/P version 2

Detta steg görs efter nästa ingest-runda och när tidsseriestöd / reachability /
eventuellt fler derivat finns stabilt i H5.

### Förbättringar som önskas från ingest

- run-start/run-end direkt i H5
- tydligare patientrelativ eller ROSC-relativ tid
- komplett reachability-panel
- stabil export av `J_dot` och eventuella TI-relevanta derivat
- block-Jacobians där de är meningsfulla
- eventmetadata för spindle-/sleep-like events när sådana används

### Version-2-mål

#### Full `C`

- `ATI`-liknande kapacitetskomposit
- `tube_log_det`
- `tube_d_eff`
- rotational reachability metrics

#### Full `TI`

- `Q-ratio_H4`
- `CaptureGate`
- `MDR` eller bättre stabiliserad `J_dot / J`

#### Full `P`

- `ACI`
- Jacobian condition number
- `CFCA` eller motsvarande block-asymmetri
- eventuellt regional lock-in-summaries

### Version-2-analyser

- full patient/tidsbin-analys i C/TI/P
- robusthetsanalyser per sjukhus
- outcome prediction med:
  - baseline kliniska variabler
  - spectral baseline
  - MNPS
  - full C/TI/P
- incremental validity över spektrala features

### Version-2-figurer

- slutlig 3D C/TI/P-occupancy figur
- trajectories med early-to-late arrows
- heatmaps över transitionsannolikheter mellan regioner i C/TI/P-rummet

## Fas 4. Sleep spindles / sleep-like microstructure

Detta är en sekundär gren. Den får inte bli huvudfrågan, men den kan bli en
viktig mekanistisk eller repertoire-relaterad analys.

### Huvudfråga

När spindle-like eller sleep-like mikrostruktur förekommer i coma-EEG, är den
associerad med mer bevarad eller mer återhämtningsbar lokal geometri?

### Delspår

#### 4A. Presence/absence

- Förekommer spindle-like events oftare hos bättre-outcome-patienter?
- Förekommer de tidigare eller senare i förloppet?
- Är de knutna till specifika runs eller tidsbin?

#### 4B. Event-locked geometri

Återanvänd från `articles/Sleep_Spindle_deep_dive/src`:

- event-locked windows
- subject-level aggregation
- matched controls
- bootstrap/sign-tester
- figurmallar

Frågor:

- Skiljer event windows sig från matched non-event windows i `3D`, `9D`,
  Jacobian, reachability?
- Är spindle-like events associerade med lokalt rikare geometri snarare än
  enkel suppression?

#### 4C. Repertoire marker

- Är presence av spindle-like/sleep-like events associerad med högre `C`?
- Är den associerad med lägre `P`?
- Är den associerad med mer innovation-dominerad lågkapacitetsgeometri snarare
  än rigid capture?

### Viktig begränsning

Sleep spindles i coma får inte automatiskt behandlas som samma biologiska objekt
som normala N2-spindles. Artikeln måste hålla isär:

- verkliga fysiologiska homologier,
- detector-definierade spindle-like events,
- och endast geometriskt informativa korttidsregimer.

## Statistisk plan

### Primär inferensnivå

- patientnivå eller patient/tidsbin-nivå
- inte window-nivå som huvudinferens

### Primära kontraster

- `Good` vs `Poor`
- tidig vs senare inom patient
- `outcome x time`

### Robusthetsblock

- sjukhusstratifiering eller sjukhus-kovariat
- täckning / antal windows
- artefaktbörda om tillgängligt
- spektral baseline
- eventuellt matching på tid-since-ROSC

### Falsifikationsblock

- slumpad outcome-label
- time-bin shuffle där meningsfullt
- spectral-only baseline
- spectral + geometry incremental validity

## Prioriterad leveransordning

### Nu direkt

1. Stabil kohort- och tidsmappning
2. Run- och patient/tidsbin-sammanfattningar för klassisk `3D/9D/Jacobian`
3. Första outcome-jämförelser
4. Första `C/TI/P-light`

### Efter ingest v2

5. Full reachability-analys
6. `C/TI/P v2`
7. Incremental validity mot spektrala baselines
8. Sleep spindle / sleep-like microstructure event-locked branch

## Förväntade manus-deliverables

Det färdiga papperspaketet bör minst innehålla:

- en kohort-/coverage-tabell
- en klassisk MNPS-panel (`3D`, `9D`, Jacobian, reachability)
- en `C/TI/P-light` eller full `C/TI/P` huvudfigur
- en tidsutvecklingsfigur över patienttrajektorier
- en incremental-validity-tabell
- en sekundär figur eller supplement för sleep spindles / sleep-like events

## Praktisk filstruktur

Föreslagen struktur under `articles/comatose_ndt/`:

- `src/icare_patient_timeline_analysis.py`
- `src/icare_mnps_summary_analysis.py`
- `src/icare_ctip_light_analysis.py`
- `src/icare_reachability_analysis.py`
- `src/icare_incremental_validity_analysis.py`
- `src/icare_spindle_like_analysis.py`
- `results/timeline_analysis/`
- `results/mnps_summary/`
- `results/ctip_light/`
- `results/reachability/`
- `results/incremental_validity/`
- `results/spindle_like/`
- `figures/`

## Bottom line

Den rekommenderade strategin är:

1. bygg först ett starkt klassiskt MNPS-resultatpaket,
2. använd därefter `C/TI/P-light` som första geometriska syntes,
3. uppgradera sedan till full `C/TI/P v2` när ingest stöder det ordentligt,
4. håll sleep spindle-grenen som en tydligt sekundär men potentiellt mycket
   informativ repertoire-analys.
