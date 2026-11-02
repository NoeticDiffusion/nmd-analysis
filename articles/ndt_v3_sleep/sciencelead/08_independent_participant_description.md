# Andra deltagaren: blandat deskriptivt utfall

**PASS** fÃƒÂ¶r kÃƒÂ¶rning, proveniens och den fÃƒÂ¶rutbestÃƒÂ¤mda analysen. **PARTIAL PASS** fÃƒÂ¶r ÃƒÂ¶verfÃƒÂ¶rbarheten hos den deskriptiva riktningen; **METHOD-LIMITED** fÃƒÂ¶r biologisk och stadieintrinsisk kvalifikation.

Sub-1 valdes som lÃƒÂ¤gsta numeriska BIDS-ID utom sub-99 med tillgÃƒÂ¤nglig PSG-EDF och humanbedÃƒÂ¶mda events. Urvalet gjordes utan inspektion av koordinatkontraster eller stadieantal. Deltagartabellen och H5-metadata anger pid89 fÃƒÂ¶r sub-1 och pid66 fÃƒÂ¶r sub-99. Detta ÃƒÂ¤r datasetets identitetsunderlag fÃƒÂ¶r tvÃƒÂ¥ olika deltagare. Ingen senare inspelning valdes fÃƒÂ¶r att fÃƒÂ¶rbÃƒÂ¤ttra utfallet.

Samma helnattskedja kÃƒÂ¶rdes frÃƒÂ¥n rÃƒÂ¥fil utan cache, med ofÃƒÂ¶rÃƒÂ¤ndrade mÃƒÂ¤tdefinitioner och gemensam normalisering inom respektive inspelning. Alla tolv fit-populationers hashvÃƒÂ¤rden och antal (915) rekonstruerades och matchade; EDF/TSV-hashar matchade. KÃƒÂ¤llkoden fÃƒÂ¶r ingest ÃƒÂ¤r ofÃƒÂ¶rÃƒÂ¤ndrad. Den enda exporterÃƒÂ¤ndringen tillÃƒÂ¥ter ett explicit konfigurerat H5-filnamn, med sub-99 kvar som standard. En separat omexport av sub-99 gav exakt samma epoktabell och sammanfattningar.

| Stadium | Sub-99 | Sub-1 |
|---|---:|---:|
| Wake | 275 | 200 |
| N1 | 20 | 57 |
| N2 | 642 | 398 |
| N3 | 15 | 172 |
| REM | 107 | 87 |
| Kod 8, separat | 9 | 1 |
| Totalt | 1068 | 915 |

Alla 914 epoker med kÃƒÂ¤nda stadier i sub-1 uppfyller de fasta koordinat-/maskreglerna fÃƒÂ¶r 3D och 9D. Kod 8 bevaras som okÃƒÂ¤nd och exkluderas frÃƒÂ¥n stadiekontrasterna. Producer-masker ÃƒÂ¤r inte certifikat fÃƒÂ¶r filterrenhet.

Den frysta jÃƒÂ¤mfÃƒÂ¶relsen ÃƒÂ¤r median(N2) minus median(Wake), fÃƒÂ¶r samtliga tolv koordinater och varje deltagare separat. Skillnaderna har inspelningsrelativa enheter och ska inte tolkas som kalibrerade mellanpersons-effektstorlekar. Riktningar ÃƒÂ¶verensstÃƒÂ¤mmer i 7/12 koordinater; fyra byter tecken och en har exakt nollskillnad i sub-1. Koordinaterna ÃƒÂ¤r beroende av varandra och 7/12 ÃƒÂ¤r ingen statistisk signifikans eller tolv oberoende replikationer.

| Koordinat | Sub-99: N2Ã¢Ë†â€™Wake | Sub-1: N2Ã¢Ë†â€™Wake | Samma riktning |
|---|---:|---:|---|
| 3d_m | -1.2661 | 0.5380 | Nej |
| 3d_d | -2.0240 | -1.1562 | Ja |
| 3d_e | -0.4569 | 0.0937 | Nej |
| 9d_m_a | -1.2836 | -0.4565 | Ja |
| 9d_m_e | -1.0536 | 1.0671 | Nej |
| 9d_m_o | -1.9767 | 0.7512 | Nej |
| 9d_d_n | -2.0596 | -0.7220 | Ja |
| 9d_d_l | -2.1855 | -0.1911 | Ja |
| 9d_d_s | -1.3962 | -2.8552 | Ja |
| 9d_e_e | -1.7296 | -0.0124 | Ja |
| 9d_e_s | 1.3819 | 0.5105 | Ja |
| 9d_e_m | 0.5114 | 0.0000 | Nej |

I 3D behÃƒÂ¥ller d en negativ N2Ã¢â‚¬â€œWake-skillnad, medan m och e byter tecken. Vi kan dÃƒÂ¤rfÃƒÂ¶r inte beskriva hela 3D-mÃƒÂ¶nstret som reproducerat. Allt redovisas, inklusive negativa och nollresultat. Ingen omnormalisering per stadium, parameterjustering, p-vÃƒÂ¤rdesberÃƒÂ¤kning eller poolning gjordes.

Fullt temporalt filterstÃƒÂ¶d fÃƒÂ¶rblir unknown, kvalificerade inkrement null och stadieintrinsisk Q/WQ/diffusion oprÃƒÂ¶vad. Det kÃƒÂ¤nda PPG-/fallbackberoendet mÃƒÂ¥ste beaktas fÃƒÂ¶r e_m och den sammansatta e-axeln. Exakt noll median-skillnad ÃƒÂ¤r ett berÃƒÂ¤knat utfall, inte en ersÃƒÂ¤ttning fÃƒÂ¶r saknade data eller ett bevis fÃƒÂ¶r avsaknad av fysiologisk variation.

NÃƒÂ¤sta prioritet ÃƒÂ¤r en lÃƒÂ¥st diagnostik av m/e-axlarnas kÃƒÂ¤ll- och normaliseringsberoenden i de tvÃƒÂ¥ redan analyserade inspelningarna. Bevara dessa huvudresultat; anvÃƒÂ¤nd diagnostiken fÃƒÂ¶r att skilja mÃƒÂ¤tproblem frÃƒÂ¥n verklig mellanpersonsvariation, utan att optimera fÃƒÂ¶r en ÃƒÂ¶nskad riktning. DÃƒÂ¤refter bÃƒÂ¶r nÃƒÂ¤sta fÃƒÂ¶rhandsvalda deltagare analyseras med ofÃƒÂ¶rÃƒÂ¤ndrad huvudregel. TvÃƒÂ¥ deltagare rÃƒÂ¤cker inte fÃƒÂ¶r populationsslutsatser.

Oberoende tester rÃƒÂ¤knar om medianer och riktningar frÃƒÂ¥n bÃƒÂ¥da epoktabellerna. Den nya testsviten passerade 10 tester fÃƒÂ¶re installation. Slutliga installationstester, hashkvitto och resultat finns i H:/SourceRepo2/NeuralManifoldDynamics/project/v3/independent_sleep_20260910. Granskning: peer_review/13_independent_sleep_review.md. Artikeldata: results/independent_sub1_20260910.
