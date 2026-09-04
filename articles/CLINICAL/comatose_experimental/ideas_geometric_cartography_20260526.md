# Geometrisk kartografi för koma — kandidatformer bortom 9D-Jacobian, reachability och Laguerre

**Datum:** 2026-05-26
**Författare:** Robin Langell + AI research lead (explorativ läsning)
**Status:** Idé-dokument. Inga av dessa förslag är implementerade eller validerade i NDT-bundles. Varje kandidat är märkt enligt kategorier 1–5 i `role.mdc` (1 = etablerat externt, 2 = internt validerat, 3 = plausibel tolkning, 4 = spekulativ utvidgning, 5 = förkastat).
**Avgränsning:** Detta är en kartografi över *vilka geometriska former* som kan förklara koma bättre, *givet* den empiriska signaturen som redan finns i `comatose_ndt_jacobian_9d`, `comatose_ndt_regional`, `comatose_laguerre` och `comatose_ndt`. Det är inte en hypotes-prövning och inte en artikel.

---

## 1. Vad som redan utforskas (för att inte upprepa)

Den nuvarande NDT-geometrin för koma består av sex aktiva lager. Varje lager är välmotiverat, men varje lager har också en specifik tolknings-blindfläck som motiverar att leta efter nya former.

| Lager | Objekt | Främsta CPC1/CPC5-signal | Blindfläck |
|---|---|---|---|
| **MNPS-3D** | $x_t = [m_t, d_t, e_t]^T$ | Coordinat-spread (`coords_9d_global_std_mean`) | Komposit-3D maskerar kompenserande sub-skift |
| **Stratifierad 9D** | $x_t^{(9)} \in \mathbb{R}^9$ | Möjliggör block-Jacobian | Används som *flata features*, inte som en stratifierad rymd |
| **MNJ (Jacobian-spektrum)** | $J_t \in \mathbb{R}^{9 \times 9}$, eigen | `spectral_radius_median` $d \approx -0.62$ pooled; `anisotropy_abs_eig`; `rotational_power`; `frobenius_norm` | Eigenvärden ensamma fångar inte *robusthet* (pseudospektrum); skin-effect av non-Hermitian struktur är inte tagen |
| **Reachability-koner** | $\Sigma_t^{(h)}$ ellipsoid | `tube_d_eff_median` $d \approx +0.7$; `tube_a_operator_norm`; `tube_capture_gate` | Reduceras till patient-median; *tids-trajektorian* av $\Sigma_t$ är inte ett objekt |
| **Laguerre Surface A** | Lokala kvadratiska patches på MNPS-punktmoln | Förkastat i syntetisk kontroll (sfär gav `saddle_fraction ≈ 0.93`) | Kategori 5 — estimator-dominerat |
| **Laguerre Surface B** | Log-Euklidean deformation av $\Sigma_t$ | Pooled residual $d \approx 0.24$ efter reachability-kontroll | Genuint nytt, men numeriskt skört (matris-log singularitet vid rang-kollaps) |
| **C/TI/P regime-tripel** | $(C_t, \mathrm{TI}_t, P_t)$ | Konceptuell — operationaliserad mest tydligt i epileptisk ictal, inte i koma | Klinisk tolkningsram, inte ett mätbart geometriskt objekt i koma-bundles |

**Kärnan i den empiriska signaturen** (vad ska den nya geometrin förklara?):

- CPC1 har *lägre* lokal Jacobian-spektralradie ($\rho(J_t)$), *lägre* rotationskraft ($\sum_i |\mathrm{Im}(\lambda_i)|$), *bredare* effektiv reachability-dimension, och *mer* deformation av $\Sigma_t$ över tid (Surface B-residualen).
- CPC5 är *stelare i tid* (lägre $\dot\Sigma$), *mer roterande lokalt* (högre $|\mathrm{Im}\lambda|$), *mer captured* (hög `tube_capture_gate`), men inte alltid mindre *anisotropisk* per ellipsoid.

