Below is a **first reference map** for `psychosis_first_time_episode.txt`. Your draft’s core claim is not “FEP has an EEG signature” in general, but that **cohort-anchored, medication-stratified resting EEG geometry** exposes different separation layers across ds003944 and ds003947: static/stratified *m*-axis displacement in ds003944 and dynamic *m_delta* disturbance in ds003947. That framing is supported by the draft itself, which uses two resting-state FEP EEG cohorts, splits FEP by CPZ_at_scan, and reports five paper-facing blocks: 3D MNPS, 9D MNPS, 3D MNJ, 9D MNJ, and block-MNJ. 

## Best references to add, and where

### 1. Add to the **Introduction**, first paragraph: schizophrenia/psychosis as dysconnectivity

Use these to justify why a geometry/dynamics framework is relevant at all.

Stephan et al. (2009) is the strongest conceptual anchor: it reviews schizophrenia as abnormal functional integration and frames dysconnectivity in terms of NMDAR-mediated synaptic plasticity and neuromodulatory regulation.  Pettersson-Yeo et al. (2011) is useful as a broad structural/functional connectivity review across illness stages, emphasizing that connectivity reductions, especially frontal, are common but heterogeneous. ([ScienceDirect][1])

**Suggested insertion:**

> Psychosis and schizophrenia have long been framed as disorders of disturbed functional integration rather than focal regional abnormality alone. The dysconnection hypothesis links symptoms to abnormal interactions among distributed neural systems, with later formulations emphasizing abnormal synaptic plasticity and NMDAR-mediated modulation. Resting EEG/MEG/fMRI therefore provide a natural empirical surface for testing whether first-episode psychosis is better described by altered state-space geometry and local dynamics than by a single scalar abnormality.

### 2. Add to **Introduction / EEG background**: resting EEG spectral abnormalities in first-episode schizophrenia/FEP

Sponheim et al. (1994) is an older but very relevant baseline for resting EEG in first-episode and chronic schizophrenia: more delta/theta and less alpha, with no major difference between first-episode and chronic groups, suggesting that some spectral abnormalities are present early. ([Experts@Minnesota][2]) Renaldi et al. (2019) is a directly FEP-focused resting EEG prognosis paper: frontal/posterior delta power differed in FEP and predicted 1-year symptom/function changes. ([KCI][3])

**Suggested insertion:**

> Resting EEG studies already suggest that psychosis-related abnormalities are present near illness onset. Classical qEEG work found increased low-frequency activity and reduced alpha in first-episode and chronic schizophrenia, while later FEP work linked resting delta power to 1-year symptomatic and functional outcome.

### 3. Add to **Dataset / prior use of ds003944 and ds003947**

Your two datasets have already been reused in EEG classification work. Gengeç Benli et al. (2023) explicitly used the two public FEP datasets, with 78 FEP and 60 controls across both, 5 min resting-state EEG, 64-channel acquisition with the first 60 EEG channels analyzed. ([MDPI][4]) This supports your dataset description and helps reviewers see that these OpenNeuro cohorts are not obscure one-off files.

Also cite Phalen et al. (2020), because it is probably the most important “source-neighbor” for your work: it used network analysis of resting alpha-band activity and found abnormal cortical alpha networks in first-episode schizophrenia-spectrum psychosis. ([ScienceDirect][5])

**Suggested insertion:**

> The same OpenNeuro FEP resting EEG cohorts have recently been used for automated EEG classification and sub-band feature extraction, while source/network analyses of resting alpha activity have identified abnormal cortical alpha networks in first-episode schizophrenia-spectrum psychosis. The present study differs by treating these recordings as trajectories in a shared cohort-anchored coordinate system rather than as independent classification inputs.

### 4. Add to **Methods / medication stratification rationale**

