## Fynd

- **Major: abstractet är för packat och bär nästan hela supplementlogiken i ett stycke.** Det frontlastar kohortbokföring, overlap-audit, flera metricfamiljer, flera `d/p/q`, hourly localization, nulltest och prediktionsresultat. Effekten blir att huvudpoängen blir mindre tydlig än den egentligen är.

```24:26:articles/CLINICAL/comatose_ndt/Recovery-Linked Neural Geometry After Cardiac-Arrest Coma.typ
abstract: [
  Early electroencephalography (EEG) after cardiac arrest may encode not only static severity but also the geometry of short-horizon neural dynamics. We analyzed harmonized NeuroComBat exports ...
  The pooled bundle contains `298` analyzable patients ... across `4667` H5 runs ... `tube_d_eff_median` ... Cohen's `d = 0.638`, BH-FDR `q = 1.23e-05` ...
  ... adding the five-feature geometry layer ... improved `AUROC` from `0.595` to `0.687` ...
]
```

  För en extern reviewer blir detta lätt mer “resultatdump” än “abstract”. Det finns ett starkt budskap här, men det drunknar i detaljnivån. Er `author-summary` är faktiskt närmare rätt tonläge än nuvarande abstract.

- **Major: `MNJ 9D` riskerar att väcka statistisk misstanke om ni inte förklarar skillnaden mellan liten `d` och mycket liten `p`.** Det behöver inte vara fel, men en reviewer kommer sannolikt att stanna upp här.

```145:152:articles/CLINICAL/comatose_ndt/Recovery-Linked Neural Geometry After Cardiac-Arrest Coma.typ
table.header([*Family / metric*], [*Interpretation*], [*`part1` `d`*], [*`part2` `d`*], [*Pooled `d`*], [*Pooled `p`*]),
[`MNPS 3D / m_std`], [lower pooled `3D` spread in `CPC 1`], [`-0.303`], [`-0.501`], [`-0.409`], [`0.00553`],
[`MNPS 9D / m_e_std`], [lower pooled `9D` spread in `CPC 1`], [`-0.335`], [`-0.548`], [`-0.436`], [`9.05e-05`],
[`Reachability / tube_d_eff_median`], [broader reachability dimensionality in `CPC 1`], [`+0.696`], [`+0.589`], [`+0.638`], [`1.02e-06`],
[`MNJ 3D / spectral_radius_median`], [lower dominant local expansion in `CPC 1`], [`-0.447`], [`-0.712`], [`-0.536`], [`1.70e-08`],
[`MNJ 3D / frobenius_norm_median`], [lower overall local deformation in `CPC 1`], [`-0.554`], [`-0.515`], [`-0.536`], [`1.14e-06`],
[`MNJ 9D / spectral_radius_median`], [supportive repaired `9D` expansion marker], [`-0.183`], [`-0.736`], [`-0.138`], [`2.75e-09`],
[`MNJ 9D / frobenius_norm_median`], [supportive repaired `9D` deformation scale], [`-0.175`], [`-0.525`], [`-0.126`], [`5.23e-05`],
```

  Jag hade antingen lagt in en kort förklaring i `Results`/`S2`, eller dubbelkollat att `d` och `p` verkligen kommer från samma analysnivå och att skillnaden inte ser ut som en artefakt av definitionerna.

- **Major: begränsningsramen är bra, men den kommer lite sent i den narrativa prioriteringen.** Manusets styrka är att ni faktiskt är ovanligt disciplinerade kring claim boundaries, men i abstractet och delvis i resultaten kommer den ramen efter många positiva signaler.