Det är en signatur av **en stel oscillator instängd i ett smalt reachable-fönster**, medan CPC1 är **en bredare diffuserande sökare med organiserad kontraktion**. Det är den signaturen som de nya kandidatgeometrierna ska försöka *separera* eller *kausalt förankra*.

---

## 2. Sex tolknings-gap som motiverar nya geometrier

1. **Tids-trajektorian av reachability är reducerad till en median.** Surface B går halvvägs (lokala $\Sigma_t \to \Sigma_{t+\Delta}$-gradienter) men hela 12-timmars-banan i $\mathcal{P}_n$ (SPD-mångfalden) är inte ett mätobjekt. Geodetisk krökning, banlängd, vridning — okänt.
2. **9D-stratifieringen används flat.** Den hierarkiska strukturen ($m$-familj, $d$-familj, $e$-familj) som motiverade hela chartdesignen behandlas inte som en *foliation* med flera strata.
3. **Non-Hermitian struktur av $J_t$ används bara via spektrum.** Pseudospektrum, transient amplification ($\|e^{tJ}\|$), och skin-effect saknas. En non-normal $J$ kan ha alla eigenvärden i vänster halvplan men *ändå* visa stark transient tillväxt.
4. **Skillnaden mellan "låg-kapacitet smooth" och "låg-kapacitet pathological" är inte avgjort.** H2a vs H2b i Laguerre-typ är fortfarande oavgjord. En topologisk distinktion (Betti-tal) skulle kanske skilja en *smooth flattened arrest* från en *fragmenterad multi-komponent kollaps* på ett sätt som en spektral-storlek-skala inte kan.
5. **"Recovery as bifurcation"-hypotesen är inte testad.** Den empiriska signaturen (CPC5 = lägre $\rho$, högre rotationskraft) liknar starkt ett system som passerat en *sub-kritisk Hopf-bifurkation* till en lokal limit cycle. Birkhoff normal form skulle kunna ge en *kvalitativ* (inte bara kvantitativ) markör.
6. **Skala/amplitud-invarians är inte säkrad.** EEG-amplitudvariation mellan patienter är dramatisk. Geometrier som *bara* använder vinkel/form (konforma, projektiva) skulle vara robustare mot detta.

---

## 3. Sju kandidatgeometrier

Varje kandidat presenteras som: (a) matematisk definition, (b) klinisk hypotes (vad den ska skilja), (c) implementations-väg från befintliga H5-bundles, (d) falsifierbarhet (negativ-kontroll), (e) kategori-stämpel.

### 3.1 Fisher–Bures-geodetisk geometri på reachability-banan

**Kategori: 3 (plausibel tolkning) — direkt utvidgning av Surface B på matematiskt välbeprövad grund.**

Behandla varje patients tids-bana $\{\Sigma_t\}_{t=0}^{12h}$ inte som en sekvens av punkter i $\mathbb{R}^{n \times n}$, utan som en *kurva* $\gamma : [0, 12\mathrm{h}] \to \mathcal{P}_n$ i den positiva-definita mångfalden $\mathcal{P}_n$, utrustad med Bures-metriken (eller den ekvivalenta affine-invarianta Fisher-Riemannska metriken). Dessa metriker är *välkända* från kvantinformation och informationsgeometri och är icke-degenererade även vid rang-skiftning (med korrekt regularisering).

Definiera tre nya skalärer:
$$
L_{\mathrm{geod}} = \int_0^{12h} \|\dot\Sigma_t\|_{\Sigma_t} \, dt, \quad
\kappa_{\mathrm{geod}}(t) = \frac{\|\nabla_{\dot\gamma} \dot\gamma\|}{\|\dot\gamma\|^2}, \quad
\theta_{\mathrm{torsion}} = \angle(\Sigma_0 \to \Sigma_{6h}, \Sigma_{6h} \to \Sigma_{12h})
$$

