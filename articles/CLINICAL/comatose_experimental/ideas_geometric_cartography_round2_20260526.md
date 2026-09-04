# Geometrisk kartografi rond 2 — koma-geometrier byggda på MNPS och MNJ, informerade av aktuell forskning

**Datum:** 2026-05-26
**Författare:** Robin Langell + AI research lead (litteratur-informerad andra rond)
**Status:** Idé-dokument. Bygger vidare på `ideas_geometric_cartography_20260526.md` i samma mapp. Inga av kandidaterna är implementerade. Varje kandidat är märkt enligt kategorier 1–5 i `role.mdc` (1 = etablerat externt, 2 = internt validerat, 3 = plausibel tolkning, 4 = spekulativ utvidgning, 5 = förkastat).
**Avgränsning:** Detta dokument är specifikt om geometrier som **byggs på MNPS-koordinater och/eller MNJ-Jacobianer** (inte på reachability-tubernas SPD-mångfald, som täcktes av Surface B-piloten och rond 1-kandidat 3.1). Sökt litteratur: aktuell (2024–2026) forskning om koma-EEG, medvetande, kritikalitet, neural manifold dynamics, persistent homology, och whole-brain modeling.

---

## 1. Vad rond 1 lämnade öppet och varför rond 2 behövs

Rond 1 var bred och kategoriserade sju nya kandidatgeometrier från ren matematik. Den var disciplinerad men *litteratur-naiv* — den letade inte aktivt efter klinisk-empirisk validering eller konkurrerande publicerade ramar. Efter en strukturerad sökning i koma-EEG-, medvetande- och dynamic-systems-litteraturen från 2024–2026 har sex fynd identifierats som direkt påverkar vilka geometrier som *redan har klinisk hävstång* och vilka som är spekulativa.

Det viktigaste byte mellan rond 1 och rond 2: i rond 1 var prioriteringen "ärlig ny information per implementationskostnad" intern. I rond 2 prioriteras geometrier som har en *publicerad extern referens* som etablerar deras klinisk-empiriska giltighet. Detta höjer vissa kandidater från kategori 4 till kategori 1, och förkastar andra.

---

## 2. Sex litteraturfynd som ändrar urvalet

### 2.1 Edge-of-chaos är ett validerat medvetandekorrelat

- **Toker et al., PNAS 2022** ("Consciousness is supported by near-critical slow cortical electrodynamics") använder det modifierade *0-1 chaos test* (Gottwald & Melbourne) på ECoG och MEG från vakna, ictala, anestesi- och psykedeliska tillstånd. Vakenhet ligger nära edge-of-chaos; medvetslöshet drar sig bort från det, antingen mot ordnad eller mot stark kaotisk sida. Psykedelika *närmar sig* edge-of-chaos från kaotisk sida.
- **Maschke et al., Commun Biol 2024** ("Critical dynamics in spontaneous EEG predict anesthetic-induced loss of consciousness and perturbational complexity") visar att avstånd från edge-of-chaos *predikterar individens PCI-värde* med medelabsolutfel <7%. Detta är *ett av de starkaste empiriska sambanden mellan en geometrisk markör och PCI* som finns i litteraturen.
- **Larkin et al., arxiv:2509.00730 (2025)** ger ett teoretiskt response-function-bevis för att rekurrenta neurala nät har maximal informationsbearbetnings-kapacitet *exakt* vid edge-of-chaos.

**Implikation för NDT:** Edge-of-chaos är inte längre en abstrakt nonlinear-dynamics-idé. Det är ett *kliniskt-empiriskt validerat* medvetandekorrelat med direkt PCI-koppling. Min rond-1-kandidat 3.2 (Birkhoff normal form / Hopf-bifurkationsavstånd) lyfts härmed från **kategori 4 (spekulativ)** till **kategori 1 (etablerat externt)** vad gäller dess kliniska motivering — men kvarstår som kategori 3 (plausibel) vad gäller dess MNJ-specifika operationalisering.

### 2.2 Universal Map of EEG är en direkt konkurrent till MNPS

- **Tjepkema-Cloostermans et al., Annals of Neurology 2025** ("Toward a Universal Map of EEG", AN-2024-13486) presenterar UM-EEG: en 128-dimensionell semantisk EEG-manifold lärd från 288 986 segment över 11 medvetande-/patologi-tillstånd (W, N1, N2, N3, REM, SZ, GPD, LPD, GRDA, LRDA, BS). För cardiac-arrest-koma rapporterar de:
  - AUROC = 0.86 för CPC1-2 vs CPC5 vid out-of-sample center-cross-validation.
  - De starkaste prognostiska signalerna är *avståndet till en healthy reference manifold*, *övergångsentropi mellan tillstånd*, och *tid spenderad i burst suppression*.

