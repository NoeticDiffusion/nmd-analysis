Ja, jag tycker kollegans slutsats är rätt: **speed-transienter är fel eventklass**. Det negativa resultatet är nyttigt, inte dåligt. Det säger att “MNPS rör sig snabbt” inte automatiskt betyder “patienten processar något”.

Det jag skulle göra nu är **(a) först**: bygg en burst/suppression-detektor från `/features_raw`, sedan gör peri-event NDT.

Förslag på nytt mått: **Spontaneous Burst-Evoked Geometry (SBEG)**.

```text
1. Detektera suppression:
   low broadband power + låg Hjorth mobility/complexity + låg entropy

2. Detektera burst-onset:
   suppression -> active transition
   med krav på min suppression före och min active duration efter

3. Lägg peri-event-fönster runt burst-onset:
   pre:  -60..0 s
   peak: 0..30 s
   recovery: 30..120 s

4. Mät evoked NDT-deformation:
   Δspectral_radius
   Δfrobenius
   Δtube_d_eff / proxy
   ΔNRCA
   recovery residual
   hysteresis area i (capacity, deformation)-planet
```

Min hypotes skulle vara:

- **CPC1:** färre men mer organiserade bursts, kontrollerad transient, lägre residual, snabbare återgång.
- **CPC5:** antingen ingen verklig respons, eller hög baseline-explosivitet där burst-onset inte ger en distinkt återhämtningsform.

Viktig skillnad mot kollegans test: man ska inte bara jämföra “under event” vs “quiet”. Man ska mäta **formen runt onset**:

```text
baseline -> deformation -> recovery
```

Det är mer analogt med photic/ESB och mer NDT-rent.

Jag skulle inte börja med regionala/9D först. Kör först global 3D + MNJ3D på burst-onsets för att se om peri-event-formen finns alls. Om signalen syns, då blir nästa steg regional/9D för lokalisering och mekanism.

En sak att dubbelkolla: kollegan såg H5 med ~788 fönster och 97 features, medan ComBat-H5 jag tittade på hade kortare runs och 13 features. Det kan vara olika exportroot. För burst-onset-detektorn vill vi helst använda den rikare/raware H5-roten, annars riskerar vi en för grov suppressionklassare.

---

## Matematisk specifikation

Målet är att göra vilodata till kvasi-evoked data genom att låsa NDT-geometrin till spontana burst-onsets. Vi vill alltså inte fråga “hur ser median-geometrin ut under hela körningen?”, utan:

> När hjärnan spontant går från suppression till aktivitet, hur deformeras och återhämtas NDT-geometrin?

Låt varje H5-run ge en fönstersekvens med tidssteg `Delta t`:

```text
t_k                     = fönstrets mittid
z_k = (m_k, d_k, e_k)    = MNPS 3D
z_k^(9)                  = MNPS 9D
u_k                      = rå EEG-featurevektor från /features_raw
J_k                      = lokal MNJ 3D
J_k^(9)                  = lokal MNJ 9D
```

### 1. Suppression / active state

Bygg först en robust per-run amplitud-/aktivitetskoordinat. En enkel första version:

```text
B_k = mean_j rank_z_run(log(1 + |u_{k,j}|)),  j in power features
M_k = rank_z_run(Hjorth_mobility_k)
H_k = rank_z_run(entropy_k)
```

Där `rank_z_run(.)` betyder rank-normalisering inom run:

```text
rank_z_run(x_k) = Phi^-1((rank(x_k) - 0.5) / n)
```

Definiera activity score:

```text
A_k = w_B B_k + w_M M_k + w_H H_k
```

Första konservativa vikter:

```text
w_B = 0.50
w_M = 0.25
w_H = 0.25
```

Suppression och active state definieras med robusta trösklar:

```text
S_k = 1[A_k <= q_s]
U_k = 1[A_k >= q_u]
```

med exempelvis:

```text
q_s = quantile_run(A, 0.25)
q_u = quantile_run(A, 0.60)
```

Alternativt kan `q_s` och `q_u` frysas globalt efter train-fold-kalibrering. För claim-disciplin bör all tröskelkalibrering ske inom train-fold eller part1.

### 2. Burst-onset events

