Absolut. Här är **batch 2** med referenser. Jag undviker i huvudsak att upprepa första batchen och fokuserar på källor som stärker fyra saker i artikeln: **riktlinjer**, **konfounders/klinisk försiktighet**, **qEEG-baselines**, och **ML/deep-learning-jämförelser**.

## 1. Nolan et al. 2025 — ERC/ESICM Guidelines 2025: post-resuscitation care

**Vad den tillför:**
Detta är den färskaste tunga riktlinjekällan för post-resuscitation care. Den täcker bland annat post-cardiac-arrest syndrome, temperaturkontroll, seizure control, prognostik, långtidsutfall och rehabilitering. Eftersom din artikel skrivs 2026 bör 2025-riktlinjen ersätta eller åtminstone komplettera 2021-riktlinjen som primär guideline-källa. ([resus.org.uk][1])

**Var i texten:**
I **Introduction**, när du skriver att EEG efter hjärtstopp ska tolkas inom multimodal intensivvård och inte som en ensam prediktor. Även i **Discussion / Clinical interpretation boundary**.

**Föreslagen formulering:**

> Contemporary ERC/ESICM post-resuscitation guidelines emphasize that neuroprognostication after cardiac arrest belongs within a multimodal clinical framework rather than relying on any single EEG-derived marker.

---

## 2. Rajajee et al. 2023 — Neurocritical Care guidelines for neuroprognostication

**Vad den tillför:**
Denna är särskilt bra för att förstärka din försiktighetslinje. Guidelines rekommenderar att prognostisk bedömning skjuts upp minst 72 h efter ROSC/rewarming, att sedation och andra konfounders ska undvikas, och att prognostik ska vara multimodal och aldrig bygga på en enskild variabel. ([Assets][2])

**Var i texten:**
I **Bounded claims and non-claims**, **Outcome framing**, och **Limitations**.

**Föreslagen formulering:**

> The present analysis should not be interpreted as clinical neuroprognostication at the bedside. Current neuroprognostication guidelines recommend delayed, multimodal assessment in the absence of sedation or other major confounders.

Detta är viktigt eftersom din 0–12 h-analys annars kan misstolkas som “tidig bedside-prognostik”.

---

## 3. Moseby-Knappe et al. 2020 — guideline-recommended prognostication algorithm

**Vad den tillför:**
Den testar prestanda för en guideline-rekommenderad algoritm för dåligt neurologiskt utfall efter hjärtstopp. Den är bra som kontrast till din artikel: du gör inte en ersättare för ERC/ESICM-algoritmen, utan ett tidigare, dynamiskt recovery-geometry lager som kan analyseras innan full klinisk prognostik. Studien rapporteras i *Intensive Care Medicine* 46(10):1852–1862, DOI 10.1007/s00134-020-06080-9. ([Københavns Universitets Forskningsportal][3])

**Var i texten:**
I **Introduction**, efter stycket om att etablerad prognostik redan finns. Även i **Discussion**, där du placerar NMD som ett kompletterande forskningsmått.

**Föreslagen formulering:**

> Rather than replacing guideline-based algorithms for poor-outcome prognostication, the present work asks whether earlier local geometry contains complementary recovery-potential information.

---

## 4. Ruijter et al. 2018 — qEEG background continuity and burst-suppression amplitude

**Vad den tillför:**
Mycket viktig som qEEG-baseline. Studien analyserade EEG under de första 72 h efter hjärtstopp och använde bland annat background continuity index och burst-suppression amplitude ratio. Background continuity index ≥ 0.80 vid 12 h eller ≥ 0.92 vid 24 h predicerade gott utfall, och burst-suppression amplitude ratio kunde predicera dåligt utfall. ([ScienceDirect][4])

**Var i texten:**
I **Methods / Comparator models** och **Introduction / conventional EEG baselines**.

**Föreslagen formulering:**

> Geometry metrics were compared against conventional quantitative EEG baselines, including continuity- and suppression-related summaries motivated by prior qEEG work in postanoxic coma.

