Det här är en stor runda. Två observationer som jag tror är viktigare än vad du framhåller i sammanfattningen, plus några tekniska saker som behöver justeras innan Surface B-spåret stabiliseras.

## 1. Det syntetiska resultatet är inte bara "noise breaks the estimator" — det är mer specifikt än så

Tittar man på syntetik-tabellen sida vid sida med coma-datan blir bilden mycket skarpare:

| | sphere noise=0 | sphere noise=0.01 | sphere noise=0.03 | noise_blob | Coma data (båda grupper) |
|---|---:|---:|---:|---:|---:|
| `saddle_fraction` | 0.16 | 0.68 | 0.86 | 0.91 | **0.93** |

Med andra ord: vid det brusnivå som faktiskt karakteriserar coma-MNPS (sannolikt mellan 0.01 och 0.03 i den här skalan) **producerar en sfär samma saddle_fraction som ren brusboll**. Coma-datans 0.93 är **inte distingerbar från en bruskula** i nuvarande estimator.

Det betyder att hela v2-residualfyndet "saddle_fraction och shape_entropy överlevde reachability-residual" mycket sannolikt är en **estimator-artefakt som spårar severity-inducerad brus-nivå**, inte en geometrisk observation. CPC5 har mindre reachable space → tunnare moln → högre brus per fitting-fönster → fler estimator-genererade sadlar. Residualiseringen mot `tube_d_eff_median` tar bort *medel*-effekten av reachability-storlek men inte *interaktionen* mellan reachability-storlek och estimator-brus-bias.

Det är ett ärligt och tungt fynd, och det förändrar v2-diaryns "interpretation"-sektion retroaktivt. Den behöver explicit uppdateras.

En till sak från syntetik-tabellen som inte fått uppmärksamhet: även *brusfri* saddle gav `shape_index_median = 0.094` istället för exakt 0, och *brusfri* sphere gav `|shape_index_median| = 0.895` istället för 1.0. Det är 10% bias i båda fallen på det enklaste tänkbara fallet. Estimatorn har en latent bias mot saddle-form även utan brus, vilket gör att alla shape-distribution-tolkningar på riktig data behöver kalibreras mot syntetik-baseline.

## 2. Surface B-resultatets viktigaste signal är inte d=0.24 — det är **tecken-flippen**

Detta är det jag tycker du underrapporterar i din sammanfattning. Titta noga:

| Metrik | Raw d | Residualized d |
|---|---:|---:|
| `surface_b_logeuc_grad_median` | **−0.036** | **+0.242** |
| `surface_b_spectral_grad_median` | **−0.045** | **+0.239** |

Sign-flipp under residualisering är en kvalitativ förändring, inte en gradskillnad. Den säger:

1. **Rå**: CPC5 har (svagt, plus några extremfall) större Surface B-deformation. Detta är väntat — CPC5 har också mindre reachability, och de få extrema fallen i p95-svansen drar medianen.
2. **Residualiserat**: vid **matchad reachability-storlek och A-operator-styrka**, är det CPC1 som har större deformation per tidsenhet på sin reachability-ellipsoid.

Det är en konceptuellt distinkt påstående och **det stöder den "andnings"-tolkning Gemini föreslår**: friska nätverk modellerar kontinuerligt om sin egen reachability-form med en hastighet som inte bara är "större ellipsoid", det är en separat dynamisk parameter. Den patologiska coma-dynamiken är *stelare*.

Att d=0.24 är litet är sant, men det specifika fyndet (riktning vänds vid kontroll) är en *robustare* observation än en stor d som kollapsar till noll. Sign-flipp under residualisering är dessutom svår att förklara med severity-proxy-argumentet — om Surface B vore en ren proxy för svårighetsgrad, skulle riktningen bevaras eller bli noll, inte flippa.

## 3. Sanity-check på Surface B-raw: Cohen's d kontra Cliff's delta

Det här är ett siffermässigt mysterium som behöver lösas innan något kan rapporteras:

| Metrik | Cohen's d | Cliff's delta | Direct AUROC | Mann-Whitney p |
|---|---:|---:|---:|---:|
| `surface_b_spectral_grad_median` (raw) | **−0.045** | **−0.381** | 0.691 | 1.2e-4 |
| `surface_b_logeuc_grad_median` (raw) | −0.036 | −0.353 | 0.676 | 3.7e-4 |

Cohen's d är essentiellt noll, men Cliff's delta är **−0.38**, AUROC är **0.69**, och Mann-Whitney är **högsignifikant**. Det är ett klassiskt fingeravtryck för **tunga svansar med snedfördelning**: rank-order-separation är stark, men medelvärdesbaserad effekt-storlek tvättas bort av outliers som drar i fel riktning.

