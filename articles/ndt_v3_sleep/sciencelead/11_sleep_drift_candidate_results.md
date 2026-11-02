# E3: driftkandidatförsöket genomfört

Koordinatorbeslut: **PARTIAL PASS för kandidatens indatastöd; PASS för implementation och numerisk verifiering; METHOD-LIMITED för vetenskaplig tolkning.**

Två Luna/xhigh-subagenter utförde implementation/körning respektive oberoende stödgranskning. Koordinatorn verifierade direkt mot HDF5, gjorde slutlig kodgranskning och skrev resultat och dagbok. Befintlig M3-estimator återanvändes utan ändring. MNPS-definitioner, Jacobianer, diffusion, giltighetsflaggor och tidigare sömnresultat är oförändrade.

| Registrering | 3D lokal medel / lokal linjär | 9D lokal medel / lokal linjär | Utfall |
|---|---|---|---|
| sub-99 | 100 / 100 ändliga kandidatvektorer | 100 / 100 ändliga kandidatvektorer | Beräknad, ej kvalificerad kandidat |
| sub-1 | null / null | null / null | Avvisad av befintligt källkontrakt |

Sub-1 har geometrikontraktstatus `adjusted`, medan den frysta M3-referensen kräver `ok`. Bakgrunden är 57 ogiltiga 9D-Jacobianfönster enligt konditionstalskontrollen. De valda koordinatarrayerna är ändliga; avslaget bevisar alltså varken numeriskt ogiltiga koordinater eller avsaknad av drift. Vi ändrade inte regeln för att få ett positivt utfall. Stödgranskningens separata explorativa direktanrop för sub-1 ingår inte i den accepterade primärkörningen.

Det frysta försöket använder träningsinkrement 0–599 och utvärderingsinkrement 700–799, 32 grannar, minst 12 träningsobservationer, dt 30 sekunder och embargo 60 sekunder. De närmaste registrerade stödfönstren ligger 2 970 sekunder isär. Inga ändpunkter delas mellan träning och utvärdering. De 400 vektorerna är fyra beräkningar vid samma 100 utvärderingsinkrement, inte 400 oberoende observationer.

Koordinatorns omräkning utan import av körningen eller estimatorn reproducerade alla 400 kandidatvektorer exakt och kontrollerade deras utvärderingsinkrement, index, tidsstöd och hashvärden. Alla fyra sub-1-avslag har null-prediktioner. Båda H5-källorna har oförändrad SHA-256. **161 tester passerar** i den slutliga artikel- och driftregressionen. Slutgranskningen har inga kvarstående kodfynd.

## Vad resultatet tillåter

Vi kan beräkna reproducerbara kandidater för lokal koordinathastighet i sub-99 med separerade tränings- och utvärderingsinkrement. Det är ännu inte identifierad Itô-drift, en stadiespecifik effekt eller oberoende genom hela bearbetningskedjan. Normaliseringens referensanpassning omfattar samtliga 1 068 respektive 915 rader, inklusive utvärderingsraderna. Effektivt filterstöd är fortfarande okänt. PPG/EOG-skillnaden i `e_m` är bevarad i proveniensen.

De explicita koordinatsökvägarna innehåller samma värden som de subjektankrade lagren i just dessa H5-filer. Det ger ingen generell garanti om alias och kvalificerar inte drift–diffusionskoppling. `candidate_not_qualified` och `no_biological_claim` kvarstår. A_bD och R_b_over_a är fortsatt ej testbara i de kanoniska ytorna; inga nya sömnstadiekontraster har beräknats.

Nästa avgränsade grind är en separat dokumenterad regel för kandidatens koordinatstöd när övergripande geometrikontrakt är `adjusted`, med det ursprungliga avslaget bevarat. En starkare oberoendeprövning kräver dessutom en på förhand fastställd behandling av koordinatanpassning och effektivt signalstöd. Dessa frågor ska avgöras före nya tolkningar av drift eller drift–diffusionskoppling.

## Accepterat underlag

- Körning: `results/sleep_drift_candidate_20260910/run_r2`; den första körningen i föräldrakatalogen är historik. Prediktionsartefakten är oförändrad mellan körningarna.
- Specifikation: `config/sleep_drift_candidate_20260910.json`, fryst spec-hash `fb95a1b4a1fa3058e5fcb065d48978ef87e7b505044fcd57e14120e0978c7c77`.
- Reproduktion: `handover/20260910_sleep_drift_candidate_commands.md`.
- Granskning: `peer_review/16_sleep_drift_candidate_support_audit.md` och `peer_review/17_sleep_drift_candidate_final_review.md`.
- Direkt verifiering: `H:/SourceRepo2/NeuralManifoldDynamics/project/v3/sleep_drift_candidate_20260910/coordinator_direct_verification_r2.json` och dess verifieringsskript.