Detta är en nästan nödvändig källa om du vill visa att `tube_log_det_median` inte bara återupptäcker kontinuitet/suppression.

---

## 5. Tjepkema-Cloostermans et al. 2019 — deep learning on postanoxic coma EEG

**Vad den tillför:**
Den visar att deep learning på EEG kan ge stark prediktion av neurologiskt utfall efter postanoxisk koma, inklusive extern validering. Studien använde kontinuerlig EEG under de första tre dagarna, CPC 1–2 vs 3–5 vid sex månader, och rapporterade att poor outcome kunde prediceras vid 12 h med 58% sensitivitet vid 0% false positive rate i extern validering. ([Utwente Forskning][5])

**Var i texten:**
I **Introduction / machine-learning baselines** och **Discussion / incremental value**.

**Föreslagen formulering:**

> Deep-learning approaches have already shown that raw or minimally processed EEG trajectories can support early outcome prediction; the present study therefore evaluates whether interpretable geometry summaries provide a complementary, auditable feature layer rather than merely competing with end-to-end models.

---

## 6. Zheng et al. 2021 — multiscale deep neural networks for EEG outcome prediction

**Vad den tillför:**
Denna ligger ännu närmare din dynamiska idé eftersom den uttryckligen modellerar EEG-evolution över tid. Den multiskaliga modellen kombinerade CNN och LSTM och använde EEG + demografisk information från 1 038 patienter. AUC ökade med EEG-duration, från 0.83 vid 12 h till 0.91 vid 66 h, vilket stöder idén att tidsutveckling i EEG bär prognostisk information. ([Illinois Experts][6])

**Var i texten:**
I **Introduction**, när du motiverar att återhämtningsgeometri bör vara longitudinell snarare än en enstaka snapshot. Även i **Methods**, om du jämför 0–6 h, 6–12 h och hela 0–12 h.

**Föreslagen formulering:**

> Prior multiscale deep-learning work suggests that EEG evolution over time improves outcome prediction, motivating the present focus on early trajectory geometry rather than isolated windows.

---

## 7. Benghanem et al. 2022 — review om EEG/evoked potentials i prognostik

**Vad den tillför:**
Bra review-källa för att rama in neurofysiologiska test efter cardiac arrest. Den diskuterar EEG och evoked potentials som bedside-verktyg och lyfter att benign EEG mellan 12–24 h verkar starkt associerad med gynnsamt utfall. ([PMC][7])

**Var i texten:**
I **Introduction** och **Discussion**, särskilt där du argumenterar för att artikeln bör handla om recovery potential, inte bara poor-outcome prediction.

**Föreslagen formulering:**

> Because favorable recovery is not simply the inverse of poor-outcome prediction, early benign or recovering EEG structure provides an important comparator for recovery-oriented geometry metrics.

---

## 8. van Putten et al. 2024 — quantitative characterization of rhythmic and periodic patterns

**Vad den tillför:**
Den är relevant om din artikel har någon form av secondary branch kring epileptiforma/rhythmic/periodic patterns, pathological capture eller “not just low capacity”. Studien analyserar rhythmic and periodic EEG patterns hos komatösa post-cardiac-arrest-patienter och relaterar qEEG-karakteristik till utfall. ([neurology.org][8])

**Var i texten:**
I **Limitations** eller **Secondary pathological-capture branch**, särskilt om du diskuterar att dålig geometri kan bero på epileptiform/periodisk aktivitet snarare än global irreversibel skada.

**Föreslagen formulering:**

> Future analyses should explicitly stratify or adjust for rhythmic and periodic EEG patterns, since these may introduce pathological local dynamics that could affect reachability and Jacobian-derived measures.

---

# Rekommenderad placering i manus

