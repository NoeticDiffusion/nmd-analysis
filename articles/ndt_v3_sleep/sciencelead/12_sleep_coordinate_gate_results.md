# Koordinatstödsgrinden genomförd

Koordinatorbeslut: **PASS för den avgränsade koordinatstödsgrinden; METHOD-LIMITED för vetenskaplig driftkvalificering.**

Den separata regeln tillåter nu beräkning av driftkandidater i båda utvecklingsregistreringarna, utan att ändra det ursprungliga geometrikontraktet eller estimatorn.

| Registrering | Ursprunglig strikt kontroll | Ny koordinatstödsregel | Kandidatvektorer |
|---|---|---|---:|
| sub-99 | Godkänd | Godkänd | 400 |
| sub-1 | Avslag, `adjusted` | Godkänd för avgränsat koordinatstöd | 400 |

Varje registrering har 100 utvärderingsinkrement och fyra beräkningar: lokal medel/lokal linjär estimator i 3D/9D. De 800 vektorerna är inte 800 oberoende observationer. Alla 800 matchar koordinatorns separata omräkning från HDF5 exakt. Sub-99 är numeriskt oförändrad sedan förra E3-körningen. Källfilerna är oförändrade, och sub-1:s ursprungliga avslag finns kvar i varje resultatkombination.

Regeln kräver att 9D-Jacobianens avvisade fönster helt förklaras av konditionstalskontrollen, medan 3D-Jacobianen, koordinaterna, tidsaxeln och det gemensamma epokstödet klarar sina kontroller. Antalet 57 är dokumenterad observation, inte ett tröskelvärde. Saknade eller motsägande metadata, okända felorsaker, tidsluckor, degenererade axlar och icke-ändliga koordinater ger fortsatt avslag. Ingen källstatus skrivs om till `ok`.

Luna/xhigh-subagenter utförde policy, implementation och oberoende granskning. Koordinatorn verifierade numerik och proveniens, gjorde slutlig kodgranskning och skrev resultat/artikel/dagbok. **178 tester passerar**, inklusive 17 nya regressionstester. Kod- och testfynd skickades tillbaka och rättades; negativa testutfall och tidigare körningar är bevarade.

Detta är en utvecklingspolicy efter tidigare datainspektion, fryst före den nya primärkörningen. Det är ingen preregistrering eller validering på osedda data. Normaliseringens referensanpassning omfattar hela inspelningen, inklusive utvärderingsraderna, och effektivt filterstöd är okänt. PPG/EOG-skillnaden kvarstår. Därför är kandidaterna fortfarande `candidate_not_qualified` med `no_biological_claim`; A_bD och R_b_over_a är inte etablerade och inga nya sömnstadiekontraster har gjorts.

**Nästa grind** är en separat specifikation och avgränsad prövning av oberoende i koordinatanpassning och effektivt signalstöd. Den måste klarläggas före starkare påståenden om drift eller drift–diffusionskoppling. Den här koordinatstödsfrågan är däremot besvarad för de två frysta artefakterna.

Accepterad körning: `results/sleep_drift_coordinate_gate_20260912/run_r4`. Specifikation: `coordinate_support_policy_20260912.md` och dess JSON. Reproduktion: `handover/20260912_sleep_drift_coordinate_gate_commands.md`. Granskning: `peer_review/18_sleep_drift_coordinate_policy_review.md` och `peer_review/19_sleep_coordinate_gate_final_review.md`. Direkt verifiering: `H:/SourceRepo2/NeuralManifoldDynamics/project/v3/sleep_drift_coordinate_gate_20260912/coordinator_final_verification_r4.json`. Dagbok: H371 och nmd-analysis330.
