# Preliminära resultat: I-CARE coma cohort

Detta dokument sammanfattar de första preliminära resultaten från den nya I-CARE-kohorten som körts genom den tunna coma-specifika NDT-pipelinen. Syftet är att ge en arbetsnära översikt över datatäckning, metoder, huvudsakliga signaler och nuvarande begränsningar innan resultaten formuleras mer formellt i manus.

## Kort sammanfattning

Det preliminära huvudfyndet är att `Good` och `Poor` framför allt separerar i `reachability`-familjen snarare än i de enklaste 3D-måtten. De starkaste skillnaderna återkommer i mått som `tube_log_det_median`, `cone_log_det_h1/h2/h3/h4_median`, `tube_log_eig_var_median`, `cone_log_eig_var_*`, `tube_kappa_median` och relaterade cone-/tube-mått. Det tyder på att utfallsskillnader i denna lilla kohort i hög grad ligger i hur det lokala tillståndsrummet är geometriskt tillgängligt och strukturerat, inte bara i enkla läges- eller amplitudskillnader.

Samtidigt syns enklare skillnader också. `Good` tenderar att ha högre spridning i vissa delrum, till exempel högre `m_std` och högre `d_n_median`, medan `Poor` tenderar att ha högre `rotational_power_median`. Ett första arbetsantagande är därför att bättre utfall i denna cohort hänger ihop med en annan geometrisk regim snarare än endast "mer aktivitet".

`C/TI/P-light` ser lovande ut som explorativt sammanfattningslager, men ska ännu inte användas som ett centralt resultatspår. Det nuvarande patient-timebin-underlaget är glest och `P`-axeln domineras delvis av extrema värden.

## Data och kohort

- `14` patienter ingår i den första körningen.
- Utfallsfördelning: `8 Good`, `6 Poor`.
- Totalt processades `726` H5-runs.
- Adapterlagret gav `3630` run-level rows och `0` unmatched joins.
- `701` runs använde `time_reference.v1` direkt, medan `25` runs föll tillbaka till `wfdb_header_subject_anchor` på grund av ogiltiga start-/sluttider i `time_reference`.

Patienterna i denna körning var:

- `Good`: `sub-0332`, `sub-0365`, `sub-0387`, `sub-0404`, `sub-0410`, `sub-0422`, `sub-0435`, `sub-0439`
- `Poor`: `sub-0379`, `sub-0383`, `sub-0406`, `sub-0409`, `sub-0420`, `sub-0428`

Inspelningsspannet varierade tydligt mellan patienter, men grupperna var inte grovt obalanserade:

- `Good`: median coverage cirka `45.4 h`, spann ungefär `12.7-100.3 h`
- `Poor`: median coverage cirka `48.0 h`, spann ungefär `24.7-65.3 h`

Detta minskar risken att de tydligaste gruppskillnaderna bara är ett enkelt täckningsartefakt, även om täckning fortfarande måste kontrolleras i senare, striktare analyser.

## Metoder

### Översikt

Analysen byggdes som ett tunt I-CARE-/coma-lager ovanpå den generiska motorn i `ndt-analysis/ndt_analysis`. I stället för att skriva om kärnlogik användes befintliga adaptrar för att läsa H5-filer och extrahera run-level-mått, varefter coma-specifika steg lades till för:

- tidsankring och time-bin-aggregering,
- outcome-koppling (`Good` vs `Poor`),
- prognostiska kontraster,
- ett första derivat av `C/TI/P-light`.

### Steg 1: run-level summering

Run-level summeringar byggdes med `articles/comatose_ndt/src/icare_mnps_summary_analysis.py`, som:

1. läser alla H5-runs i den nya ingest-exporten,
2. kör ett urval av generiska analyser via `legacy_adapters.build_adapters(...)`,
3. joinar dessa rader mot coma-specifik tids- och metadata-information,
4. skriver både adaptertabeller och long-format signal-metric-tabeller.

Följande analysfamiljer aktiverades:

- `global_mnps_3d`
- `global_mnps_9d`
- `global_mnps_jacobian_3d`
- `global_mnps_jacobian_9d`
- `global_mnps_jacobian_9d_block_jacobian`
- `reachability_cones`

### Steg 2: tidsaxel och patient-bin-aggregering

Tidsinformation togs i första hand från H5-fält i `time_reference.v1`, med fallback till WFDB-header när nödvändigt. Därefter aggregerades runs till patient/time-bin-summaries. Den aktuella pipelinen arbetar med fyra grova bin:

- `0_24h`
- `24_48h`
- `48_72h`
- `72h_plus`

Aggregering gjordes viktat över tillgängliga run-level observationsvikter, i praktiken med de numeriska viktkolumner som fanns tillgängliga för respektive analysfamilj.

### Steg 3: outcome-kontraster

Outcome-kontraster byggdes med `articles/comatose_ndt/src/icare_outcome_contrast_analysis.py`. För varje analysfamilj, metrik och tidsbin jämfördes `Good` och `Poor` med:

- Mann-Whitney U-test
- Welch's t-test
- Cohen's d
- Cliff's delta

Kontraster kördes både på:

- `run_level`
- `patient_timebin`

I denna cohort blev `632` kontraster estimabla (`status = ok`) på båda nivåerna, medan `158` hade `insufficient_outcome_groups`, främst i sena tidsbin där bara ena utfallsgruppen återstod.

### Steg 4: C/TI/P-light

`C/TI/P-light` byggdes med `articles/comatose_ndt/src/icare_ctip_light_analysis.py` som ett första sammanfattande lager ovanpå handoff-metrikerna från `mnps_summary`.

Kortfattat konstruerades:

- `C` från spread-/capacity-relaterade mått i 3D, 9D och reachability
- `TI` från en kombination av ATI-liknande proxy, låg `q_ratio_h4` och låg `capture_gate`
- `P` från patologilika mått såsom `jacobian_cond`, `aci`, anisotropi och, när tillgängligt, `cfca`

Samtliga komponenter robust-z-skalerades inom aktuell tabell innan de sammanfattades. Det är viktigt att betona att detta fortfarande är ett internt explorativt lager, inte ett färdigvaliderat huvudresultat.

## Huvudsakliga preliminära fynd

### 1. Reachability verkar vara den starkaste signalbäraren

Den tydligaste separationen mellan `Good` och `Poor` ligger i `reachability_cones`.

På `run_level` var flera av de starkaste skillnaderna:

- `tube_log_det_median`: `Good = -12.36`, `Poor = -10.33`, `mannwhitney_p ~ 2.4e-26`
- `cone_log_det_h1_median`: `Good = -15.32`, `Poor = -13.18`, `mannwhitney_p ~ 7.7e-34`
- `cone_log_eig_var_h4_median`: `Good = 10.09`, `Poor = 8.83`, `mannwhitney_p ~ 1.8e-28`
- `tube_kappa_median`: `Good = 72945`, `Poor = 7476`, `mannwhitney_p ~ 2.1e-22`
- `median_cond`: `Good = 63746`, `Poor = 6249`, `mannwhitney_p ~ 2.6e-22`

På `patient_timebin` återkommer samma familj, men med mer modest statistisk styrka, vilket är väntat med ett mycket mindre antal observationsenheter. Några av de tydligaste patient/time-bin-kontrasterna var:

- `cone_log_eig_var_h4_median`: `Good = 11.52`, `Poor = 8.92`, `mannwhitney_p ~ 0.0013`
- `tube_log_det_mean`: `Good = -13.35`, `Poor = -10.64`, `mannwhitney_p ~ 0.013`
- `tube_log_det_median`: `Good = -13.45`, `Poor = -10.79`, `mannwhitney_p ~ 0.017`

Det viktigaste tolkningsmässiga budskapet är inte att alla reachability-mått rör sig i exakt samma "bättre/sämre"-riktning, utan att outcome-skillnader systematiskt dyker upp just i denna geometriska familj. Det stärker arbetshypotesen att prognostiskt relevant information kan ligga i hur lokalt tillståndsrum öppnas, stängs eller deformeras över tid.