This is essential, because your paper’s strongest design choice is medication stratification. Ozaki et al. (2021) directly supports the concern: antipsychotic monotherapy was associated with increased theta/alpha/beta power, and CPZ-equivalent dose was positively associated with theta power. ([KCI][6]) For fMRI, Zhong et al. (2024) supports the broader claim that antipsychotic treatment can alter dynamic resting-state brain measures in first-episode schizophrenia. ([Frontiers][7])

**Suggested insertion:**

> Medication state was treated as a primary stratification variable rather than a nuisance-only covariate because antipsychotic exposure can alter resting neurophysiology. Quantitative EEG work shows dose- and drug-specific spectral effects, including CPZ-equivalent associations with theta power, and longitudinal fMRI work indicates that antipsychotic treatment can change dynamic regional activity stability in first-episode schizophrenia.

### 5. Add to **Discussion / oscillatory interpretation of m-axis and m-dynamics**

For oscillatory mechanisms, use the gamma/ASSR/MEG literature carefully. Grent-’t-Jong et al. (2018) links MEG resting gamma alterations across CHR, FEP, and chronic schizophrenia to E/I-balance and Glx/GABA measures. ([eLife][8]) Zouaoui et al. (2023) gives an updated ASSR meta-analysis showing moderate 40 Hz gamma reductions in schizophrenia and moderate-to-large effects in first-episode psychosis for 40 Hz ASSR power and phase. ([MDPI][9])

**Suggested insertion:**

> The m-family effects should not be read as a simple arousal axis. A more defensible interpretation is that they reflect altered rhythm-weighted coordination and oscillatory organization. This interpretation is consistent with MEG and ASSR literature showing stage-sensitive gamma abnormalities and altered E/I-balance signatures in early psychosis.

### 6. Add to **Discussion / fMRI bridge**

Even though your paper is EEG-based, it will benefit from a short bridge to rs-fMRI dysconnectivity in early psychosis. Alonso-Solís et al. (2012) found altered default-network resting-state connectivity in first-episode psychosis. ([PMC][10]) Jensen et al. (2024) is a strong recent whole-brain rs-fMRI reference: 117 FEP/early psychosis participants and 130 controls, with aberrant cortical–subcortical–cerebellar functional network connectivity. ([ScienceDirect][11]) Huang et al. (2022) supports salience-network framing, including schizophrenia-specific SN connectivity differences. ([Nature][12])

**Suggested insertion:**

> The EEG findings fit within a broader multimodal dysconnectivity literature. Resting fMRI studies in first-episode and early psychosis report default-mode, salience-network, cortical–subcortical, temporal, thalamic, and cerebellar connectivity abnormalities, suggesting that the EEG cohort-anchor results may be one modality-specific expression of a broader network-level disturbance.

### 7. Add to **Limitations**

Use MMN literature to show that not all early-psychosis electrophysiology is uniform or straightforward. Tada et al. (2019) reviews MMN as a robust schizophrenia biomarker with relevance to early psychosis, function, and translational animal work. ([ScienceDirect][13]) Haigh et al. (2017) specifically notes debate about whether MMN is reliably reduced in first-episode schizophrenia, which helps justify your cautious “layer shift, not universal feature” conclusion. ([Sage Journals][14])

**Suggested insertion:**

> The absence of a single universal feature across ds003944 and ds003947 should not be treated as a failure by default. Early-psychosis electrophysiology is heterogeneous: even for well-studied markers such as MMN, the literature distinguishes robust chronic schizophrenia effects from more debated first-episode reductions. The present results should therefore be interpreted as cohort- and medication-sensitive geometry rather than as a universal FEP biomarker.

---

## Prioritized reference list