**Implikation för NDT:** UM-EEG är ett *icke-interpretabelt* deep-NN-embedding, medan MNPS har explicita axlar. De konkurrerar inte på samma dimensioner. Men UM-EEG visar att en *trajektoria-i-latent-space*-stil är empiriskt stark. **Det starkaste tillskottet till NDT är en distans-till-healthy-MNPS-manifold-metrik** som är *interpretabel* (eftersom MNPS-axlarna är det) men funktionellt parallell med UM-EEG:s ledande signal.

### 2.3 Hopf-bifurkation är standard-ramverket i whole-brain anestesi-modeller

- **Haddad et al., Mathematical Neuroscience 2015**, formaliserar medvetande→medvetslöshet-övergång som en Poincaré-Andronov-Hopf-bifurkation med supercritical reverse Hopf-passage.
- **The Virtual Brain (TVB)** använder Stuart-Landau-noder (den enklaste icke-linjära oscillator-formen som visar Hopf-bifurkation) som standard-byggsten för whole-brain-modeller (Deco et al. 2017 Sci Rep; Ipiña et al. 2020).
- **Steyn-Ross & Steyn-Ross, Phys Rev X 2013** — Turing-Hopf-interaktion driver slow-wave-aktivitet i koma/anestesi.
- **State-dependent brain responsiveness, eLife reviewed-preprints 2024–2025** — använder *Hopf-modell* för att lokalisera *subcritical (fluctuating) vs supercritical (oscillatory)* regim per region från fMRI/EEG.

**Implikation för NDT:** Hopf-bifurkations-avstånd kan operationaliseras genom *Stuart-Landau-fit på MNPS-koordinater* per fönster — ett etablerat ramverk vars parametrar (bifurkationsparameter $a$, eigenfrekvens $\omega$) är direkt klinisk-tolkbara. Detta är mer specifikt än min rond-1-kandidat 3.2 och har direkta validerings-referenser från Deco-gruppen.

### 2.4 Persistent homology har ett färdigt consciousness-paket

- **TopoConscious (github.com/Chege-N/TopoConscious)** — Python-paket med Vietoris-Rips-filtration, $H_0/H_1/H_2$-persistens, Wasserstein- och Müller-Lyer-distanser på persistens-diagram, HMM-decodering med 2-state conscious/unconscious-modell, plus *Topological Transfer Entropy* (C++/OpenMP-implementation). Testat på OpenNeuro propofol (ds002898), REM/NREM-sömn (ds000201), och Liège disorders-of-consciousness-data.
- Kärnhypotes (validerad): conscious states har högre persistens av $H_1$-cyklar (dynamisk integration). Unconscious states domineras av $H_0$-kluster (segregation).
- **Frontiers Hum Neurosci 2025** ("Topological signatures of brain dynamics") — fMRI-baserad PH visar individ-specifika *topologiska fingeravtryck* som överträffar konventionella temporala features i prediktionsuppgifter.

**Implikation för NDT:** Min rond-1-kandidat 3.3 (persistent homology av reachable cloud) lyfts till **kategori 1 (etablerat externt)** vad gäller medvetandetillämpning. Men en *NDT-specifik* operationalisering bör inte bara köra PH på MNPS-punktmoln (vilket TopoConscious redan gör för fMRI). Den bör utnyttja MNPS-stratifieringen och MNJ-flödet — annars är NDT bara ett substrat för en redan publicerad metod.

### 2.5 Band-stratifierad temporal graph theory dominerar i sABI

- **Bartolini et al., Sci Rep 2025** ("Temporal network instability and low-frequency overconnectivity underlie disorders of consciousness in severe brain injury") på n=217 sABI-patienter med och utan pDoC:
  - Higher *burstiness coefficient* i $\delta$- och $\theta$-band → pDoC.
  - Higher *temporal degree centrality* i $\delta$/$\theta$ → pDoC.
  - Lower *temporal correlation coefficient* i $\alpha$ → pDoC.
  - Higher *average topological overlap* i $\alpha$ → eMCS (medveten).
  - Frekvensspecifik temporal graph analys (TVGA).

**Implikation för NDT:** Det här fyndet är *direkt operationaliserbart* som en kritik av nuvarande NDT-pipeline: MNPS-koordinaterna är band-aggregerade ($e_e$, $e_s$, $e_m$ definieras över hela spektrumet enligt compendium-equations @eq:ee–@eq:em). En *band-stratifierad* MNJ — där vi bygger separat Jacobian per frekvensband — är inte längre en spekulativ utvidgning. Det är en specifik fix för en specifik fråga som Bartolini visat har klinisk diskriminerande kraft.

