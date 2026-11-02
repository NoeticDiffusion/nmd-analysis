# Hela lokala sömnkohorten: H5-leverans och deskriptiva resultat

**PASS för full H5-täckning och oberoende verifierad deskriptiv analys. PARTIAL PASS för strikt exekveringsproveniens; METHOD-LIMITED för biologisk eller mekanistisk tolkning.**

Leveransen omfattar hela den lokalt tillgängliga ds005555-kohorten: **128 PSG-nätter, 100 unika personer och 120 091 epoker**, motsvarande 1 000,758 timmar. Samtidiga headband-filer ingår inte. Inga historiska stage-samplade H5-filer används som ersättning för fulla registreringar.

## Resultat

D_total är lägre i N2 än i vakenhet hos **97 av 100 personer**. Medianerna för numerisk abskissa och reaktivitetsgap minskar i både 3D och 9D. Diffusionens effektiva dimension och koncentration varierar mer mellan personer; deras kvartilintervall korsar noll. Även de spektrala abskissornas kvartilintervall korsar noll trots negativa medianer.

Varje kontrast beräknas först inom en natt, därefter som median över tillgängliga nattkontraster inom personen och slutligen över personer. Stages från olika nätter paras inte ihop. Tabellen behåller samtliga nio förvalda mått. Teckenantalen är en kompletterande deskriptiv presentation av samma personvärden; inga p-värden eller konfidensintervall har lagts till.

| Mått | Representation | Personer | Median N2−Wake | Q25, Q75 | Negativ/positiv |
|---|---|---:|---:|---|---:|
| spectral_abscissa | 3D | 100 | -0.000548 | -0.001740, 0.000559 | 64/36 |
| numerical_abscissa | 3D | 100 | -0.002415 | -0.004762, -0.001024 | 90/10 |
| reactivity_gap | 3D | 100 | -0.001519 | -0.002682, -0.000511 | 86/14 |
| spectral_abscissa | 9D | 98 | -0.001558 | -0.003079, 0.000034 | 72/26 |
| numerical_abscissa | 9D | 98 | -0.008233 | -0.015480, -0.002711 | 81/17 |
| reactivity_gap | 9D | 98 | -0.006188 | -0.013053, -0.000215 | 74/24 |
| D_total | 3D | 100 | -0.033018 | -0.061145, -0.017320 | 97/3 |
| d_diff | 3D | 100 | 0.066915 | -0.051590, 0.171578 | 36/64 |
| c_diff | 3D | 100 | -0.019379 | -0.050428, 0.015149 | 59/41 |

Abskissor och gap har enheten 1/s. D_total har inspelningsrelativa koordinat²/s; d_diff och c_diff är dimensionslösa. Kvartilintervall beskriver variation mellan personer, inte inferentiell osäkerhet. Lägre abskissa i N2 betyder inte att den absoluta abskissan är negativ eller att stabilitet har etablerats.

## Täckning och saknade värden

Alla 128 H5-filer har godkända tidsrutnät och etiketter som exakt matchar rådatats `stage_hum`. Wake/N1/N2/N3/REM omfattar 19 133 / 4 462 / 72 181 / 5 225 / 18 754 epoker. Kod 8 omfattar 336 epoker och hålls separat; inga andra okända koder förekommer.

3D-Jacobian och diffusion är registrerade som beräknade i alla 128 nätter. 9D-Jacobianexport saknas i **sub-3 och sub-4**. Deras 9D-rader är n=0/null, medan deras tillgängliga 3D-resultat används. Därför har 9D-kontrasterna 98 personer; övriga kontraster har 100. Ingen saknad mätning har ersatts med noll.

Den lokala personfilen anger 100 unika pid, trots README-uppgiften 108. Fördelningen är 80 personer med en natt, 12 med två och åtta med tre. Personerna bakom sub-1 och sub-99 behåller markeringen som tidigare utvecklingsmaterial, oberoende av om ett enskilt mått har giltiga rader.

Fyra registreringar (sub-36, sub-57, sub-104 och sub-126) förlorar vardera ett sista 30-sekundersfönster genom den befintliga crop-gränsens uteslutning av ett slutprov. Dessa fönster är dokumenterat utanför det exekverade stödet. Full leverans betyder samtliga registreringar med hela stödda epokgridet, inte att varje råprov har exporterats.

## Oberoende verifiering och kodgranskning

Koordinatorns HDF5-läsare importerar varken analysrunnern eller dess endpoint-läsare. Den verifierar hela rådatastödet, mänskliga etiketter, personidentiteter, koordinatformer, faktiska Jacobianmatriser, producentmasker och H5-hashar. Alla **16 488 tabellrader** matchar: 8 064 natt/stage-rader, 1 152 nattkontraster, 6 300 person/stage-rader, 900 personkontraster, 63 kohort/stage-rader och nio kohortkontraster. Antal, medianer, kvartiler, null-resultat och unika tabellnycklar är kontrollerade.