| Manusdel                                        | Lägg till                                            |
| ----------------------------------------------- | ---------------------------------------------------- |
| Introduction: clinical context                  | Nolan 2025; Rajajee 2023                             |
| Introduction: why not a bedside prognostic tool | Rajajee 2023; Moseby-Knappe 2020                     |
| Introduction: early EEG and recovery trajectory | Benghanem 2022; Zheng 2021                           |
| Methods: comparator models                      | Ruijter 2018; Tjepkema-Cloostermans 2019; Zheng 2021 |
| Methods: confounders                            | Rajajee 2023; Nolan 2025                             |
| Discussion: clinical boundary                   | Nolan 2025; Rajajee 2023                             |
| Discussion: incremental value vs ML/qEEG        | Ruijter 2018; Tjepkema-Cloostermans 2019; Zheng 2021 |
| Limitations: pathological EEG patterns          | van Putten 2024                                      |

---

# BibTeX dump

```bibtex
@article{nolan2025postresuscitation,
  title        = {European Resuscitation Council and European Society of Intensive Care Medicine Guidelines 2025: Post-Resuscitation Care},
  author       = {Nolan, Jerry P. and Sandroni, Claudio and Cariou, Alain and Cronberg, Tobias and D'Arrigo, Sonia and Haywood, Kirstie and Hoedemaekers, Astrid and Lilja, Gisela and Nikolaou, Nikolaos and Olasveengen, Theresa Mariero and Robba, Chiara and Skrifvars, Markus B. and Swindell, Paul and Soar, Jasmeet},
  journal      = {Resuscitation},
  year         = {2025},
  volume       = {215},
  pages        = {110809},
  doi          = {10.1016/j.resuscitation.2025.110809}
}

@article{rajajee2023neuroprognostication,
  title        = {Guidelines for Neuroprognostication in Comatose Adult Survivors of Cardiac Arrest},
  author       = {Rajajee, Venkatakrishna and Muehlschlegel, Susanne and Wartenberg, Katja E. and Alexander, Susan A. and Busl, Katharina M. and Chou, Sherry H. Y. and others},
  journal      = {Neurocritical Care},
  year         = {2023},
  volume       = {38},
  number       = {3},
  pages        = {533--563},
  doi          = {10.1007/s12028-023-01688-3}
}

@article{mosebyknappe2020algorithm,
  title        = {Performance of a Guideline-Recommended Algorithm for Prognostication of Poor Neurological Outcome After Cardiac Arrest},
  author       = {Moseby-Knappe, Marion and Westhall, Erik and Backman, Sofia and Mattsson-Carlgren, Niklas and Dragancea, Irina and Lybeck, Anna and Friberg, Hans and Stammet, Pascal and Lilja, Gisela and Horn, Janneke and Kjaergaard, Jesper and Rylander, Christian and Hassager, Christian and Ull{\'e}n, Susann and Nielsen, Niklas and Cronberg, Tobias},
  journal      = {Intensive Care Medicine},
  year         = {2020},
  volume       = {46},
  number       = {10},
  pages        = {1852--1862},
  doi          = {10.1007/s00134-020-06080-9}
}

@article{ruijter2018discontinuous,
  title        = {The Prognostic Value of Discontinuous EEG Patterns in Postanoxic Coma},
  author       = {Ruijter, Barry J. and Hofmeijer, Jeannette and Tjepkema-Cloostermans, Marleen C. and van Putten, Michel J. A. M.},
  journal      = {Clinical Neurophysiology},
  year         = {2018},
  volume       = {129},
  number       = {8},
  pages        = {1534--1543},
  doi          = {10.1016/j.clinph.2018.04.745}
}

@article{tjepkema2019deeplearning,
  title        = {Outcome Prediction in Postanoxic Coma With Deep Learning},
  author       = {Tjepkema-Cloostermans, Marleen C. and da Silva Louren{\c c}o, Catarina and Ruijter, Barry J. and Tromp, Selma C. and Drost, Gea and Kornips, Fran{\c c}ois H. M. and Beishuizen, Albertus and Bosch, Frank H. and Hofmeijer, Jeannette and van Putten, Michel J. A. M.},
  journal      = {Critical Care Medicine},
  year         = {2019},
  volume       = {47},
  number       = {10},
  pages        = {1424--1432},
  doi          = {10.1097/CCM.0000000000003854}
}

@article{zheng2021multiscale,
  title        = {Predicting Neurological Outcome in Comatose Patients After Cardiac Arrest With Multiscale Deep Neural Networks},
  author       = {Zheng, Wei Long and Amorim, Edilberto and Jing, Jin and Ge, Wendong and Hong, Shenda and Wu, Ona and Ghassemi, Mohammad and Lee, Jong Woo and Sivaraju, Adithya and Pang, Trudy and Herman, Susan T. and Gaspard, Nicolas and Ruijter, Barry J. and Sun, Jimeng and Tjepkema-Cloostermans, Marleen C. and Hofmeijer, Jeannette and van Putten, Michel J. A. M. and Westover, M. Brandon},
  journal      = {Resuscitation},
  year         = {2021},
  volume       = {169},
  pages        = {86--94},
  doi          = {10.1016/j.resuscitation.2021.10.034}
}

@article{benghanem2022eeg,
  title        = {Prognostication After Cardiac Arrest: How EEG and Evoked Potentials May Improve the Challenge},
  author       = {Benghanem, Sarah and Paul, Michael and Charpentier, Julien and Cariou, Alain and Sandroni, Claudio and Geri, Guillaume},
  journal      = {Annals of Intensive Care},
  year         = {2022},
  volume       = {12},
  number       = {1},
  pages        = {111},
  doi          = {10.1186/s13613-022-01083-9}
}

@article{vanputten2024rpp,
  title        = {Quantitative Characterization of Rhythmic and Periodic EEG Patterns in Patients in a Coma After Cardiac Arrest and Association With Outcome},
  author       = {van Putten, Michel J. A. M. and others},
  journal      = {Neurology},
  year         = {2024},
  doi          = {10.1212/WNL.0000000000209608}
}
```

