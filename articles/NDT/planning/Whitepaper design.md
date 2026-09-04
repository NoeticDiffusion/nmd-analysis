# Direction memo (Phase 1 → White paper)

## 1) Övergripande tes (1–2 meningar)

**Consciousness as Diffusive Reconstruction:** Medvetandet uppstår ur en flerskalig, rytmstyrd **denoising-process** som omvandlar affektiv–mnemonisk “brus” till koherent, förstapersonlig verklighetsupplevelse; psykopatologi är distinkta **diffusionsfel** (brusöverskott, låsta attraktorbrunnar, desynkronisering).

## 2) Scope & ton

* **Human brain only.** Inga AI-paralleller i huvudtext (kan nämnas kort i Appendix).
* **Empiriskt informerad, testbar teori**: varje större påstående ska följas av 2–3 *falsifierbara prediktioner* och *mätbara biomarkörer*.
* **Integration av era brev**: vi destillerar Letter 2–4 till tre kärnaxlar: **(A) Tidskalor & kritikalitet**, **(B) Embodiment & self-prior**, **(C) Topologi för breakdown**.

## 3) Struktur för white paper (≈12–18 sidor)

1. **Abstract (200–250 ord)**
2. **Introduction: From Noise to Self**

   * Problembild: disparate modeller (prediktiv kodning, psykiatri) saknar en *generativ* mekanik för upplevelse.
3. **Core Hypothesis**

   * Diffusion som flerskalig denoising (mikro ↔ meso ↔ makro)
   * “Self-prior” som gravitationscentrum (embodiment/interoception)
4. **Rhythm, Criticality, and Stability**

   * CFC (t.ex. theta–gamma), sömnarkitektur, metastabilitet som “regularization”.
5. **Topology of Failure (Psychopathology)**

   * Psykos (prematur sampling), PTSD (mode collapse), depression (negativt biased manifold), mania (överkrökning/över-variance), depersonalisation (svag self-prior).
6. **Testable Predictions & Paradigms**

   * (Se listan nedan: mätningar, paradigm, biomarkörer.)
7. **Methods Roadmap (Phase-1 experiments)**

   * Minimalmodell + dataset + analysplan.
8. **Discussion: Differentialdiagnostik mot alternativa ramar**

   * Vad diffusion tillför vs. predictive processing/active inference.
9. **Limitations & Falsification Paths**
10. **Conclusions & Next Steps**
    **Appendices**: Kort matematik (score-SDE-skiss), etik, AI-parallell (valfritt).

## 4) Nyckelpåståenden → mätbara prediktioner

**A. Timescales & denoising cascade**

* *Prediktion A1:* Störning i **cross-frequency coupling** (t.ex. theta–gamma) ger “partial denoising”: ökad perceptuell instabilitet/bistabilitet utan full psykos.
* *Mått:* EEG/MEG CFC-index; beteende i bistabilitetsparadigm (Necker cube).

**B. Attention/thalamus som “variance schedule”**

* *Prediktion B1:* TRN/thalamo-kortikal gating korrelerar med minskande entropi under replay (tidig REM: högre entropi → sen REM: lägre).
* *Mått:* sömn-EEG + hippocampal replay (i djurdata) / människa: TMR-paradigm, LZ-komplexitet/Multiscale Entropy.

**C. Rhythm as regularizer**

* *Prediktion C1:* Försämrad slow-wave sleep förutspår “stela priorer” (lägre belief-updating) i Bayesian surprise-uppgifter.
* *Mått:* polysomnografi + beteende; driftsmått på belief updating.

**D. Self-prior (embodied anchor)**

* *Prediktion D1:* Modulation av **insula** (neurofeedback/TMS) ändrar interoceptiv precision → skift i “body ownership” och affektiv klarhet.
* *Mått:* heartbeat detection, kroppsägaruppgifter, självrapporter.

**E. Topology of breakdown**

* *Prediktion E1 (PTSD):* Hög återkommande likhet i mönster (representational similarity) vid traumacues → “mode collapse”.
* *Prediktion E2 (Depression):* Lägre varians/curvature i affektiv manifolddynamik; reducerad övergångssannolikhet mellan tillstånd.
* *Prediktion E3 (Psykos):* Ökad signalentropi + försvagat prefrontalt “denoising-gain” → prematura percept.
* *Mått:* fMRI state-space, manifold-inlindning (Laplacian eigenmaps/PHATE), HMM-dwell times; EEG-entropi; prefrontala kontrollmått.