En burst-onset är en transition från suppression till active:

```text
tau_i = t_k
```

så att:

```text
mean(S_{k-L_s : k-1}) >= p_s
mean(U_{k : k+L_a})   >= p_a
```

Föreslagen första definition:

```text
L_s = 5 fönster   (~20 s vid Delta t = 4 s)
L_a = 3 fönster   (~12 s)
p_s = 0.80
p_a = 0.67
```

Lägg också in en refractory period så att samma burst inte räknas flera gånger:

```text
tau_{i+1} - tau_i >= T_ref
T_ref = 60 s
```

Eventmängden per patient blir:

```text
E_i = { tau_{i,1}, ..., tau_{i,N_i} }
```

och event rate:

```text
r_i = N_i / T_i
```

där `T_i` är analyserad tid i minuter eller timmar.

### 3. Peri-event windows

För varje burst-onset `tau`, definiera tre tidszoner:

```text
W_pre(tau)  = [tau - 60 s, tau)
W_peak(tau) = [tau, tau + 30 s]
W_rec(tau)  = (tau + 30 s, tau + 120 s]
```

För ett generiskt geometriskt mått `g_k`, exempelvis `spectral_radius(J_k)`, `||J_k||_F`, `NRCA_k` eller en reachability-proxy, definiera:

```text
g_pre(tau)  = median_{k in W_pre(tau)}  g_k
g_peak(tau) = max_or_median_{k in W_peak(tau)} g_k
g_rec(tau)  = median_{k in W_rec(tau)}  g_k
```

Evoked deformation:

```text
Delta g_peak(tau) = g_peak(tau) - g_pre(tau)
Delta g_rec(tau)  = g_rec(tau)  - g_pre(tau)
```

Robust normaliserad variant:

```text
E_g(tau) = (g_peak(tau) - g_pre(tau)) / (MAD_run(g) + epsilon)
R_g(tau) = |g_rec(tau) - g_pre(tau)| / (MAD_run(g) + epsilon)
```

`E_g` är evoked amplitude. `R_g` är recovery residual.

### 4. MNJ response components

Från `J_k`:

```text
lambda_k = spectral_radius(J_k)
F_k      = ||J_k||_F
S_k^J    = (J_k + J_k^T) / 2
Omega_k  = (J_k - J_k^T) / 2
Rho_k    = ||Omega_k||_F
```

Föreslagna peri-burst MNJ-mått:

```text
E_lambda(tau) = (lambda_peak - lambda_pre) / (MAD_run(lambda) + epsilon)
E_F(tau)      = (F_peak      - F_pre)      / (MAD_run(F)      + epsilon)
E_Rho(tau)    = (Rho_peak    - Rho_pre)    / (MAD_run(Rho)    + epsilon)

R_lambda(tau) = |lambda_rec - lambda_pre| / (MAD_run(lambda) + epsilon)
R_F(tau)      = |F_rec      - F_pre|      / (MAD_run(F)      + epsilon)
R_Rho(tau)    = |Rho_rec    - Rho_pre|    / (MAD_run(Rho)    + epsilon)
```

Tolkning:

- hög `E_lambda` eller `E_F` = stark lokal deformation efter burst-onset
- hög `R_lambda` eller `R_F` = dålig återgång
- hög `E_Rho` = rotations-/guidance-shift under spontan burst

### 5. Capacity/deformation plane

Om reachability-mått finns per fönster eller kan approximeras från lokala covariance/Jacobian-diagnostik, definiera:

```text
C_k = capacity coordinate
D_k = deformation coordinate
```

Första pragmatiska version om full reachability inte finns per fönster:

```text
C_k = -F_k                 # låg deformation som proxy för bevarad lokal kapacitet
D_k = lambda_k             # expansion / brittleness
```

Bättre version om per-window reachability kan beräknas:

```text
C_k = tube_d_eff,k
D_k = spectral_radius(J_k)
```

Peri-event path i planet:

```text
p_k = (C_k, D_k)
```

Hysteresis area runt event:

```text
H_CD(tau) =
  1/2 | sum_{k in W_all(tau)}
        C_k D_{k+1} - D_k C_{k+1} |
```

där:

```text
W_all(tau) = [tau - 60 s, tau + 120 s]
```

