Jag har läst igenom diary-anteckningen, pilot-koden, effect-tabellen, den (tomma) Laguerre-typ-filen samt 9D-Jacobian-systerartikeln. Här är min utförliga forskningsledar-läsning av vad piloten faktiskt visade, vad som är trasigt, och vilka tweakar/alternativa mått som är värda en v2-pilot.

## 1. Vad piloten faktiskt sa (innan vi tweaker något)

Effekt-tabellen (12 vs 12, part2, 0–12h) är ärlig men begränsad:

- Reachability-baseline dominerar: `tube_d_eff_median` d=+1.27, AUROC 0.833; `tube_a_operator_norm_median` d=−1.02, AUROC 0.778.
- Bästa Laguerre-medlemmen är `laguerre_norm_p95` d=−0.78, AUROC 0.778, dvs. **CPC5 har större "kurvaturförändring"**.
- `laguerre_norm_median` d=−0.72, AUROC 0.715, samma riktning.
- `laguerre_bending_norm_median` d=−0.58, modest.
- `laguerre_anisotropy` saturerar vid 1.000 i båda grupperna → metriken är **bruten by construction**, inte ett "fynd".
- `laguerre_persistence` och `laguerre_hourly_slope` är effektivt brus (|d|≤0.24).

Två tolkningsproblem som inte får glömmas bort:

1. Signalriktningen är **samma riktning som svårighetsgrad**: CPC5 har mindre reachable space och mer kurvaturförändring. Vi vet inte än om det är ett nytt geometrilager eller ett brusigare proxy för samma `tube_d_eff`/`tube_a_operator_norm`-signal. Den residual-mot-reachability-test som H3 i typ-filen kräver gjordes **inte** i piloten.
2. Patchen byggs på spatially-sampled point clouds över 12h (`max_points_per_run=60`, `neighborhood_size=25`). När CPC5-molnet är smalare blir kvadratiska anpassningen sämre konditionerad, vilket i sig kan generera mer "förändring".

Sammanfattat: piloten är konsistent med antingen H2b ("pathological folding" i CPC5) eller "estimator-noise tracking severity". Den nuvarande designen kan inte separera dessa.

## 2. Vad jag tycker är trasigt eller suboptimalt i nuvarande implementation

Tittar man i `laguerre_subject_pilot.py`:

- **A. Anisotropi-formeln saturerar.** `|λ2 − λ1| / (|λ2| + |λ1| + ε)` blir alltid ≈1 när en eigenvärde dominerar — vilket händer nästan jämt med en 6-parameters kvadrat på 25 brusiga grannar. Behöver bytas ut.
- **B. "Laguerre change norm" är inte `|∇II|`.** Det är euklidiskt avstånd mellan robust-skalade 4-vektorer av `(bending_norm, mean_curv, gauss_curv, anisotropy)` till **temporala** grannar. Det blandar dessutom redundanta storheter: mean = λ1+λ2, gauss = λ1·λ2, så 4-vektorn ligger på en 2-dim mångfald. Det är därför `norm_p95` och `bending_norm_median` rör sig korrelerat.
- **C. Surface-validity gate saknas.** `singular_values` sparas men används inte. Patch där `s3/s2 ≈ 1` är inte en 2D-yta utan ett blob, och `|II|` där är meningslös.
- **D. 6-parameters fit på 25 grannar.** Linjär-termerna `(u,v)` plockar upp tilt, inte bending; konstanten plockar upp brusgolvet. För 24 frihetsgrader efter centrering ger 6 koefficienter overfit.
- **E. Surface A användes, Surface B (reachability-tube-yta) inte alls.** Det är ironiskt eftersom reachability är där huvudsignalen ligger. Hela motivationen i typ-filen pekar på Surface B som det geometriskt mer principfast objektet.
- **F. Ingen residual-mot-reachability-analys.** H3 från typ-filen är hela poängen med att skriva en uppföljningsartikel.

## 3. Tre familjer av tweaks och alternativa mått

Sorterat efter implementations-kostnad och förväntat informationsvärde.

### Tier 1 — Fixa det som redan finns (cheap, hög odds att förbättra)

