# Event-Sliced Analysis — Summary
**Senast uppdaterad:** 2026-06-07  
**Datakällor:** `neuralmanifolddynamics_physionet_icare_2_1_20260605_202236` (part1) och `…_210700` (part2)  
**Skript:** `src/analyze_event_sliced_ndt.py`, `src/run_sbeg_detector.py`, `src/sbeg_mnps_extended.py`, `src/sbeg_reachability_windows.py`  
**Resultat:** `results/sbeg_20260607_fullcohort/`, `results/sbeg_mnps_20260607_fullcohort/`, `results/sbeg_reachability_20260607_fullcohort/`

---

## 1. Bakgrund och hypoteser

Tre separata analysspår testades mot de invalidity-fixade dataseten:

1. **LPR (Latent Perturbation Reactivity)** — ursprunglig metod, speed-transient-baserade event. Körs i `analyze_event_sliced_ndt.py`.
2. **SBEG (Spontaneous Burst-Evoked Geometry)** — ny eventklass: suppression→aktiv burst-onset. Specificerad i `ideas.md`. Körs i `run_sbeg_detector.py`.
3. **MNPS/MNJ/Reachability i peri-event-fönster** — klassiska geometrimått beräknade specifikt i pre/peak/recovery-zoner kring burst-onset. Körs i `sbeg_mnps_extended.py` och `sbeg_reachability_windows.py`.

Primär hypotes för SBEG (från `ideas.md`): CPC5-patienter visar antingen ingen distinkt burst-respons, eller hög baseline-deformation med dålig återhämtningsform — till skillnad från CPC1 som förväntas ha mer organiserade, kontrollerade burst-responser.

---

## 2. LPR med invalidity-fixad data (analyze_event_sliced_ndt.py)

**Kohort:** 261 subjekt (jfr 278 på äldre data — minskning pga striktare invalidity-filtrering)  
**Effekt av invalidity-fix:** Tydlig förbättring av signalnivå.

| Mått | Gamla data AUC | Nya data AUC | Förändring |
|---|---|---|---|
| `run_median_spec` | 0.679 | **0.689** | +0.010 |
| `run_median_spec_9d` (ny) | — | **0.692** | Bästa enskilda feature |
| `run_median_spec_plus_lpr_profile` (CV) | 0.678 | **0.696** | +0.018 |

**Slutsats:** Invalidity-fixningen förbättrade signalen. `run_median_spec_9d` (9D Jacobian spektralradius) är starkaste enskilda mått i LPR-analysen.

---

## 3. SBEG-detektor (run_sbeg_detector.py)

**Kohort:** 277 subjekt, CPC1 = 140 / CPC5 = 137, 4 645 körningar  
**Burst-detektor:** Activity score A_k = 0.5·rank_z(log power) + 0.25·rank_z(Hjorth mobility) + 0.25·rank_z(entropy). Suppression ≤ q25, Active ≥ q60, L_sup = 5 fönster, L_act = 3 fönster, refractory = 60 s.  
**Peri-event zoner:** pre = [−60, 0 s], peak = [0, +30 s], rec = [+30, +120 s]  
**Evoked mått:** E_λ, E_F, R_λ, R_F (normaliserade med run-MAD). SBEG_recovery = E_λ + E_F + R_λ + R_F.

### Resultat (patient-nivå, medianaggrerat)

| Mått | CPC1 med | CPC5 med | Cohen's d | p | Eff. AUROC |
|---|---|---|---|---|---|
| `run_median_frob` | 0.151 | 0.170 | −0.517 | 1.7e−7 | **0.682** |
| `run_median_lambda` | 0.072 | 0.075 | −0.461 | 3.6e−7 | **0.677** |
| `R_CD` (recovery residual i C/D-plan) | 0.030 | 0.036 | −0.354 | 9.7e−6 | 0.660 |
| `H_CD` (hysteres-area) | 0.0077 | 0.0098 | −0.227 | 1.9e−8 | 0.703 |
| `R_lambda` | 0.528 | 0.581 | −0.264 | 0.012 | 0.591 |
| `sbeg_recovery` (composite) | 1.341 | 1.299 | −0.187 | **0.489** (ns) | — |
| `event_rate_per_min` | 0.025 | 0.025 | −0.044 | 0.977 | — |
| `no_burst` | 0 | 0 | — | — | — |