1. **Stephan et al. 2009** — foundational dysconnection hypothesis / mechanistic framing.
2. **Pettersson-Yeo et al. 2011** — broad connectivity review across schizophrenia stages.
3. **Sponheim et al. 1994** — classic resting EEG in first-episode and chronic schizophrenia.
4. **Renaldi et al. 2019** — resting EEG spectral power as 1-year prognostic marker in FEP.
5. **Phalen et al. 2020** — resting alpha network abnormalities in first-episode schizophrenia-spectrum.
6. **Gengeç Benli et al. 2023** — direct prior ML use of ds003944/ds003947 EEG.
7. **Redwan et al. 2024** — PSD-based classification of FEP using resting EEG.
8. **Ozaki et al. 2021** — antipsychotic effects on qEEG and CPZ-equivalent association.
9. **Grent-’t-Jong et al. 2018** — MEG resting gamma and E/I balance across illness stages.
10. **Zouaoui et al. 2023** — ASSR meta-analysis, including early psychosis.
11. **Tada et al. 2019** — MMN as early-psychosis translational biomarker.
12. **Haigh et al. 2017** — MMN in first-episode schizophrenia meta-analysis.
13. **Alonso-Solís et al. 2012** — default network rs-fMRI in FEP.
14. **Jensen et al. 2024** — whole-brain rs-fMRI FEP/early psychosis functional network connectivity.
15. **Huang et al. 2022** — salience-network rs-fMRI in schizophrenia/depression.
16. **Zhong et al. 2024** — antipsychotic treatment and dynamic fMRI instability in FES.

## BibTeX-style dump

