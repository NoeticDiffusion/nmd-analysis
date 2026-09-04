Below is a **first citation batch** for *Recovery-Linked Neural Geometry After Cardiac-Arrest Coma*. I would use these mainly to strengthen the **Introduction**, **dataset framing**, **clinical EEG baseline**, and **incremental-validity argument**. Your draft already positions the paper as recovery-geometry rather than direct consciousness decoding, and it explicitly emphasizes patient-level outcome framing and fixed measurement contracts. 

---

## 1. Amorim et al. — I-CARE database paper / dataset anchor

**What it adds:**
This should be the primary dataset citation. It establishes I-CARE as a large, real-world multicenter dataset of clinical, EEG, and ECG data from adult cardiac-arrest patients who achieved ROSC but remained comatose, with variable recording start time and duration across ICU patients. PhysioNet v2.1 also states that the public training set contains 607 patients, with hidden validation/test data retained for the 2023 PhysioNet Challenge. ([PhysioNet][1])

**Where to place it:**
In **“Dataset and current local exports”**, immediately after:

> “The empirical target is the I-CARE database processed through NeuralManifoldDynamics.”

Also cite it in **Data Availability** and **Methods / Dataset**.

**Why it matters for reviewers:**
It grounds your work in a recognized public ICU EEG resource, and it gives you a legitimate reason to emphasize heterogeneity, site variation, variable monitoring onset, and clinically realistic artifact burden.

---

## 2. Hirsch et al. 2021 — ACNS critical care EEG terminology

**What it adds:**
This is the standard terminology paper for critical-care EEG description. It gives you the clinical vocabulary for background frequency, continuity, suppression/attenuation, burst-suppression, rhythmic/periodic patterns, state changes, and seizures. The ACNS paper explicitly defines ICU EEG background descriptors such as predominant background frequency and continuity categories. 

**Where to place it:**
In the **Introduction**, where the draft currently says that standard EEG interpretation already has prognostic value. Also cite it in **Methods**, especially if you compare NMD geometry to “static EEG severity markers.”

Suggested sentence:

> Conventional ICU EEG interpretation was referenced to standardized ACNS terminology, including background frequency, continuity, suppression, burst-suppression, rhythmic/periodic patterns, seizures, and state changes.

**Why it matters:**
It prevents the paper from sounding like it invents its own language while ignoring the clinical EEG standard.

---

## 3. Westhall et al. 2016 — standardized EEG prognostication after cardiac arrest

**What it adds:**
This is one of the key prognostic EEG papers after cardiac arrest. It showed that highly malignant EEG patterns after rewarming predicted poor outcome with very high specificity, while benign EEG was strongly predictive of good outcome. The study also reports that specificity and sensitivity were not significantly affected by targeted temperature or sedation in that cohort. ([Lund University][2])

**Where to place it:**
In the **Introduction**, after:

> “Standardized interpretation of malignant and benign EEG patterns after cardiac arrest has substantial prognostic value…”

Also cite it in **baseline comparator methods**, if you include a clinical EEG severity baseline.

**Why it matters:**
This is the key “you must compare against this world” source. Your paper should explicitly say that NMD geometry is intended to complement, not replace, malignant/benign EEG interpretation.

---

## 4. Hofmeijer et al. 2015 — early EEG contributes to multimodal prediction

**What it adds:**
This supports your 0–12 h / first-24 h framing. Hofmeijer et al. found that EEG within 24 h contributes robustly to prediction of good or poor outcome, and that favorable EEG patterns at 12 h were strongly associated with good outcome. ([Utwente Forskning][3])

**Where to place it:**
In the **Introduction**, exactly where your draft says early EEG can already be informative within 12–24 h.

Also in **Primary endpoint draft**, next to your planned 0–12 h article scope.

**Why it matters:**
This lets you justify the early-window design without making it sound arbitrary.

---

## 5. Ruijter et al. 2019 — prospective early EEG outcome prediction

**What it adds:**
This strengthens the claim that early EEG can predict both good and poor outcome after cardiac arrest. The PubMed summary states that EEG allowed reliable prediction of poor outcome with maximum sensitivity in the first 24 h, and continuous patterns at 12 h were associated with good recovery. ([PubMed][4])

**Where to place it:**
In the same **Introduction paragraph** as Hofmeijer et al., but use it to support the broader prospective-cohort evidence rather than the initial multimodal-model claim.

Suggested placement:

> Several prospective studies have shown that early EEG patterns, especially within the first 12–24 h, carry prognostic information for both poor and favorable recovery.

**Why it matters:**
Hofmeijer gives you the multimodal prediction anchor; Ruijter gives you a later prospective EEG-specific support.

---

## 6. Carrasco-Gómez et al. 2021 — functional connectivity baseline