### 2.6 Nonlinear chaos-mått är standard i DOC-litteratur

- **Frontiers Hum Neurosci 2025 / PMC12463835** ("Discriminative power of diverse nonlinear EEG dynamics") använder Lyapunov-exponent (LE), Approximate Entropy (ApEn), Lempel-Ziv Complexity (LZC), och Correlation Dimension ($D_2$) i DOC. VS/UWS visar konsekvent *reducerad* LE, $D_2$, ApEn jämfört med MCS och friska kontroller.
- **Sensors 2025 / MDPI** (Robust EEG Characteristics for Coma Recovery) — funktionell konnektivitet 70%, burst suppression 20%, Higuchi Fractal Dimension är topfeatures (SHAP).

**Implikation för NDT:** Lyapunov-spektrum är *standard* för medvetande-kvantifiering, men NDT-pipelinen har det inte. Vi har $\rho(J_t)$ (spectral radius) som är *en* eigenstrukturskattning, men inte den fulla Lyapunov-spektrum-skalan som integrerar Jacobian längs en faktisk bana. Detta är ett uppenbart gap.

---

## 3. Sju nya kandidatgeometrier byggda på MNPS och MNJ

### 3.1 MNPS distance-to-healthy-manifold (UM-EEG-inspirerad)

**Kategori: 3 (plausibel tolkning) — direkt operationaliserar UM-EEG:s ledande prognostiska signal i NDT-koordinater.**

Konstruktion:
1. Bygg en *healthy MNPS-referensmanifold* $\mathcal{M}_{\text{healthy}}$ från friska kontroller (eller från CPC1-patienter sent i recovery, $t > 48$ h efter anchor, som proxy om kontrolldata saknas).
2. För varje patient och tidsbin, beräkna minsta avstånd till $\mathcal{M}_{\text{healthy}}$ i MNPS-3D eller 9D-utrymmet.

Tre operationaliseringar att prova parallellt:

$$
d_{\text{euclid}}(t) = \min_{m \in \mathcal{M}_{\text{healthy}}} \|x_t - m\|_2
$$
$$
d_{\text{mahal}}(t) = \min_{m \in \mathcal{M}_{\text{healthy}}} \sqrt{(x_t - m)^T \Sigma_{\text{healthy}}^{-1} (x_t - m)}
$$
$$
d_W(t) = W_2(\rho_{\text{patient},W}, \rho_{\text{healthy}})
$$

där $W_2$ är Wasserstein-2-distansen mellan fönsterfördelningen $\rho_{\text{patient},W}$ (alla MNPS-punkter i ett $W$-långt fönster runt $t$) och referensfördelningen $\rho_{\text{healthy}}$.

**Klinisk hypotes:** CPC1 har *minskande* $d(t)$ över 0–12 h (närmar sig healthy manifold), CPC5 har $d(t)$ som är högre och *flat* (inget tillnärmningsförlopp). Den temporala derivatan $\dot d(t)$ är möjligen mer informativ än absolut $d$.

**Implementations-väg:** `coords_9d/values` är redan exporterat. Healthy reference kan tas från publika EEG-databaser (HMM-prep från PhysioNet-Sleep eller TUH normal EEG) projicerade genom samma NeuralManifoldDynamics-pipeline. Wasserstein-2 mellan empiriska distributioner är tillgänglig i `POT` (Python Optimal Transport).

**Falsifierbarhet:** Om healthy reference *inte är tillgänglig från oberoende kohort* utan måste konstrueras från CPC1-tail-data, finns en cirkularitetsrisk. Pre-registreringen måste explicit förklara hur referensen byggs och varför den inte är cirkulär. Negativ kontroll: använd en "anti-healthy" referens (CPC5 mid-window) och bekräfta att tecknet vänder.

**Risk:** UM-EEG har redan publicerat denna idé på en högre upplösning (128D NN-embedding vs 9D MNPS). NDT-versionen måste motivera *varför explicita MNPS-axlar är bättre* än ett opaque embedding för klinisk tolkning. Detta är en stark tolknings-fördel men en svag prediktiv-fördel.

---

### 3.2 0-1 chaos test på MNPS-trajektoria

**Kategori: 1 (etablerat externt) — det modifierade 0-1 chaos test är publicerat (Gottwald & Melbourne 2009; Toker PNAS 2022). Aldrig tillämpat på NDT-koordinater.**

Det modifierade 0-1 chaos test tar en skalär tidsserie $\phi(t)$ och returnerar ett tal $K \in [0, 1]$, där $K \approx 0$ indikerar regulär/periodisk dynamik och $K \approx 1$ indikerar kaotisk dynamik. Toker et al. PNAS 2022 tillämpar den på *band-pass-filtrerad slow-wave EEG* (1–6 Hz) per kanal.