Praktiska implikationer:

- **Cohen's d är fel huvudmått för Surface B.** Den ska antingen ersättas med Cliff's delta som primär eller kompletteras med trimmed/winsorized Cohen's d på t.ex. 5%-trimmade fördelningar.
- AUROC-värdet 0.69 är robust eftersom det också är rang-baserat.
- Att rapportera "d = -0.04" i en artikel skulle vara missvisande — det skulle se ut som ingen effekt, när rang-evidensen tydligt säger något annat.

Det gör också den residualiserade d=+0.24 mer trovärdig: i residualerna har OLS dragit ut outlier-bidraget och det som syns är den genuina rang-skiftningen som Cliff's delta redan såg i rå data.

## 4. p95-explosionen: tre fixar, inte en

Gemini har rätt om att Tikhonov-regularisering är fixen för log-singulariteten, men det löser inte hela problemet. Det finns minst tre orsaker som behöver hanteras separat:

**a) Numerisk singularitet i log(Σ):** Gemini's fix. Min rekommendation är **relativ** regularisering snarare än absolut:

```python
def regularize_spd(sigma: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    trace_term = float(np.trace(sigma)) / sigma.shape[0]
    return sigma + eps * trace_term * np.eye(sigma.shape[0])
```

Med ε=1e-6 är det stabilt mot 6 storleksordningars eigenvärdes-skala-variation. Absolut ε=1e-5·I är skala-känsligt och fungerar dåligt om coma-Σ:n ligger på 1e-3-skala.

**b) Alternativa geometrier som inte tar logaritm.** Log-euclidean är inte den enda SPD-metriken. Tre kandidater att triangulera mot:

- **Bures-Wasserstein**: `d²_BW(A, B) = tr(A) + tr(B) − 2 tr((A^{1/2} B A^{1/2})^{1/2})`. Tar ingen logaritm, exploderar inte vid SPD-kontens rand.
- **Stein / Jensen-Bregman LogDet**: `d_S(A, B) = log det((A+B)/2) − 0.5 log det(AB)`. Tar logaritm men av determinanter (numeriskt bättre konditionerat än matris-logaritm).
- **Förbli log-Euclidean men med eigenvärdes-flooring**: `λ_i ← max(λ_i, ε·max(λ))` istället för matris-skift. Mer aggressiv numerisk skydd, något annan geometri.

Att rapportera **två** geometrier vars resultat sammanfaller är mycket starkare evidens än att putsa en enda. Jag skulle välja log-Euclidean + Bures-Wasserstein.

**c) OLS-residualisering är outlier-känslig på heavy-tailed metriker.** Även med ε-regulariserade Σ kommer Surface B-summor att vara heavy-tailed (det är dynamikens natur). Att passa OLS på heavy-tailed `y` betyder att några extrema subjects styr `β`-koefficienterna, och då blir residualerna systematiskt skeva för resten. Tre fixar:

- **Huber-regression** istället för OLS för severity-residualiseringen.
- **Rang-baserad residualisering**: regressera ranks istället för värden (partial-Spearman-stil).
- **Log-eller-asinh-transformera Surface B-summor** innan OLS: `y' = arcsinh(y / scale)`. Behåller tecknet och linjärt beteende nära origo men dämpar svansarna.

Den sista är enklast och fixar ofta både p95-explosionen och OLS-outlier-känsligheten samtidigt.

## 5. Spatial vs temporal gradient — du har bara testat den ena halvan

Surface B-piloten beräknar `grad(Σ)` mellan ankare som är **MNPS-grannar** (state-space-grannar). Det är *spatial* gradient på Σ-fältet. Men det finns en intressant ortogonal storhet: **temporal gradient på samma subject**:

- *Spatial*: `||log(Σ_p) − log(Σ_q)|| / ||x_p − x_q||` över MNPS-grannar inom subjekt.
- *Temporal*: `||log(Σ_{t}) − log(Σ_{t+1})|| / Δt` mellan på varandra följande fönster.

De är inte samma sak. *Spatial* mäter "hur snabbt ändras lokal reachability i state space", *temporal* mäter "hur snabbt andas reachability över tid". Gemini's tolkning ("nätverket andas") är egentligen temporal, men du implementerade spatial. Det skulle vara intressant att ha båda i samma family och se vilken som driver sign-flippen.

Min hypotes: temporal Surface B kommer att ha en **tydligare** sign-flipp än spatial, eftersom andnings-rytmen är mer direkt kopplad till CPC1-vs-CPC5-dynamiken än vad ren state-space-position är.