där $L_{\mathrm{geod}}$ är banlängd i Fisher-Bures-metric, $\kappa_{\mathrm{geod}}$ är geodetisk krökning (hur "vinglig" banan är gentemot rakaste väg), och $\theta_{\mathrm{torsion}}$ är vinkeln mellan parallell-transporterade tangentvektorer för första vs andra halvan.

**Klinisk hypotes:** CPC1 har högre $L_{\mathrm{geod}}$ (mer aktiv re-modellering av reachability), lägre $\kappa_{\mathrm{geod}}$ (rakare väg mot expansion), och mer konsistent $\theta_{\mathrm{torsion}}$ (riktningsstabilitet). CPC5 har låg $L_{\mathrm{geod}}$ (stagnation) eller hög $\kappa_{\mathrm{geod}}$ (vingligt brus).

**Implementations-väg:** Existerande $\Sigma_t$ per fönster finns redan i Surface B-pipelinen (`articles/CLINICAL/comatose_laguerre/results/laguerre_surface_b_v2_extended_20260525_part2_fullbatch/`). Lägg till Bures-/affine-invariant-distance och numerisk integral. Regulariseringen som diskuterades i `ideas_response_gemini2.md` ($\tilde\Sigma = \Sigma + \epsilon I$) är obligatorisk här.

**Falsifierbarhet:** Tids-shuffle ska kollapsa $L_{\mathrm{geod}}$ (banlängden växer) och $\kappa_{\mathrm{geod}}$ ska blåsas upp. Om gruppsignaturen *inte* förändras under tids-shuffle är effekten artefakt-dominerad.

**Risk:** Korrelerar potentiellt starkt med Surface B men ger *temporala* (inte lokala) summor. Måste residual-testas mot både Surface B *och* `tube_d_eff_median`.

---

### 3.2 Birkhoff normal form / Hopf-bifurkationsavstånd

**Kategori: 4 (spekulativ utvidgning) — väl-etablerat i nonlinear dynamics, oprövat på EEG-Jacobianer.**

Det empiriska mönstret (lägre $\rho(J)$ + högre $|\mathrm{Im}(\lambda)|$ i CPC5) är *exakt* signaturen av ett system som passerat en sub-kritisk Hopf-bifurkation: två komplex-konjugerade egenvärden har korsat imaginära axeln och systemet sitter fast i en liten lokal limit cycle. Birkhoff normal form klassificerar lokal dynamik nära en bifurkationspunkt.

För en 2D center-mångfald nära en Hopf-bifurkation kan dynamiken (efter koordinatbyte) skrivas som:
$$
\dot r = \mu r + a_1 r^3 + a_2 r^5 + \dots, \quad \dot\theta = \omega + b_1 r^2 + \dots
$$

där $\mu$ är "avstånd till bifurkation", $a_1$ är **första Lyapunov-koefficienten**, och tecknet på $a_1$ avgör super- vs sub-kritisk Hopf. Beräkningen av $a_1$ från en empirisk lokal flödesskattning är välbeskriven (Kuznetsov, *Elements of Applied Bifurcation Theory*).

Definiera per patient:
- **`birkhoff_lyap_coeff_median`**: median över fönster av första Lyapunov-koefficienten $a_1(t)$ för det dominanta komplexa egenvärdesparet av $J_t$.
- **`bifurc_distance_median`**: median av $\mu(t) = \mathrm{Re}(\lambda_1(t))$, där $\lambda_1$ är det egenvärde närmast imaginära axeln.
- **`subcritical_fraction`**: andel av fönstren där $a_1 > 0$ (sub-kritisk regim, indikerar fastlåst limit cycle).

**Klinisk hypotes:** CPC5 har högre `subcritical_fraction` (sub-kritisk Hopf = lock-in), $\mu \approx 0$ med små svängningar (sitter vid bifurkationen), CPC1 har $\mu < 0$ stabilt (icke-roterande kontraktion) eller super-kritisk regim (släppt limit cycle med organiserad sökning).