Tillämpa på MNPS:
$$
K_c = \text{0-1-test}(x_c(t)) \quad \text{för } c \in \{m, d, e\} \text{ eller } c \in \text{9D-koordinater}
$$

Definiera per patient:
- **`mnps_chaos_index_median`**: median över 9D-koordinater av $K_c$.
- **`mnps_chaos_index_anisotropy`**: variation av $K_c$ tvärs koordinater — fångar om vissa axlar har förlorat kaotisk struktur (lokaliserad bifurkation).
- **`mnps_edge_of_chaos_distance`**: $|K_c - 1| + |K_c - 0|/2$ — avstånd från det optimala $K_c = 1$ (alternativt en cohort-bestämd "wake midline" $K^*$).

**Klinisk hypotes:** Toker et al. visar att medvetslöshet är *bidirektional* — vissa patienter blir för regulära ($K \to 0$, dominerad av deltavågor), andra blir för stokastiska ($K$ förblir hög men förlorar strukturerad recurrence). CPC1 förväntas ligga närmare en cohort-specifik "wake $K^*$"-punkt än CPC5.

**Implementations-väg:** Det modifierade 0-1 chaos test finns som Matlab-implementation i Toker PNAS 2022 supplementary, plus Python-version i `nolds`-paketet eller direkt implementation (~80 rader). Indata: `coords_9d/values` tidsserie per patient.

**Falsifierbarhet:** Skall reagera korrekt på syntetiska kontroller — periodisk sinus ger $K \approx 0$, Lorenz-attraktor ger $K \approx 1$, vit brus ger... oklart men separerat från båda. Toker et al. publicerade kalibreringskurvor.

**Risk:** $K_c$-måttet är *känsligt för seriens längd och sampling rate*. NDT-fönsterstorleken (~2–10 s typiskt) kan vara på gränsen av detekterbarhet. Pre-implementations-validering på syntetiska 9D-bana från Lorenz vs vit brus krävs.

---

### 3.3 Lyapunov-spektrum av MNJ-flödet

**Kategori: 1 (etablerat externt) — Eckmann-Kamphorst-Ruelle 1986; Sano-Sawada 1985. Standard i nonlinear dynamics. NDT saknar det.**

Givet en sekvens av lokala Jacobianer $J_{t_1}, J_{t_2}, \ldots, J_{t_N}$ längs en empirisk bana, beräkna Lyapunov-exponenterna via QR-faktorisering:

$$
J_{t_k} Q_{k-1} = Q_k R_k
$$
$$
\lambda_i = \lim_{N \to \infty} \frac{1}{N \Delta t} \sum_{k=1}^{N} \log |R_{k,ii}|
$$

Detta ger 9 Lyapunov-exponenter $\lambda_1 \geq \lambda_2 \geq \ldots \geq \lambda_9$ per patient (eller per tidsbin).

Definiera:
- **`largest_lyapunov_median`**: $\lambda_1$.
- **`kaplan_yorke_dimension`**: $D_{KY} = k + \frac{\sum_{i=1}^{k} \lambda_i}{|\lambda_{k+1}|}$, där $k$ är största index med $\sum_{i=1}^{k} \lambda_i \geq 0$. Detta är en *frakt­dimension* av attractorn.
- **`metric_entropy_pesin`**: $h_{KS} = \sum_{i : \lambda_i > 0} \lambda_i$ (Pesin-identiteten).

**Klinisk hypotes:** CPC1 har $\lambda_1 > 0$ (kaos retained, attraktor med positiv Pesin-entropi), $D_{KY} > 1$ (inte en limit cycle). CPC5 har $\lambda_1 \leq 0$ (over-contraction = limit point) eller $\lambda_1 = 0$ med övriga negativa (limit cycle = fastlåst oscillation, exakt sub-kritisk-Hopf-signaturen).

**Implementations-väg:** `jacobian_9D/J_hat` finns redan i H5. QR-faktoriseringsalgoritmen är ~40 rader Python med NumPy. Beräkningen är linjär i antal fönster.

**Falsifierbarhet:** Stark — *Pesin-identiteten kan kontrolleras* mot oberoende skattning av Kolmogorov-Sinai-entropin från symboliska sekvens-metoder. Om de inte stämmer är någon av estimatorerna fel.

**Risk:** QR-baserad Lyapunov-skattning kräver att Jacobianerna är skattade *längs en faktisk bana* med konsistent grannskap. Den nuvarande MNJ-skattningen är *grannskaps-baserad* (kNN), inte trajektoria-baserad. En övergångsmetod krävs eller en explicit *trajectory-MNJ-rerun*.