En liten notering: för **van Putten et al. 2024** bör vi senare komplettera exakt fullständig author list innan slutlig inlämning. DOI och titel är stabila, men jag vill inte låtsas att jag har verifierat hela författarlistan här.

[1]: https://www.resus.org.uk/professional-library/2025-resuscitation-guidelines/post-resuscitation-care-guidelines?utm_source=chatgpt.com "Post-resuscitation care Guidelines"
[2]: https://assets.ctfassets.net/07cwnclyy106/4z9x6OehQoIyXhD5ahsiOL/c7cd0b98284eb014472864b39f14113b/EGT-3211.v1_Download.pdf?utm_source=chatgpt.com "Guidelines for neuroprognostication in comatose adult ..."
[3]: https://researchprofiles.ku.dk/en/publications/performance-of-a-guideline-recommended-algorithm-for-prognosticat/ "
        Performance of a guideline-recommended algorithm for prognostication of poor neurological outcome after cardiac arrest
      \-  University of Copenhagen Research Portal"
[4]: https://www.sciencedirect.com/science/article/abs/pii/S1388245718310575 "The prognostic value of discontinuous EEG patterns in postanoxic coma - ScienceDirect"
[5]: https://research.utwente.nl/en/publications/outcome-prediction-in-postanoxic-coma-with-deep-learning/ "
        Outcome Prediction in Postanoxic Coma With Deep Learning
      \-  University of Twente Research Information"
[6]: https://experts.illinois.edu/en/publications/predicting-neurological-outcome-in-comatose-patients-after-cardia/ "
        Predicting neurological outcome in comatose patients after cardiac arrest with multiscale deep neural networks
      \-  Illinois Experts"
[7]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9732180/?utm_source=chatgpt.com "Prognostication after cardiac arrest: how EEG and evoked ..."
[8]: https://www.neurology.org/doi/10.1212/WNL.0000000000209608?utm_source=chatgpt.com "Quantitative Characterization of Rhythmic and Periodic ..."
