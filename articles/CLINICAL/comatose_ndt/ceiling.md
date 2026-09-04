Nu kan jag svara med data i ryggen, inte bara teori. Jag körde tre diagnostik på samma 277-patientmatris (166 mått).

## Bevisen

| Modell / riktning | AUC |
|---|---|
| Bästa enskilda måttet (MNJ9D spectral radius) | 0.715 |
| LPR-reaktivitetsprofil | 0.714 |
| **Kitchen-sink logistic (alla 166 mått, L2)** | **0.655** |
| Kitchen-sink L1 (gles) | 0.662 |
| **Gradient boosting (icke-linjär, 166 mått)** | **0.658** |
| Artikelns clinical+qEEG+geometry | 0.687 |
| PC2 (den diskriminativa PCA-riktningen) | 0.685 |
| Topp-2 PCs (CV) | 0.684 |

Tre saker faller ut:
- **Att kasta in fler features hjälper inte — det skadar.** 166-features-modeller och en icke-linjär gradient boosting hamnar *under* ett enda välvalt mått. Taket är alltså **inte** ett feature-engineering-problem.
- **Den diskriminativa signalen bor i ~2 dimensioner.** PC1 (22 % varians) bär nästan ingen signal (0.566) — den är amplitud/skala. PC2 bär den (0.685), och topp-2 PCs (0.684) fångar i princip allt kitchen-sink når. Olika mått (expansion, reachability, reaktivitet) projicerar alla på ungefär samma severity-riktning (medel-|Spearman| = 0.45), så de är klassificerings-redundanta → kombinationer adderar inget.

## Vad taket beror på (rangordnat)

**1. Endpoint-orenhet — det irreducibla golvet (primär orsak).**
CPC 5 är inte "hjärndöd". Den absorberar WLST (avbruten livsuppehållande vård), systemisk mortalitet och behandlings-/self-fulfilling-prophecy-effekter. En del av CPC 5-hjärnorna ser geometriskt ut som CPC 1 vid 0–12 h — och *ingen* EEG-geometri kan skilja dem. Det sätter ett Bayes-felgolv. **Smoking gun:** kitchen-sink, icke-linjär GB *och* clinical+qEEG+geometry konvergerar alla till ~0.66–0.72 — när helt olika informationskällor (kliniska variabler OCH EEG-geometri) landar på samma tak är taket bundet av *etiketten/datat*, inte av representationen.

**2. En lågdimensionell delad latent faktor (därför hittar varje mått samma siffra).**
All separerbar signal ligger i ~2 riktningar. Så fort du mätt "severity/expansion"-axeln är du klar; allt annat är samma varians omklätt. Det förklarar exakt varför NRCA, NBP, kvoten, LPR och median alla landar på 0.71–0.73.

**3. Tidigt-fönster + ofångade confounders (biologisk gräns).**
0–12 h ankarrelativt, ingen ROSC-klocka, sedering/TTM/artefakt oobserverade. Tidig post-arrest-EEG är bara måttligt prognostisk i litteraturen (enmodal AUC ~0.7–0.8). Vi ligger sannolikt nära den *sanna* biologiska signalstyrkan i detta fönster.

## Konsekvens

Taket går **inte** att slå med smartare geometri eller fler mått — det har vi nu visat empiriskt. Hävstängerna som faktiskt skulle flytta det:
- en **renare endpoint** (exkludera WLST/systemisk död; neural-specifik etikett),
- **senare / multipla tidsfönster** (24–72 h), multimodalt,
- **reducera confounders** (sedering, artefakt-QC).

Med andra ord: 0.71–0.73 är taket för "hur väl tidig vilo-EEG-geometri *ensam* kan spegla ett orent recovery-utfall" — och LPR/Event-Sliced når det taket från perturbationssidan, vilket är det bästa man rimligen kan begära av just den här datan.

Vill du att jag lägger till den här tak-diagnosen som ett stycke i diary `162` (eller en egen `163`), så den är dokumenterad inför artikel-diskussionen?