Bra batch — och faktiskt mer informativ än "Cohen's d 0.36 låter modest" ger sken av. Jag har läst både v2-koden, effect-tabellen och idé-noterna. Här är min läsning, både teknisk och som artikel-strategi.

## 1. Den största meta-iakttagelsen (måste in i ledger)

Reachability-baselinen kraschar från v1 till v2:

- v1 (12+12 cherry-picked): `tube_d_eff_median` d=+1.27, AUROC 0.833
- v2 (67+70 full part2): `tube_d_eff_median` d=+0.70, AUROC 0.687

Det är inte en kohort-effekt — det är **selection bias** i v1. `select_subjects` sorterade på `n_runs_with_coords` och `coverage_hours`, och det visar sig dessa är **korrelerade med separation** (tydligast EEG = oftast tydligast prognos). Lärdomen: **inga v1-storlek-pilot-tal får tas till en artikel utan att paret det är cherry-picked är öppet noterat.** Detta sänker dessutom retroaktivt min ursprungliga "Utfall A-tröskel d>0.5 efter residual" — den var kalibrerad mot en inflaterad baseline.

## 2. Vad v2 faktiskt säger (icke-trivial reframing)

Det som överlevde reachability-residualiseringen är **inte** det jag rekommenderade som primärt:

| Metrik (residualiserad) | d | AUROC | Konceptuell familj |
|---|---:|---:|---|
| `legacy_change_norm_median` | −0.36 | 0.640 | temporal change in (curvedness, shape_index, λ_min, λ_max) |
| `shape_entropy` | −0.34 | 0.657 | distribution-of-shape |
| `saddle_fraction` | −0.32 | 0.651 | distribution-of-shape |
| `grad_ii_norm_median` (T2, min favorit) | −0.21 | 0.552 | gradient-of-II |
| `direction_coherence` (T7) | −0.09 | 0.512 | direction-of-bending |
| `shape_index_median` | +0.20 | 0.551 | central-tendency-of-shape |

Det är **inte ett `|∇II|`-fynd**. Det är ett **distribution-of-curvature-shape-fynd**. De tre överlevande metrikerna mäter alla någon variant av "hur ser blandningen av krökningstyper ut över subjektets 12h", inte "hur snabbt förändras II mellan grannar".

Det är en betydande omkalibrering av tolkningen. Den ursprungliga Laguerre-typen i `Curvature-Change Geometry...typ` förutsätter att signal kommer från `|\nabla II|`. Vad v2-evidensen säger är: **signalkällan ligger i krökningsfördelningens form, inte i krökningens gradient**. Det är konceptuellt närmare H2b ("pathological folding") än H1 ("adaptive unfolding"). Direction coherence (T7) som var min hypotes för H1 dog helt efter residual.

## 3. Tekniska saker som måste valideras innan en ny runda

Innan jag rekommenderar nästa steg, fyra saker jag såg i `laguerre_subject_pilot_v2.py` som kräver kontroll:

**a) `compute_state_space_gradients` är *spektral*, inte matris-Frobenius.** Den använder `eig_pair = (lam_min, lam_max)` och beräknar `||eig_pair_i − eig_pair_j|| / dist`. Det missar rotationen av huvudriktningarna. Min T2-rekommendation var `||II_i − II_j||_F`, vilket också fångar att principal-riktningen vrider sig. Detta kan vara en av anledningarna till att grad-II underpresterade — den är "döv" för riktningsförändringar. Borde rättas innan man dödar grad-II som koncept.

**b) Saddle fraction är ~0.93 i båda grupperna.** Det är extremt högt. Antingen är ytan i MNPS-3D-punktmolnet faktiskt nästan alltid en sadel (intressant!), eller så är 2×2-Hessianen så bruskontaminerad att eigenvärden i princip har slumpvis tecken (mindre intressant). Detta måste testas på syntetisk sfär (förvänta dig saddle_fraction ≈ 0), saddel (≈ 1), och brus-blob (≈ 0.5). Om brus-blob ger 0.93 så är `saddle_fraction` en estimator-artefakt, inte en geometrisk observation.

**c) `compute_legacy_change` använder 4-vektor `(curvedness, shape_index, λ_min, λ_max)` som har strukturellt beroende.** `curvedness = sqrt(0.5(λ_min² + λ_max²))` så vektorn är 3-dimensionell på en 2D-mångfald. Att den ändå *vinner* residualtestet är ett robust fynd — men det betyder att den **fångar något om temporal autokorrelation** snarare än om geometrin per se. Skulle vara värt att testa med bara `(shape_index, curvedness)` (2D, ortogonala-by-design) för att se om signalen sitter i geometrin eller i den temporala dimensionen.

**d) `add_scale_invariant_metrics` multiplicerar, vilket är OK dimensionsanalysmässigt** (1/length × length = dimensionslös), men resultatet är **konstruktionsmässigt korrelerat med reachability**. Det är därför `curvedness_scaled_median` ligger i topp raw (d=+0.46) men kollapsar residualiserat (d=−0.13). Den ska aldrig framställas som ett "independent Laguerre-mått"; den är en interaktionsterm med reachability och behöver märkas som sådan.

## 4. Tre vägar framåt

Jag tycker man borde explicit välja, inte hala fram.