**What it adds:**
This is especially important for your paper because it is closer to your dynamical/geometry direction than purely visual EEG classification. The study tested whether EEG functional-connectivity features add value beyond non-coupling EEG features, using coherence, phase-locking value, and mutual information at 12, 24, and 48 h after cardiac arrest; the combined model outperformed either feature family alone. ([ScienceDirect][5])

**Where to place it:**
In a new paragraph near the end of the **Introduction** or start of **Methods**, under something like:

> “Relation to quantitative EEG and connectivity baselines.”

Also cite it in **Statistical analysis / Incremental validity**, if you add a model comparison:

> clinical + spectral/qEEG baseline vs clinical + qEEG + NMD geometry.

**Why it matters:**
This is the reviewer-facing bridge: if connectivity already adds value beyond static EEG, then your geometry metrics must be tested as another incremental layer, not merely as a new vocabulary.

---

## 7. Turella et al. 2024 — good outcome prediction and EEG reactivity

**What it adds:**
This gives you a recent good-outcome comparator. In a multicentre cohort, non-highly malignant and reactive EEG predicted good long-term outcome with 56% sensitivity and 83% specificity, and EEG reactivity contributed to prognostic performance beyond background pattern alone. ([Lund University][6])

**Where to place it:**
In **Outcome framing** and **Discussion**, especially where you distinguish “recovery potential” from direct consciousness decoding.

Suggested use:

> Recent multicentre work suggests that preserved EEG reactivity and absence of highly malignant patterns can support prediction of good long-term outcome, reinforcing the need to evaluate recovery-positive structure rather than only poor-outcome markers.

**Why it matters:**
Your paper is conceptually closer to “retained recoverability” than to only predicting futility. This citation supports that orientation.

---

# Suggested insertion map

| Draft location                                                           | Add citations                                                                 |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| Abstract / first paragraph                                               | Amorim et al.; possibly Hofmeijer/Ruijter if you mention early prognostic EEG |
| Introduction: “EEG appears slow/suppressed/disorganized…”                | Hirsch 2021; Westhall 2016                                                    |
| Introduction: “early EEG informative within 12–24 h”                     | Hofmeijer 2015; Ruijter 2019                                                  |
| Introduction: “geometry-centered analysis may recover dynamic structure” | Carrasco-Gómez 2021                                                           |
| Dataset and current local exports                                        | Amorim et al.; PhysioNet/I-CARE dataset citation                              |
| Outcome framing                                                          | Hofmeijer 2015; Ruijter 2019; Turella 2024                                    |
| Methods: comparator models                                               | Hirsch 2021; Westhall 2016; Carrasco-Gómez 2021                               |
| Discussion: “not a standalone oracle”                                    | Westhall 2016; Turella 2024; Carrasco-Gómez 2021                              |

---

# BibTeX dump