### 2. Good visar större spridning i vissa subrum

Utöver reachability syns återkommande skillnader i enklare manifoldmått:

- `global_mnps_3d.m_std` är högre i `Good`
- `global_mnps_9d.d_n_median` är högre i `Good`
- `global_mnps_9d.e_e_std` är också högre i `Good` på patient/time-bin-nivå

På `run_level` var till exempel:

- `m_std`: `Good = 0.7877`, `Poor = 0.6693`, `mannwhitney_p ~ 3.0e-14`
- `d_n_median`: `Good = 0.0558`, `Poor = -0.0188`, `mannwhitney_p ~ 2.9e-14`

Detta är förenligt med en preliminär bild där `Good` inte bara skiljer sig genom reachability, utan också genom större eller mer differentierad variation i vissa lokala koordinataxlar.

### 3. Poor tenderar att ha högre rotational power

Ett mindre men konsekvent fynd är att `Poor` tenderar att ha högre `rotational_power_median`, särskilt i `global_mnps_jacobian_9d`.

På `run_level`:

- `rotational_power_median`: `Good = 0.0230`, `Poor = 0.0255`, `mannwhitney_p ~ 3.5e-13`

Skillnaden är numeriskt liten men relativt stabil. Detta skulle kunna peka mot att vissa mer roterande eller cykliska lokaldynamiska regimer är vanligare i sämre utfall, men den tolkningen är fortfarande spekulativ.

### 4. C/TI/P-light är användbart som explorativt lager, men ännu inte robust nog för starka slutsatser

`C/TI/P-light` kunde byggas för alla `7` patient/time-bin-rader i den nuvarande filen och för `149` run-level-rader. Reachability-komponenterna fanns dock inte fullt ut på run-level i denna derivation, och `cfca` saknades i den aktuella patient-timebin-slicen.

En grov första bild är:

- `Good` har högre `C`
- `Good` har också högre `TI`
- `P` varierar kraftigt och drivs delvis av extrema värden

Detta gör att `C/TI/P-light` i nuläget bör användas som ett hjälpmedel för strukturering och hypotesgenerering snarare än som ett självständigt resultatspår.

## När börjar Good och Poor divergera?

Den viktigaste nya observationen är att separationen inte verkar börja först efter ett eller två dygn. Flera skillnader syns redan under de första timmarna, men mönstret är metrikberoende och inte helt monotont.

### Grov bild från de fördefinierade tidsbinnen

Om man bara tittar på de grova patient-bin-kontrasterna (`0_24h`, `24_48h`, `48_72h`, `72h_plus`) ser man att:

- `tube_log_det_median` redan skiljer grupperna i `0_24h` (`Good = -12.50`, `Poor = -9.91`, `mannwhitney_p ~ 0.008`)
- `rotational_power_median` i `global_mnps_jacobian_9d` också redan skiljer i `0_24h` (`Good < Poor`, `mannwhitney_p ~ 0.013`)
- `m_std` och `d_n_median` visar tidiga skillnader i samma riktning (`Good > Poor`), men når på patient-bin-nivå bara trendnivå i `0_24h`

Det betyder att man redan i det första dygnet ser tecken på separation, särskilt i reachability- och rotationsrelaterade mått.

### Finare run-level-bild: skillnader syns redan inom 0-6 timmar

När samma fråga bryts ned mer finmaskigt på run-level till ungefärliga fönster `0_6h`, `6_12h`, `12_24h`, `24_48h` och `48_72h` blir bilden tydligare.

Redan inom `0-6 h` ses skillnader i flera centrala mått:

- `tube_log_det_median`: `Good = -14.12`, `Poor = -9.45`, `mannwhitney_p ~ 7.7e-05`
- `rotational_power_median`: `Good = 0.0211`, `Poor = 0.0252`, `mannwhitney_p ~ 1.1e-04`
- `tube_d_eff_median`: `Good = 2.80`, `Poor = 2.53`, `mannwhitney_p ~ 0.0039`
- `tube_capture_gate_median`: `Good = 1.86`, `Poor = 2.23`, `mannwhitney_p ~ 0.012`
- `q_ratio_h4_median`: `Good = 0.340`, `Poor = 0.264`, `mannwhitney_p ~ 0.010`
- `d_n_median`: `Good = 0.043`, `Poor = 0.010`, `mannwhitney_p ~ 0.016`