**Implementations-väg:** $J_t$ exporteras redan per fönster i `jacobian/J_hat` på H5-bundles. Beräkningen av $a_1$ kräver också $\dot J_t$ och projektion på centrumriktning — alla redan tillgängliga. Bibliotek: SciPy + manuell implementation av Kuznetsovs normalform-formel (~60 rader Python).

**Falsifierbarhet:** Detta är *den enda* av kandidaterna som har ett kvalitativt (tecken-baserat) bestämt utfall. Om `subcritical_fraction` inte separerar grupper alls efter residualisering mot `rotational_power_mean` och `spectral_radius_median`, är hypotesen *kausalt* falsifierad — inte bara statistiskt svag.

**Risk:** Birkhoff normalform kräver att vi *antar* att vi är *nära* en Hopf — om inte (dvs. lokala $J_t$ inte har komplexa egenvärden med $\mathrm{Re}(\lambda) \approx 0$), så är hela transformationen meningslös. Ett pre-filter (andel fönster med "Hopf-aktuella" egenvärden) måste rapporteras tillsammans med metriken.

---

### 3.3 Persistent homology av tids-evolverande reachable cloud

**Kategori: 1 (etablerat externt) i ren matematik / topologisk data-analys + 4 (spekulativ tillämpning) på koma.**

Persistent homology (PH) är ett etablerat verktyg för att kvantifiera *topologisk struktur* (komponenter, loopar, voids) i punktmoln över skalor. Vid varje tids-fönster $t$ konstruera Vietoris-Rips-komplex på de senaste $W$ MNPS-punkterna och beräkna persistens-diagram $\mathrm{PD}_k(t)$ för $k = 0, 1, 2$.

Definiera:
- **`H0_total_persistence_median`**: median (över $t$) av summa-livslängd av $H_0$-streck (komponentstabilitet).
- **`H1_max_persistence_median`**: median av längsta $H_1$-streck (cykelpersistens — fångar "ringar" i state-rummet).
- **`bottleneck_drift`**: bottleneck-avstånd mellan $\mathrm{PD}_1(0\text{-}6\mathrm{h})$ och $\mathrm{PD}_1(6\text{-}12\mathrm{h})$ — fångar topologisk omorganisation.

**Klinisk hypotes (två konkurrerande):**
- **H2a-test** (smooth flattened arrest): CPC5 har låg $H_0$- och $H_1$-persistens (allt klumpas i en boll, inga cykler). CPC1 har stabila $H_0$ men måttlig $H_1$.
- **H2b-test** (pathological folding): CPC5 har *hög* $H_1$-persistens med många kortlivade streck (fragmenterad topologi), medan CPC1 har färre men längre $H_1$-streck (en stabil cykel = healthy alpha-rytm).

Detta är den första kandidat som *strukturellt* kan separera de två tolkningsalternativen som har varit oavgjorda i Laguerre-typ-filen sedan oktober.

**Implementations-väg:** `ripser` eller `gudhi` (båda har Python-bindings) på MNPS-3D-fönster. Beräkning är O($n^3$) i punktantal per fönster, men $W$ behöver bara vara ~30–50 så det är hanterligt på 281 patienter.

**Falsifierbarhet:** Slumpad MNPS-koordinatordning ska förstöra `bottleneck_drift` men *inte* `H0_total_persistence_median` (eftersom det är form-baserat, inte sekvens-baserat). Detta är en användbar inbyggd dissociation: om båda kollapsar är hela PH-signalen artefakt.

**Risk:** PH är *invariant under monotoniska skaltransformeringar*, vilket är en styrka för EEG-amplitudsruckningar — men det betyder också att det är *insensitivt* för viktiga skala-effekter (storleken på reachable space). Måste alltid rapporteras parallellt med en skala-metrik.

---

### 3.4 Stratifierad singular foliation av 9D-charten

**Kategori: 3 (plausibel tolkning) — operationaliserar den befintliga 9D-stratifieringen som den faktiskt är konstruerad.**

