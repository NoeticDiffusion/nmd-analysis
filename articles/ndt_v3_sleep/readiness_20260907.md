# Epoch-tabell och intern peer review

2026-09-07. **PASS för verifierad epoch-export på H:. BLOCKED för integration
i artikelmappen på J:, som fortfarande har 0 byte ledigt.**

## Genomfört

Luna-subagenterna byggde exportören, dokumenterade källans tidsstöd, skrev
oberoende tester och utförde första kod- och körningsgranskningen.
Koordinatorn kontrollerade därefter resultatet direkt mot källfilen.

- Ny körbar `src/epoch_support.py` och en aktiv config som låser källfilens
  sökväg och SHA256. Ingen ny ingest eller ny mätdefinition.
- En Parquet-tabell med **1 068 rader och 31 kolumner**: MNPS 3D/9D,
  epoch-ID, tider, fönstergränser, stadiekoder/etiketter, separata
  finitetsflaggor och fyra ursprungliga QC-masker.
- **39 passerade regressionstester**, inklusive 14 nya tester. Syntetiska
  fall täcker bland annat okända etiketter, koordinat-NaN, saknade masker,
  felaktiga maskformer/värden och tidsluckor.
- Exakt värdejämförelse mot HDF5 passerar för koordinater, ID, tidsuppgifter,
  stadiekoder och samtliga fyra masker. Källfilen är oförändrad; config-,
  registrerade kod- och tabellhashar stämmer.
- Den tidigare accepterade artikelpilotens manifest och 16 tabeller är
  också oförändrade enligt en separat integritetskontroll.

Körningen är [epoch_support_20260907](results/epoch_support_20260907).
Se [intern review](peer_review/02_epoch_support_review.md),
[koordinatorns maskinläsbara kontroll](handover/20260907_epoch_coordinator_validation.json)
och [tidsstödskontraktet](support_contract.md).

## Vad resultatet tillåter

Vi har nu ett verifierat underlag på epochnivå för den fortsatta
sömnstudieutvecklingen. Nio stadieetiketter är okända och behålls som sådana.
Finita koordinater och registrerade QC-masker hålls isär från vetenskaplig
giltighet. Saknade masker blir explicit okända, inte nollor. Masker med fel
form eller otillåtna värden stoppas.

Fönsteretiketternas anpassning bevisar inte fullständigt filterstöd eller
stadierenhet i diffusionens grannskap. Dessa fält förblir `not_assessed`.
Q/W_Q har inte kopierats till epoch-rader. PPG-fallbacken i e_m och saknade
ankaridentifierare finns kvar som proveniensbegränsningar. Inga kontraster,
p-värden eller biologiska slutsatser har producerats.

## Återstående arbete

Först behöver de granskade filerna kopieras till
`J:/repos/nmd-analysis/articles/ndt_v3_sleep` när J: får skrivutrymme.
`handover/integration_manifest.json` listar filerna och deras hashvärden.
Tidigare data och resultat har inte raderats. Tre nya J:-filer blev tomma
vid misslyckade skrivförsök. Efter kontroll av exakt sökväg och noll filstorlek
togs endast dessa tomma filer bort; de granskade versionerna finns på H:.

Därefter är nästa analytiska steg att låsa hur övergångsfönster och okänt
filter-/grannskapsstöd ska hanteras, och skilja en jämförelse av global
geometri vid olika stadier från separat stadiebetingad skattning. Sedan kan
vi skapa beskrivande figurer för utvecklingspiloten och förhandsbestämma
kontraster inför ett separat deltagarbaserat kohortprotokoll. Ingen
omställning av skattarna behövs för att slutföra denna exportintegration.
