# Stadiumberoenden: fryst utvecklingspolicy och verifiering

Koordinatorbeslut: **PASS** för auditens implementation och **PARTIAL PASS** för analysberedskap. Vetenskaplig kvalifikation är `not_assessed`.

Vi får beskriva associationer mellan registrerade sömnstadier och kanoniska MNPS-koordinater inom en fast, gemensam referens för den bearbetade inspelningen. Referensen kan avse en beskuren inspelning; den är inte automatiskt hela natten. Separat normalisering per stadium är inte tillåten enligt denna policy. Känd global normalisering och okänt effektivt filterstöd är skilda beroenden.

Policyn är framtagen efter tidigare datainspektion och är inte en preregistrering. Den nya kontrollen beräknar inga kontraster, anpassar inga estimatorer och ändrar inga mätvärden, etiketter, masker eller tensorer. Antalet fullt kvalificerade inkrement är fortfarande null, inte noll. Inspelningsövergripande Q/WQ får inte tillskrivas enskilda stadier.

Den slutliga referenskörningen behandlar två artefakter från samma deltagare separat:

| Underlag | Epoker | Stadiumkoder och antal | Signalstöd |
|---|---:|---|---|
| Ny 900-sekundersreferens | 30 | 0: 30 | recorded |
| Äldre helnattsunderlag | 1068 | 0: 275, 1: 20, 2: 642, 3: 15, 4: 107, 8: 9 | legacy_missing |

Båda har noll observerade tidsluckor, fönsteröverlapp, epok-ID-brott och källfilsbyten. Detta bevisar inte filterrenhet. Den nya referensen har registrerad PPG-tröskelanpassning över hela signalströmmen (median/MAD) och registrerade normaliseringspopulationer. Motsvarande information för legacy-filen lämnas okänd. Nya referensen saknar stadievariation och kan därför inte användas till en stadiejämförelse. Två artefakter från samma deltagare är ingen replikation.

Valideringen omfattar syntetiska feltester och en läsande körning mot båda H5-filerna, med oförändrade SHA256 före/efter. Externa EDF/TSV-hashar återberäknas inte av denna audit. Oberoende granskning och testutfall dokumenteras i `peer_review/11_stage_dependency_policy_review.md`.

Reproducerbar evidens finns i `H:/SourceRepo2/NeuralManifoldDynamics/project/v3/stage_dependency_20260910/reference_final/stage_dependency_audit.json`; installationsmanifest och kvitto ligger i samma arbetskatalog. Policyns kanoniska SHA256 är `97367837c4838746a22450a8750f4c423ebbc3fc9b7920ceb54c174e9032b954`.

Nästa empiriska steg är en avgränsad helnattskörning för sub-99 med nya stödmetadata och fast inspelningsreferens, följd av en deskriptiv stadieanalys med redovisad validitet, saknade värden och kod 8. Först därefter bör motsvarande kontrast prövas på en oberoende deltagare. Artikeln kan redovisa deskriptiva resultat med dessa begränsningar; detta steg etablerar varken biologisk diskrimination eller stadieintrinsisk diffusion.