```bibtex
@article{amorim2023icare,
  title        = {The International Cardiac Arrest Research (I-CARE) Consortium Electroencephalography Database},
  author       = {Amorim, Edilberto and Zheng, Wei-Long and Ghassemi, Mohammad M. and Aghaeeaval, Mahsa and Kandhare, Pravinkumar and Karukonda, Vishnu and Lee, Jong Woo and Herman, Susan T. and Sivaraju, Adithya and Gaspard, Nicolas and Hofmeijer, Jeannette and van Putten, Michel J. A. M. and Sameni, Reza and Reyna, Matthew A. and Clifford, Gari D. and Westover, M. Brandon},
  journal      = {Critical Care Medicine},
  year         = {2023},
  volume       = {51},
  number       = {12},
  pages        = {1802--1811},
  doi          = {10.1097/CCM.0000000000006074}
}

@article{hirsch2021acns,
  title        = {American Clinical Neurophysiology Society's Standardized Critical Care EEG Terminology: 2021 Version},
  author       = {Hirsch, Lawrence J. and Fong, Michele W. K. and Leitinger, Markus and LaRoche, Suzette M. and Beniczky, Sandor and Abend, Nicholas S. and Lee, Jong Woo and Wusthoff, Courtney J. and Hahn, Cecil D. and Westover, M. Brandon and Gerard, Elizabeth E. and Herman, Susan T. and Haider, Hiba A. and Osman, Gamal and Rodriguez-Ruiz, Antonio and Maciel, Camila B. and Gilmore, Emily J. and Fernandez, Alexandra and Rosenthal, Eric S. and Claassen, Jan},
  journal      = {Journal of Clinical Neurophysiology},
  year         = {2021},
  volume       = {38},
  number       = {1},
  pages        = {1--29},
  doi          = {10.1097/WNP.0000000000000806}
}

@article{westhall2016standardized,
  title        = {Standardized EEG Interpretation Accurately Predicts Prognosis After Cardiac Arrest},
  author       = {Westhall, Erik and Rossetti, Andrea O. and van Rootselaar, Anne-Fleur and Kjaer, Troels W. and Horn, Janneke and Ull{\'e}n, Susann and Friberg, Hans and Nielsen, Niklas and Ros{\'e}n, Ingmar and Aneman, Anders and Erlinge, David and Gasche, Yvan and Hassager, Christian and Hovdenes, Jan and Kjaergaard, Jesper and Kuiper, Michael and Pellis, Tommaso and Stammet, Pascal and Wanscher, Michael and Wetterslev, J{\o}rn and Wise, Matthew P. and Cronberg, Tobias},
  journal      = {Neurology},
  year         = {2016},
  volume       = {86},
  number       = {16},
  pages        = {1482--1490},
  doi          = {10.1212/WNL.0000000000002462}
}

@article{hofmeijer2015early,
  title        = {Early EEG Contributes to Multimodal Outcome Prediction of Postanoxic Coma},
  author       = {Hofmeijer, Jeannette and Beernink, Tim M. J. and Bosch, Frank H. and Beishuizen, Albertus and Tjepkema-Cloostermans, Marleen C. and van Putten, Michel J. A. M.},
  journal      = {Neurology},
  year         = {2015},
  volume       = {85},
  number       = {2},
  pages        = {137--143},
  doi          = {10.1212/WNL.0000000000001742}
}

@article{ruijter2019early,
  title        = {Early Electroencephalography for Outcome Prediction of Postanoxic Coma: A Prospective Cohort Study},
  author       = {Ruijter, Barry J. and Tjepkema-Cloostermans, Marleen C. and Tromp, Selma C. and van den Bergh, Walter M. and Foudraine, Niels A. and Kornips, Frans H. M. and Drost, Gea and Scholten, Esther and Bosch, Frank H. and Beishuizen, Albertus and van Putten, Michel J. A. M. and Hofmeijer, Jeannette},
  journal      = {Annals of Neurology},
  year         = {2019},
  volume       = {86},
  number       = {2},
  pages        = {203--214},
  doi          = {10.1002/ana.25514}
}

@article{carrascogomez2021connectivity,
  title        = {EEG Functional Connectivity Contributes to Outcome Prediction of Postanoxic Coma},
  author       = {Carrasco-G{\'o}mez, Mart{\'i}n and Keijzer, Hanneke M. and Ruijter, Barry J. and Bru{\~n}a, Ricardo and Tjepkema-Cloostermans, Marleen C. and Hofmeijer, Jeannette and van Putten, Michel J. A. M.},
  journal      = {Clinical Neurophysiology},
  year         = {2021},
  volume       = {132},
  number       = {6},
  pages        = {1312--1320},
  doi          = {10.1016/j.clinph.2021.02.011}
}

@article{turella2024goodoutcome,
  title        = {EEG for Good Outcome Prediction After Cardiac Arrest: A Multicentre Cohort Study},
  author       = {Turella, Sara and Dankiewicz, Josef and Ben-Hamouda, Nadia and Nilsen, K. B. and D{\"u}ring, Jonathan and Endisch, Christian and Engstr{\o}m, Maria and Fl{\"u}gel, Daniel and Gaspard, Nicolas and Grejs, Anna M. and Haenggi, Matthias and Haffey, Sarah and Imbach, Lukas and Johnsen, B. and Kemlink, David and Leithner, Christoph and Legriel, St{\'e}phane and Lindehammar, Helena and Mazzon, G. and Nielsen, Niklas and Rossetti, Andrea O. and others},
  journal      = {Resuscitation},
  year         = {2024},
  volume       = {202},
  pages        = {110319},
  doi          = {10.1016/j.resuscitation.2024.110319}
}
```

[1]: https://physionet.org/content/i-care/ "I-CARE: International Cardiac Arrest REsearch consortium Database v2.1"
[2]: https://portal.research.lu.se/sv/publications/standardized-eeg-interpretation-accurately-predicts-prognosis-aft/ "
        Standardized EEG interpretation accurately predicts prognosis after cardiac arrest
      \-  Lunds universitet"
[3]: https://research.utwente.nl/en/publications/early-eeg-contributes-to-multimodal-outcome-prediction-of-postano/ "
        Early EEG contributes to multimodal outcome prediction of postanoxic coma
      \-  University of Twente Research Information"
[4]: https://pubmed.ncbi.nlm.nih.gov/31155751/?utm_source=chatgpt.com "Early Electroencephalography for Outcome Prediction of ..."
[5]: https://www.sciencedirect.com/science/article/abs/pii/S138824572100078X "EEG functional connectivity contributes to outcome prediction of postanoxic coma - ScienceDirect"
[6]: https://portal.research.lu.se/en/publications/eeg-for-good-outcome-prediction-after-cardiac-arrest-a-multicentr/ "
        EEG for good outcome prediction after cardiac arrest: A multicentre cohort study
      \-  Lund University"
