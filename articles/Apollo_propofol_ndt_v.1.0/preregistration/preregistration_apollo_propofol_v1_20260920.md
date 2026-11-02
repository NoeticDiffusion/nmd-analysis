# Apollo: propofol, dynamisk spridning och villkorad tillgänglighet

**Version:** 1.0, 2026-09-20. **Status:** preregistreringsutkast för sekundäranalys av redan insamlade och processade data; inte externt registrerat eller slutligt låst. Hypoteser och analysregler anges före nya tillståndskontraster. Metadata- och metodgrindarna i avsnitt 8 måste stängas före konfirmatorisk analys. Ett misslyckat metodsteg är inte ett biologiskt nollresultat.

## 1. Fråga och tidigare insyn

Vi undersöker om propofolsedering förändrar lokal spridning och dess effektiva dimensionalitet i det exporterade MNPS-diagrammet, och om ytterligare dynamiska egenskaper tillför information om beteendemässig respons utöver statiska och spektrala egenskaper. Vi skiljer läkemedelsexponering, experimentfas och responsförmåga. Ingen av dessa är ensam ett direkt mått på förekomst eller frånvaro av subjektiv upplevelse.

Det lokala manuskriptet *Reduced Dynamical Capacity Does Not Imply Unconsciousness* rapporterar tidigare Apollo-analyser av samma källdataset: kapacitetsminskning, men inga korrigerat signifikanta transport-/patologimått och ingen monoton fördjupningsprofil. Dessa resultat är kända och motiverar hypoteserna; den nya exporten är **inte en oberoende replikation**. Dess nya estimatorer är inte utbytbara med manuskriptets `ati_reduced`, `tube_log_det`, `q_ratio_h4` eller `capture_gate`.

Vid arbetet med detta dokument öppnades en H5-fil. Den första breda metadatautskriften visade också numeriska sammanfattningar från denna inspelning, inklusive koordinat-, Jacobian- och turning-/fitinformation. Det är därför fel att beskriva arbetet som helt blindat mot alla nya värden. Inga nya tillståndskontraster, gruppmedel, effektstorlekar eller klassificerare har beräknats. Den fortsatta inventeringen begränsades till schema, certifikat, stöd och tidsmetadata. Forskarnas övriga tidigare insyn måste deklareras vid registrering.

Chennu et al. visar varför respons och läkemedelsexponering bör hållas isär i just denna studie [1]. NDT-underlaget skiljer observerad koordinat, villkorad framtida övergångslag och latent mekanism [3]. En skillnad i en exporterad skalär identifierar inte ensam denna mekanism.

## 2. Datakälla och begränsad H5-kontroll

De angivna mapparna motsvaras på denna dator av:

- Underlag: `J:\repos\nmd-analysis\articles\aa_basicinfo`.
- Data: `J:\repos\nmd-analysis\data\raw\neuralmanifolddynamics_Sedation-RestingState_20260918_075713`.
- Artikel: `J:\repos\nmd-analysis\articles\Apollo_propofol_ndt_v.1.0`.

`run_manifest.json` anger 80 H5-filer och 20 personer; filnamnsinventeringen hittar 80 H5-filer. Manifestet anger endast villkoret `sedation`, inga labelnycklar. Detta bevisar inte att alla har samma responsnivå eller att varje person har fyra korrekt identifierade faser. Det äldre manuskriptets tillståndsnamn får inte överföras via antaganden om filordning.

Kontrollerad fil, vald som den lexikografiskt första fullständiga H5-sökvägen:

`sub-002_sedation_rest_run-003_acq-135/sub-002_sedation_rest_run-003_acq-135.h5`

SHA-256: `1635513f690ae01807a9495d920052ddc2a2c9a568d3b8a76bb04139bca993ba`.

Filen innehåller 96 tidpunkter med observerat steg 4 s och 8 s featurefönster enligt manifestet. Tidsstegen är regelbundna i denna fil; det visar inte att andra filer saknar luckor. Attributet `fs_out=4.0` får inte användas som 4 Hz MNPS-sampling när de observerade tidpunkterna ligger 4 s isär.

