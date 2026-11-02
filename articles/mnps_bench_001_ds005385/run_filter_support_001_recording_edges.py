from __future__ import annotations
import csv,json
from datetime import datetime,timezone
from pathlib import Path
import h5py
import numpy as np
import mne
import run_filter_support_001 as base
DATA=base.DATA;OUT=base.OUT; SUBJECTS=base.SUBJECTS; SFREQ_OUT=base.SFREQ_OUT; GUARDS=base.GUARDS

def main():
 rows=[]; hashes={}
 for sub in SUBJECTS:
  p=DATA/sub/"eeg"/f"{sub}_task-memory_eeg.set"
  with h5py.File(p,"r") as h:n=int(h["data"].shape[0])
  for orient,boundary in (("recording_start",0),("recording_end",n)):
   arr,inj,bst,wave_rms=base.make_signals(n,boundary,orient)
   stages=base.process(arr); target_n=stages["bandpass"].shape[1]
   bout=0 if orient=="recording_start" else target_n
   for g in GUARDS:
    gs=int(np.ceil(g*SFREQ_OUT-1e-12))
    if orient=="recording_start":left,right=gs,min(target_n,gs+20*int(SFREQ_OUT))
    else:left,right=max(0,bout-gs-20*int(SFREQ_OUT)),bout-gs
    for stage,data in stages.items():
     for k,name in enumerate(("impulse_100uV","burst_10Hz","burst_30Hz","burst_80Hz")):
      r=base.stats(data[k,left:right],100e-6,wave_rms[k],18/19)
      rows.append({"subject":sub,"boundary":orient,"guard_seconds":g,"stage":stage,"waveform":name,"sample_start_250hz":left,"sample_end_250hz_exclusive":right,**r})
   print("completed",sub,orient,flush=True)
   del arr,stages
 byguard=[]; operational=None
 for g in GUARDS:
  q=[r for r in rows if r["stage"]=="bandpass" and r["guard_seconds"]==g]
  nonempty=[r for r in q if r["n"]>0]
  ok=bool(q) and len(nonempty)==len(q) and all(r["pass"] for r in q)
  byguard.append({"guard_seconds":g,"case_count":len(q),"nonempty_case_count":len(nonempty),"all_cases_pass":ok,
   "max_peak_ratio":max((r["max_peak_ratio"] for r in nonempty),default=None),"max_rms_stimulus_ratio":max((r["rms_stimulus_ratio"] for r in nonempty),default=None)})
  if operational is None and ok:operational=g
 OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/"recording_edge_guard_grid.csv").open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 with (OUT/"recording_edge_guard_summary.csv").open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(byguard[0]));w.writeheader();w.writerows(byguard)
 res={"schema":"mnps.filter_support_001_recording_edge_results.v1","created_utc":datetime.now(timezone.utc).isoformat(),
  "participants":list(SUBJECTS),"case_count":len(rows),"operational_recording_edge_guard_seconds":operational,"summary":byguard,
  "interpretation":"Synthetic impulses/bursts are injected at the first or final source sample. This characterizes numerical influence near recording boundaries; no source artifact or actual signal contamination is inferred."}
 (OUT/"recording_edge_manifest.json").write_text(json.dumps(res,indent=2,ensure_ascii=False),encoding="utf-8")
 print(json.dumps({"operational_recording_edge_guard_seconds":operational,"summary":byguard},indent=2),flush=True)
if __name__=="__main__":main()
