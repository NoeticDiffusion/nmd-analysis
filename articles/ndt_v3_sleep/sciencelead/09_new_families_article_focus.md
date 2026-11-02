# Artikelns huvudspår: nya dynamiska mätvärdesfamiljer

Koordinatorbeslut: **PASS för inventering och genomförbar analysplan**. Ingen ny abskissa-/diffusionskontrast eller empirisk driftkvalificering har beräknats i detta steg.

| Huvudfråga | Första analys | Läget |
|---|---|---|
| Lokal tillväxt och reaktivitet | Spektral/numerisk abskissa och reaktivitetsgap, 3D och 9D separat, kopplade till respektive centrums sömnetikett | Kan köras från befintliga filer |
| Diffusionsgeometri | D_total, d_diff (effektiv dimension) och c_diff (koncentration) i befintlig 3D-tensor, kopplade till frågepunktens etikett | Kan köras från befintliga filer |
| Drift och drift–diffusionskoppling | Befintlig cross-fit-kandidat och etablerade kontrollförsök, med separata utvärderingsinkrement | Avgränsad uppföljning; nuvarande A_bD/R_b_over_a är inte testbara |

Sub-99 har 1066 Jacobianrader i båda representationerna och 1068 diffusionsrader. Sub-1 har 913 Jacobianrader i 3D, 856 i 9D och 915 diffusionsrader. Centrumindex styr etikettkopplingen; serierna får inte längdmatchas genom kopiering eller padding. Kanonisk 9D-diffusion saknas i dessa filer.

Jag har oberoende räknat om abskissorna och reaktivitetsgapet ur lagrade Jacobianer, samt kontrollerat diffusionstensorernas spår och identiska alias. Kontrollerna passerade (rtol 2e-6, atol 1e-8), med oförändrade källhashar. Detta verifierar lagrade definitioner, inte biologisk eller stadieintrinsisk giltighet. Antal vetenskapligt kvalificerade rader är null.

Nästa konkreta leverans är en gemensam E1/E2-körning: två figurgrupper, kompletta måttabeller per etikett med medianer och kvartiler, samt N2-minus-Wake för alla förvalda mått inom varje inspelning. Ingen ny ingest, deltagarutökning eller per-stadium-anpassning behövs. FTR:s recording-horizon och Q/WQ:s inspelningsnivå hålls utanför första leveransen.

m/e-källproblemet dokumenteras där det påverkar tolkningen men blockerar inte de deskriptiva familjeanalyserna. Etikettassociationer av befintliga globala skattningar ska samtidigt inte kallas stadieintrinsisk dynamik. Driftkandidaten återanvänder befintlig M3-kod och tidigare benchmarkevidens; utvecklingskedjan startas inte om.

Detaljer: analysis_plan_new_families_20260910.md och dess JSON. Inventering: new_family_inventory_20260910.md samt results/new_family_inventory_20260910. Oberoende granskning: peer_review/14_new_families_analysis_plan_review.md. Tidigare resultat och begränsningar bevaras.
