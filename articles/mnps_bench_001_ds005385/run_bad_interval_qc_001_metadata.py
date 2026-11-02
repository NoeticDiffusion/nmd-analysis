from __future__ import annotations
import csv, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
import h5py
DATA=Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
ARTICLE=Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
OUT=ARTICLE/"outputs"/"bad_interval_qc_001_pilot_v1_20261009"
BAD=re.compile(r"\b(?:bad|artifact|artefact|reject(?:ed)?|discontinuity)\b",re.I)

def tsv(path):
 with path.open(encoding="utf-8-sig",newline="") as f:
  r=csv.DictReader(f,delimiter="\t");return list(r.fieldnames or []),list(r)
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def reject_inventory(path):
 with h5py.File(path,"r") as h:
  if "reject" not in h:return 0,[],[]
  fields=[k for k in h["reject"].keys() if k.lower().startswith(("rej","icarej")) and not k.lower().endswith("col")]
  empty=[]; nonempty=[]
  for k in fields:
   ds=h["reject"][k]
   (empty if bool(ds.attrs.get("MATLAB_empty",0)) else nonempty).append(k)
  return len(fields),empty,nonempty
def event_types(path):
 with h5py.File(path,"r") as h:
  if "event/type" not in h:return []
  values=[]
  for ref in h["event/type"][:,0]:
   if not ref: values.append("");continue
   a=h[ref][()]
   values.append("".join(chr(int(x)) for x in a.reshape(-1) if int(x)).strip())
  return values
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 with (DATA/"participants.tsv").open(encoding="utf-8-sig",newline="") as f: roster=list(csv.DictReader(f,delimiter="\t"))
 people=[r["participant_id"] for r in roster if str(r.get("EEG_excluded","")).strip().lower()=="no"]
 rows=[]; hashes={}
 for sub in people:
  eeg=DATA/sub/"eeg"; evp=eeg/f"{sub}_task-memory_events.tsv"; chp=eeg/f"{sub}_task-memory_channels.tsv"; jp=eeg/f"{sub}_task-memory_eeg.json"; sp=eeg/f"{sub}_task-memory_eeg.set"
  ef,ev=tsv(evp); cf,ch=tsv(chp); meta=json.loads(jp.read_text(encoding="utf-8"))
  annotated=[]
  for r in ev:
   desc=" ".join(str(r.get(k,"")) for k in ("trial_type","value","description","HED"))
   if BAD.search(desc): annotated.append(r)
  status_fields=[x for x in cf if x.casefold() in {"status","status_description","quality","quality_description"}]
  status_values=[str(r.get(k,"")) for r in ch for k in status_fields if str(r.get(k,"" )).strip()]
  nreject,empty,nonempty=reject_inventory(sp)
  types=event_types(sp)
  mismatch=(len(types)!=len(ev) or any(a!=str(b.get("value","" )).strip() for a,b in zip(types,ev)))
  rows.append({"participant_id":sub,"bids_event_rows":len(ev),"bad_like_event_rows":len(annotated),
   "bad_like_event_has_positive_duration":sum(float(r.get("duration") or 0)>0 for r in annotated),
   "channels_tsv_fields":",".join(cf),"channel_status_fields":",".join(status_fields),"channel_status_values_present":len(status_values),
   "eeglab_event_rows":len(types),"eeglab_bids_event_sequence_mismatch":mismatch,
   "eeglab_rejection_field_count":nreject,"eeglab_rejection_empty_field_count":len(empty),"eeglab_rejection_nonempty_fields":",".join(nonempty),
   "eeg_channel_count":meta.get("EEGChannelCount"),"emg_channel_count":meta.get("EMGChannelCount",0),"misc_channel_count":meta.get("MiscChannelCount",0),
   "source_bad_annotation_status":"available_bad_event_marker" if annotated else "unknown_no_usable_bad_interval_annotation_seen",
   "source_bad_interval_free":None,"eeg_set_bytes":sp.stat().st_size})
  for p in (evp,chp,jp):hashes[str(p)]=sha(p)
  # Deliberately record only size and prior-artifact link for .set; hashing would read the signal payload.
 writepath=OUT/"participant_annotation_inventory.csv"
 with writepath.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 n_bad=sum(r["bad_like_event_rows"] for r in rows); n_status=sum(r["channel_status_values_present"] for r in rows)
 n_nonempty=sum(bool(r["eeglab_rejection_nonempty_fields"]) for r in rows)
 mismatches=sum(r["eeglab_event_rows"]!=r["bids_event_rows"] or r["eeglab_bids_event_sequence_mismatch"] for r in rows)
 report={"schema":"mnps.bad_interval_qc_001_metadata_inventory.v1","created_utc":datetime.now(timezone.utc).isoformat(),
  "dataset":"OpenNeuro ds003838 v1.0.6","scope":"metadata-only; no EEG signal arrays read or measurements computed","eligible_eeg_participant_count":len(people),
  "event_row_count":sum(r["bids_event_rows"] for r in rows),"bad_like_event_row_count":n_bad,"bad_like_positive_duration_count":sum(r["bad_like_event_has_positive_duration"] for r in rows),
  "participants_with_channel_status_values":sum(bool(r["channel_status_values_present"]) for r in rows),"channel_status_field_instances":n_status,
  "participants_with_nonempty_eeglab_rejection_fields":n_nonempty,"eeglab_bids_event_mismatch_count":mismatches,
  "source_bad_interval_free_global":"unknown","explicit_clean_interval_annotations_found":False,
  "limitations":"No BAD-like event marker does not establish clean EEG. EEGLAB reject fields and BIDS channel status are inventoried separately; absent values remain unknown.","source_hashes":hashes}
 (OUT/"metadata_manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
 print(json.dumps({k:v for k,v in report.items() if k not in ("source_hashes",)},indent=2))
if __name__=="__main__":main()
