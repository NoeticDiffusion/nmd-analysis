# Sömnstudien: första verifierade artikelpilot

2026-09-06. **PASS för artikelstart och avgränsad importkontroll. PARTIAL PASS
för analysberedskap:** sömnstadiekontraster är ännu inte genomförda.

Artikelmallen är kopierad och anpassad. Ett huvudmanuskript, S1–S6, analysplan,
artikelkod, tester och en aktiv källfilslåst config finns. Huvudmanuskriptet
kompilerar till en tvåsidig PDF som har granskats visuellt. Manuskriptet är
ett utvecklingsutkast, inte en förregistrering eller en färdig resultatartikel.

## Accepterad körning

Använd endast [pilot_verified_final_20260906](../results/pilot_verified_final_20260906).
Två tidigare utvecklingskörningar är bevarade och markerade som ersatta.

En verifierad kontinuerlig sub-99-inspelning lästes utan ändring. Samtliga
16 aktiverade analystabeller exporterades utan fel eller saknade tabeller.
Koordinatorn verifierade källfilens hash före/efter, konfigurationshash och
sex kodfilshashar mot aktuell kod. Separata hashvärden för exporterade tabeller
finns i [koordinatorns kontroll](../handover/20260906_coordinator_validation.json).

| Underlag | Utfall |
|---|---|
| MNPS 3D och 9D | 1 068 rader i respektive koordinatlager; alla koordinatvärden finita. Inspelningssammanfattningar exporterade. |
| Diffusion | 1 068 beräknade tensorrader; `D_total`, `d_diff`, `c_diff` finita i 1 068/1 068. |
| Driftberoende diffusion | `A_bD` och `R_b_over_a` saknar finita värden i alla 1 068 rader; `drift_mode=not_supplied`. |
| Jacobian och FTR | 3D/9D-tabeller exporterade; FTR har tre inspelningshorisonter per gren. |
| Q | Båda dimensionsgrenarna beräknade på inspelningsnivå. |
| W_Q | 3D beräknad; 9D fortsatt `invalid/reachability_numerical_overflow`. |
| Destination | `not_testable`: explicit A/B- och reaktionskoordinatkontrakt saknas. |
| Resilience | `not_testable`: perturbationsprotokoll saknas. |

Diffusionens tensorgiltighet innebär alltså inte att varje skalar i familjen
är tillgänglig. De nya familjernas beräknade värden är fortfarande
`measurement_validity=not_assessed` och `claim_status=no_biological_claim`.
Äldre MNPS-sammanfattningstabeller saknar motsvarande certifikatkolumner;
deras kontrakt måste läsas tillsammans med pilotmanifestet.

## Sömnstadieunderlag

| Registrerad etikett | Fönster |
|---|---:|
| Wake | 275 |
| N1 | 20 |
| N2 | 642 |
| N3 | 15 |
| REM | 107 |
| Okänd, kod 8 | 9 |
| Totalt | 1 068 |

Tider, etiketter och fönstergränser är indexmässigt anpassade. Inga gap eller
överlapp flaggades mellan dessa källfönster. Detta bevisar inte att varje
features filterstöd eller varje diffusionsskattnings grannskap ligger inom
ett och samma stadium. Alla rader har därför `stage_purity_status=not_assessed`.
De små antalen N1/N3 är stödbegränsningar i denna pilot, inte skäl att i
efterhand välja gynnsamma kontraster. Fönster är inte oberoende deltagare.

## Ytterligare kontraktsbegränsningar

Koordinatkontraktet är `subject_anchored`. Ankarets `anchor_id`, `anchor_hash`
och `anchor_source` är dock inte registrerade i den upplösta proveniensen;
vi har inte verifierat dessa genom andra källor i detta steg.

Supportsignaturen anger `e_m` som fallback från `ppg_rate_bpm` och
`semantic_equivalence=false`; den sammansatta e-axelns källa är `mixed`.
En analys får inte presentera detta som ett helt direkt uppmätt, semantiskt
utbytbart EEG-lager. Signaturen ska behållas när individer och mätlager väljs.

Den aktuella diffusionsimplementationen väljer grannar i tillståndsrummet.
Pilotens centrala sömnstadieetikett visar inte vilka stadier dessa grannars
inkrement kommer från. Att studera en globalt skattad geometris värden vid
olika stadier är en annan fråga än att skatta separata stadiebetingade
diffusionsobjekt. Ingen av dessa kontraster är genomförd här.

## Nästa steg

1. Bygg en explicit MNPS-tabell per epoch med koordinatproveniens, labels,
   källfönster och tillgängliga giltighetsmasker. Verifiera vad som är känt om
   feature-/filterstöd över stadiegränser; håll okänt stöd synligt.
2. Specificera diffusionens analysfråga och kartlägg grannskapens stöd.
   Behåll skattaren oförändrad under denna kontroll. Stadiebetingad
   omskattning vore ett separat metodbeslut, inte en enkel tabellkoppling.
3. Lås ett litet antal primära mått och kontraster före deras utvärdering.
   Gör först beskrivande figurer för utvecklingspiloten, sedan ett separat
   deltagarbaserat kohortprotokoll. Håll 9D-volym och okvalificerad drift
   utanför biologiska slutsatser.

Ingen ny ingest, helkohort, hypotesprövning eller publicering genomfördes.
Subagenterna stod för artikel, implementation, oberoende tester och första
kod-/körningsreview. Koordinatorns slutliga regressionstestning:
**25 passed in 3.27s**. Se [oberoende review](../peer_review/01_pilot_review.md)
och [körningsanteckning](../handover/20260906_verified_pilot.md).