- **T1. Shape index + curvedness istället för anisotropy.**
  Klassisk differentialgeometri ger två icke-mättade, ortogonala kurvatursummeringar:

  ```python
  shape_index = (2.0 / np.pi) * np.arctan2(lam_max + lam_min, lam_max - lam_min)   # in [-1, 1]
  curvedness  = np.sqrt(0.5 * (lam_max**2 + lam_min**2))                            # >= 0
  ```

  Shape index dekomponerar cup/rut/saddel/dome **utan att blandas med skala**. Curvedness är skalan. Detta löser saturationen direkt.

- **T2. Riktig `|∇II|`-proxy.**
  Representera II som 2×2-matris `[[2a, b], [b, 2c]]` i lokal tangentbas och beräkna

  ```python
  grad_II = np.linalg.norm(II_i - II_j, ord='fro') / (np.linalg.norm(p_i - p_j) + EPS)
  ```

  över **state-space-grannar** (inte temporala grannar). Detta är mycket närmare det som typ-filen kallar `L_χ(p) = |∇II(p)|` och separerar konceptuellt från trajektoriekurvatur.

- **T3. 3-parameter Hessian-fit istället för 6-parameter.**
  Subtrahera median-tilt-plan från `w` och lös

  ```python
  w = a*u**2 + b*u*v + c*v**2
  ```

  Med 25 grannar och 3 koefficienter får Hessianen mycket lägre varians.

- **T4. Singular-value-gate.**
  Acceptera patch endast om `s3 / s2 < tau` (t.ex. 0.5). Rapportera `valid_fraction` per subject och stratifiera effekt-storlekarna efter den.

- **T5. Reachability-residual-version av varje Laguerre-metrik.**
  Per subject: regrera `laguerre_*` linjärt på `tube_d_eff_median` och `tube_a_operator_norm_median` på subject-nivå **inom hela part2**, ta residualen, och rapportera Cohen's d och AUROC på residualen. Detta är H3-testet och avgör om Laguerre tillför något bortom severity-proxyn.

### Tier 2 — Nya men små family-members (få rader kod, riktigt annorlunda mått)

- **T6. Cup–saddel-fraktion.**
  Andel patchar med `sign(λ_max) == sign(λ_min)` (elliptisk) vs olika tecken (saddel). H2b förutsäger att CPC5 har högre saddel-fraktion ("pathological folding").

- **T7. Bending-direction-coherence.**
  För varje patch, lyfta dominanta krökningsriktningen (eigenvektorn av Hessianen) tillbaka till MNPS via tangent-basen. Räkna von Mises–Fisher-koncentrationen κ över alla patchar i subjektets 12h. H1 ("adaptive unfolding") förutsäger högre κ i CPC1: krökningen pekar konsekvent, ytan unfoldar koherent.

- **T8. Mann–Kendall τ istället för linear slope.**
  `laguerre_hourly_slope` är meningslös med 6–10 timmars-bins och tung högertail-brus. Mann–Kendall τ på den medianbinnade hourly bending-norm är robustare.

- **T9. Curvature-spectrum-entropi.**
  Shannon-entropin av histogrammet över `shape_index` per subject. Mäter om kurvatur-fördelningen är peakad (homogent format) eller spridd (heterogen ytstruktur).

### Tier 3 — Ny yta (mer plumbing, principfast bästa motivering)

- **T10. Reachability-tube-yta (Surface B).**
  Använd inte MNPS-3D-point-cloud direkt. Använd istället ankarpunkternas **reachability-kovariansmatriser** (eller deras 2 dominerande egenvärden/-vektorer) som lokal 2-form på MNPS, och fit en yta över hur den 2-formen varierar mellan grannar i MNPS. Detta ger ett `|∇II|`-objekt som är konceptuellt det reachability-ytans andra fundamentalform.

- **T11. Reachability deformation distance.**
  Per par av närliggande ankare `(p, q)` i MNPS: log-euclidean eller affine-invariant Riemann-avstånd mellan deras reachability-ellipsoider `Σ_p` och `Σ_q`, normerat med `||p − q||`. Median + p95 över subjektet. Detta är det mest principfasta nya måttet — det är en konkret skattning av hur snabbt det lokala reachable shape **förändras** över state space.

