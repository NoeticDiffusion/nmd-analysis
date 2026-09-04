[12 tools called]

## Peer review (NoeticDiffusionTheory.typ)

### 1. Overall verdict: **Major revisions**
Manuskriptet har en stark kärnmodell (MNDM + RVC + MNPS/Atlas) men blandar den med flera hög‑risk‑påståenden och mekanistiska detaljer som inte är empiriskt bundna eller tydligt avgränsade. För ett topp‑tidskrift‑läge krävs striktare separation mellan kärnmodellens testbara prediktioner och spekulativa/brostycken (EAP, TRN‑biologi, NDHI som “health index”). Flera kvantitativa trösklar presenteras utan dataset‑specifik motivering eller tydlig falsifieringsplan.

---

### 2. Top issues (blockers)

1) **NDHI introduceras som central “health index” utan operationalisering eller valideringsplan**  
- **Location**: Abstract + NDHI‑sektionen  
- **Quote**  
```22:52:articles/NDT/NoeticDiffusionTheory.typ
We introduce the Noetic Atlas ... and a composite Noetic Diffusion Health Index (NDHI)
that integrates manifold topology, recurrence structure, curvature smoothness,
dimensionality, and metastability.
```
```1637:1667:articles/NDT/NoeticDiffusionTheory.typ
NDHI aggregates manifold dimensionality, curvature smoothness,
hub‑centrality/connector reliability, recurrence structure, and metastability
into a single score ...
```
- **Problem**: NDHI är en central headline‑idé men saknar explicit formel, viktning, reliabilitetsanalys och valideringskrav. Det gör den otestbar på “Nature/Cell‑nivå”.  
- **Why it matters**: Övergripande index kräver rigorös operationalisering och falsifierbarhet. Annars riskerar NDHI att vara en retorisk förstärkare utan empirisk bindning.  
- **Proposed fix**: Antingen (A) stryk NDHI helt ur kärntexten och flytta till appendix/roadmap, eller (B) ge **formel + komponentlista + estimationspipeline + prereg‑kriterier** för när NDHI får kallas “valid”. Särskilj “visualization composite” från kliniskt/biomarkör‑språk.

2) **TRN‑>variance‑mapping med numeriska parametrar presenteras som om det vore empiriskt etablerat**  
- **Location**: RVC/TRN‑gating  
- **Quote**  
```981:1011:articles/NDT/NoeticDiffusionTheory.typ
sigma(t) = sigma_min + (sigma_0 - sigma_min) exp(- kappa g_TRN(t)),
kappa approx 5–10 nS^(-1)
```
- **Problem**: Du anger ett specifikt biophysik‑intervall för `kappa` utan primärdata eller exakta referenser. Detta läser som “hård sanning” men är i bästa fall en ansatz.  
- **Why it matters**: Detta skapar falsk precision och riskerar att hela modellen uppfattas som biologiskt överbestämd.  
- **Proposed fix**: Märk som **[Speculative]**, flytta till appendix, eller ersätt med icke‑numerisk mapping och tydlig notis om att `kappa` är **free parameter** som endast används i simuleringar.

3) **Kvantitativa prediktioner och effektstorlekar saknar dataset‑specifik motivering**  
- **Location**: Prediktioner  
- **Quote**  
```1688:1717:articles/NDT/NoeticDiffusionTheory.typ
Effect size priors ... d >= 0.6 ... Delta E approx 15–30% ... r ~ 0.3–0.5
```
- **Problem**: Dessa trösklar presenteras som “konservativa targets” men utan explicit koppling till dataset, sample size, pipeline eller prereg‑power.  
- **Why it matters**: Utan definierad mätkedja är “falsifikation” vag och kan efterhandsjusteras.  
- **Proposed fix**: Koppla varje tröskel till **specifik dataset‑konfiguration** (t.ex. Sleep‑EDF med specificerat fönster, spindeldetektion, predicerad varians). Alternativt ta bort numeriska trösklar ur huvudtexten och lägg i prereg‑bilaga.

4) **Fenomenologisk “pulsed experience” + EAP blandas in i huvudnarrativet utan tydlig empirisk modulär status**  
- **Location**: Introduction + EAP‑delen  
- **Quote**  
```130:144:articles/NDT/NoeticDiffusionTheory.typ
We propose conscious episodes may exhibit a discretely pulsed quality ...
```
- **Problem**: Denna block tar stor plats och driver läsarens fokus bort från kärnmodellens mätbarhet. Den är inte testad och kräver hög‑upplöst neurofenomenologi som du själv säger inte finns.  
- **Why it matters**: Försvagar falsifierbarhet och sänker “Churchland‑rigor”.  
- **Proposed fix**: Gör EAP/phenomenology strikt **Tier‑2** och flytta den
  detaljerade behandlingen (inkl. interoceptiv pipeline) till Appendix. I
  huvudtexten räcker 1–2 meningar om att det är en framtida modul.

---

### 3. Medium issues

1) **Invarians‑argumentet översträcker vad som faktiskt är invariant**  
- **Location**: “Assumptions and invariances” + MNPS invariance claims  
- **Problem**: Du säger att topologiska egenskaper är invarianta under smooth transforms, men flera rapporterade mått (volym, hub‑betweenness, RQA) är chart‑beroende.  
- **Why**: Risk för post‑hoc flexibilitet.  
- **Fix**: Dela upp: (i) strikt invarianta egenskaper (t.ex. topologisk ekvivalens), (ii) robusta men chart‑beroende metrik med tydliga multiverse‑krav.

