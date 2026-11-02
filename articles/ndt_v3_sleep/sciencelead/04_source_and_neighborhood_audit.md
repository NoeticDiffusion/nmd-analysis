# Sömnpiloten: källannoteringar och diffusionens stöd

2026-09-07. Utvecklingspilot, sub-99. Den tidigare beskrivande r10-körningen
och kanoniska mätdefinitioner är oförändrade.

**PASS för den avgränsade annoteringsgranskningen och numeriska
kandidatrekonstruktionen. PARTIAL PASS för vetenskaplig beredskap:** fullständigt
feature-/filterstöd och deltagarbaserad replikation återstår. Artikelns 65 tester
passerar. Manuskriptets fyra sidor har kompilerats och granskats visuellt.

## Källannoteringar: verifierat

Alla 1 068 exporterade fönster matchar den mänskliga `stage_hum`-annoteringen
rad för rad, inklusive tidsgränser och den 256 Hz-baserade sampelklockan.
Källans kod 8 betyder PSG-frånkoppling; dessa nio fönster behåller analysens
okänd-status. AI-etiketter används inte som ersättning.

| Stadium | Sammanhängande avsnitt | Fönster | Kvar med tvåsidig etikettregel |
| --- | ---: | ---: | ---: |
| Wake | 17 | 275 | 249 |
| N1 | 16 | 20 | 2 |
| N2 | 33 | 642 | 581 |
| N3 | 15 | 15 | 0 |
| REM | 2 | 107 | 103 |

Totalt finns 83 kända stadieavsnitt och ett frånkopplingsavsnitt. Alla N3-avsnitt
är enstaka 30-sekundersfönster. Det förklarar bortfallet under den fastställda
etikettregeln, men visar inte att etiketter är fel eller att N3-fysiologi saknas.

Den lokala EEG-metadatafilen och EDF-headern anger 32 064 sekunders inspelning.
Exportens annoterade fönster slutar vid 32 040 sekunder. De återstående
24 sekunderna är ingen extra komplett epok och har inte tilldelats ett stadium.
EDF-headern har kontrollerats; råsignalens fullständiga vågform har inte granskats.

Källunderlag: [audit r7](../results/stage_support_audit_20260907_r7),
[metadata och EDF-header](../handover/20260907_source_metadata_context.json),
[utvecklingsprotokoll](../support_audit_plan_20260907.md).

## Diffusion: exakt matchande kandidat, blandat stadiestöd

Den accepterade kandidaten är
[rekonstruktion r9](../results/diffusion_support_reconstruction_sub99_20260907_r9).
Alla 1 068 lagrade tensorer, stödantal och giltighetsvärden matchar exakt.
En separat omräkning utan producentens eller analysrunnerns funktioner
matchar alla 21 360 grannval och deras tensorer. Inga exakta avståndslikheter
vid urvalsgränsen påträffades.

- **281 av 1 059 kända stadiefönster (26,5 %)** har samtliga 20 inkrement med
  båda ändpunkterna i samma stadium som frågefönstret.
- **33 kända stadiefönster** har minst ett valt inkrement som berör en
  PSG-frånkoppling. Totalt berör 88 grannrader sådana ändpunkter.
- Raderna är upprepade urval, inte 88 oberoende händelser. Nio frånkopplings-
  fönster finns kvar i producentens ursprungliga finita indatapool.

Detta gäller en exakt matchande **kandidatrekonstruktion**. Ursprungliga
diffusionsgrannar sparades inte i HDF5, så unika historiska grannidentiteter
är fortfarande inte fastställda. Diffusionens ursprungliga mått är per fönster
med inspelningen som överordnad enhet; grannpoolen är global. Inga separata
stadiebetingade skattningar eller ändrade exklusionsmasker har införts.

Se [koordinatorns direkta omräkning](../handover/20260907_support_coordinator_validation.json)
och [oberoende review](../peer_review/07_diffusion_support_reconstruction_review.md).

## Nästa vetenskapliga beslut

Frys ett avgränsat protokoll för deltagarbaserad replikation efter att
fullständigt feature-/filterstöd och giltiga inkrement har kartlagts. Inventera
annoteringsstöd innan nya stadiekontraster läses. Behåll sub-99 som utvecklingsdata.
N1/N3 ska inte räddas genom etikettbyte eller en efterhandsanpassad stödregel.

Före kohortinferens behöver personkopplingen också klarläggas: den lokala
`participants.tsv` har 128 rader med 100 olika `pid`, medan README anger
108 individer. Antalet identifierare är ingen självständig verifiering av
antalet personer. Ingen populationsanalys har körts.

PPG-fallbackens bristande semantiska ekvivalens och den metodbegränsade 9D-volymen
kvarstår. Dessa kontrollresultat kvalificerar inte en medvetandeteori eller
en biologisk markör.
