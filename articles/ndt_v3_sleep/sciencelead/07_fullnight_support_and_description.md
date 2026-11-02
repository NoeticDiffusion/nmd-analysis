# Helnattsanalys med registrerad signalproveniens

**PASS** för helnattskörning, bevarade mätvärden och deskriptiv analys. **METHOD-LIMITED** för stadieintrinsisk dynamik och biologisk kvalifikation.

Vi har nu kört om hela sub-99 från rå-EDF med nya stödmetadata och utan cache eller stadieurval. 1 068 epoker täcker 0–32 040 sekunder; råfilens sista 24 sekunder ligger utanför de fullständiga 30-sekundersfönstren. Ingen råfil eller tidigare analys ersattes.

531 gemensamma numeriska dataset är exakt oförändrade mot den verifierade helnattsreferensen. Av 390 jämförda boolean-/strängdataset skiljer sig endast tre förväntade körmetadatafält. Alla tolv normaliseringspopulationers hashvärden och antal har rekonstruerats från den faktiskt använda featuretabellen, och EDF/TSV-hasharna matchar källproveniensen. Normaliseringen är gemensam för inspelningen; ingen anpassning gjordes per stadium.

De 1 059 epokerna med kända stadier uppfyller de fasta koordinat- och maskreglerna för både 3D och 9D. Nio kod-8-epoker bevaras separat och ingår inte i stadiesammanfattningarna. Producer-maskerna är true för samtliga 1 068 epoker; detta certifierar inte fullt filterstöd.

| Stadium | Epoker | Median m | Median d | Median e |
|---|---:|---:|---:|---:|
| Wake | 275 | 0.922 | 1.769 | 0.336 |
| N1 | 20 | 0.679 | 1.354 | 0.132 |
| N2 | 642 | -0.344 | -0.255 | -0.121 |
| N3 | 15 | -1.392 | -1.007 | -0.255 |
| REM | 107 | 0.701 | 0.190 | 0.121 |

Koordinaterna beskriver positioner i denna inspelnings gemensamma referens. Medianer och kvartiler i både 3D och 9D reproducerar de tidigare accepterade deskriptiva resultaten inom 4,4e-16. Det nya resultatet är således förbättrad spårbarhet och reproducerad beskrivning, inte en oberoende replikation. N1 och N3 har fortfarande litet stöd (20 respektive 15 epoker); tidsberoendet mellan epoker försvinner inte av att antalet redovisas.

Effektivt filterstöd förblir unknown och fullt kvalificerade inkrement null. PPG:s globala median/MAD-tröskel är registrerad; den tidigare icke-ekvivalenta e_m-fallbacken kvarstår. Vi har inte kvalificerat stadievisa Q/WQ- eller diffusionsmått, medvetandemarkörer eller populationseffekter.

Validering: 90 befintliga artikeltester och 7 nya wrapper-/referenstester passerade före installation. Oberoende granskning finns i `peer_review/12_fullnight_support_review.md`. Resultat, epoktabell och proveniens finns i `results/fullnight_support_sub99_20260910`; exakta kommandon finns i `handover/20260910_fullnight_commands.md`.

Nästa prioritet är en andra oberoende deltagare: välj deltagare med en förutbestämd regel före inspektion av koordinatkontraster, kontrollera rådata/etiketter och kör samma helnattskedja och fasta sammanfattningar. Behåll deltagarna separata och redovisa stöd per stadium. Detta prövar överförbarheten hos den deskriptiva associationen; filterren stadiedynamik kräver fortfarande en separat metodutvärdering.