---

### 3.4 Band-stratifierad MNJ

**Kategori: 3 (plausibel tolkning) — direkt operationaliserar Bartolini Sci Rep 2025-fynden.**

Bygg fyra parallella MNJ-strömmar genom att band-pass-filtrera EEG *innan* MNPS-extraktion:

- $\delta$-band (0.5–4 Hz): $J_t^{(\delta)}$
- $\theta$-band (4–8 Hz): $J_t^{(\theta)}$
- $\alpha$-band (8–13 Hz): $J_t^{(\alpha)}$
- $\beta/\gamma$-band (13–45 Hz): $J_t^{(\beta\gamma)}$

För varje band, beräkna alla redan-etablerade MNJ-summor (`spectral_radius_median`, `anisotropy_abs_eig_median`, `frobenius_norm_median`, `rotational_power_mean`, `mdr_median`).

Nya cross-band-metriker:

$$
\text{mnj\_cross\_band\_coupling} = \frac{1}{6} \sum_{(b_1, b_2)} \frac{\|J_t^{(b_1)} - J_t^{(b_2)}\|_F}{\|J_t^{(b_1)}\|_F + \|J_t^{(b_2)}\|_F}
$$

(genomsnittlig relativ Frobenius-skillnad över band-par; sex par av fyra band).

$$
\text{mnj\_alpha\_dominance} = \frac{\rho(J_t^{(\alpha)})}{\sum_b \rho(J_t^{(b)})}
$$

**Klinisk hypotes (direkt från Bartolini):** CPC1 har högre `mnj_alpha_dominance` (alpha-strukturen styr lokal Jacobian) och högre $\alpha$-temporal-coherence. CPC5 har högre `spectral_radius` i $\delta$- och $\theta$-banden, plus högre `mnj_cross_band_coupling` (oorganiserad korsbandstörning).

**Implementations-väg:** Kräver en *upstream rerun* av NeuralManifoldDynamics med band-pass-filter applicerat. Måttligt arbete — det är samma pipeline med en filter-flagga. Ingen ny matematik.

**Falsifierbarhet:** Klart — om alla band-stratifierade MNJ-metriker är högkorrelerade med samma broadband-metrik är band-stratifieringen redundant. Ortogonalitetstest mot broadband-MNJ obligatoriskt.

**Risk:** *Band-pass-filtrering ändrar tidsskalan*. Lokal Jacobian av en alpha-bandpassfiltrerad signal är en *annan dynamisk operator* än Jacobian av broadband-signalen — detta måste tolkas försiktigt. Det är inte "samma flöde sett genom ett alpha-fönster".

---

### 3.5 Burstiness av MNJ-spectral-radius-tidsserien

**Kategori: 3 (plausibel tolkning) — Goh-Barabási burstiness är klassiskt; direkt motiverat av Bartolini Sci Rep 2025.**

Goh-Barabási burstiness coefficient på interevent-tidsintervall är klassisk (Goh & Barabási EPL 2008). I Bartolini Sci Rep 2025 är burstiness av node-aktivering i temporala grafer en av de starkaste pDoC-markörerna. Tillämpa direkt på *tidsserien* av $\rho(J_t)$ inom 12-h-fönstret:

$$
B = \frac{\sigma_T - \mu_T}{\sigma_T + \mu_T}, \quad T = \{\tau_i : \rho(J_{t_i}) > q_{90}(\rho(J_\cdot))\}_{i}
$$

där $T$ är interevent-tider mellan "höga rotationskraft-spikar" definierade som överskrid av 90-percentilen. $B \in (-1, 1)$; $B > 0$ indikerar bursty (klusterade events), $B < 0$ regulär (jämnt utspridda events).

Sex nya metriker:
- **`mnj_rho_burstiness`** ($B$ av $\rho$-spikar)
- **`mnj_rotational_burstiness`** ($B$ av `rotational_power`-spikar)
- **`mnj_anisotropy_burstiness`** ($B$ av `anisotropy_abs_eig`-spikar)
- ... motsvarande för de andra primära MNJ-måtten.

**Klinisk hypotes:** Direkt från Bartolini — CPC5 har *högre burstiness* (intermittent rigid periods + relaxation = bursty regim). CPC1 mer kontinuerlig dynamik (lägre burstiness).

**Implementations-väg:** Trivial. `numpy.diff` på spike-tider följt av $B$-formeln. ~10 rader.

**Falsifierbarhet:** Negativ kontroll: tids-shuffle av $\rho(J_t)$-serien ska kollapsa $B \to 0$. Om gruppsignaturen *inte* ändras under tids-shuffle är effekten en magnitud-effekt och inte en temporal-burstiness-effekt.