Detta talar för att divergence inte bara uppstår sent, utan att skillnader i geometrisk regim redan kan anas under de första timmarna efter inspelningsankaret.

### 12-24 timmar: separationen blir bredare och mer stabil

Mellan `12-24 h` blir skillnaderna tydligare och mer konsekventa över flera familjer:

- `tube_log_det_median` förblir tydligt separerat (`mannwhitney_p ~ 6.5e-09`)
- `rotational_power_median` är fortsatt högre i `Poor` (`mannwhitney_p ~ 3.0e-14`)
- `m_std` blir tydligare högre i `Good` (`mannwhitney_p ~ 2.3e-04`)
- `d_n_median` blir tydligare högre i `Good` (`mannwhitney_p ~ 1.4e-04`)
- `tube_capture_gate_median` byter riktning jämfört med `0-6 h`, så att `Good > Poor` i detta fönster (`mannwhitney_p ~ 0.0029`)

Detta tyder på att den första separationen följs av en mer utbredd omstrukturering där både reachability- och manifoldmått differentierar grupperna.

### 24-48 timmar: tydlig separation kvarstår, men vissa mått byter riktning

Under `24-48 h` kvarstår flera av de tydligaste skillnaderna:

- `tube_log_det_median` förblir starkt separerat (`mannwhitney_p ~ 3.0e-13`)
- `rotational_power_median` är fortsatt högre i `Poor` (`mannwhitney_p ~ 0.0021`)
- `m_std` är fortsatt högre i `Good` (`mannwhitney_p ~ 4.5e-07`)
- `d_n_median` är fortsatt högre i `Good` (`mannwhitney_p ~ 3.2e-04`)

Samtidigt verkar vissa reachabilitymått inte bara förstärkas linjärt utan byta relation mellan grupperna:

- `tube_d_eff_median` är högre i `Good` tidigt (`0-6 h`), men lägre i `Good` under `24-48 h`
- `tube_capture_gate_median` är lägre i `Good` tidigt, men högre i `Good` under `12-24 h` och `24-48 h`
- `q_ratio_h4_median` är högre i `Good` tidigt, men lägre i `Good` under `24-48 h`

Detta är viktigt, eftersom det antyder att skillnaden mellan grupperna inte bara är en statisk offset. Snarare ser det ut som att grupperna följer olika tidsbanor genom flera geometriska regimer.

### 48-72 timmar: färre observationer och svagare stabilitet

I `48-72 h` finns fortfarande signal i vissa mått, exempelvis:

- `tube_log_det_median` är fortsatt lägre i `Good`
- `m_std` är fortsatt högre i `Good`

men antalet patienter är då mindre och flera kontraster blir mindre stabila. Resultaten i detta fönster bör därför tolkas försiktigare än de tidiga och mellantidiga fönstren.

### Praktisk tolkning

Den mest försiktiga sammanfattningen är därför:

1. `Ja`, vissa skillnader mellan `Good` och `Poor` syns redan under de första timmarna.
2. Den tydligaste tidiga separationen syns i `reachability` (`tube_log_det`) och i rotationsrelaterade mått (`rotational_power`).
3. Mellan ungefär `12-48 h` blir separationen bredare och mer konsekvent över flera metrikfamiljer.
4. Flera mått verkar ändra riktning över tid, vilket talar för att det inte räcker att bara jämföra grupper utan att också modellera deras tidsförlopp.

## Ännu finare tidupplösning: 0-1 h, 1-2 h, ... 11-12 h

För att testa om separationen verkligen börjar omedelbart eller om den växer fram under första halvdagen gjordes en extra run-level-genomgång i en-timmesfönster från `0-1 h` till `11-12 h` för sex nyckelmått:

- `tube_log_det_median`
- `rotational_power_median`
- `tube_d_eff_median`
- `tube_capture_gate_median`
- `q_ratio_h4_median`
- `d_n_median`

Detta är fortfarande ett litet underlag, så dessa timvisa resultat ska läsas som en explorativ tidskarta snarare än som slutlig inferens. Men de är ändå tillräckligt informativa för att säga något om *när* separationen tycks börja.

### 1. `tube_log_det_median` divergerar omedelbart

Det tydligaste mönstret i den finfördelade analysen är att `tube_log_det_median` redan skiljer grupperna i det allra första fönstret:

- `0-1 h`: `Good = -20.01`, `Poor = -8.96`, `mannwhitney_p ~ 0.005`

Detta är den starkaste tidigaste signalen i hela timanalysen. Därefter ligger `Good` fortsatt lägre än `Poor` i nästan alla fönster upp till `11-12 h`, även om inte varje enskild timma når signifikans. Mönstret talar därför för att den huvudsakliga reachability-separationen i log-determinantliknande mått redan är närvarande från början av inspelningsförloppet.

### 2. `tube_capture_gate_median` och `q_ratio_h4_median` visar också mycket tidig skillnad, men mer instabilt

Två andra reachabilityrelaterade mått visar också mycket tydlig separation redan i `0-1 h`:

- `tube_capture_gate_median`:
  - `0-1 h`: `Good = 1.47`, `Poor = 2.41`, `mannwhitney_p ~ 0.0016`
- `q_ratio_h4_median`:
  - `0-1 h`: `Good = 0.414`, `Poor = 0.214`, `mannwhitney_p ~ 0.0031`

Men till skillnad från `tube_log_det_median` är dessa mått mer dynamiska efter första timmen:

- `tube_capture_gate_median` är tydligt lägre i `Good` i `0-1 h`, men försvagas snabbt och tenderar senare att byta riktning
- `q_ratio_h4_median` är tydligt högre i `Good` i `0-1 h`, men blir sedan mycket mindre stabilt och visar tecken på riktningsskifte efter några timmar

Detta tyder på att mycket tidiga skillnader i capture-/gatingregim kan finnas redan omedelbart, men att deras tidsutveckling sannolikt är mer komplicerad än en enkel bestående gruppoffset.

### 3. `rotational_power_median` verkar bli tydligare efter några timmar

`rotational_power_median` visar en konsekvent tendens till högre värden i `Poor`, men på en-timmesnivå ser effekten inte lika omedelbart ren ut som för `tube_log_det_median`.

Några nyckelfönster:

- `0-1 h`: `Good = 0.0172`, `Poor = 0.0245`, Welch `p ~ 0.030`, men Mann-Whitney ännu inte tydligt signifikant
- `4-5 h`: `Good = 0.0230`, `Poor = 0.0285`, `mannwhitney_p ~ 0.0037`
- `7-8 h`: trend (`mannwhitney_p ~ 0.066`)
- `9-10 h`: trend (`mannwhitney_p ~ 0.059`)

Den praktiska läsningen är därför att rotationsskillnaden sannolikt finns mycket tidigt i svag form, men blir tydligare runt `4-5 h` och fortsätter därefter som ett mer stabilt sekundärt separationsspår.

### 4. `d_n_median` ser ut att börja divergera runt 4-7 timmar

`d_n_median` har inte samma omedelbara `0-1 h`-signal som `tube_log_det_median`, men utvecklar i stället en tydligare separation efter några timmar:

- `4-5 h`: `Good = 0.053`, `Poor = -0.048`, `mannwhitney_p ~ 0.00033`
- `6-7 h`: `Good = 0.062`, `Poor = -0.086`, `mannwhitney_p ~ 0.0080`
- `11-12 h`: `Good = 0.055`, `Poor = -0.094`, `mannwhitney_p ~ 0.029`

Detta tyder på att `d_n_median` inte primärt är en omedelbar "first-hour marker", utan snarare en måttfamilj där skillnaden blir tydligare när de två gruppernas trajectories redan hunnit börja separera.