**F. Farmaka som topologimodulatorer**

* *Prediktion F1 (Litium):* Minskad variance-överskjutning (stabilare state-space), ökad återhämtnings-resiliens efter perturbation.
* *Mått:* fMRI-recurrence plots, recovery-time efter TMS-puls/odd-ball.

## 5) Minimal matematik (Appendix-skiss)

* **Latent SDE:**  (dx_t = f_\theta(x_t, \phi, r),dt + g(\sigma_t), dW_t)
  där (x_t)=neural state, (\phi)=self-prior, (r)=rhythm/phase; (f_\theta)=score-liknande denoiser; (\sigma_t)=brusnivå styrd av attention/thalamus.
* **Health vs. pathology:** stabila/metastabila attraktorer vs. mode collapse/över-krökning; mät med Lyapunov-approx + manifold-curvature.

## 6) Experimentell Phase-1 (realistisk, låg tröskel)

* **Dataspår**

  1. **Öppna EEG-dataset** med sömn + kognitiv uppgift (CFC, entropi, bistabilitet).
  2. **fMRI-rest + task** (HCP/open) för state-space/manifold-analys.
* **Analysplan**

  * CFC-index ↔ perceptuell stabilitet; LZ/Multiscale Entropy över sömncykler ↔ belief updating.
  * fMRI-manifold: curvature/variance/dwell ↔ symtomskalor i öppna kliniska kohorter (om tillgängligt).
* **Förhandsregistrering**: Hypoteser A1–F1, primära/sekundära mått, föranalysplan.

## 7) Integrering av Letter 2–4 i white paper

* **Letter 2 (Claude):** Tidskalor/kritikalitet → sektion 3–4 + Appendix-prediktioner.
* **Letter 3 (Gemini):** Embodiment/self-prior → sektion 3 & 5 (depersonalisation/anxiety).
* **Letter 4 (Grok):** Entropi/evolutionärt ramverk → Discussion (konvergens med free-energy; vad diffusion tillför).

## 8) Repo-struktur (för Zenodo-release)

```
/README.md                  # Core hypothesis (du har grunden)
/whitepaper/00_abstract.md
/whitepaper/01_intro.md
/whitepaper/02_hypothesis.md
/whitepaper/03_rhythm_criticality.md
/whitepaper/04_self_prior_embodiment.md
/whitepaper/05_topology_breakdown.md
/whitepaper/06_predictions_methods.md
/whitepaper/07_discussion_limits.md
/whitepaper/08_conclusion.md
/whitepaper/appendix_math.md
/letters/Letter1.md
/letters/Letter2.md
/letters/Letter3.md
/letters/Letter4.md
/analysis/EEG_CFC_plan.md
/analysis/fMRI_manifold_plan.md
```

## 9) Milestones (2–3 veckor, rimlig “Phase 1”)

* **M1 (Idag–+2 dagar):** Fastställ rubriker + fyll 02_hypothesis.md (du + jag).
* **M2 (vecka 1):** Skriv 03–05 med destillat från Letter 2–4; lägg in prediktionstabeller.
* **M3 (vecka 2):** 06_predictions_methods + appendix_math; förhandsregistreringsutkast.
* **M4 (vecka 3):** Redigering, sammanfogning till en PDF/markdown-release, Zenodo-metadata.

## 10) Nästa steg (konkreta)

* Jag tar fram **skelettfilerna** enligt strukturen ovan och fyller **02_hypothesis.md** + **06_predictions_methods.md (utkast)**.
* Du laddar upp **Letter 2–4** under `/letters/` (som du skissat) och markerar *vilka stycken* vi ska citera direkt i huvudtexten.
* Därefter börja vi med **03_rhythm_criticality.md** (jag gör första utkastet baserat på dina prioriteringar).

Vill du att jag direkt skriver in **skelettfilerna + två sektioner (02 & 06) som första kommit?** Jag kan också paketera en kort **Contrib-guide** för hur våra Cursor-kollegor lämnar PRs/Letters.



Super! Här är en fokuserad plan för vad vi bör diskutera och fördjupa för att få tyngd i ett **första white paper utan egna experiment** — fortfarande strikt om den mänskliga hjärnan.