**Risk:** Tröskelvalet ($q_{90}$ vs $q_{95}$ vs ett absolut värde) påverkar $B$ markant. Pre-registrera tröskeln eller rapportera $B$ över flera trösklar.

---

### 3.6 Topological Transfer Entropy mellan 9D-MNPS-koordinater

**Kategori: 1 (etablerat externt — TopoConscious-paketet) + 3 (plausibel tillämpning på NDT).**

Topological Transfer Entropy (TTE) mäter riktad informationsöverföring mellan två tidsserier $X, Y$ baserat på topologiska egenskaper:
$$
\text{TTE}(X \to Y) = H(Y_t | Y_{t-1}) - H(Y_t | Y_{t-1}, X_{t-1})
$$
i diskret approximation, beräknad på persistens-bar-codes från sliding-window persistent homology.

För NDT: beräkna alla 9×9 = 81 par-vis TTE-värden bland 9D-MNPS-koordinaterna. Detta ger en *directed adjacency matrix* per patient.

Definiera:
- **`mnps_tte_total_flow`**: $\sum_{i,j} \text{TTE}(x_i \to x_j)$ — total informationsöverföring.
- **`mnps_tte_asymmetry`**: $\frac{1}{n(n-1)} \sum_{i \neq j} |\text{TTE}(x_i \to x_j) - \text{TTE}(x_j \to x_i)|$ — hur asymmetriskt är informationsflödet?
- **`mnps_tte_hierarchical_depth`**: längsta riktade väg i den binariserade TTE-grafen — fångar hierarkisk djup i informationskedjan.

**Klinisk hypotes:** CPC1 har högre `mnps_tte_asymmetry` (clear directional flow = hierarkisk informationsbearbetning). CPC5 har symmetrisk eller låg TTE-struktur (allt-till-allt = synkron breakdown). `mnps_tte_hierarchical_depth` förväntas vara större i CPC1 (information traverserar fler 9D-noder innan den absorberas).

**Implementations-väg:** TopoConscious-koden är open-source på GitHub (Chege-N/TopoConscious). C++/OpenMP-implementation av TTE finns. Kan anropas på `coords_9d/values` per patient.

**Falsifierbarhet:** Negativ kontroll: koordinat-permutation ska förstöra `mnps_tte_asymmetry` men *inte* `mnps_tte_total_flow` (eftersom totalflöde är invariant under nodbyte). Inbyggd dissociation.

**Risk:** TTE-beräkningen är dyr ($O(n^2)$ per fönsterpar). 281 patienter × 12 h × 81 par är hanterligt men kräver C++-implementation. NDT-pipelinen är Python-centrerad; integrationen är icke-trivial.

---

### 3.7 Hopf-bifurcation distance via Stuart-Landau-fit på MNPS

**Kategori: 1 (etablerat externt — Stuart-Landau + Deco TVB-ramverket) + 3 (plausibel NDT-tillämpning).**

Den enklaste icke-linjära oscillator med Hopf-bifurkation är Stuart-Landau:
$$
\dot z = (a + i\omega) z - |z|^2 z, \quad z \in \mathbb{C}
$$
där $a$ är bifurkationsparametern: $a < 0$ är *subcritical* (stabil fix punkt), $a > 0$ är *supercritical* (stabil limit cycle med radie $\sqrt{a}$).

I Deco et al. (2017) Sci Rep används Stuart-Landau som standard whole-brain-byggsten. Varje hjärnregion får sin egen $(a_i, \omega_i)$.

Operationalisering för NDT: för varje patient och tidsbin, fitta Stuart-Landau-parametrar $(a, \omega)$ till MNPS-trajektoria projicerad på en dominant 2D-subrum (PCA av MNPS-windows). Två tolkningar:
1. **Window-wise fit**: $a$ och $\omega$ per fönster, sedan median per patient.
2. **Patient-wise fit**: en uppsättning $(a, \omega)$ per patient över hela 12-h-fönstret.

Definiera:
- **`stuart_landau_a_median`**: median av $a$ — fångar var systemet ligger relativt Hopf-bifurkationen.
- **`stuart_landau_omega_median`**: median av $\omega$ — eigenfrekvens (förväntas falla i $\alpha$-band för wakefulness, $\delta$ för djup koma).
- **`stuart_landau_a_dispersion`**: variation av $a$ över fönster — fångar hur stabilt systemet sitter på en sida av bifurkationen.

**Klinisk hypotes:** CPC1 ligger nära $a = 0$ (edge-of-Hopf, motsvarar wake-like fluktuationer mellan stabilitet och oscillation; matchar Toker 2022:s edge-of-chaos-hypotes). CPC5 ligger antingen $a \ll 0$ (kollapsad fix-punkt) eller $a \gg 0$ med liten amplitud (fastlåst limit cycle = sub-kritisk Hopf-signaturen igen).