Recovery residual i planet:

```text
R_CD(tau) = || median_{W_rec} p_k - median_{W_pre} p_k ||_2
```

### 6. Event-level SBEG score

För varje event:

```text
SBEG_event(tau) =
    a_1 E_lambda(tau)
  + a_2 E_F(tau)
  + a_3 R_lambda(tau)
  + a_4 R_F(tau)
  + a_5 H_CD(tau)
```

Eftersom riktningen kan vara kliniskt viktig bör man också behålla komponenterna separat. En mer recovery-orienterad score kan definieras som:

```text
SBEG_recovery(tau) =
    E_lambda(tau)
  + E_F(tau)
  + R_lambda(tau)
  + R_F(tau)
```

högre värde = mer evoked brittleness / sämre kontroll.

Om `NRCA_k` går att beräkna per fönster:

```text
Delta NRCA_peak(tau) = NRCA_peak(tau) - NRCA_pre(tau)
Delta NRCA_rec(tau)  = NRCA_rec(tau)  - NRCA_pre(tau)
```

Förväntad riktning:

```text
CPC1: liten negativ eller snabb normaliserad Delta NRCA, låg residual
CPC5: stor negativ Delta NRCA eller utebliven organiserad response, hög residual
```

### 7. Patient-level aggregation

För patient `i` med eventmängd `E_i`:

```text
SBEG_i = median_{tau in E_i} SBEG_event(tau)
SBEG_p95_i = quantile_{tau in E_i}(SBEG_event(tau), 0.95)
RecoveryResidual_i = median_{tau in E_i} R_CD(tau)
Hysteresis_i = median_{tau in E_i} H_CD(tau)
EventRate_i = |E_i| / T_i
```

Om `|E_i| = 0`, ska patienten inte automatiskt få låg risk. Avsaknad av bursts kan vara patologiskt. Rapportera därför:

```text
NoBurst_i = 1[|E_i| = 0]
```

och använd separata modeller:

```text
model A: SBEG bland patienter med events
model B: NoBurst + EventRate + SBEG-komponenter
```

### 8. Primär hypotes

Den mest NDT-rimliga hypotesen är inte bara att CPC5 har större eventamplitud, utan att CPC5 har sämre kontrollerad form:

```text
CPC1:
  organized burst response
  moderate E_lambda / E_F
  low R_lambda / R_F
  low H_CD

CPC5:
  no burst response, or
  high baseline deformation with weak event contrast, or
  large E_lambda / E_F and high recovery residual
```

Alltså bör analysen inte bara testa:

```text
event vs quiet
```

utan:

```text
pre -> peak -> recovery
```

### 9. Nuller och kontroller

Minimikrav för att undvika post hoc-artefakt:

```text
1. Circular-shift null:
   Skifta eventtider inom run och behåll samma peri-event-fönster.

2. Random active-onset null:
   Välj slumpade active-state startpunkter med samma run/tidsfördelning.

3. Time-reversal check:
   Om recovery-måttet är meningsfullt ska pre->post inte vara symmetriskt.

4. Feature-only QC:
   Testa om SBEG bara är bandpower/amplitud-QC genom att predicera från burstdetektorns råkomponenter.

5. Part1/part2 freeze:
   Kalibrera q_s, q_u, vikter och eventregler i part1; utvärdera i part2.
```

### 10. Minimal första implementation

Första körbara versionen bör vara liten:

```text
Detector:
  A_k = 0.5 rank_z(log broadband power)
      + 0.25 rank_z(Hjorth mobility)
      + 0.25 rank_z(Hjorth complexity or entropy)

Events:
  suppression >= 20 s före onset
  active >= 12 s efter onset
  refractory = 60 s

Geometry:
  lambda_k = spectral_radius(J_k)
  F_k = ||J_k||_F
  z_k = MNPS 3D

Outputs:
  event table
  patient table
  SBEG_recovery
  EventRate
  NoBurst
  circular-shift null
  part1-fit / part2-test summary
```

Det här är tillräckligt för att falsifiera grundidén:

> Finns det en reproducerbar peri-burst NDT-response-form som skiljer CPC1 från CPC5 bättre än run-medianer?