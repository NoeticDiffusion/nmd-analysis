## Handover: `ds006036` photonic-events

- **Rå eventkälla (BIDS):** `sub-*/eeg/sub-*_task-photomark_events.tsv` med kolumner `onset`, `duration`, `sample`, `value` (enligt `mndm/docs/ds006036/readme.md`).
- **Implementerad tolkning i pipeline:** `mndm/config/config_ingest_ds006036.yaml` läser `value` som stage-kolumn och mappar:
  - `PHOTO 5Hz -> 50`
  - `PHOTO 10Hz -> 51`
  - `PHOTO 15Hz -> 52`
  - `PHOTO 20Hz -> 53`
  - `open eyes -> 60`
  - `closed eyes -> 61`
  - `eye movement -> 62`
- **Viktig fix:** punkt-events (`duration=0`) mappas nu till **fönstret som innehåller onset** (inte bara midpoint-match), via `mndm/src/mndm/features/epoch_selection.py` och `mndm/src/mndm/pipeline/summary_events.py`.

## Vad datat innehåller i praktiken

- **Alla rå events (88 filer, 51 939 rader) – vanligaste `value`:**
  - `Photo/HV mark`: 49 342
  - `closed eyes`: 556
  - `open eyes`: 538
  - `eye movement`: 347
  - `Swallowing`: 166
  - plus mindre mängder (`PHOTO 5/10/15/20Hz`, `RESET condition`, `CAL mode`, etc.)

- **Features-stage (hela körningen, 6 820 epoker):**
  - `-1`: 4 365 (64.0%)  *(omappade/övriga labels, inkl. mycket `Photo/HV mark`)*
  - `50`: 73
  - `51`: 60
  - `52`: 59
  - `53`: 49
  - `60`: 501
  - `61`: 1 090
  - `62`: 623

- **Label-täckning (`stage_frac_labeled`) över subjects:**  
  mean `0.437`, median `0.399`, min `0.111`, max `0.941`.

## Hur det syns i outputs

- I `features.csv`: kolumn `stage`.
- I `summary.json`: `labels: ["stage"]`, `stage_source: "features_csv"`, `stage_column: "stage"`.
- `events` är tom (`[]`) i nuvarande setup; event-information används alltså främst via `stage`-labeln.

## Analysrekommendation (kort)

- För photic-analys: använd `stage in {50,51,52,53}`.
- För ögonstatus: använd `stage in {60,61,62}`.
- Behandla `stage=-1` som “övrigt/omappat” (inte “ingen händelse”).
- Om du vill analysera `Photo/HV mark` explicit kan vi lägga till en kod (t.ex. `54`) i mappingen.
- Om du vill ha **multi-label per epoch** (flera events samtidigt) behöver vi lägga till explicit `event_*`-export, eftersom `stage` är single-label.