```bibtex
@article{stephan2009dysconnection,
  title={Dysconnection in schizophrenia: From abnormal synaptic plasticity to failures of self-monitoring},
  author={Stephan, Klaas E. and Friston, Karl J. and Frith, Chris D.},
  journal={Schizophrenia Bulletin},
  volume={35},
  number={3},
  pages={509--527},
  year={2009},
  doi={10.1093/schbul/sbn176}
}

@article{petterssonyeo2011dysconnectivity,
  title={Dysconnectivity in schizophrenia: Where are we now?},
  author={Pettersson-Yeo, William and Allen, Paul and Benetti, Stefania and McGuire, Philip and Mechelli, Andrea},
  journal={Neuroscience and Biobehavioral Reviews},
  volume={35},
  number={5},
  pages={1110--1124},
  year={2011},
  doi={10.1016/j.neubiorev.2010.11.004}
}

@article{sponheim1994resting,
  title={Resting EEG in first-episode and chronic schizophrenia},
  author={Sponheim, Scott R. and Clementz, Brett A. and Iacono, William G. and Beiser, Morton},
  journal={Psychophysiology},
  volume={31},
  number={1},
  pages={37--43},
  year={1994},
  doi={10.1111/j.1469-8986.1994.tb01023.x}
}

@article{renaldi2019fep_eeg,
  title={Predicting symptomatic and functional improvements over 1 year in patients with first-episode psychosis using resting-state electroencephalography},
  author={Renaldi, Rinvil and Kim, Minah and Lee, Tak Hyung and Kwak, Yoo Bin and Tanra, Andi J. and Kwon, Jun Soo},
  journal={Psychiatry Investigation},
  volume={16},
  number={9},
  pages={695--703},
  year={2019},
  doi={10.30773/pi.2019.06.20.1}
}

@article{phalen2020alpha,
  title={Non-negative matrix factorization reveals resting-state cortical alpha network abnormalities in the first-episode schizophrenia spectrum},
  author={Phalen, Henry and Coffman, Brian A. and Ghuman, Avniel and Sejdić, Ervin and Salisbury, Dean F.},
  journal={Biological Psychiatry: Cognitive Neuroscience and Neuroimaging},
  volume={5},
  number={10},
  pages={961--970},
  year={2020},
  doi={10.1016/j.bpsc.2019.06.010}
}

@article{gengecbenli2023cissa,
  title={Classification of first-episode psychosis with EEG signals: ciSSA and machine learning approach},
  author={Gengeç Benli, Ş. and others},
  journal={Biomedicines},
  volume={11},
  number={12},
  pages={3223},
  year={2023},
  doi={10.3390/biomedicines11123223}
}

@article{redwan2024psd,
  title={Power spectral density-based resting-state EEG classification of first-episode psychosis},
  author={Redwan, Sadi Md. and Uddin, Md Palash and Ulhaq, Anwaar and Sharif, Muhammad Imran and Krishnamoorthy, Govind},
  journal={Scientific Reports},
  volume={14},
  pages={15154},
  year={2024},
  doi={10.1038/s41598-024-66110-0}
}

@article{ozaki2021qEEG_antipsychotics,
  title={Quantitative resting state electroencephalography in patients with schizophrenia spectrum disorders treated with strict monotherapy using atypical antipsychotics},
  author={Ozaki, Takashi and Toyomaki, Atsuhito and Hashimoto, Naoki and Kusumi, Ichiro},
  journal={Clinical Psychopharmacology and Neuroscience},
  volume={19},
  number={2},
  pages={313--322},
  year={2021},
  doi={10.9758/cpn.2021.19.2.313}
}

@article{grent2018gamma,
  title={Resting-state gamma-band power alterations in schizophrenia reveal E/I-balance abnormalities across illness stages},
  author={Grent-'t-Jong, T. and others},
  journal={eLife},
  volume={7},
  pages={e37799},
  year={2018},
  doi={10.7554/eLife.37799}
}

@article{zouaoui2023assr,
  title={Auditory steady-state responses in schizophrenia: An updated meta-analysis},
  author={Zouaoui, I. and others},
  journal={Brain Sciences},
  volume={13},
  number={12},
  pages={1722},
  year={2023},
  doi={10.3390/brainsci13121722}
}

@article{tada2019mmn,
  title={Mismatch negativity (MMN) as a tool for translational investigations into early psychosis: A review},
  author={Tada, Mariko and Kirihara, Ken and Koshiyama, Daisuke and Fujioka, Makoto and Usui, Kiyoto and Uka, Takanori and Kasai, Kiyoto},
  journal={International Journal of Psychophysiology},
  volume={145},
  pages={5--14},
  year={2019},
  doi={10.1016/j.ijpsycho.2019.02.009}
}

@article{haigh2017mmn_fes,
  title={Mismatch negativity in first-episode schizophrenia: A meta-analysis},
  author={Haigh, Sarah M. and Coffman, Brian A. and Salisbury, Dean F.},
  journal={Clinical EEG and Neuroscience},
  volume={48},
  number={1},
  pages={3--10},
  year={2017},
  doi={10.1177/1550059416645980}
}

@article{salisbury2002mmn,
  title={Mismatch negativity in chronic schizophrenia and first-episode schizophrenia},
  author={Salisbury, Dean F. and Shenton, Martha E. and Griggs, Christine B. and Bonner-Jackson, Aaron and McCarley, Robert W.},
  journal={Archives of General Psychiatry},
  volume={59},
  number={8},
  pages={686--694},
  year={2002},
  doi={10.1001/archpsyc.59.8.686}
}

@article{alonsosolis2012default,
  title={Altered default network resting state functional connectivity in patients with a first episode of psychosis},
  author={Alonso-Solís, A. and others},
  journal={Schizophrenia Research},
  volume={139},
  number={1--3},
  pages={13--18},
  year={2012},
  doi={10.1016/j.schres.2012.05.005}
}

@article{argyelan2015rsfmri,
  title={Abnormal resting state fMRI activity predicts processing speed deficits in first-episode psychosis},
  author={Argyelan, Miklos and Gallego, Juan A. and Robinson, Delbert G. and others},
  journal={Neuropsychopharmacology},
  volume={40},
  pages={1631--1639},
  year={2015},
  doi={10.1038/npp.2015.7}
}

@article{jensen2024neuromark,
  title={A whole-brain neuromark resting-state fMRI analysis of first-episode and early psychosis: Evidence of aberrant cortical-subcortical-cerebellar functional circuitry},
  author={Jensen, K. M. and others},
  journal={NeuroImage: Clinical},
  volume={42},
  pages={103623},
  year={2024},
  doi={10.1016/j.nicl.2024.103623}
}

@article{huang2022salience,
  title={Resting-state functional connectivity of salience network in schizophrenia and depression},
  author={Huang, Huan and Chen, Cheng and Rong, Bei and Wan, Qirong and Chen, Jingang and Liu, Zhongchun and Zhou, Yuan and Wang, Gaohua and Wang, Huiling},
  journal={Scientific Reports},
  volume={12},
  pages={11204},
  year={2022},
  doi={10.1038/s41598-022-15489-9}
}

@article{zhong2024antipsychotic_fmri,
  title={Effects of long-term antipsychotic medication on brain instability in first-episode schizophrenia patients: A resting-state fMRI study},
  author={Zhong, Maoxing and Liu, Zhening and Wang, Feiwen and Yang, Jun and Chen, Eric and Lee, Edwin and Wu, Guowei and Yang, Jie},
  journal={Frontiers in Pharmacology},
  volume={15},
  pages={1387123},
  year={2024},
  doi={10.3389/fphar.2024.1387123}
}
```

