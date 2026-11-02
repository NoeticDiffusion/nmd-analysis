# Sömnpiloten: signalstöd och tillåtna inkrement

2026-09-08. Avgränsad utvecklingsanalys av sub-99.

**PASS för den avgränsade inkrementauditen. PARTIAL PASS för forskningsberedskap:**
det fullständiga feature-/filterstödet kan inte kvalificeras från dagens export.
Oberoende kod-, data- och manuskriptgranskning är godkända. **80 artikeltester
passerar**, och koordinatorns separata omräkning matchar tabeller och hashvärden.

## Frågan

Vi skiljer mellan tre kontroller: tidsmässigt giltiga inkrement, ändpunkter
med samma kända sömnstadium och fullständigt dokumenterat feature-/filterstöd.
De två första räcker inte för att godkänna det tredje. Originalets globala
koordinater och diffusionstensorer behålls; inga nya stadiebetingade tensorer
skattas i denna audit.

## Tidsprofilen är klarlagd

HDF5-filens generella attribut `window_sec=8` och `fs_out=4` beskriver inte
den effektiva epokprofilen. Den inbäddade körningsauditen skiljer uttryckligen
de generella inställningarna från den upplösta epokprofilen och bekräftar
30 sekunders fönster och 30 sekunders steg, i överensstämmelse med tidsarrayerna.
Detta är ingen påvisad tidsaxeldefekt och ingen certifiering av filtrens stöd.

Se [bevarad tidsprofil](../handover/20260908_effective_time_grid.json).

## Resultat från hela inkrementpoolen

Alla 1 067 angränsande par uppfyller den strukturella regeln. Av dessa har
976 samma kända stadium i båda ändpunkterna:

| Stadium | Inkrement med samma kända stadium i båda ändpunkterna |
| --- | ---: |
| Wake | 258 |
| N1 | 4 |
| N2 | 609 |
| N3 | 0 |
| REM | 105 |

Tio tidsmässiga inkrement berör en kod-8-frånkoppling. Dessa antal avser hela
den angränsande poolen, inte de 21 360 upprepade grannvalen i diffusionens
kandidatrekonstruktion. Alla grannval har också kontrollerats. Ingen ny tensor
har skattats från ett filtrerat urval.

N3 saknar alltså sammanhängande inom-stadium-inkrement i denna inspelning,
och N1 har endast fyra. Det ger inte underlag för den planerade lokala
diffusionsskattningen för dessa stadier. Det är en stödbegränsning, inte ett
negativt biologiskt resultat. Antalet fullt stödkvalificerade inkrement är
**okänt (`null`), inte noll**.

Se [accepterad körning r2](../results/increment_support_sub99_20260908_r2),
[oberoende omräkning](../handover/20260908_increment_artifact_crosscheck.json)
och [koordinatorns kontroll](../handover/20260908_increment_coordinator_validation.json).

## Vad kartläggningen tillför

Robust-z-normaliseringen använder hela inspelningens 1 068 featurerader. Det
är ett dokumenterat referensberoende över inspelningen. EEG/PPG-features använder
30-sekundersinput, men det bevisar inte att råsignalstödet stannar inom dessa
gränser efter föregående filtrering och omsampling. Körningsproveniensen saknar
bland annat fullständiga filter-, padding- och exekveringsuppgifter.

[Kartläggning med källhänvisningar och hashvärden](../handover/20260908_feature_filter_support_audit.md).

## Vad nästa experiment måste skilja åt

En jämförelse av globala koordinater vid olika registrerade stadier är möjlig
som beskrivande analys med synliga begränsningar. En separat stadiebetingad
dynamikskattning kräver en uttrycklig regel för inkrement, signalstöd och
referenspassning. En global normaliseringsreferens ska beskrivas som en sådan;
den är inte automatiskt samma problem som tidsmässig filtrering över en gräns.

Vi ska inte välja en godtycklig marginal kring stadiebyten och kalla den
fullständigt filterstöd. Om ett beräkningssteg saknar exakt ändligt stöd måste
eventuellt effektivt stöd definieras och verifieras separat, med en dokumenterad
felgräns. Saknad information förblir `not_assessed`.

Min nästa prioritet är därför en liten ändring i ingest som loggar det körda
signalstödet och referenspassningen, följd av en avgränsad referenskörning.
[Konkret implementationsunderlag](../handover/20260908_ingest_support_export_request.md)
beskriver exporten och acceptanskraven. Därefter kan vi frysa en gemensam
koordinat- och inkrementpolicy samt inventera annoteringsstöd i fler inspelningar
inför deltagarbaserad replikation. Dagens filer och mätdefinitioner är bevarade.