### 5. `tube_d_eff_median` visar tidig trend men inte stark timvis stabilitet

`tube_d_eff_median` pekar i samma riktning tidigt:

- `0-1 h`: `Good = 2.55`, `Poor = 2.37`
- `1-2 h`: `Good = 2.98`, `Poor = 2.50`, `mannwhitney_p ~ 0.081`
- `3-4 h`: `Good = 2.81`, `Poor = 2.44`, `mannwhitney_p ~ 0.081`

men på en-timmesupplösning når det sällan tydlig signifikans inom `0-12 h`. Tillsammans med den tidigare `0-6 h`-analysen antyder detta att effekten finns där, men är fördelad över flera tidiga fönster snarare än koncentrerad till en enda "skarp timme".

### Sammanfattning av första tydliga timmar per mått

En praktisk arbetskarta blir därför:

- `tube_log_det_median`: tydligast redan vid `0-1 h`
- `tube_capture_gate_median`: tydligast redan vid `0-1 h`, men mer instabilt efteråt
- `q_ratio_h4_median`: tydligast redan vid `0-1 h`, men mer instabilt efteråt
- `rotational_power_median`: blir tydligare runt `4-5 h`
- `d_n_median`: börjar se tydligare separation runt `4-7 h`
- `tube_d_eff_median`: tidig trend, men ingen enskild timma sticker ut lika tydligt som för `tube_log_det_median`

### Arbetsmässig tolkning av timanalysen

Den finfördelade bilden talar för att `Good` och `Poor` inte bara divergerar "någon gång under första dygnet". I stället verkar minst två saker ske:

1. En mycket tidig separation finns redan under första timmen i vissa centrala reachabilitymått, särskilt `tube_log_det_median`, `tube_capture_gate_median` och `q_ratio_h4_median`.
2. Andra mått, som `rotational_power_median` och `d_n_median`, verkar i större grad spegla en efterföljande divergence som blir tydligare efter några timmar, ungefär kring `4-7 h`.

Det gör att en rimlig arbetshypotes är att outcome-relaterad geometrisk separation börjar mycket tidigt, men att olika metrikfamiljer fångar olika faser av denna separation.

## Vad vi ännu inte kan säga

### Sleep spindles

Det går ännu inte att göra ett starkt påstående om `sleep spindles` från denna cohort-körning. Den aktuella bunten innehåller inte ett direkt spindle-event-lager, och därför bör inga påståenden om faktiska spindle-händelser göras enbart från dessa outputs.

### Starka kausala eller kliniska slutsatser

Kohorten är fortfarande liten och analyserna är i detta skede explorativa. Resultaten ska därför främst läsas som:

- signalspaning,
- prioritering av vilka analysfamiljer som verkar mest lovande,
- och vägledning för vilka figurer, tabeller och robusthetskontroller som bör byggas härnäst.

## Begränsningar

- Endast `14` patienter ingår hittills.
- Coverage skiljer sig mellan patienter.
- Sena tidsbin saknar ibland båda utfallsgrupperna.
- `25` runs hade bristfällig `time_reference` och krävde fallback till WFDB-header.
- `C/TI/P-light` är fortfarande glest och delvis ofullständigt, särskilt för `cfca`.
- Någon separat spindle-/event-locked-analys är ännu inte integrerad i denna coma-bundle.

## Arbetsmässig slutsats

Om vi ska välja ett huvudspår för nästa manusnära resultatsektion är det just nu `reachability`. Det är där skillnaderna mellan `Good` och `Poor` är mest konsekventa och mest statistiskt framträdande, både på patient/time-bin- och run-level-nivå. Ett rimligt nästa steg är därför att:

1. skriva en första reachability-fokuserad resultattext till manus,
2. bygga 1-2 paper-facing figurer för de starkaste cone-/tube-måtten,
3. fortsätta använda `C/TI/P-light` som ett sekundärt synteslager,
4. och först därefter avgöra om spindle-spåret ska lyftas in som separat modul när event-data finns på plats.