# Vad som bör ingå (och varför)

## 1) Kärnteori (kort och exakt)

* **Påstående:** Medvetandet är en flerskalig **denoising-diffusion** i ett affekt–minnes-tillståndsrum; rytmer (sömn/oscillationer) reglerar när och hur starkt denoising sker; **self-prior** (embodiment/interoception) är gravitationscentrum.
* **Bidrag:** Ger mekanism (inte bara metafor) och binder samman fenomenologi, neurodynamik och psykopatologi.
* **Leverabel:** 1 sida med tydliga definitioner (noise, denoiser, variance schedule, self-prior, rhythm).

## 2) Relation till existerande ramar (positionering)

* **Prediktiv kodning/Active Inference:** var konvergerar vi (felminimering/överraskning) och var tillför diffusion något nytt (iterativ generering från latenta tillstånd; variansschema; topologi)?
* **Dynamisk kritikalitet/metastabilitet:** hur vår diffusion behöver “edge of criticality” och varför rytm fungerar som regularisering.
* **Leverabel:** jämförelsetabell + illustrerad “varför diffusion?”-ruta.

## 3) Tidskalor och kaskad-denoising

* **Kärna:** mikro (jonkanaler) → meso (lokala nät/oscillationer) → makro (limbiskt–kortikalt, neuromodulatorer) → ultraslow (cirkadian/sömn).
* **Argument utan experiment:** sammanväg tidigare fynd (icke-experimentellt), formulera **falsifierbara prediktioner** (t.ex. störd theta–gamma-koppling ⇒ “partial denoising”).
* **Leverabel:** figur: “Nested diffusions” över tidsskalor + 3–5 prediktioner.

## 4) Thalamo-kortikal gating & uppmärksamhet som “variance schedule”

* **Kärna:** TRN/thalamo-kortikala slingor avgör hur många “denoising-iterationer” som får löpa och med vilken varians.
* **Tyngd:** neuroanatomi + sömn/replay-literatur (kvalitativ syntes), kliniska kopplingar (antipsykotika/uppmärksamhet).
* **Leverabel:** schema över loopar + prediktioner om sömn-replay (tidig REM hög entropi → sen REM lägre).

## 5) Embodiment: interoception/insula som self-prior

* **Kärna:** kroppen som primär brus-/bias-källa; insula/ACC integrerar interoceptiva signaler → **gravitation** som förankrar diffusion till “värld-för-mig”.
* **Klinisk relevans:** depersonalisation (svag “gravity”), ångest/panik (hyper-interoceptivt brus).
* **Leverabel:** karta över interoceptiva kretsar + 3 prediktioner (t.ex. insula-modulation ⇒ skift i body-ownership/affektiv klarhet).

## 6) Psykopatologi som topologiska fel

* **Psykos:** prematur sampling/under-denoising (brusövervikt).
* **PTSD:** mode collapse (fast attraktor).
* **Depression:** negativt biasad manifold (låg varians/kurvatur).
* **Mani:** överkrökning/över-varians (överskjutande denoising).
* **Depersonalisering:** svagt self-prior (låg gravitation).
* **Leverabel:** topologiska skisser + biomarkör-förslag (entropimått, HMM-dwell, manifold-kurvatur).

## 7) “Matematisk ryggrad” (lätt, i appendix)

* **Form:** latent SDE/score-baserat ramverk: drift (denoiser), diffusion (brus), rytm som tidsberoende koefficient, self-prior som potential.
* **Syfte:** göra hypotesen **falsifierbar** och möjlig att simulera (utan att vi kör egna experiment).
* **Leverabel:** 1–2 sidor med symboler + tolkningar (ingen tung bevisföring).

## 8) Farmakologi som topologimodulation (kort)

* **Litium:** variance clamp/stabilisering av landskap;
* **SSRIs:** ökad utforskbarhet (affektiv varians);
* **Antipsykotika:** förstärkt denoiser-gain.
* **Leverabel:** liten ruta “Therapeutics as topology”.

## 9) Prediktioner & mätbara proxies (utan egna data)

* **EEG/MEG:** Lempel-Ziv, multiscale entropy, CFC-index.
* **fMRI:** state-space/manifold (PHATE/Laplacian), dwell times, återhämtnings-resiliens.
* **Beteende:** bistabil perception, Bayesian surprise/paradigm.
* **Leverabel:** tabell “Prediktion → mätbar proxy → tidigare stöd (kvalitativt) → hur falsifiera”.

