Jag har gått igenom Resuscitations aktuella författarinformation och de fem Typst-filerna. Journalens krav finns här:

- https://www.resuscitationjournal.com/content/authorinfo
- Aktuell Elsevier-guide: https://www.sciencedirect.com/journal/resuscitation/publish/guide-for-authors

För denna artikel är **Original paper** den rimliga kategorin: maximalt 3 000 ord, 6 tabeller/illustrationer och 80 referenser. Abstract får vara högst 250 ord, och journalen kräver 1–6 engelska nyckelord.

## Föreslagen omformateringslista

### 1. Byt huvudram från NDT till klinisk EEG-fråga

- Gör den kliniska frågan till artikelns centrum:
  - om tidiga EEG-dynamiska egenskaper skiljer patienter med senare CPC 1 respektive CPC 5
  - om signalen finns redan tidigt efter EEG-start
  - om dynamiska EEG-mått tillför information utöver de begränsade variabler som finns i exporten
- Ta bort eller tona ned:
  - “NDT”
  - “neural geometry program”
  - “attractor”
  - “reachability” som centralt teoretiskt begrepp
  - formuleringar som antyder en ny generell teori om hjärnans dynamik
- Presentera NeuralManifoldDynamics som ett tekniskt analys- och feature-extraktionsramverk, inte som artikelns biologiska teori.
- Undvik formuleringar där geometriska mått låter som direkta mått på neural viabilitet, medvetande eller hjärnans “förmåga”.

Möjlig kliniskt orienterad titel:

> Early EEG dynamical features associated with neurological outcome after cardiac arrest: a pooled analysis of I-CARE data

### 2. Förenkla terminologin

Föreslagen första översättning av tekniska termer:

- `MNPS` → static EEG-state dispersion
- `MNJ` → local EEG dynamical expansion/deformation
- `tube_d_eff_median` → effective short-horizon dynamical dimensionality
- `persistence_*` → temporal persistence of short-horizon dynamics
- `tube_capture_gate_median` → transport/capture balance
- between-run MAD/IQR → between-recording temporal variability
- “broader reachable futures” → broader short-horizon dynamical variation
- “attractor stability” → recording-to-recording stability of the derived EEG features

De ursprungliga namnen kan behållas i S1/S2 som tekniska variabelnamn.

### 3. Skriv om abstractet till Resuscitation-format

Det nuvarande abstractet är för långt och för tekniskt. Det bör komprimeras till högst 250 ord och innehålla:

- **Aim**
- **Methods**
- **Results**
- **Conclusions**

Abstractet bör:

- börja med cardiac arrest och tidig EEG-bedömning
- ange I-CARE, kohortstorlek och CPC 1/CPC 5-kontrast
- beskriva måtten med kliniskt begriplig terminologi
- rapportera ett fåtal huvudresultat
- nämna AUROC-förbättringen men tydligt ange att baseline är feature-begränsad
- avsluta med att resultatet är en gruppnivåassociation, inte ett validerat prognostiskt verktyg
- undvika NDT/NMD-förkortningar om de inte är absolut nödvändiga
- inte innehålla referenser

### 4. Gör huvudmanuskriptet kortare och mer standardiserat

Resuscitation rekommenderar tydligt strukturen:

1. Introduction  
2. Materials and Methods  
3. Results  
4. Discussion  
5. Conclusions  
6. Conflict of Interest  
7. Acknowledgements  
8. References  
9. Figure legends

Det nuvarande manuskriptet bör därför omorganiseras från den mer essayistiska strukturen till en strikt IMRaD-struktur.

Följande delar bör flyttas ut ur huvudtexten eller kortas kraftigt:

- långa konceptuella förklaringar av NMD
- fullständiga matematiska definitioner
- detaljerade validerings- och QC-resonemang
- sena explorativa analyser
- långa “claim hierarchy”-boxar
- upprepade begränsningar
- fullständiga beskrivningar av alla sekundära mått

### 5. Begränsa huvudresultaten till ett fåtal kliniskt begripliga budskap

Huvudtexten bör sannolikt fokusera på:

- kohort och utfall
- ett primärt block med de fem reachability-måtten
- ett sekundärt block med Jacobian/local-dynamics-måtten
- tidig signal i `0–1 h`, men utan exakt peak-tidsanspråk
- between-recording variability som kompletterande resultat
- begränsad incremental validity

Undvik att ge alla mått samma status. Ange tydligt:

- primär familj
- sekundära jämförelsemått
- explorativa tids- och late-window-analyser

### 6. Tona ned resultatens biologiska tolkning

Föredra:

- “was associated with”
- “showed group-level separation”
- “is compatible with”
- “may reflect”
- “requires external validation”

Undvik:

- “retained broader neural geometry” som om detta vore direkt biologiskt observerat
- “preserved neural viability”
- “attractor stability” som etablerad mekanism
- “the brain retains broader future movement”
- “clinically useful early prognostic signal” utan extern validering

Diskussionen bör uttryckligen skilja mellan:

1. observerad statistisk association  
2. möjlig fysiologisk tolkning  
3. ej visad mekanism  
4. ej visad klinisk användbarhet  

### 7. Skärp endpoint- och prognostikbegränsningen

Detta bör vara en central, inte perifer, begränsning:

- CPC 5 är inte ett rent mått på neural viabilitet.
- WLST, tid till död, sederingsbelastning och vårdvägsfaktorer saknas.
- CPC 2–4 används inte i den primära kontrasten.
- Resultatet kan därför inte beskrivas som WLST-oberoende neuroprognostik.
- Studien är en recovery-linked association study, inte en bedside prognostic assay.

### 8. Förklara baseline-modellen mer neutralt

Nuvarande AUROC-jämförelse riskerar att övertyga läsaren om att geometrin överträffar klinisk praxis.

Ändra framing till:

- “restricted locked-export comparator”
- inte “clinical model”
- inte jämförelse mot standard-of-care
- tydlig lista över saknade variabler:
  - SSEP
  - pupillometri
  - motoriskt svar
  - NSE
  - neuroimaging
  - expertbedömning av EEG

`+0.062 AUROC` bör beskrivas som:

> incremental information beyond the limited variables retained in the locked export

inte som förbättring över klinisk prognostik.

### 9. Minska huvudmanuskriptets tabell- och figurantal

Original paper tillåter högst sex tabeller/illustrationer totalt i huvudartikeln. En möjlig prioritering är:

1. Kohort- och analysöversikt  
2. Primära fem dynamiska mått  
3. Huvudfigur med effektstorlekar  
4. Tidig-till-sen timprofil, tydligt markerad explorativ  
5. Between-recording variability  
6. Incremental validity  

Följande bör flyttas till supplement:

- detaljerade Jacobian-tabeller
- fullständiga timvisa tabeller
- late-window-analyser
- fullständig QC
- permutationer
- leave-one-site/subject-out-resultat
- matematiska definitioner
- gamla kontra korrigerade exportjämförelser

### 10. Gör supplementen till separata, tydliga onlinefiler

Elsevier kräver att supplement:

- citeras i huvudtexten
- laddas upp samtidigt
- har beskrivande captions
- är relevanta och korrekta
- inte förväntas bli omformaterade av produktionen

Föreslagen rollfördelning:

- **S1:** tekniska metoder, feature-definitioner, analyskontrakt
- **S2:** fullständiga resultat- och explorativa tabeller
- **S3:** QC, robusthet, permutationer och valideringskänslighet
- **S4:** klinisk tolkningsguide, eventuellt kortad och tydligt märkt som supplementary clinical interpretation

S4 bör inte upprepa huvudmanuskriptet utan fungera som en kort klinisk läsanvisning.

### 11. Kontrollera etiska uppgifter

Den nuvarande huvudartikeln behöver kompletteras med:

- etikgodkännande för den använda I-CARE-datan
- relevant etiknämnd/institution
- godkännandenummer eller referensnummer
- information om samtycke eller varför sekundäranalysen omfattas av datasetets godkännande
- dataskydd och anonymisering
- tydlig beskrivning av att detta är sekundäranalys av ett offentligt/åtkomligt dataset

Resuscitation kräver att humanstudier innehåller etik- och samtyckesinformation.

### 12. Ändra referensformatet