```119:123:articles/CLINICAL/comatose_ndt/Recovery-Linked Neural Geometry After Cardiac-Arrest Coma.typ
The endpoint should be interpreted as an extreme-outcome association contrast rather than as a neural-viability label. `CPC 5` can absorb mortality-process, systemic illness, treatment-limitation, and site-pathway effects in addition to brain injury severity. Because WLST, time-to-death, and sedation burden are unavailable in the manuscript-facing export, this analysis cannot separate recovery-linked geometry from those clinical pathway effects and should not be read as an early neuroprognostication study.@rajajee2023neuroprognostication, @sandroni2021european

#netn-box(title: [ComBat contract and validation boundary])[
  The article-facing analysis did not fit NeuroComBat inside the manuscript code. ...
```

  Jag skulle flytta upp denna gräns tidigare i abstractet, helst före eller direkt efter prediktionsdelen, så att läsaren inte överläser det som en biomarkör- eller prognostikstudie.

- **Medium: språket är ibland mer internt/audit-orienterat än journal-orienterat.** Formuleringar som `article-facing`, `discovery-linked`, `verification-side cohort`, `inferential contract` och `fixed upstream preprocessing layer` är precisa för intern provenance, men de låter inte helt naturliga i en extern submission. Det gör texten lite mer “repo-aware” än “reviewer-friendly”. Samma sak gäller viss upprepning av huvudhierarkin: “layered story”, “`MNJ 9D` supportive not dominant”, och “`3_4h` exploratory not definitive” återkommer flera gånger i `Introduction`, `Results`, `Discussion`, `Limitations` och `Conclusion`. Budskapet är bra, men texten kan stramas 10-15 % utan att förlora disciplinen.

## Förslag på omskrivet abstract

Nedan är en mer journalmässig och mindre siffertung version på engelska, avsiktligt nedskalad i numerisk detalj men trogen manusets claim boundaries:

```text
Early electroencephalography (EEG) after cardiac arrest may capture not only static severity but also the short-horizon geometry of neural dynamics. We analyzed harmonized I-CARE exports from two non-overlapping cohorts and asked whether patients with good neurological outcome (CPC 1) and poor outcome (CPC 5) differed during the first 12 h after EEG anchor. Across 298 analyzable patients, later good outcome was associated with broader short-horizon reachability and lower local Jacobian expansion. Reachability effective dimensionality provided the clearest pooled separation, while classical spread measures and 3D Jacobian summaries offered convergent support. Repaired 9D Jacobian measures remained informative but were weaker after pooling and are best interpreted as supportive rather than leading evidence. Exploratory hourly analyses suggested greater separation around 3-4 h after anchor, but circular-shift null analyses did not support a strong claim of precise peak timing. Adding a five-feature geometry layer to the restricted clinical+qEEG feature set modestly improved internal prediction, consistent with complementary value rather than a standalone biomarker. Because withdrawal-of-life-sustaining-therapy, time-to-death, and sedation annotations were unavailable, the CPC 1 versus CPC 5 contrast should be interpreted as recovery-linked geometry rather than a pure assay of neural viability. The pooled analysis therefore supports a layered view of early post-arrest EEG geometry within clear endpoint, timing, and validation boundaries.
```

Om du vill göra det ännu skarpare skulle jag överväga en version som bara behåller **en** siffra i abstractet: `n = 298`.

## Öppna frågor

- Vilken tidskrift siktar du på? För en mer klinisk tidskrift skulle jag förenkla terminologin ännu ett steg.
- Finns en hård ordgräns för abstractet? Det styr hur mycket av prediktionsdelen som bör vara kvar.
- Vill du att prediktionsdelen ska finnas i abstractet alls, eller räcker det att den finns i resultaten och slutsatsen?

## Kort helhetsbedömning

Det här är ett starkare och mer moget manus än många interna forskningsutkast, främst för att du redan har en tydlig claim hierarchy och ovanligt bra begränsningsspråk. Den viktigaste förbättringen nu är inte mer analys, utan redaktionell fokusering: lättare abstract, tydligare förklaring av `MNJ 9D`-tabellen, och lite mindre intern processvokabulär.

Om du vill kan jag ta nästa steg och skriva in en stramare abstractversion direkt i `Recovery-Linked Neural Geometry After Cardiac-Arrest Coma.typ`, plus putsa 3-5 formuleringar i `Introduction`/`Methods` så att tonen blir mer submission-klar.