**Circular-shift null (sbeg_recovery):** observed |d| = 0.187, null p95 = 0.249, empirisk p = 0.174 → ej signifikant över null.

### Tolkning
- SBEG-hypotesen om distinkt *form* av burst-respons (pre→peak→rec) erhöll **partiellt stöd**: H_CD och R_CD är signifikanta och konceptuellt SBEG-specifika.
- Det sammansatta `sbeg_recovery`-måttet är **inte signifikant** och överstiger inte circular-shift-nultet.
- Burst-detektorn hittar events i nästan alla patienter — avsaknad av bursts diskriminerar inte.
- Baslinjetaten (`run_median_frob`, `run_median_lambda`) dominerar fortfarande.

---

## 4. MNPS/MNJ-utökning i peri-event-fönster (sbeg_mnps_extended.py)

**Kohort:** 257 subjekt, CPC1 = 130 / CPC5 = 127, 3 175 körningar med detekterade bursts  
**Nya mått:** `rho` (rotationsfraktion = ||Ω||_F / ||J||_F), `trace` (divergens), MNPS-hastighet (`speed`), MNPS-avvikelse från centroid (`disp`)

### Resultat

| Mått | d | p | Eff. AUROC |
|---|---|---|---|
| `run_med_lambda` | −0.636 | 4.2e−8 | **0.698** |
| `run_med_rho` (rotation) | −0.292 | 0.00025 | **0.632** ★ NY |
| `peak_rho` | −0.258 | 0.006 | 0.599 |
| `pre_rho` | −0.251 | 0.006 | 0.599 |
| `R_speed` (hastighetens återhämtning) | −0.149 | 0.014 | 0.588 |
| Evoked (E_*) | alla svaga | ns | — |

**★ Nytt fynd: `rho` (rotationsfraktion)** — CPC5 har konsekvent högre rotatorisk/spiral-dynamik i Jacobianen. Mäter *formen* på dynamiken (oscillatorisk vs kontraktiv), oberoende av amplitud. d = −0.29, p = 0.0003. Ej testat i NDT-artikeln.

### Tolkning
- Pre/peak/rec-snapshot-värden är nära identiska — signalen sitter i den **kroniska tillståndsnivån**, inte i förändringen kring onset.
- `R_speed` (p = 0.014) antyder att CPC1 återgår till normalhasighet snabbare, men effekten är liten.

---

## 5. Klassiska reachability-proxier i peri-event-fönster (sbeg_reachability_windows.py)

**Kohort:** 277 subjekt, CPC1 = 141 / CPC5 = 136, 3 501 körningar  
**Mått:**
- `local_min_eig` — minsta eigenvalue i lokal kNN-kovariansmatris (tube_d_eff-proxy, beräknat från nn/indices)
- `local_log_det` — log-determinant av lokal kovarians (volymproxy)
- `local_lev_var` — log-eigenvalue-varians (anisotropi)
- `log_cond` — log-konditionstal från `jacobian/diagnostics/condition_number_windows`
- `dot_speed` — MNPS-hastighet från `mnps_3d_dot`

### Resultat

| Mått | d | p | Eff. AUROC |
|---|---|---|---|
| `run_med_local_min_eig` | +0.354 | 0.0031 | **0.603** ★ |
| `rec_local_min_eig` | +0.339 | 0.0056 | 0.596 |
| `peak_local_min_eig` | +0.327 | 0.0087 | 0.591 |
| `pre_local_min_eig` | +0.300 | 0.0096 | 0.590 |
| `run_med_log_cond` | ≈ 0 | 2.2e−5 | **0.648** ★ (icke-normal) |
| `pre_log_cond` | ≈ 0 | 1.2e−4 | **0.638** |
| `peak_log_cond` | ≈ 0 | 5.6e−4 | 0.624 |
| `pre_local_lev_var` | +0.048 | 0.015 | 0.584 |
| `peak_local_lev_var` | +0.003 | 0.007 | 0.594 |
| Evoked (E_*) | alla svaga | ns | — |