**Implementations-väg:** Stuart-Landau-fit kan göras via maximum likelihood på diskretiserad SDE, eller approximation via lokal linearisering. ~120 rader Python. Indata: `mnps_3d` eller `coords_9d/values` projicerad på 2D.

**Falsifierbarhet:** Stuart-Landau är *minimalistiskt*. Om den inte fittar 9D-MNPS-dynamik tillräckligt bra (residual variance > 50%) är hela ramen inadekvat. Förkasta om så.

**Risk:** Stuart-Landau har bara 2D dynamik. Att projicera 9D MNPS på 2D är en informationsförlust. Alternativet är generaliserad Stuart-Landau med flera kopplade oscillatorer — mer trogen 9D men kräver mer numerisk maskinen.

---

## 4. Förkastade alternativ

Två förslag som dykt upp i litteraturen men som efter eftertanke är *icke* lämpliga för NDT-pipelinen:

- **Hyperbolic embedding av EEG (ManifoldFormer 2025).** ManifoldFormer använder hyperbolic projections för cross-subject alignment i deep learning. För NDT, där MNPS-axlarna är specifikt designade för att vara *Euklidiska* och *interpretabla* (compendium @eq:base-chart), skulle hyperbolic embedding bryta mot ett designval. Det är intressant för deep-learning-konkurrenter men inte för NDT.
- **Quantum information geometry of consciousness (preprints.org 2025).** Använder kvant-Fisher-metric på Hilbertrumvektorer för att modellera medvetande-övergångar. Detta är *djupt spekulativt* — det kräver att postulera kvant-tillstånd som motsvarande medvetande, vilket är en filosofisk position snarare än en empirisk modell. Kategori 5.

---

## 5. Förslag på sammansatt "edge-of-chaos triad"

De tre kandidaterna 3.2, 3.3 och 3.7 mäter *samma underliggande hypotes* (edge-of-chaos / Hopf-bifurkations-avstånd) på tre olika sätt:

1. **3.2 ($K_c$ från 0-1 chaos test)** — *modellfri* skalär markör direkt från tidsserien.
2. **3.3 ($\lambda_1$, $D_{KY}$, $h_{KS}$)** — *dynamics-from-Jacobian* spektral skattning.
3. **3.7 ($a$, $\omega$ från Stuart-Landau)** — *parametrisk modell* med eksplicit bifurkations-koordinat.

En *triangulering* mellan dessa tre är epistemiskt värdefull: om alla tre pekar på samma kliniska riktning (CPC5 är längre från edge-of-chaos i alla tre skalor), är slutsatsen robust mot enskild-metod-artefakter. Om de divergerar, har vi diagnosticerat *vilken* aspekt av edge-of-chaos-hypotesen som är gilig i NDT-data.

Sammansatt prognos-feature:
$$
\text{eoc\_triad\_score} = w_1 \cdot z(K_c) + w_2 \cdot z(\lambda_1) + w_3 \cdot z(a)
$$
med vikter $w_i$ kalibrerade på en oberoende validering-split. Eller, mer epistemiskt rent, behandla dem som *tre separata features* och låta en linjär modell väga dem.

---

## 6. Hur NDT positionerar sig mot UM-EEG och Stuart-Landau-baserade whole-brain-modeller

Litteratursökningen avslöjar att NDT 2026 inte längre är ensam i sin geometriska ansats. Tre konkurrenter:

1. **UM-EEG (Tjepkema-Cloostermans, Annals Neurol 2025)** — deep-NN-embedding, 128D, AUROC 0.86 på cardiac arrest, *ointerpreterbart*. Fördelarna mot UM-EEG är (a) explicit interpretabla MNPS-axlar, (b) operativ kontroll över vad som mätas, (c) inget krav på 20 000+ patient-träningsset. Nackdelarna är (a) lägre prognostisk prestanda för närvarande, (b) ingen prospektiv validering. Strategi: kandidat 3.1 (distance-to-healthy-manifold) gör NDT *direkt jämförbar* med UM-EEG:s ledande signal.

2. **The Virtual Brain (TVB) Stuart-Landau-modeller (Deco-gruppen, m.fl.)** — *generativa* whole-brain-modeller där varje region är en Stuart-Landau-oscillator, parametrar fittas till empiriska connectomes. NDT är *deskriptiv* (mäter geometri från data) medan TVB är *generativ* (simulerar). Strategi: kandidat 3.7 (Stuart-Landau-fit på MNPS) brygger de två genom att tolka NDT-koordinater i TVB-vokabulär.