Primärt koordinatlager är `coords_3d_subject_anchored`, med kanonisk ordning `[m,d,e]`; stratifierad 9D finns också. Namnet `subject_anchored` garanterar inte ett gemensamt ankare mellan personens faser: featureproveniens anger lokala fitpopulationer. Normaliseringsproveniensen anger `status=disabled` trots metodnamnet `combat`; ComBat får inte antas vara utförd. `e_m` har fallback `eeg_highfreq_power_30_45` med `semantic_equivalence=false`, och e-axeln är märkt mixed. Det är inte ett direkt autonomt eller metaboliskt mått. Signalstödet har `temporal_support_status=unknown` eftersom filterstödet inte är certifierat av epokgränserna, och `source_quality_status=not_recorded`.

### Skapade mätvärdesfamiljer i den kontrollerade filen

Alla sökvägar nedan är relativt H5-roten. `computed` betyder beräknat under exportens kontrakt, inte biologiskt validerat. Beräknade familjer har `measurement_validity=not_assessed`.

| Familj och fysisk sökväg | Exempel på skapade mått | Observerad status och tolkningsgräns |
|---|---|---|
| `dynamical_families/diffusion/v1` | `diffusion_total`/`D_total`, `diffusion_effective_dimension`/`d_diff`, koncentration, tensor, `A_bD`, `R_b_over_a`; även `increment_covariance_level0` | Beräknad lokal inkrementkovarians; `ito_not_qualified`. Inkrement-, residual- och Itô-kovarians är olika objekt. |
| `dynamical_families/drift/v1` | `realized_velocity_level0`; `conditional_mean_rate_level1/{pooled,blocked_crossfit,lag_diagnostics}` | Beräknade ändliga differenser och villkorade medelhastigheter; ingen identifierad Itô-drift. |
| `dynamical_families/one_step/v1` | Affin karta, medelhastighet, innovationskovarians; operatorns maxgain-, volymgain- och rotationshastighet; generatorproxyns spektrala/numeriska abskissa, divergens och rotation | Lag 1 beräknat/identifierat enligt exportens grind. Funktionsvärden är inte självständigt OOS-validerade mekanismer. Direkta lag-2-kartan har otillräckligt stöd; dess härledda mått är ej testbara. Itererad horisontkarta har otillräckligt stöd. |
| `dynamical_families/amplification/v1` | `neighbor_gain_q90`, gainhastighet, separationshastighet, molnvolymförändring | Beräknade observationer av samma grannpar framåt; inte operatorns maximala förstärkning. |
| `dynamical_families/history/v1` | `history_predictive_gain_level1`, `history_conditioned_operator_level2` | Beräknade; historikkonditionerad operator identifierad enligt exporten. Varken återställd Markovegenskap eller bevis för latent minne. |
| `dynamical_families/turning/v1` | Vinkel och vinkelhastighet | Beräknade realiserade riktningsändringar; inte operatorrotation. |
| `dynamical_families/destination/v1` | Certifikat, ingen användbar kommittorserie | `not_testable`; explicit A/B-/reaktionskoordinat saknas. |
| `dynamical_families/resilience/v1` | Certifikat, ingen perturbationsserie | `not_testable`; perturbationsprotokoll saknas. |
| `jacobian/derived_metrics/v1`, `jacobian_9D/derived_metrics/v1` | Abskissor, reaktivitetsgap, rotation, spår, Henrici-mått, stable-reactive-fraktion | Beräknade chart-Jacobianmått; separat estimator från enstegsoperatorn. |
| `finite_time_response/v1/{primary,stratified_9d}` | Gain, responsdimension och koncentration vid 1, 2, 4 steg | Beräknade, `validation_level=model_derived`; 4, 8, 16 s nominellt här. |
| `transition_residuals/v1/*`, `transition_residual_covariance_proxy/v1/*` | Prediktionsresidualer och Q-proxy | Beräknade; Q är residualkovarians, inte identifierat processbrus. |
| `stochastic_reachability/v1/{primary,stratified_9d}` | `w_q`, `d_eff`, `v_norm`, `a_q`, `c_1_q` | Beräknad modellpropagerad spridning. Primärgrenen anger **93 propagatorsteg**, inte ett standardiserat H4-mått. |