## 10) Begränsningar & hur teorin kan falla

* **Riskzoner:** för bred metafor, kausalitetsoklarhet, överlapp med predictive processing.
* **Motdrag:** explicit differens, tydliga prediktioner, föreslagna naturalistiska test.

---

# Var vi bör fördjupa oss (för att öka vetenskaplig tyngd)

Här är **fem områden** där en djup syntes (utan egna experiment) ger störst legitimitet:

1. **Cross-Frequency Coupling & Sömnarkitektur (rytmer som regularisering)**

   * Sammanfoga evidens för theta–gamma/alpha-koppling, SWS/REM-roller, och hur rytmer stabiliserar perception/minne.
   * Skriv en stringent logik: *om diffusion kräver variance-schema → då måste rytmer modulera varians → därför bör CFC korrelera med “denoising-grad” och kognitiv stabilitet.*

2. **Thalamo-kortikal gating & TRN som variansschema**

   * Djupare neuroanatomi och funktion (sensorisk gating, selektiv uppmärksamhet, replay).
   * Koppla till psykos (sensorisk förstärkning/aberrant salience) och sedativa/antipsykotika.

3. **Interoception/Insula & Self-prior**

   * Syntes av interoceptiv inferens, body-ownership, ACC/insula i affektiv precision.
   * Klinisk brygga: depersonalisation, panik, ångest—hur self-prior ändrar topologin och tolkningen av bruset.

4. **Topologi & Manifold-geometri för hjärnans tillståndsrum**

   * Introducera modern analys (manifold-inlindning, metastabilitet, TDA/recurrence).
   * Göra tydlig karta: *hälsa = rörlig, men koherent manifold; patologi = kollaps/fragmentering/överkrökning*.
   * Detta ger oss **kvantitativa, för-registrerbara** hypoteser utan nya data.

5. **Psykofarmakologi som landskaps-/varians-modulator**

   * Kort översikt med tydlig begreppskarta (inte detaljer om molekyler).
   * Förklara varför litium är ett teoretiskt “ankare” i vår modell (stabilitet på tvärs av tillstånd).

---

# Föreslagen disposition (komprimerad)

1. **Abstract**
2. **Introduction: From Noise to Self**
3. **Core Hypothesis (definitions + figur)**
4. **Timescales, Rhythm & Criticality (CFC, sömn)**
5. **Thalamic Gating & Attention as Variance Schedule**
6. **Embodiment & the Self-Prior (insula/interoception)**
7. **Topology of Failure (psychosis/PTSD/depression/mania/derealisation)**
8. **Predictions & Observable Proxies (tabell)**
9. **Differentiation from Predictive Processing / Active Inference**
10. **Therapeutics as Topology (kort)**
11. **Limitations & Falsification**
12. **Conclusion & Roadmap**
    **Appendix:** Lätt matematik (SDE/score), etiknot, ev. AI-parallell (valfritt).

---

# Figurer vi bör rita (utan data)

* **Fig 1:** “Nested Diffusions” över tidsskalor (mikro→ultraslow).
* **Fig 2:** Thalamo-kortikala loopar och TRN som variance-schema.
* **Fig 3:** Self-prior som gravitationsbrunn (embodiment/interoception).
* **Fig 4:** Topologi vid hälsa vs. psykos/PTSD/depression/mani (skematisk manifold).
* **Fig 5:** Prediktionskarta: mätbar proxy ↔ förväntad förändring.

---

# Varför detta räcker för ett starkt white paper nu

* Vi **binder ihop** tre robusta literaturströmmar (rytmer/kritikalitet, thalamo-kortikal gating, interoception/self) med **en ny generativ mekanik** (diffusiv denoising) och **konkreta, mätbara prediktioner**.
* Vi gör teorin **falsifierbar** (prediktionstabell, manifolddynamik) och **testbar** mot öppna dataset i framtida fas.
* Vi håller spekulationer (t.ex. kosmiskt/kvant) utanför huvudtexten (högst i en diskussionsruta/appendix).

Vill du att jag börjar fylla **03 (Timescales/Rhythm)** och **05 (Embodiment/Self-prior)** enligt ovan, så har vi ryggraden på plats inför resten?