2) **RTB / flera namnlagers (RTB/NDT/MNDM/MNPS/NDHI) skapar kognitiv friktion**  
- **Location**: Introduction  
- **Problem**: Flera nomenklaturskikt är onödigt i en teknisk artikel.  
- **Fix**: Flytta RTB till en kort fotnot eller Appendix; håll “NDT/MNDM/MNPS” i huvudtexten.

3) **“Geometric pharmacology” och kliniska implikationer är för tidiga**  
- **Location**: Abstract/Conclusion  
- **Problem**: Inget empiriskt stöd i detta manus.  
- **Fix**: Re‑label som [Speculative] eller flytta till framtidsarbete.

---

### 4. Minor issues

- Stavfel: “sensitivty” → “sensitivity”.  
```973:979:articles/NDT/NoeticDiffusionTheory.typ
... perturbation sensitivty ...
```
- Notation: I vissa stycken blandas `E/R/D` och `m/d/e` utan tydligt “mapping‑statement” i närheten.  
- För långt “Related work” i appendix för en kärnmodell‑artikel — riskerar att späda fokus.

---

### 5. Claim taxonomy audit (behöver label/omlabel)

Följande bör explicit märkas **[Supported]/[Provisional]/[Speculative]** i text:

- **[Speculative]**: “denoising dynamics may be constitutive of consciousness” (Abstract + Scope).  
- **[Provisional]**: TRN‑VG som konkret implementationsmekanism med param‑mapping.  
- **[Provisional]**: “sleep as curriculum” konkretiserad med kvantitativa volymförändringar och hub‑mått.  
- **[Provisional]**: disorder‑signaturer (depression/psychosis) med exakta effektstorlekar.  
- **[Speculative]**: EAP + pulsed phenomenology + “presence/embodiment alignment”.  
- **[Speculative]**: “geometric pharmacology” och kliniska pathway‑påståenden.

---

### 6. Falsification audit

**Falsifierare 1: “Entropy declines are smooth/continuous, not event‑locked.”**  
- **Measurable variable(s)**: event‑locked entropy change in 500ms windows.  
- **Contrast**: SO‑spindle‑aligned vs shuffled events.  
- **Threshold type**: **Currently unspecified** (needs prereg “step index” or delta threshold).  
- **Confounds**: spindle detection bias, filtering‑induced smoothing. Add control with surrogate events.

**Falsifierare 2: “Manifold geometry invariant across wake/sleep/pathology.”**  
- **Measurable variable(s)**: specified topology metrics (Mapper component count, hub betweenness, RQA DET).  
- **Contrast**: sleep stages vs wake; clinical vs controls.  
- **Threshold type**: **Missing**; needs effect‑size or consistency criterion across multiverse.  
- **Confounds**: window length, preprocessing, modality differences.

**Falsifierare 3: “Anti‑phase affects only magnitude, not temporal structure.”**  
- **Measurable variable(s)**: temporal order error rate vs item memory.  
- **Contrast**: anti‑phase vs sham, with within‑subject design.  
- **Threshold type**: **Missing**; must define minimum order‑error delta.  
- **Confounds**: stimulation‑induced arousal or attention shifts.

**Falsifierare 4: “All effects derivable from precision‑only models.”**  
- **Measurable variable(s)**: model comparison metrics (ΔBIC, held‑out likelihood, step‑index).  
- **Contrast**: Minimal‑MNDM vs continuous‑precision model.  
- **Threshold type**: Partially specified (ΔBIC > 10), but needs dataset‑specific expected variance.  
- **Confounds**: over‑fit in flexible models.

**Falsifierare 5: “Phenomenology uncorrelated with (m,d,e), Omega, NDHI.”**  
- **Measurable variable(s)**: experience‑sampling scores.  
- **Contrast**: within‑subject correlations.  
- **Threshold type**: **Missing**; needs prespecified effect size & correction.  
- **Confounds**: measurement noise, timing mismatch.

---

## Förslag: vad kan tas bort helt (för att satsa på kärnidén)

Om målet är en stram, kärn‑fokuserad NDT‑artikel:

**Flytta bort från kärntext (till appendix/future work)**  
- `Embodied Anchoring Principle (EAP)` + detaljerad interoceptiv pipeline → Appendix.  
- TRN‑biologiska detaljsektioner och numerisk `kappa`‑mapping → Appendix.  
- “Geometric pharmacology” som klinisk roadmap → “Limitations and future work”.  
- `RTB` (Reconstructive Theory of Being) och populärfilosofiska referenser → Appendix/footnote.

**Behåll som kärna**  
- Minimal + extended MNDM (med tydlig koppling till m/d/e).  
- RVC som **funktionell** mekanism (utan över‑precis biologi).  
- MNPS + Noetic Atlas (som mätlager).  
- Tier‑1 prediktioner + falsifieringsplan (men med strikt operationalisering).

---

Om du vill kan jag göra en **kort “kärn‑version”** av manusets struktur (rubriker + vad som finns kvar/stryks), eller markera exakt vilka sektioner som bör flyttas till appendix i nästa revision.