Alias räknas inte som oberoende mätvärden. Enstegskartans window-formade serier kan vara upprepningar av en inspelningsoperator och får inte räknas som separata observationer. Fullständig lista över 4 339 datasetvägar/former och 52 statusbärande grupper finns i [inventeringen](h5_inventory_20260920.json), reproducerbar med [inspektionsskriptet](inspect_single_h5.py). Dessa antal beskriver schemaobjekt, inte 4 339 vetenskapliga utfall. Kontroll av en fil etablerar inte kohortens täckning.

## 3. Förväntningar och hypoteshierarki

**Huvudförväntan:** propofol kan minska den lokala spridningens storlek och antalet effektivt utnyttjade riktningar. Detta är en rimlig men osäker överföring från tidigare kapacitetsresultat till nya inkrementmått. Lokal inkrementkovarians är inte samma sak som framtida tillgänglighet eller tidigare reachabilitykapacitet. Separat skalning inom inspelningar kan dessutom dölja amplitudminskning eller förändra geometrin.

| ID | Förhandsutsaga | Exakt primärt utfall och status |
|---|---|---|
| H1 | Lägre lokal inkrementspridning under första protokollbestämda sederingsfasen än vid baseline | Median av `dynamical_families/diffusion/v1/series/diffusion_total` över giltiga tidpunkter. Primär, villkorad av avsnitt 8. |
| H2 | Lägre effektiv dimensionalitet i samma kontrast | Median av `.../series/diffusion_effective_dimension`. Primär, samma grindar. |
| S1 | Förändrad balans mellan medelrörelse och inkrementvariation; möjlig ökning av transportdominans | `R_b_over_a` och `A_bD`, sekundärt och tvåsidigt. Ingen säker riktning registreras; tidigare Apollo-resultat stöder inte ett robust capturepåstående. |
| S2 | Minskad kortsiktig förstärkning är möjlig | `neighbor_gain_q90_level1/series/neighbor_gain_q90` under amplification och `operator_max_gain_rate_level2/series/operator_max_gain_rate` under one_step; separata explorativa utfall med svag förväntan om minskning. |
| S3 | Historik kan bära information utöver aktuellt tillstånd | `history_predictive_gain_level1/summary/history_predictive_gain` under history; positivt gain är en metodfråga, skillnaden mellan faser analyseras tvåsidigt och explorativt. |
| S4 | Responsförmåga kan vara mer informativ än dos för vissa dynamiska egenskaper | Explorativ association/prediktion efter verifierad beteende- och doskoppling. Ingen förhandsrangordning av familjer. |

H1/H2 har riktade förväntningar men testas tvåsidigt. Motsatt signifikant riktning motsäger utsagan. Utebliven signifikans visar inte likvärdighet. Vi antar varken monotonitet baseline → sedering → djupare sedering, nödvändig patologisk lock-in, specifikt tecken för turning/reaktivitet eller att lägre dimensionalitet betyder medvetslöshet.

Recovery analyseras som separat sekundär fas: återgång mot baseline är en förväntan, inte en garanterad reversering. Responsfrånvaro, om faktiskt dokumenterad, används som beteendevariabel och benämns inte automatiskt medvetslöshet. Utan sömn- och epilepsidata kan denna studie inte bevisa dissociationen mellan fysiologisk låg kapacitet och patologisk infångning.

## 4. Population, kontraster och datagrain

Alla 20 personer i den frysta exporten är målpopulation; inga personer läggs till eller tas bort på grund av observerade effekter. Primär kontrast är **första protokollbestämda sederingsfas minus pre-drug baseline**, parad inom person. Fasen definieras från originalprotokoll/metadata, aldrig som den med störst geometrisk förändring. Recovery får inte ersätta saknad baseline. Om dessa faser inte kan identifieras tillförlitligt är H1/H2 ej testbara; annan kontrast blir ett daterat tillägg eller explorativ.

