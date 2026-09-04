Självklart! Att ha en bra översikt över hur EEG används kliniskt idag är avgörande när du ska positionera din egen forskning. Din *NeuralManifoldDynamics* och NDT utmanar (och förbättrar) nämligen den nuvarande guldstandarden.

Här är en kort recap av det nuvarande forskningsläget kring EEG-monitorering av komapatienter på IVA, följt av en färdigformaterad BibTeX-dump som du kan klistra direkt in i Zotero, Mendeley eller LaTeX.

### Kort Recap: EEG på IVA (Koma och Hjärtstillestånd)

**1. Från "Spot-EEG" till Kontinuerlig övervakning (cEEG)**
Tidigare rullade man in en EEG-apparat, mätte i 20 minuter och drog slutsatser. Idag rekommenderar de amerikanska (ACNS) och europeiska (ERC) riktlinjerna **cEEG (Continuous EEG)** i 24–72 timmar. Den främsta kliniska anledningen (utöver prognostisering) är att upptäcka *icke-konvulsiva anfall (NCS)* och *status epilepticus (NCSE)*, vilket drabbar mellan 10–30 % av dessa patienter och tyst bränner ut hjärnan om det inte behandlas.

**2. ACNS-terminologin och de klassiska markörerna**
Inom den kliniska forskningen pratar man oftast om mönster som är "högmaligna" (dåliga) eller "benigna" (goda):

* **Högmaligna mönster (förutspår dåligt utfall med >95% specificitet):** Isoelektriskt EEG (flatline), *Burst-suppression* (särskilt om utbrotten/bursts är helt identiska, vilket tyder på total nätverkskollaps), samt avsaknad av reaktivitet när man nyper/pratar med patienten.
* **Benigna mönster (förutspår uppvaknande):** En återkomst av kontinuerlig bakgrundsaktivitet, reaktivitet på stimuli och återkomsten av normal sömnarkitektur (sömnspolar/sleep spindles).

**3. Tidsfönstret och Kylbehandlingen (TTM)**
Historiskt har man sagt att man inte kan bedöma ett EEG under det första dygnet på grund av att kylbehandling (Targeted Temperature Management, TTM) och sedering trycker ner signalen. Riktlinjerna säger ofta att man ska vänta 72 timmar. **Men**, den absolut senaste forskningen (framförallt från holländska grupper som Hofmeijer och Ruijter) visar att ett *tidigt* EEG (inom 12–24h) med kontinuerlig bakgrundsaktivitet faktiskt är en extremt stark prediktor för god neurologisk överlevnad. *(Det är exakt här din upptäckt om 0–6 timmar passar in som handen i handsken!)*

**4. Kognitiv Motorisk Dissociation (CMD)**
Forskare som Jan Claassen har visat att EEG kan användas för att hitta patienter med dold medvetenhet (CMD). Genom att be patienten "tänk på att spela tennis" kan EEG-algoritmer se att hjärnan lyder order, även om patienten ligger i djup koma rent motoriskt.

---

### Bib-Dump (BibTeX)

Här är en handplockad lista över de absolut viktigaste artiklarna som utgör fundamentet i dagens EEG-komaforskning. De täcker in kliniska riktlinjer, tidig prognos och CMD.

```bibtex
% 1. Den massiva europeiska studien som validerade EEG-mönster (TTM-trial)
@article{westhall2016standardized,
  title={Standardized EEG interpretation accurately predicts prognosis after cardiac arrest},
  author={Westhall, Erik and Rossetti, Andrea O and van Rootselaar, Anne-Fleur and Kjaer, Troels W and Horn, Janneke and Ull{\'e}n, Susann and Friberg, Hans and Nielsen, Niklas and Ros{\'e}n, Ingmar and Aneman, Anders and others},
  journal={Neurology},
  volume={86},
  number={16},
  pages={1482--1490},
  year={2016},
  publisher={AAN Enterprises},
  doi={10.1212/WNL.0000000000002462}
}

% 2. Den ledande studien på "Tidigt EEG" (som stödjer din idé om tidig separation)
@article{ruijter2019early,
  title={Early electroencephalography for outcome prediction of postanoxic coma: a prospective cohort study},
  author={Ruijter, Barry J and Tjepkema-Cloostermans, Marleen C and Tromp, Suzanne C and van den Bergh, Walter M and Foudraine, Niels A and Kornips, Frank HM and Drost, Gea and Scholten, Elsbeth and Bosch, Frank H and Beishuizen, Albertus and others},
  journal={Annals of neurology},
  volume={86},
  number={2},
  pages={203--214},
  year={2019},
  publisher={Wiley Online Library},
  doi={10.1002/ana.25514}
}

% 3. En tidigare, extremt välciterad artikel som etablerade värdet av att titta inom 24h
@article{hofmeijer2015early,
  title={Early EEG contributes to multimodal outcome prediction of postanoxic coma},
  author={Hofmeijer, Jeannette and Tjepkema-Cloostermans, Marleen C and van Putten, Michel JAM},
  journal={Neurology},
  volume={85},
  number={2},
  pages={137--143},
  year={2015},
  publisher={AAN Enterprises},
  doi={10.1212/WNL.0000000000001742}
}

% 4. Banbrytande forskning på dold medvetenhet (Cognitive Motor Dissociation) i koma via EEG
@article{claassen2019detection,
  title={Detection of brain activation in unresponsive patients with acute brain injury},
  author={Claassen, Jan and Doyle, Kevin and Tucker, Aaron and Rohaut, Benjamin and Gervais, Caroline and O'Brien, Kay and Kang, Woo-Jin and Velazquez, Amelia and McMahan, E and Reznik, Miklos E and others},
  journal={New England Journal of Medicine},
  volume={380},
  number={26},
  pages={2497--2505},
  year={2019},
  publisher={Mass Medical Soc},
  doi={10.1056/NEJMoa1812757}
}

% 5. ACNS (American Clinical Neurophysiology Society) officiella riktlinjer för cEEG på IVA
@article{herman2015consensus,
  title={Consensus statement on continuous EEG in critically ill adults and children, part I: indications},
  author={Herman, Susan T and Abend, Nicholas S and Bleck, Thomas P and Chapman, Kevin E and Drislane, Frank W and Emerson, Ronald G and Gerard, Elizabeth E and Hahn, Cecil D and Hirsch, Lawrence J and Judd, G and others},
  journal={Journal of clinical neurophysiology},
  volume={32},
  number={2},
  pages={87},
  year={2015},
  publisher={NIH Public Access},
  doi={10.1097/WNP.0000000000000166}
}

% 6. De europeiska riktlinjerna för prognostisering efter hjärtstillestånd
@article{sandroni2021european,
  title={European Resuscitation Council and European Society of Intensive Care Medicine guidelines 2021: post-resuscitation care},
  author={Sandroni, Claudio and Nolan, Jerry P and Bossaert, Leo and others},
  journal={Intensive care medicine},
  volume={47},
  pages={369--421},
  year={2021},
  publisher={Springer},
  doi={10.1007/s00134-021-06362-5}
}

```