[1]: https://www.sciencedirect.com/science/article/abs/pii/S0149763410001855 "Dysconnectivity in schizophrenia: Where are we now? - ScienceDirect"
[2]: https://experts.umn.edu/en/publications/resting-eeg-in-firstepisode-and-chronic-schizophrenia/ "
        Resting EEG in first‐episode and chronic schizophrenia
      \-  Experts@Minnesota"
[3]: https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART002504333 "Predicting Symptomatic and Functional Improvements over 1 Year in Patients with First-Episode Psychosis Using Resting-State Electroencephalography"
[4]: https://www.mdpi.com/2227-9059/11/12/3223 "Classification of First-Episode Psychosis with EEG Signals: ciSSA and Machine Learning Approach | MDPI"
[5]: https://www.sciencedirect.com/science/article/abs/pii/S2451902219301752?utm_source=chatgpt.com "Non-negative Matrix Factorization Reveals Resting-State ..."
[6]: https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART002718181 "Quantitative Resting State Electroencephalography in Patients with Schizophrenia Spectrum Disorders Treated with Strict Monotherapy Using Atypical Antipsychotics"
[7]: https://www.frontiersin.org/journals/pharmacology/articles/10.3389/fphar.2024.1387123/full "Frontiers | Effects of long-term antipsychotic medication on brain instability in first-episode schizophrenia patients: a resting-state fMRI study"
[8]: https://elifesciences.org/articles/37799 "Resting-state gamma-band power alterations in schizophrenia reveal E/I-balance abnormalities across illness-stages | eLife"
[9]: https://www.mdpi.com/2076-3425/13/12/1722 "Auditory Steady-State Responses in Schizophrenia: An Updated Meta-Analysis | MDPI"
[10]: https://pmc.ncbi.nlm.nih.gov/articles/PMC3393844/?utm_source=chatgpt.com "Altered Default Network Resting State Functional Connectivity ..."
[11]: https://www.sciencedirect.com/science/article/pii/S2213158224000238 "A whole-brain neuromark resting-state fMRI analysis of first-episode and early psychosis: Evidence of aberrant cortical-subcortical-cerebellar functional circuitry - ScienceDirect"
[12]: https://www.nature.com/articles/s41598-022-15489-9 "Resting-state functional connectivity of salience network in schizophrenia and depression | Scientific Reports"
[13]: https://www.sciencedirect.com/science/article/pii/S0167876018310274 "Mismatch negativity (MMN) as a tool for translational investigations into early psychosis: A review - ScienceDirect"
[14]: https://journals.sagepub.com/doi/abs/10.1177/1550059416645980?utm_source=chatgpt.com "Mismatch Negativity in First-Episode Schizophrenia"