Alla inspelningar får en tabell med subjekt, session, run/acq, källfil, protokollfas, tid, faktisk responsvariabel och eventuell uppmätt koncentration. Varje mappning ska ha en källa. Nummer på run/acq och `condition=sedation` räcker inte. Baseline–senare sederingsfas, baseline–recovery och responsiv–icke-responsiv är sekundära kontraster endast där metadata stödjer dem.

Aggregering: giltiga epoker → inspelningsmedian → median över eventuella upprepade inspelningar i samma subjekt/fas → parad subjektskillnad. Alla personer får lika vikt. För skalarer på inspelningsnivå används värdet en gång. Ingen epokbaserad ökning av stickprovsstorlek tillåts. Om flera separata sessioner finns aggregeras först de inom-session-parade skillnaderna med median per person.

## 5. Giltighet, luckor och skalning

Primäranalysen använder exakt den exporterade 3D-koordinaten och dess redan exporterade diffusionmått. Ingen justering av MNPS-/9D-definitioner, ingen tuning mot önskad tillståndsskillnad och ingen ersättning av saknade mått med noll görs.

Inklusionsregler per utfall/inspelning: korrekt schema och koordinatkontrakt; `computation_status=computed`; `support_status=sufficient` där fältet finns; ändliga värden på rätt source-/tidsindex och giltig lokal mask. För diffusion krävs minst 30 giltiga tidpunkter och minst 50 % giltiga exporterade tidpunkter; befintliga hårdare estimatorgränser gäller också. Dessa analysgränser är förhandsvalda praktiska stödkrav, inte bevis för biologisk validitet. Antal och orsaker för bortfall redovisas per fas och person. Ingen global complete-case-reduktion över alla familjer görs.

Inget inkrement får korsa inspelnings-, sessions- eller stödbrott. Positiva observerade tidssteg, källindex, filterstöd och transition-support-ID ska granskas. Gap ska ge bortfall, inte interpolation. Ett regulariserat egenvärde är inte belägg för en biologiskt aktiv dimension. För H1/H2 redovisas därför som känslighetsanalys resultat efter att tidpunkter med `psd_floor_applied` exkluderats med samma stödregler; om ingen stödd analys kvarstår anges detta.

Skalgrinden är central: lokalt standardiserade inspelningar kan jämföras som **relativ chartgeometri**, men får inte användas för att hävda absolut neural kapacitets-/variansminskning. Om gemensamt, dokumenterat fasöverskridande ankare saknas nedgraderas H1/H2 till explorativa kontraster i den lokalt standardiserade exporten. Konfirmatorisk amplitudtolkning kräver separat fryst omexport med ankare definierat utan tillståndsresultat; den nuvarande exporten skrivs inte över. Även H2 kan ändras av anisotrop skalning. 9D är endast känslighets-/explorativ analys med samma fallbacksignatur, inte en ersättare om 3D ger oönskat resultat.

## 6. Statistik och beslut

För H1 och H2 beräknas varje persons skillnad sedering minus baseline i ovanstående inspelningsmedianer. Primär inferens är ett exakt tvåsidigt parat **teckentest** av sannolikheten för positiv respektive negativ skillnad, villkorat på icke-nollskillnader. Exakta nollor tas bort enbart från teckentestets binomialnämnare och deras antal redovisas. Inga toleranser väljs efter data. Effektstorlek: median parad skillnad i ursprungliga enheter, tillsammans med alla individuella skillnader och ett 95 % percentil-bootstrapintervall (10 000 resamplingar av personer, seed 20260920). Bootstrapintervallet är deskriptivt och inte ett ersättningstest för teckentestets estimand.

De två primära p-värdena Holm-korrigeras tillsammans vid familjevis alfa 0,05. En ej testbar hypotes behålls som p=1 enbart i multiplicitetsbokföringen, aldrig som ett observerat nollresultat. Konfirmatorisk testning kräver minst 10 giltiga personer med icke-nollskillnad per utfall; annars rapporteras endast effekt/bortfall och otillräcklig precision. Detta är en rapporteringsgrind, inte en styrkeberäkning. Med högst 20 personer väntas begränsad precision; ingen observerad post-hoc-power används.