**172 artikeltester passerar**, inklusive sju fokuserade kohorttester. Implementation, körning, figurverktyg och separat granskning utfördes av Luna/xhigh-subagenter. Koordinatorn verifierade artefakter och kod samt skrev resultat, artikel och dagböcker. Fynd om personmarkering, återstart, manifestlänkar och figurens proveniens skickades tillbaka och rättades.

## Exekvering och begränsningar

Det första fyrarbetarjobbet fick TerminatedWorkerError; orsaken är inte fastställd. Den första återstarten rensade temporära featurefiler men hoppade över registreringar utifrån JSON-cache, vilket gav endast 42 registreringar. Koordinatorns ursprungliga granskning missade denna kombination. Felet bevaras som negativ evidens.

De 42 fullprecisionsresultaten säkerhetskopierades och 86 registreringar räknades om från rådata. Ett senare avbrott inträffade efter 54 nya registreringar. De 54 shardparen bevarades och sammanfogades med de 42, med exakt värdekontroll av 90 887 rader. De sista 32 kördes därefter från rådata. Sluttabellen innehåller 120 091 rader; samtliga 96 återanvända registreringars värden är exakt bevarade. Avrundad mellan-JSON användes inte för att återskapa vetenskapliga featurevärden.

Under slutkörningen ändrade ett separat I-CARE-arbete fyra CLI/orchestration-filer för `--resume-run`. Sömnprocessen hade redan laddat sin summary-modul och använde en gemensam trådpool utan omladdning eller denna flagga. Att den behöll den laddade koden är en dokumenterad exekveringsinferens, inte ett påstående att filsystemet var fryst. **`source_hashes_stable=false` ligger kvar.** Konfiguration och konfigurationsträd är oförändrade. Analysen använder ett separat, uttryckligen granskat direktmanifest som binder alla H5-identiteter och denna begränsning; den vanliga ingest-rutten skulle fortsatt avvisa den falska stabilitetsflaggan.

Slutlig sub-99 är inte bitidentisk med den färska piloten trots identiska gemensamma featurevärden. Maximal koordinatskillnad är 4,77e-7 och maximal 9D-Jacobianelements skillnad 5,64e-5. Det strikta identitetstestets FAIL bevaras. Slutresultatens aritmetik verifieras mot de faktiska slutliga H5-värdena.

Effektivt filterstöd är okänt i alla 128 filer, referensanpassning använder hela natten och estimatorernas grannskap är inte begränsade till en stage. Resultaten är därför label-associationer i inspelningsrelativa representationer. Ingen oberoende drift, drift–diffusionskoppling, universell koordinatkalibrering, klinisk biomarkör eller medvetandeteori har validerats. Q/W_Q, destination, resiliens och andra mått på inspelningsnivå inventeras utan att göras om till stage-mått.

## Artefakter och fortsatt kurs

- Granskat H5-manifest: `H:/SourceRepo2/NeuralManifoldDynamics/project/v3/sleep_dataset_delivery_20260912/coordinator_reviewed_analysis_inputs.json`.
- Direkt numerik-/tabellverifiering: samma katalog, `coordinator_full_analysis_verification.json`.
- Ursprunglig exekveringsproveniens och återställningskvitton: samma katalog; den ursprungliga falska stabilitetsflaggan bevaras.
- Analys: `results/sleep_cohort_20260912`, med kompletta JSON/CSV-tabeller och figur.
- Artikel: `Neural State Geometry and Dynamical Measurement Families Across Sleep.typ`.
- Tidigare artikel: `Development history before full cohort 20260912.typ`.
- Granskningar: `peer_review/20_sleep_cohort_delivery_review.md` och `peer_review/21_sleep_cohort_final_review.md`.
- Kommandon: `handover/20260912_sleep_cohort_analysis_commands.md`.
- Dagböcker: ingest 377 och nmd-analysis 332.

Kursen är nu full kohort → verifierad deskriptiv analys → kohortcentrerad artikel. En eventuell framtida inferentiell analys behöver en egen frågeställning, men ytterligare drift- eller stödgrindar är inte ett villkor för att leverera denna deskriptiva studie.

Slutlig artikel-PDF: `output/pdf/sleep_full_cohort_20260912.pdf` (fem sidor, kompilerad och visuellt verifierad). Slutmanifestet för analysen är `completed`, 128 ok/0 fel. Samlade sluthashar finns i leveranskatalogens `coordinator_final_delivery_receipt.json`.