9D-charten har redan en *naturlig stratifiering*: tre familjer ($m_a, m_e, m_o$ för mobilitet; $d_n, d_l, d_s$ för deviation; $e_e, e_s, e_m$ för entropi). I differential-geometri är en *singulär foliation* (Whitney) en uppdelning av en mångfald i blad av varierande dimension. Koma kan modelleras som en *rang-kollaps* — att systemet glider ner i ett *lägre stratum* (förlust av aktiva sub-koordinater).

Definiera den lokala *effektiva-stratum-dimensionen* per fönster:
$$
d_{\mathrm{strat}}(t) = \sum_{f \in \{m, d, e\}} \mathbf{1}[\mathrm{rank}(\mathrm{Cov}(x_f, w_t)) > \tau]
$$
där $w_t$ är ett fönster och $\tau$ en numerisk tröskel — dvs. en räkning av hur många 3D-sub-familjer som "aktivt rör sig" lokalt. För en frisk patient borde $d_{\mathrm{strat}}(t) = 3$ (alla familjer aktiva). För en kollapsad patient $\leq 1$.

Mer skarpt: definiera **stratum-transition-täthet** som antalet tidsfönster där $d_{\mathrm{strat}}$ förändras med $\geq 1$. CPC1 förväntas ha *hög* stratum-transition-täthet (systemet växlar familjer), CPC5 låg (fastnar i ett stratum).

**Implementations-väg:** Triviala beräkningar på `coords_9d/values` H5-data, redan tillgängliga.

**Falsifierbarhet:** Klar — `d_strat` ska *inte* skilja CPC1/CPC5 efter residualisering mot `coords_9d_global_std_mean`, *om* signalen är en ren spridningssignal. Om den separerar även efter, är detta ett *strukturellt* tillägg.

**Risk:** Stratifieringen är fortfarande en *post hoc* uppdelning av 9D-koordinater i tre familjer. Den biologiska tolkningen ($m$-familj som "mobilitet") är hypotetisk, inte mekanistiskt etablerad. Detta är en *operationalisering* av en befintlig hypotes, inte en oberoende verifiering av den.

---

### 3.5 Pseudospektrum av $J_t$ och transient amplification

**Kategori: 1 (etablerat externt) — Trefethen & Embree, *Spectra and Pseudospectra*. Standard i numerisk linjär algebra. Oprövat i NDT.**

Den nuvarande MNJ-analysen rapporterar bara spektrum — egenvärden $\lambda_i(J_t)$. Men för en *non-Hermitian* operator (vilket $J_t$ generellt är) säger eigenvärden inte hela sanningen. Ett system med alla $\mathrm{Re}(\lambda_i) < 0$ kan ändå visa stark transient tillväxt om $J_t$ är *icke-normal*: $JJ^* \neq J^*J$.

Definiera:
- **`pseudospec_radius_eps_median`**: för $\epsilon$-pseudospektrum $\sigma_\epsilon(J) = \{z \in \mathbb{C} : \|(zI - J)^{-1}\| > \epsilon^{-1}\}$, mät dess radie för fixerat litet $\epsilon$.
- **`kreiss_constant_median`**: $\sup_{\mathrm{Re}(z) > 0} \mathrm{Re}(z) \|(zI - J)^{-1}\|$ — en Kreiss-konstant som ger en undre gräns för max transient $\|e^{tJ}\|$.
- **`non_normality_median`**: $\|JJ^* - J^*J\|_F$ — direkt mått på hur långt från normal $J$ är.

**Klinisk hypotes:** CPC5 är *mer non-normal* (Jacobianer är "skinky" — eigenvärden är stabila i analys men en mindre perturbation kan kasta systemet till en helt annan lokal regim). Detta är en *robusthet*-tolkning av samma spektrala data som redan finns. CPC1 är "närmare normal" — egenvärden ger en ärlig bild av framtida flöde.

Detta skulle vara en ny *tolkningsdimension* för befintliga Jacobian-data utan att kräva nya H5-export. Det är en omtolkning av samma matriser i ett mer komplett ramverk.