H1/H2 får stöd endast när respektive korrigerade test är signifikant och riktningen är negativ. Ett gemensamt påstående om både storlek och dimensionalitet kräver båda. Positiv signifikant riktning är motbevis mot respektive registrerad riktning. Osäkert intervall/icke-signifikans är inkonklusivt, inte bevis för frånvaro.

Sekundära/explorativa analyser redovisas med effektstorlekar och tydlig explorativ märkning. Denna version tillåter inga sekundära inferentiella p-värden: före sådana test krävs ett daterat tillägg med en uttömmande lista över utfall, aggregeringar och kontraster, fryst före inspektion av deras tillståndseffekter. Därefter BH-korrigeras hela den frysta sekundära familjen gemensamt; ej testbara listade test behålls med p=1 endast i multiplicitetsbokföringen. Ojusterade p-värden, familjestorlek och ej testbara test redovisas. S3/S4 förblir enbart deskriptiva tills dessutom stöd-, surrogat- och läckagegrindarna i avsnitt 7–8 passerats. Inga sekundära fynd ersätter misslyckade primärhypoteser. Likvärdighet, mediation och kausal läkemedelseffekt hävdas inte från denna plan.

## 7. Dynamisk tilläggsinformation och negativa kontroller

NDT-C2 (information utöver aktuellt tillstånd/statiska mått) och C3 (kontextberoende framtidslag vid matchat aktuellt tillstånd) är starkare än H1/H2. De förblir explorativa här. Ett lägre mått under sedering etablerar inget av dem.

En eventuell senare prediktionsanalys måste innan utfallsinspektion låsa responsdefinition, exakta råa spektral-/komplexitetsfeatures, modeller och hyperparametrar i ett daterat tillägg. Basmodellen ska omfatta aktuellt MNPS-tillstånd och spektrala/komplexitetsmått; den utökade modellen lägger till det frysta dynamiska panelvalet. Train/test ska separeras på person, med all normalisering och tuning inom träningsdata. Inga AUC-tal från denna export ska kallas konfirmatoriska utan detta tillägg. Direkta skillnader mellan personernas subject-anchored koordinatnivåer undviks; eventuell prediktion använder verifierat jämförbara inompersonsreferenser.

Historikgain kräver kontroll mot ordningsförstörda surrogat som bevarar tillstånds-/marginalfördelning samt en tidsseparerad baseline. Fönstren överlappar och effektivt filterstöd är okänt; exporterad crossfitstatus/embargo certifierar därför inte läckagefri prediktion. Ingen sådan kontroll har körts här. Exakt blocklängd, purge, surrogatantal och estimator måste låsas från stödmetadata/syntetiska data före denna senare analys; annars rapporteras enbart exporterade deskriptiva gainvärden. C3 kräver dessutom tillräckligt överlapp i aktuell koordinat mellan faser, kontrollerad skalning och matchning utan tillgång till framtidsutfallet.

Modellbaserad reachability hålls separat från H1/H2. Det exporterade `w_q` ackumuleras över 93 steg i den inspekterade primärgrenen; inspelningslängd och horisont kan då förklara skillnader. Ingen jämförelse av dessa skalarer tillåts som gemensam H4-kapacitet. En framtida analys kräver fast fysisk horisont, gap- och residualkontroller, prediktionsvalidering och en uttrycklig estimatorplan. Q-proxy, enstegskartans innovationskovarians och diffusionstensor får aldrig bytas mot varandra.

## 8. Grindar före låsning och analys

