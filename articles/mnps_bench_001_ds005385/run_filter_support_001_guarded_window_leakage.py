from __future__ import annotations
import csv,math
from pathlib import Path
import numpy as np
import run_filter_support_001 as base
OUT=base.OUT;DATA=base.DATA

def main():
 rows=[]
 for sub in base.SUBJECTS:
  eeg=DATA/sub/"eeg"; ev=base.event_trials(eeg/f"{sub}_task-memory_events.tsv")
  with __import__('h5py').File(eeg/f"{sub}_task-memory_eeg.set","r") as h:n=int(h["data"].shape[0])
  t13=[t for t in ev if t["load"]==13]
  for cond in ("control","memory"):
   t=next(x for x in t13 if x["condition"]==cond)
   start_out=math.ceil((t["start"]+2000)/4)
   end_out=start_out+5000
   trial_end=math.floor((t["end"]-2000)/4)
   if end_out>trial_end:raise ValueError("guarded v3 window not supported")
   for orient,boundary in (("trial_start",t["start"]),("trial_end",t["end"])):
    arr,inj,bst,wave_rms=base.make_signals(n,boundary,orient); stages=base.process(arr)
    for stage,data in stages.items():
     for k,wave in enumerate(("impulse_100uV","burst_10Hz","burst_30Hz","burst_80Hz")):
      r=base.stats(data[k,start_out:end_out],100e-6,wave_rms[k],18/19)
      rows.append({"subject":sub,"condition":cond,"boundary":orient,"stage":stage,"waveform":wave,
       "guarded_window_start_sample_250hz":start_out,"guarded_window_end_sample_250hz_exclusive":end_out,
       "window_gap_from_boundary_seconds":(t["end"]/4-end_out)/250 if orient=="trial_end" else (start_out-t["start"]/4)/250,
       **r})
    print("completed",sub,cond,orient,flush=True)
    del arr,stages
 p=OUT/"guarded_load13_window_leakage.csv"
 with p.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print("rows",len(rows),"output",p,flush=True)
if __name__=="__main__":main()