- **T12. Klassisk trajektoriekurvatur som negativ kontroll.**
  1D-trajektoria genom MNPS, Frenet-curvature κ(t) per ankare. Om Laguerre-effekten kollapsar till klassisk trajektorie-κ är det inget tredje-ordningens ytmått som drivit signalen. Detta är T12 = section 4.8 "Classical curvature control" i typ-filen som inte heller gjordes i piloten.

## 4. Konkret rekommendation: v2-pilot

Behåll exakt samma 12+12 subjects (`pilot_selected_subjects.csv`) för äpplen-mot-äpplen-jämförelse mot v1.

Implementera i en ny `laguerre_subject_pilot_v2.py` (eller en `--variant v2`-flagga i den befintliga):

1. **Estimator-fix**: T1, T3, T4. Lägg till `surface_fit_r2_min` och `s3_over_s2_max` som validity-grindar.
2. **Reformulera change-mått**: T2 som primary `laguerre_grad_II_norm_median/p95`; behåll det gamla "change_norm" som legacy comparator.
3. **Nya family-medlemmar**: T6 (saddle-fraction), T7 (bending-direction-coherence), T9 (curvature-entropi).
4. **Robusta tids-mått**: T8 (Mann-Kendall τ) istället för linjär slope.
5. **Severity-residual**: T5 — varje metrik rapporteras både rå och som residual mot `tube_d_eff_median` + `tube_a_operator_norm_median`.
6. **Negativ kontroll**: T12 (klassisk trajektoriekurvatur som comparator).

Det här skickar med ~7 nya kolumner i `laguerre_subject_metrics.csv` och en utökad `laguerre_effect_sizes.csv`. Hela paketet är ungefär en dags arbete och risken är liten — om alla nya metriker dör ger det också ett tydligt budskap (Laguerre-spåret är inte bärande som självständigt lager).

Surface B-arbetet (T10/T11) håller jag tillbaka till v3. Det kräver att man extraherar per-window reachability-kovarians (eller motsvarande spectral summary) ur H5/Jacobian-bundles, och det är en separat liten plumbing-uppgift som inte ska blandas in i estimator-fixarna.

## 5. Vad jag förväntar mig av v2

Tre realistiska utfall, alla informativa:

- **Utfall A** ("Laguerre överlever residual-testet"): `laguerre_grad_II_norm_p95` eller saddle-fraction har Cohen's d > 0.5 **efter** residualisering mot reachability. Då är artikel-spåret motiverat.
- **Utfall B** ("Laguerre kollapsar till severity"): residualerna har d ≈ 0. Då blir den ärliga slutsatsen att kurvatur-förändring inte adderar bortom reachability-måttet i denna 12+12, och artikeln pivoteras till en methodological note + negativt resultat.
- **Utfall C** ("Bending-direction-coherence är ett separat mått"): T7 hittar en effekt i ortogonal riktning mot `tube_d_eff`. Det är det mest intressanta utfallet eftersom det skulle stödja H1 (adaptive unfolding) snarare än H2b.

## 6. Varningsord

- Detta förblir n=24. Inget av detta är confirmatory. Pilotresultatet kommer säga "går det att frysa familjen och köra full part2 (140 subjects)", inte "är hypotesen sann".
- Anisotropy-saturationen i v1 är ett tecken att man måste vara försiktig med att läsa in betydelse i metriker som inte är validerade. Innan v2 körs behöver alla nya metriker sanity-testas på simulerade ytor (en sfärisk patch, en saddel-patch, en cylinder, ett brus-blob) så att man vet vilka värden de tar på kända geometrier.
- Severity-residualiseringen kräver eftertanke om confounding: `tube_d_eff_median` är själv en geometrisk skattning från samma H5-koordinater, så att "residualisera bort" det och fortfarande hitta signal är ett strängt test — och man måste vara beredd på att det neutraliserar Laguerre.

---

Säg till om du vill att jag faktiskt implementerar v2 nu (jag föreslår då att jag skriver `laguerre_subject_pilot_v2.py` som lägger sina resultat under `results/laguerre_pilot_20260526_part2_v2/` och kör mot exakt samma 24 subjects). Alternativt kan jag börja med bara estimator-fixarna (T1+T3+T4) som en mindre incremental commit för att se hur mycket bara byggnadsfelen står för. Vilken nivå vill du gå med?