**`local_min_eig`:** CPC1 > CPC5 (d ≈ +0.30–0.35), signifikant i alla zoner. Oberoende bekräftelse av NDT-artikelns tube_d_eff-fynd via kNN-grannskap-baserad väg.

**`log_cond` (konditionstal):** Stark AUROC men liten d — tung svans av höga konditionstal hos CPC5. CPC5 har periodvis närmast singulär lokal dynamik. Icke-parametrisk AUROC mer informativ än d för detta mått.

---

## 6. Jämförelse mot NDT-artikeln

| | NDT-artikel (bäst) | Event-sliced (bäst) |
|---|---|---|
| Reachability lead | `persistence_log_det` **d = +0.90** | `local_min_eig` d = +0.35 |
| MNJ Frobenius | d = −0.499 | d = −0.52 (≈ samma) |
| MNJ spektralradius | d = −0.521 | d = −0.64 (≈ samma) |
| Between-run MAD | `tube_capture_gate` **d = −1.033** | — |
| Incremental AUROC | **0.662** | — |
| Konditionstal | ej rapporterat | eff. AUROC 0.648 |
| Rotationsfraktion ρ | ej rapporterat | d = −0.29 |
| SBEG-specifik respons | ej testat | H_CD d = −0.23, R_CD d = −0.35 |

**NDT-artikeln är avsevärt starkare** (d ≈ 0.84–0.91 för reachability-family vs d ≈ 0.35 här). MNJ-raderna är i paritet. Event-sliced-analysen adderar inget substantiellt prediktivt värde utöver NDT-artikeln.

---

## 7. Nyckelfynd och metodologiska slutsatser

### Vad som höll
1. Invalidity-fix förbättrade LPR-signalen (+0.018 CV-AUROC).
2. `run_median_spec_9d` är starkaste enskilda LPR-feature.
3. `rho` (rotationsfraktion) är ett nytt, robust MNJ-mått (d = −0.29, p = 0.0003) — ej i NDT-artikeln.
4. `local_min_eig` bekräftar tube_d_eff-signalen oberoende via kNN-kovarians.
5. `log_cond` har stark icke-parametrisk AUROC (0.648).
6. H_CD och R_CD ger partiellt stöd för SBEG-hypotesen (sämre återhämtningsform hos CPC5).

### Vad som inte höll
1. **SBEG-composite (`sbeg_recovery`) ej signifikant** — passerar inte circular-shift-nullet.
2. **Evoked-kontraster (E_*, R_*) är genomgående svaga** — signalen är kronisk, inte transient.
3. **Peri-event-fönster tillför inget substantiellt** utöver run-medianer för något mått.
4. **Burst-frånvaro diskriminerar inte** — nästan alla patienter har detekterbara bursts.

### Huvudsaklig metodologisk insikt
Signalen i dessa koma-EEG-data sitter i den **kroniska tillståndsnivån** (run-medianer), inte i den transienta responsen kring spontana burst-onsets. Det argumenterar mot peri-event-analys som primärmetod för denna datamängd. SBEG-konceptet är inte falsifierat — det kan finnas i en annan eventklass, med annan detektor, eller i data med bättre temporal upplösning.

---

## 8. Öppna frågor och möjliga nästa steg (parkerade)

- Del1/del2-frysning av SBEG-detektortrösklar (specificerat i `ideas.md` sektion 9).
- Inkrementell AUROC för `rho` och `log_cond` utöver NDT-artikelns fem reachability-features.
- SBEG med alternativ eventklass (t.ex. EEG-burst-suppression-ratio-baserad detektor snarare än activity-score-baserad).
- Regionalt 9D SBEG om detektorn visar signal på global 3D nivå (specificerat som nästa steg i `ideas.md`).