**Implementations-väg:** SciPy + `pseudopy` eller manuell SVD-baserad beräkning per $J_t$. Mest CPU-tunga av alla kandidater, men <1h på 281 patienter med rimliga horisonter.

**Falsifierbarhet:** Om `non_normality_median` korrelerar perfekt med `frobenius_norm_median` (vilket den *kan* göra eftersom båda är operator-storheter), är pseudospektrum-tolkningen redundant. Test: ortogonalisera `non_normality` mot `frobenius` och se om residualen har klinisk signal.

**Risk:** Pseudospektrum-radien har en parameter $\epsilon$ vars val är arbiträrt. Borde rapporteras för flera $\epsilon$-värden eller normaliseras mot $\rho(J)$.

---

### 3.6 Magnitude function av reachable state cloud

**Kategori: 1 (etablerat matematiskt) — Leinster, magnitude för metriska rum. Oprövat i neurovetenskap.**

Magnitude $|X|(t)$ för ett metriskt rum $(X, d)$ är en *generaliserad volym* parametriserad av en skala $t$. Den definieras som $|X|(t) = \mathbf{1}^T Z^{-1}(t) \mathbf{1}$ där $Z_{ij}(t) = e^{-t \cdot d(x_i, x_j)}$. För små $t$ är magnitude $\approx 1$ (ett "punktlikt" objekt); för stora $t$ är magnitude $\approx n$ (antal punkter). Mellanliggande $t$ avslöjar *skalstruktur*.

Definiera:
- **`magnitude_dim_at_t_star`**: $d|X|/d\log t$ vid en optimalt vald skala $t^*$ — en *skala-baserad* effektiv dimension.
- **`magnitude_function_area`**: integral av $|X|(t)$ över relevant skalintervall — en sammansatt invariant.

**Klinisk hypotes:** Magnitude är *känsligare* för fragmentering än effective dimensionality. En stelnad CPC5-patient som ändå har punkter i många riktningar (men i två separerade kluster) kommer ha låg magnitude-area, medan effective dimensionality kan vara missvisande hög.

