# Sömnpiloten: beskrivande resultat och nästa experiment

2026-09-07. **PASS för integration, reproducerbarhet och den avgränsade
beskrivande analysen. PARTIAL PASS för forskningsberedskap.** Stadiebetingad
dynamik och slutsatser på deltagar-/populationsnivå är ännu inte kvalificerade.

## Vad som nu finns

Den granskade epoch-exporten är integrerad i nmd-analysis. En ny körning från
J: gav en byte-identisk tabell. Den accepterade beskrivande körningen är
[r10](../results/descriptive_epoch_sub99_20260907_r10); r1-r9 är bevarad
utvecklingshistorik. Källans HDF5-hash är oförändrad.

Alla 3D- och 9D-koordinater har medianer och kvartiler per registrerat stadium,
både för grundurvalet och en i förväg fastlagd lokal etikettregel. Regeln
kräver samma kända stadium i föregående, aktuellt och efterföljande fönster,
konsekutiva ID:n och angränsande tidsgränser. Detta är ingen kontroll av hela
filterstödet eller diffusionens grannskap.

| Registrerat stadium | Grundurval | Gränsregel |
| --- | ---: | ---: |
| Wake | 275 | 249 |
| N1 | 20 | 2 |
| N2 | 642 | 581 |
| N3 | 15 | 0 |
| REM | 107 | 103 |
| Totalt känt stadium | 1 059 | 935 |

Nio okända etiketter finns kvar i auditunderlaget, utanför koordinatsammanfattningarna.
Alla fyra registrerade QC-masker är sanna och koordinaterna är finita; här
kommer bortfallet i grundurvalet alltså från okända etiketter.

## Vad resultaten säger

Grundurvalets medianer varierar mellan registrerade stadier. Till exempel är
m-medianerna 0,922 för Wake, -0,344 för N2 och 0,701 för REM; motsvarande
d-medianer är 1,769, -0,255 och 0,190. Alla koordinater och stadier finns kvar
i tabellerna, inklusive mindre eller otillräckligt stödda grupper.

Det viktigaste nya stödresultatet är att N3 helt försvinner under gränsregeln
och att N1 bara har två fönster kvar. N3:s saknade känslighetsstatistik är
NaN, inte noll. Detta visar inte att fysiologisk N3 saknas eller att etiketter
är felaktiga; det visar begränsningen hos underlaget under den valda regeln.

Ingen populationshypotesprövning, klassificerare, separat stadiebetingad
diffusionsskattning eller klinisk validering har körts. De globala koordinaterna
kan fortfarande påverkas av tid under natten, feature-/filterstöd och blandad
proveniens. e_m använder PPG-fallback med `semantic_equivalence=false`.

## Verifiering

- 16 integrationsfiler matchar överlämningens SHA256.
- Ny epoch-export från J: matchar den accepterade Parquet-filen byte för byte.
- 42 artikeltester passerar, inklusive oberoende tester och koordinatorns
  exakta kontroller av båda grannarna, tidsluckor, överlapp, ID-hopp, tomma
  grupper, NaN, krav på config och figurlinjer.
- Oberoende review accepterar r10. Koordinatorns separata omräkning från
  indatatabellen matchar alla 120 sammanfattningsrader samt samtliga
  registrerade hashvärden. Ingen runnerfunktion används i omräkningen.
- Manuskriptet har uppdaterats med resultat, tabell, tidsfigur och begränsningar.

Se [review](../peer_review/04_stage_descriptive_review.md) och
[maskinläsbar kontroll](../handover/20260907_descriptive_coordinator_validation.json).
Tidigare reviewfel rättades före r10: felaktigt gränsurval, tappade tomma
grupper, sammanbundna figurluckor och otillräckligt validerad proveniens.

## Nästa prioritet

1. **Kontrollera etikettproveniens och sammanhängande stadieavsnitt.** Kartlägg
   särskilt N1/N3-stödet och feature-/filterstödet. Ändra inte etiketter eller
   regeln för att få ett önskat utfall.
2. **Gör diffusionens grannskapsstöd spårbart.** Den inspekterade diffusionsgruppen
   innehåller grannantal men inga påträffade grannindex. Vi behöver skilja
   global geometri vid ett stadium från separat stadiebetingad skattning och
   kontrollera vilka inkrement som bidrar innan starkare tolkning.
3. **Frys en deltagarbaserad replikation.** Inventera stöd i övriga inspelningar
   och fastställ inkludering, ett litet antal mått och kontraster, aggregering
   och robusthetskontroller före utvärderingen. Denna utvecklingspilot får inte
   återanvändas som oberoende bekräftelse.

Min bedömning: vi har nu ett konkret metod-/pilotresultat att diskutera i
artikeln. Nästa arbete bör säkra etikett- och grannskapsstödet innan vi lägger
mer vikt vid stadieskillnader eller startar inferens på en hel kohort.