3. **TopoConscious (open-source persistent homology)** — fokuserad på fMRI snarare än EEG. Strategi: kandidat 3.6 (TTE på 9D-MNPS) utnyttjar TopoConscious-implementationen men tillämpar den på *interpretabla* MNPS-axlar, vilket är en NDT-specifik förbättring.

NDT:s särart 2026 är *kombinationen* av (a) explicit interpretabla axlar (compendium @eq:ma–@eq:em), (b) lokal Jacobian-mätning som diff-geometrisk operator (compendium @eq:mnj-def), och (c) reachability-koner som kapacitets-geometri (compendium @eq:reachability-recursion). Konkurrenterna har antingen punkt (a) ELLER (b) ELLER (c), inte alla tre.

---

## 7. Prioritering och konkret nästa steg

Rangordnad efter *odds av ny information med stark publiserad referensbas per implementations-kostnad*:

1. **3.3 Lyapunov-spektrum av MNJ-flödet.** Etablerat verktyg. NDT saknar det. ~1 dag pilot. Direkt validerbart via Pesin-identiteten.
2. **3.2 0-1 chaos test på MNPS-trajektoria.** Direkt validerat i Toker PNAS 2022 + Maschke Commun Biol 2024. ~1 dag pilot. Den högsta klinisk-empiriska litteratur-basen av alla kandidater.
3. **3.1 Distance-to-healthy-MNPS-manifold.** Direkt parallell till UM-EEG:s ledande signal. ~2 dagar (inklusive byggande av healthy reference). Stark interpretabilitets-fördel.
4. **3.5 Burstiness av MNJ.** Trivial implementation. Direkt motiverat av Bartolini Sci Rep 2025. ~ 0.5 dag.
5. **3.4 Band-stratifierad MNJ.** Kräver upstream rerun av NeuralManifoldDynamics. ~1 vecka inklusive H5-pipeline-flagga.
6. **3.7 Stuart-Landau-fit.** Konceptuellt viktigt (Deco-bron) men teknikt tyngre. ~3 dagar.
7. **3.6 TTE mellan 9D-koordinater.** Mest beräknings-tunga, kräver C++-integration. ~1 vecka.

**Konkret rekommendation:** Börja med en "edge-of-chaos pilot v1" som implementerar 3.2 (0-1 test) + 3.3 (Lyapunov) parallellt och rapporterar Cohen's $d$ + residualtest mot befintliga MNJ-summor på samma 281-patient-pooling som rond-1 använde. Detta är 2 dagars arbete och svarar på den tyngsta hypotesen ("är CPC5 längre från edge-of-chaos?") med två oberoende metoder. Om båda separerar grupper är resultatet starkt; om en separerar och den andra inte, har vi diagnosticerat metodartefakt; om ingen separerar har vi *falsifierat* edge-of-chaos-hypotesen i NDT-data, vilket är ett genuint resultat värt en metodologisk note.

Pilot v2, om edge-of-chaos-piloten fungerar: lägg till 3.1 (distance-to-healthy) och 3.5 (burstiness) som adderande features i en incremental-validity-test mot befintliga reachability + 9D-Jacobian-ladders.

---

## 8. Slutord — vad detta säger om NDT 2026

Sammanfattningsvis: koma-EEG-litteraturen 2024–2026 har lett *bort* från godtyckliga ML-features och *mot* fysikaliskt-motiverade lokala-dynamiska markörer (edge-of-chaos, Hopf-bifurkation, Lyapunov-spektrum, persistent homology). NDT-ramverket är väl-positionerat i denna kontext eftersom MNPS+MNJ är *just* sådana lokala-dynamiska objekt — men det är inte fullt utnyttjat. De sju kandidaterna i denna rond är inte exotiska tillägg; de är *standardverktyg från medvetandelitteraturen* som NDT-pipelinen ännu inte har implementerat.

Om alla sju implementeras och *ingen* slår nuvarande reachability+MNJ-baseline har NDT-mätstacken nått en effektivitetsgräns och nästa stora steg kommer från en annan modalitet (multimodal MEG/fMRI/intracellular) eller från en annan analys-skala (regional snarare än global). Om åtminstone två slår baseline har vi bekräftat att NDT 2026 fortfarande har outnyttjad geometrisk hävstång och kan motiverat skriva en uppföljnings-artikel.

Inget av detta är prospektivt validerat. Pilot-resultaten skulle utgöra *internal synthesis* tills oberoende validering. Den epistemiska disciplinen från rond 1 förblir intakt: falsifiering är lika informativ som bekräftelse, och kategoristämplarna måste vara explicita i alla rapporter.