**Implementations-väg:** Manuell Python (Leinster's formel är ~5 rader), enbart MNPS-koordinatdata.

**Falsifierbarhet:** Magnitude är *konstruktionsmässigt* en multiskal-effektiv-dimension. Om den korrelerar starkt med `tube_d_eff_median`, tillför den inget. Måste residualiseras.

**Risk:** Detta är ett *konstruktivt* mått snarare än ett *kvalitativt* nytt geometriskt objekt. Det löser kanske bara fragmentering-vs-koherens-frågan utan att lägga till ny mekanistisk insikt. Sannolikt mer en *bättre skalär* än en *ny geometri*.

---

### 3.7 Lorentzisk / kausal-kon-geometri på state-tids-mångfald

**Kategori: 4 (spekulativ utvidgning) — pseudo-Riemannsk geometri är etablerat i allmän relativitet, oprövat i EEG-analys.**

Hittills behandlas tid och tillstånd som ortogonala dimensioner. En *Lorentzisk* alternativ behandlar tids-tillstånd-rymd $(t, x_t) \in \mathbb{R} \times \mathbb{R}^9$ med en pseudo-metric där "kausalt nåbara" punkter ligger inom en framtidskon definierad av en lokal maximal-utbredningshastighet $c_t$ (analog till ljushastighet). Den naturliga kandidaten för $c_t$ i EEG-MNPS är $\|f(x_t, t)\|$ — den lokala drift-magnituden.

Definiera:
- **`causal_volume_median`**: volymen av framtidskonen från $(t, x_t)$ till $(t + 12h, *)$ inom MNPS — hur många framtida tillstånd är kausalt nåbara från nu?
- **`causal_diamond_anisotropy`**: anisotropin av "kausal-diamant" (skärningen av framtidskon från $t = 0$ och dåtidskon från $t = 12h$) — fångar om recovery-banan har "trångt" mellanstadium.

**Klinisk hypotes:** CPC1 har stor kausal-volym (system kan nå många olika tillstånd från nuet) och låg kausal-diamant-anisotropi (rakt utbredningsmönster). CPC5 har liten kausal-volym (instängd framtid) och kanske riktad diamant (rörelse bara längs en riktning).

**Implementations-väg:** Kräver `mnps_3d_dot` per fönster för att skatta $c_t = \|\dot x_t\|$ — finns redan. Volym-beräkningen är Monte Carlo eller analytisk för enkla kon-modeller.

**Falsifierbarhet:** Den lokala maximala hastigheten $c_t$ är arbiträr — vi definierar den. Test: använd både $\|\dot x_t\|$ och `tube_a_operator_norm` som alternativa $c_t$-definitioner. Om resultatet är robust under detta val, är effekten genuin; annars är det en parameterval-artefakt.

**Risk:** Mest "fysikalisk analogi" av alla kandidater. Den bär en metafor som lätt kan missläsas som mekanism. Det är därför kategori 4 — explicit spekulativ.

---

## 4. Prioritering

Min kartografi-rekommendation, sorterad efter *odds att ge ärlig ny information per implementationskostnad*:

1. **Pseudospektrum / non-normality (3.5)** — högst odds. Använder samma $J_t$ som redan exporterats, lägger till en *etablerad* matematisk dimension (Trefethen) som tolkar samma data robust-orienterat. Risken är låg eftersom det är en omtolkning, inte en ny hypotes. Skulle direkt belysa *varför* `spectral_radius` separerar grupper.

2. **Persistent homology (3.3)** — näst högst odds. Den första kandidat som *strukturellt* kan dissociera H2a (smooth flattened) från H2b (pathological folding). Etablerat verktyg. Kräver bara MNPS-punktmoln över fönster.

3. **Fisher-Bures-geodetisk geometri på $\Sigma_t$-banan (3.1)** — direkt utvidgning av Surface B, närmar sig den principiella form som Surface B alltid var menat att vara. Numeriskt skört (kräver regularisering) men matematiskt rigoröst.

4. **Birkhoff normal form (3.2)** — kvalitativt mest informativ (super- vs sub-kritisk Hopf är en *teckenfråga*, inte en magnitudfråga) men teknisk implementeringsrisk och förutsätter att vi *är* nära en Hopf. Värt en konceptuell pilot, inte en full körning ännu.

5. **Stratifierad singular foliation (3.4)** — har högst risk för att vara *operationalisering* av en befintlig hypotes snarare än ett oberoende test. Värdefull bara om kombinerad med en mekanistisk validering av 9D-familje-uppdelningen.

6. **Magnitude function (3.6)** — sannolikt en *bättre skalär* snarare än en ny geometri. Lågrisk att implementera, men förmodligen redundant med `tube_d_eff_median` + spridningsmått.

7. **Lorentzisk kausal-kon (3.7)** — mest spekulativ. Värd att hålla på en idé-lista men inte nästa rond.

---

## 5. Avvisade riktningar (kategori 5)

För att kartografin ska vara ärlig, även de förkastade:

- **Tropisk geometri av reachable polyhedron.** Trots eleganta diskreta invariants är skalrymden för EEG-tidsserie för låg-dimensionell för att tropisk geometri ska säga något icke-trivialt utöver effective dimensionality. Förkastat.
- **Konformell embedding i hyperbolisk rymd.** Tilltalande för hierarkiska data, men 9D-MNPS är inte naturligt trädformat. Förkastat utan starkare motivering.
- **Andersson-lokalisering / random matrix-statistik.** Skulle kräva *ensembler* av lokala $J_t$ tvärs tid eller patienter, och de kliniska kohorterna är för små för att stödja en statistisk-mekanik-rättvisa analys av spektral-gap-fördelningar. Hänvisat till framtida arbete med större cohorts.
- **Voronoi/Delaunay-celler.** För hög kombinatorisk komplexitet i 9D utan klart kliniskt mervärde jämfört med kNN-baserade reachability-skattningar. Förkastat.
- **Catastrophe-theory-klassifikation (Thom, swallowtail osv.).** Konceptuellt elegant men kräver *exakt observerbarhet* av kritiska punkter i den effektiva potentialen $\Phi$, vilket inte är direkt mätbart från EEG-MNPS. Bättre lämnat som metafor än som mätobjekt.

---

## 6. Geometriska former som *kanske* är vägledande men inte mätbara

Två slutkommentarer som hör hemma här som intellektuell hygien snarare än praktiska rekommendationer:

- **Stratifierade *Lie-grupp-action*-orbiter:** Om man skulle kunna identifiera en relevant lokal symmetrigrupp (rotation av MNPS, skalförändring av amplitud, tid-translation) skulle koma kunna karakteriseras som en *kollaps av orbit-dimensionalitet*. Detta är mer en filosofisk ram än ett mätbart objekt i nuvarande pipeline.
- **Operad / higher-category strukturer för sammansättning av neurala processer:** Detta vore en geometri på *operatorer* snarare än på tillstånd. Det är förmodligen den rätta abstraktionsnivån för att förstå hur 9D-block-strukturen *komponeras*, men det är minst tio år borta från att vara mätbart från EEG-bundles.

Båda nämns för fullständighet, inte som rekommendationer.

---

## 7. Slutsats och rekommenderad nästa rond

Min ärliga läsning: *de mest underutnyttjade geometrierna är inte exotiska nya former, utan etablerade verktyg som ännu inte är tillämpade på NDT-data.* Specifikt:

- **Pseudospektrum** är gratis-uppgradering av en redan stark MNJ-pipeline.
- **Persistent homology** är det enda föreslagna verktyget som kan ge en *strukturell* (topologisk) dissociation mellan H2a och H2b.
- **Fisher-Bures-geodetisk geometri** sluter cirkeln på Surface B-piloten genom att ge den fulla matematiska tolkningsramen som den alltid var menat att ha.

Resterande kandidater är *värda att hålla på listan* men kräver mer mognad innan implementation. Ingen av dem är garanterad att slå reachability-baseline, och om ingen gör det skulle det vara ett genuint intressant *negativt* resultat (NDT-spektrumet av lokala-linjära mått är då ungefär uttömt och nästa stora vinst kommer från en annan modalitet — t.ex. multi-modal MEG/fMRI eller intracellular).

Konkret förslag på första pilot (i prioritetsordning):

1. Skriv `pseudospectrum_pilot.py` som tar samma `part1`/`part2`-bundles, beräknar `pseudospec_radius`, `non_normality`, `kreiss_constant` per patient, och rapporterar Cohen's $d$ på CPC1 vs CPC5 plus residualtest mot befintliga MNJ-metriker. ~1 dag.
2. Skriv `persistent_homology_pilot.py` som beräknar $H_0$- och $H_1$-persistens-diagram på fönsterskala-MNPS, summerar till patient-nivå, och testar residualer mot reachability. ~2 dagar.
3. Lägg till `bures_geodesic_metrics.py` som en utvidgning av befintlig Surface B-pipeline. ~1 dag.

Totalt ~1 vecka för att evaluera vilka av dessa tre etablerade matematiska språk som faktiskt har klinisk separation-effekt i koma-data.

**Slutord (epistemisk disciplin):** Inget av detta är ett konsumtionsmarknader-redo-biomarkör. Det är *vilka geometrier som vore värda att försöka först*. Falsifiering är lika informativ som bekräftelse — om alla tre piloter ger Cohen's $d < 0.2$ residualiserat har vi lärt oss att den nuvarande koma-MNJ + reachability-pipelinen ungefär uttömmer den lokala-linjära geometrin av EEG-state-rummet, och vinstmarginalen för fortsatt geometri-utveckling i denna modalitet är liten.
