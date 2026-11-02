# Första resultaten för de nya mätvärdesfamiljerna

E1/E2 är nu genomförda på de två fastställda sömnregistreringarna. Detta är en deskriptiv utvecklingsanalys, inte en populationsvalidering eller ett test av hela medvetandeteorin.

**Diffusion visar samma riktning i båda registreringarna:** N2 har lägre D_total, högre d_diff och lägre c_diff än vakenhet. Den lagrade globala kovariansskattningen har alltså mindre total inkrementvariation och mindre koncentration till en dominerande riktning vid N2-märkta frågepunkter. Det är ännu inte en stadiespecifikt skattad diffusionstensor.

**Abskissa/reaktivitet ger ett blandat resultat:** båda 9D-abskissorna minskar från vakenhet till N2, medan båda 3D-abskissorna minskar i sub-99 och ökar i sub-1. Reaktivitetsgapet minskar i 3D i båda, men har olika riktning i 9D. En generell utsaga om lägre expansion eller reaktivitet i N2 över representationer stöds därför inte. Gruppmedianerna för abskissorna är positiva; en minskning ska inte beskrivas som bevis för stabil dynamik.

| Representation / mått | Sub-99: N2 − Wake | Sub-1: N2 − Wake |
|---|---:|---:|
| 3D spectral_abscissa | -0.00102044 | +0.00123961 |
| 3D numerical_abscissa | -0.0039051 | +0.00211499 |
| 3D reactivity_gap | -0.00180783 | -0.000115554 |
| 9D spectral_abscissa | -0.00341974 | -0.00144539 |
| 9D numerical_abscissa | -0.0108178 | -0.000357904 |
| 9D reactivity_gap | -0.00571622 | +0.00148238 |
| 3D D_total | -0.0263619 | -0.0406145 |
| 3D d_diff | +0.0937614 | +0.123157 |
| 3D c_diff | -0.0239958 | -0.0396286 |

Abskissa och gap anges i s⁻¹ efter oberoende spårning av faktisk derivattid (30 s) i kod och H5-metadata. D_total har inspelningsrelativ koordinat²/s, d_diff och c_diff är dimensionslösa. Figurerna använder den försiktigare generiska benämningen invers derivattidsenhet. Differenserna är inom respektive inspelning och ska inte behandlas som kalibrerade mellanpersonseffekter. Medianen av gapet är inte skillnaden mellan de två abskissornas gruppmedianer.

## Underlag och begränsningar

Sub-99: 1066 Jacobianrader i både 3D och 9D, varav 1057 med känd sömnetikett; 1068 diffusionsrader, varav 1059 med känd etikett. Sub-1: 913 Jacobianrader i 3D (912 kända), 856 i 9D (855 kända) och 915 diffusionsrader (914 kända). Kod8 redovisas separat: nio respektive en rad per tillgänglig serie. Sub-1 9D har glesare centrumindex; inga serier har fyllts ut eller sammanfogats över luckor.

Alla lagrade diffusionsrader har producentens valid=1, stödantal20 och psd_floor_applied=0. Detta är beräkningsdiagnostik, inte vetenskaplig kvalificering. Samtliga förvalda utfall och fem kända stadier finns i tabellerna (90 mått–stadiumrader och18 kontraster); okända etiketter har egna kategorier. Ingen nollersättning, poolning, p-värdesberäkning eller stadiespecifik omskattning gjordes.

Det finns bara två utvecklingsregistreringar. Etikettassociationer kan påverkas av tid på natten, global grannskaps- och normaliseringsreferens samt blandad signalproveniens. PPG/EOG-skillnaden kvarstår som begränsning för tolkningen av representationerna. Samma riktning är därför en observation att följa upp, inte evidens för generell diskrimination eller medvetandemarkör. Saknad oberoende drift gör A_bD/R_b_over_a fortsatt ej testbara.

## Rekommenderad nästa prioritet

Behåll dessa resultat i artikeln och gå vidare till det redan planerade separata driftkandidatförsöket, med fast koordinatlager och utvärderingsinkrement som hålls utanför träningen. Återanvänd befintlig M3-metodik. För bredare biologiska påståenden behövs senare ett i förväg fastställt deltagarurval och analysprotokoll; de två aktuella registreringarna ska fortsätta räknas som utvecklingsmaterial. De blandade abskissafynden ska bevaras, inte användas för att trimma mätdefinitionerna.