1. **G0 – provenance och insyn:** registrera ansvariga författare, deras tidigare data-/resultatinsyn, extern tidsstämpel samt denna fils hash. Spara komplett filmanifest med SHA-256 och processad kod-/konfigurationsproveniens. Inventeringsbilagan har redan hash för den kontrollerade H5-filen och körningens rotsidecars.
2. **G1 – etiketter:** verifiera faskodning och koppling till respons/dos från originalkälla, utan att studera nya dynamiska tillståndseffekter. Saknade beteendedata begränsar frågan till protokollfas.
3. **G2 – jämförbar mätning:** gör en metadata-/stödaudit av alla filer för tidssteg, faktisk feature-fitpopulation, skalning, fallback, giltighet och stödandelar. Nuvarande enfilskontroll stänger inte denna grind. Okända filterstöd blockerar starka prediktiva påståenden. Konfirmatorisk prediktion är blockerad om inte varje datadrivet fit-/normaliseringssteg, även före H5-exporten, kan visas vara begränsat till träningsdata enligt den avsedda valideringsdesignen. Förberäknade koordinater med oklar eller testdataberoende fitpopulation får endast användas deskriptivt/explorativt; en korrekt uppdelad omberäkning krävs annars.
4. **G3 – fryst analyskod:** verifiera läsare och aggregering på syntetiska fall med luckor, NaN, nollskillnader, otillräckligt stöd och broadcastade enstegsoperatorer. Bevara exportens canonical/aliasrelationer. En oberoende granskare ska kontrollera slutlig kod före tillståndskontraster.
5. **G4 – låsning:** dokumentera G0–G3 och eventuella ändringar i ett versionssatt tillägg innan gruppkontraster körs. Varken ett läsbart H5 eller ett godkänt test stänger en vetenskaplig validitetsgrind. Om ändringar görs efter inspektion av effekter märks berörda analyser explorativa/post-hoc.

**Aktuell bedömning: PARTIAL PASS för inventering och protokollutkast; konfirmatorisk analys ännu inte frigiven.** Mätkontrakt, ingestrutiner och numeriska data är oförändrade. Säker slutsats nu: familjerna finns med de certifikat som anges i en kontrollerad fil. Biologiska propofolskillnader, medvetandetillstånd, kohorttäckning och empirisk validitet är inte etablerade. Nästa grind är etikett- och skalningsaudit.

## 9. Källor och reproduktion

1. Chennu et al. (2016), *Brain Connectivity Dissociates Responsiveness from Drug Exposure during Propofol-Induced Transitions of Consciousness*, [originalartikel](https://doi.org/10.1371/journal.pcbi.1004669). Används för studiedesignens skillnad mellan exponering och respons, inte som validering av de nya NDT-måtten.
2. Lokalt tidigare manuskript: `J:\repos\NoeticDiffusion\articles\Reduced Dynamical Capacity Does Not Imply Unconsciousness\Reduced Dynamical Capacity Does Not Imply Unconsciousness.txt`. Läses som tidigare resultatunderlag, inte oberoende evidens för nya endpointdefinitioner.
3. Lokalt teoriunderlag: `J:\repos\nmd-analysis\articles\aa_basicinfo\ndt_compact_summary,md`. Särskilt NDT-C1/C2/C3 och skillnaden mellan drift, diffusion, reachability, destination och resiliens.
4. Exportguide: `J:\repos\nmd-analysis\articles\aa_basicinfo\Output_variables_guide.md`. Faktisk H5-proveniens har företräde framför generiska guideexempel; aktuell arbetskod är inte automatiskt den kod som skapade exporten.
5. Körningens `run_manifest.json`, konfigurationssnapshot, `normalization_report.json`, `features_snapshot.json` och `command_used.txt`, samt [h5_inventory_20260920.json](h5_inventory_20260920.json).

Reproducera enfilskontrollen i PowerShell:

```powershell
& 'J:\repos\nmd-analysis\.venv\Scripts\python.exe' 'J:\repos\nmd-analysis\articles\Apollo_propofol_ndt_v.1.0\preregistration\inspect_single_h5.py'
```

Skriptet öppnar H5 i läsläge och skriver endast inventeringsbilagan. Den ursprungligen lexikografiskt valda filen är nu låst med relativ sökväg och SHA-256; ändrad fil eller filräkning stoppar körningen före överskrivning. Bilagan sparar också en vitlistad metadataextraktion för manifestets antal/etiketter, fönsterlängd, axelnamn, fit-scope, normaliseringsstatus, fallback, signalstöd och propagatorsteg. Inga kohortanalyser, nya mätningar, statistiska tester eller biologiska valideringstester har körts för detta dokument.