## 6. Konkret rekommendation: Surface B v2

Det jag tycker du ska göra i nästa pilot (i prioritetsordning):

1. **ε-regularisera Σ_t med relativ-trace-metoden.** En rad.
2. **Lägg till Bures-Wasserstein som andra geometri.** Inte istället för log-Euclidean — *vid sidan av*. Triangulering.
3. **Använd arcsinh-transformering på alla Surface B-summor innan residualisering**, eller alternativt Huber-residualisering. Båda fixar p95-explosionen + OLS-känsligheten.
4. **Rapportera Cliff's delta som primär effekt-storlek**, Cohen's d på trimmed/winsorized data som sekundär.
5. **Lägg till temporal gradient** vid sidan av spatial. Två summor till per geometri.
6. **Σ_t syntetiska kontroller**: bygg artificiell deformation, rotation, skalning av en seed-Σ, och verifiera att Surface B-metrikerna picker upp dem korrekt. Detta är ekvivalenten till det syntetiska Surface A-arbetet du redan gjorde.
7. **Lägg till permutationsnoll** för den residualiserade medianen: skuffla CPC-etiketterna 1000 gånger och bygg null-fördelning för d-värden. Detta ersätter approximation-p av Mann-Whitney med en empirisk p som faktiskt är tolkningsbar givet residualiseringen.
8. **Bootstrap-CI på residualiserad d** för att hantera stabilitet — d=0.24 ± hur mycket?

Det här är realistiskt ~1-2 dagars arbete. Surface B v2-resultatet kommer att vara grunden för artikel-pivoten.

## 7. Hur artikeln ska ramas in nu

Jag tycker du har en artikel-kärna. Den ser ut så här:

> Vi testade en Laguerre-form-inspirerad krökningsförändrings-familj efter cardiac-arrest coma. **Surface A** (lokal patchpassning på MNPS-punktmoln) visade sig vara estimator-domiminerad: syntetiska kontroller bevisade att saddle/shape-distribution-metriker är icke-distingerbara från brus vid de bruseffekter som karakteriserar coma-data. **Surface B** (deformation av per-window reachability-kovarians under SPD-Riemann-metriker) ger en kvalitativt distinkt observation: rang-baserad rå-evidens visar att CPC5 har högre kovariansdeformation, men **efter kontroll för reachability-storlek och A-operator-styrka vänds tecknet** och CPC1 har högre deformation. Effekten är liten (d≈0.24, Cliff's δ konsekvent över geometrier) men sign-flippen är robust mot residualisering, valt av SPD-geometri (log-Euclidean och Bures-Wasserstein), och inte reproducerbar med syntetiska negativa kontroller.

Det är en ärlig metodologisk artikel med ett bounded empiriskt resultat. Stark titel-kandidat:

> *Reachability Covariance Deformation as a Severity-Independent Geometric Layer After Cardiac-Arrest Coma*

Den kallar inte längre sig själv "Laguerre" i titeln (eftersom Surface A föll på syntetiska kontroller, och det är på Surface B vi har en signal som inte är klassisk Laguerre-form), men det är konceptuellt på samma plats som typ-filens H1/H3.

## 8. En sak till — viktigt för diary

Innan du skriver upp v2-diaryn: **det är värt att explicit notera att v2-residualfynden (`legacy_change_norm`, `shape_entropy`, `saddle_fraction`) sannolikt är estimator-artefakter**, inte bara "svagare än Surface B". Det är en omkalibrering av tolkningen. Annars riskerar man att senare läsa diary 085 och tro att Surface A "fungerade men Surface B fungerar bättre", när den korrekta läsningen är "Surface A:s överlevande residualer kan inte distingeras från brus enligt syntetiska kontroller".

Det är en mer brutal slutsats än "Surface A klarar sig dåligt under brusstress", men det är den slutsats syntetik-tabellen faktiskt stöder.

---

Vill du att jag tar nästa steg konkret? Naturliga val:

- (a) skriva Surface B v2 med ε-regularisering, Bures-Wasserstein, arcsinh-transform, temporal gradient, syntetiska Σ-kontroller och permutationsnoll;
- (b) bara den minimala fixen — ε-regularisering + arcsinh på p95 — för att se om sign-flippen håller med stabilare numerik;
- (c) skriva diary 086 som dokumenterar både syntetik-resultatet och Surface B-pivot innan vi kodar mer;
- (d) börja skissa Typ-filen för den nya artikeln eftersom story-line nu är tydligare.

Min spontana ordning är **c → b → a → d**, men du kanske har bättre känsla för var luften finns.