Nuvarande Typst använder författare-år-citationer. Resuscitation kräver:

- Vancouver-stil
- upphöjda numrerade citationer
- referenser i den ordning de först förekommer
- högst 80 referenser för Original paper
- högst sex författare listade; vid fler än sex: tre första följt av “et al.”
- NLM-förkortningar av tidskriftsnamn
- DOI där det är relevant
- datasetreferenser med repository, version och persistent identifier

Detta kräver sannolikt en separat bibliografisk konvertering, inte bara visuell Typst-justering.

### 13. Anpassa filformatet till Elsevier

Journalen anger att redigerbara källfiler ska lämnas in som:

- `.doc/.docx`, eller
- `.tex` för LaTeX

PDF räcker inte som källfil. Typst anges inte som accepterat källformat. Därför bör nästa steg vara att besluta om:

- konvertering till Word, eller
- konvertering till LaTeX med Elsevier-kompatibel struktur

Typst kan fortsatt användas internt för arbetsversioner, men submission-versionen bör sannolikt vara Word eller LaTeX.

### 14. Skapa separat title page

Title page ska innehålla:

- fullständig titel
- alla författare
- fullständiga affilieringar och postadress
- land
- e-postadress
- corresponding author
- eventuella permanenta adresser
- ordantal för manuskript och abstract

Den nuvarande inbyggda Typst-title-sidan bör därför inte antas vara submission-formatet.

### 15. Lägg till Highlights

Journalen uppmuntrar Highlights som separat redigerbar fil:

- 3–5 punkter
- maximalt 85 tecken per punkt
- korta, resultatfokuserade formuleringar
- inga NDT-begrepp om de inte behövs

### 16. Överväg graphical abstract

Det är frivilligt men möjligt. Den bör i så fall visa:

- cardiac arrest
- tidig EEG-registrering
- derived dynamical EEG features
- CPC 1/CPC 5 group-level association
- tydlig markering: “not validated for bedside prognostication”

Den bör inte visualisera “attractors” eller en mekanistisk hjärnmodell som om detta vore direkt uppmätt.

### 17. Hantera generativ AI korrekt

Nuvarande acknowledgements nämner AI-hjälp. Resuscitation kräver en separat deklaration om generativ AI när sådana verktyg har använts i manuskriptförberedelsen.

Det behöver finnas en sektion före referenserna med:

- vilka verktyg som användes
- för vilka ändamål
- att författaren kontrollerat och redigerat materialet
- att författaren tar fullt ansvar för manuskriptet

AI ska inte anges som författare.

### 18. Komplettera obligatoriska deklarationer

Före submission bör följande finnas som separata sektioner:

- Funding
- Conflict of Interest
- Author Contributions enligt CRediT
- Ethics approval
- Consent/data governance
- Data availability
- Code availability
- Declaration of generative AI use
- Acknowledgements

### 19. Förbättra data- och kodtillgängligheten

Data statement bör skilja mellan:

- underliggande I-CARE-data
- härledda resultatfiler
- kod
- frysta analyser
- Zenodo-version
- GitHub-repository

För datasetet bör referensen innehålla datasetnamn, version, repository, år och DOI/persistent identifier.

### 20. Språk- och tillgänglighetsrevision

- Skriv konsekvent på brittisk eller amerikansk engelska.
- Definiera alla förkortningar vid första användning.
- Undvik “coma patients” när “patients with post-cardiac-arrest coma” är mer precist.
- Använd “patients with good/poor neurological outcome” i stället för att låta CPC-grupperna representera hela biologiska tillstånd.
- Förklara figurer och förkortningar så att en intensivvårdsläkare kan förstå huvudbudskapet utan S1.
- Undvik att använda “neural geometry” i varje sektion; använd det endast där det verkligen behövs.

Det viktigaste redaktionella beslutet är alltså att göra artikeln till en **klinisk, metodologiskt transparent studie av tidiga EEG-dynamiska mått efter hjärtstopp**, där NMD/NDT endast är den tekniska bakgrunden. Resultaten bör presenteras som lovande men ännu icke-validerade gruppnivåassociationer, inte som en ny neuroprognostisk teori eller kliniskt färdig biomarkör.