**Väg A — Pivotera artikeln till distribution-of-shape, skippa Surface B**
- Reframea hela typ-filen runt `shape_entropy`, `saddle_fraction`, `shape_index`-distribution istället för `|\nabla II|`.
- Lägg in syntetiska kontroller (sfär/sadel/cylinder/brus) som obligatorisk metod-figur.
- Slutsats: "Laguerre-uppföljaren tillför d≈0.35 efter reachability-residual via distribution-of-curvature-shape; svagt självständigt men additivt."
- Artikellängd: ~12 sidor, ärlig, bounded, närmast en "method note + modest empirical claim".
- Tidsåtgång: ~3-4 dagar.

**Väg B — Bygg Surface B (reachability-deformation distance), välj sedan**
- Det vi gjort hittills är Surface A. Den principfasta hypotesen i typ-filen är Surface B: per-window reachability-kovariansmatris som lokal 2-form, log-euclidean Riemann-avstånd mellan grannar i MNPS.
- Detta kräver plumbing: extrahera `tube_a_operator` eller motsvarande per-window-objekt ur H5/Jacobian-bundles, inte bara `*_median`-sammanfattningar.
- Hypotes: Surface B ger en `|\nabla \Sigma|`-storhet som inte korrelerar med `tube_d_eff_median` per konstruktion (eftersom det är *deformation* av reachability, inte *storlek* av reachability), så det är ett *äkta* additivt mått.
- Tidsåtgång: ~1 vecka för v1 pilot på samma 137 subjects.
- Risk: kan också kollapsa, vilket är OK — då är Laguerre-spåret helt klart, och nästa preprint blir negativ result note.

**Väg C — Negativt-resultat-paper, stäng spåret**
- "We tested a Laguerre-form-inspired curvature layer; after severity correction it contributes only d ≈ 0.35 / AUROC ≈ 0.65, insufficient as a standalone family. The methodological lesson is..."
- Tidsåtgång: ~2-3 dagar.
- Värde: rensar luften, skyddar konsistensen i NDT-mätprogrammet, gör att efterföljande paper (regional, Jacobian-9D) inte måste konkurrera med en ouppklarad Laguerre-tråd.

## 5. Min rekommendation

**Väg B först, sedan beslut om A eller C.** Skälen:

1. Surface A är ärligt talat **uttömd** med v2. Att lägga till fler distribution-metriker på samma punktmoln kommer förmodligen ge marginella effekter eftersom källan är samma 3D MNPS-koordinater och kvadratisk patchpassning.
2. Surface B är **den enda hypotes som strukturellt inte kan kollapsa till "samma severity-proxy"**, eftersom det opererar på reachability-objektets *deformation* (en SPD-matris-skillnad), inte på MNPS-koordinatpunkter.
3. Surface B är dessutom det enda mått som **gör Laguerre-typ-filens premiss riktig**: "the empirical surface in this study is the reachability surface, not the MNPS point cloud". Surface A var alltid en bekvämlighet, Surface B är den principfasta varianten.
4. Om Surface B levererar d > 0.5 residualiserat har man en artikel. Om den inte gör det är det enkelt att skriva Väg C på 2 dagar, och då med konkret bevis att *både* Surface A och Surface B är otillräckliga — en mycket starkare negativ slutsats än bara Surface A.

Konkret för Surface B-piloten:
- Extrahera per-window reachability-kovarians `Σ_t` ur befintliga H5-bundles. Behöver räkna ut vilket dataset-namn i H5:n som har full kovarians (inte bara median-summaries). Snabbt att kolla.
- Log-euclidean-avstånd `d_LE(Σ_p, Σ_q) = ||log Σ_p − log Σ_q||_F`.
- För varje subject: median + p95 av `d_LE(Σ_i, Σ_j) / ||x_i − x_j||` över MNPS-grannpar.
- Direkt motsvarighet till `grad_ii_norm` men på reachability-ellipsoiderna, inte på MNPS-punktmolnet.

Parallellt: **kör syntetiska kontrollerna nu**, oavsett vilken väg som väljs. De tar 1-2h, och är ett krav för att överhuvudtaget kunna publicera saddle_fraction / shape_entropy som metrik. Jag kan skriva en `laguerre_synthetic_controls.py` som genererar sfär/sadel/cylinder/brus-punktmoln, kör samma estimator på dem och rapporterar `(saddle_fraction, shape_index_median, curvedness_median, grad_ii_norm_median)` med förväntade värden. Det är ~50 rader kod, tar 30 min.

## 6. Mindre saker jag tycker borde in i diaryn

- Selection-bias-fyndet (v1 → v2 baseline-fall från 0.833 till 0.687).
- Att `grad_ii_norm` implementerades spektralt, inte matris-Frobenius. Detta är en avvikelse från T2 som påverkar tolkningen.
- Att `saddle_fraction` = 0.93 i båda grupperna är en flagga som väntar på syntetisk validering.
- Att `*_scaled` metriker är reachability-korrelerade by construction och inte ska säljas som independenta.

---

Vill du att jag (a) skriver synthetic-controls-skriptet direkt nu, (b) börjar plumba Surface B (extrahera per-window reachability-kovarians ur H5), eller (c) ingenting just nu och jag väntar tills du valt väg A/B/C?