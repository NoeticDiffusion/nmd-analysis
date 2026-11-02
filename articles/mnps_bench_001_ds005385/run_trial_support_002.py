from __future__ import annotations
import csv, hashlib, json, math, sys, time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import h5py
import mne
import numpy as np
import pandas as pd
from scipy.signal import welch

ARTICLE=Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
DATA=Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
OUT=ARTICLE/"outputs"/"trial_support_002_replay_v1_20261009"
SUBJECTS=("sub-032","sub-033","sub-034","sub-035","sub-036","sub-038")
SFREQ_IN=1000.0; SFREQ=250.0; GUARD_TRIAL_SEC=2.0; GUARD_RECORD_SEC=4.0
S4=1000; S20=5000
ARTICLE_CODE=ARTICLE/"run_bench_002_pilot_v1.py"
sys.path.insert(0,str(ARTICLE))
import run_bench_002_pilot_v1 as bench
from mndm.mnps.v3_1.pipeline_measurements import compute_pipeline_window_measurements
from mndm.mnps.v3_1.realizations import CORE19_CHANNELS

FAST_FEATURES=("PCV","TP","OI","SC")
V3_FEATURES=("PCV","TP",*(f"AR_pair_{i:02d}" for i in range(1,10)),"NIE","RD","OI","SC","ED")

def bandpower(psd,f,lo,hi):
 m=(f>=lo)&(f<=hi)
 if np.count_nonzero(m)<2:return np.full(psd.shape[0],np.nan)
 return np.trapz(psd[:,m],f[m],axis=1)

def signal_qc(x_volts, n_channels):
 # Condition-blind QC on 250-Hz, pre-notch data after realization-specific average reference.
 uv=np.asarray(x_volts,dtype=np.float64)*1e6
 finite=bool(np.isfinite(uv).all())
 if not finite:
  return {"hard_qc_pass":False,"hard_nonfinite":True,"flat_channel_count":None,"extreme_abs_channel_count":None,
   "extreme_ptp_channel_count":None,"large_step_channel_count":None,"max_abs_uv":None,"max_ptp_uv":None,
   "max_step_uv":None,"high30_45_review_channels":None,"high70_100_review_channels":None,
   "line48_52_review_channels":None,"spectral_review_required":None}
 p2p=np.ptp(uv,axis=1)
 maxabs=np.max(np.abs(uv),axis=1)
 steps=np.max(np.abs(np.diff(uv,axis=1)),axis=1)
 flat=(p2p<=0.5); extreme_abs=(maxabs>500.0); extreme_ptp=(p2p>1000.0); large_step=(steps>200.0)
 nper=min(500,uv.shape[1]);noverlap=nper//2
 f,p=welch(uv,fs=SFREQ,window="hann",nperseg=nper,noverlap=noverlap,detrend="constant",scaling="density",axis=1)
 p1_45=bandpower(p,f,1,45);p30_45=bandpower(p,f,30,45);p1_100=bandpower(p,f,1,100)
 p70_100=bandpower(p,f,70,100);p48_52=bandpower(p,f,48,52)
 with np.errstate(divide="ignore",invalid="ignore"):
  r30=np.divide(p30_45,p1_45,out=np.zeros_like(p30_45),where=p1_45>0)
  r70=np.divide(p70_100,p1_100,out=np.zeros_like(p70_100),where=p1_100>0)
  rline=np.divide(p48_52,p1_100,out=np.zeros_like(p48_52),where=p1_100>0)
 # Keep a common channel-proportion threshold for the primary 19-channel and native surfaces.
 spectral_min=int(math.ceil((5/19)*n_channels))
 c30=int(np.count_nonzero(r30>0.80));c70=int(np.count_nonzero(r70>0.20));cline=int(np.count_nonzero(rline>0.50))
 hard=not (bool(flat.any()) or bool(extreme_abs.any()) or bool(extreme_ptp.any()) or bool(large_step.any()))
 review=bool(c30>=spectral_min or c70>=spectral_min or cline>=spectral_min)
 return {"hard_qc_pass":bool(hard),"hard_nonfinite":False,"flat_channel_count":int(flat.sum()),
  "extreme_abs_channel_count":int(extreme_abs.sum()),"extreme_ptp_channel_count":int(extreme_ptp.sum()),
  "large_step_channel_count":int(large_step.sum()),"max_abs_uv":float(maxabs.max()),"max_ptp_uv":float(p2p.max()),
  "max_step_uv":float(steps.max()),"high30_45_review_channels":c30,"high70_100_review_channels":c70,
  "line48_52_review_channels":cline,"spectral_review_min_channels":spectral_min,"spectral_review_required":review,
  "median_ratio_30_45_to_1_45":float(np.median(r30)),"median_ratio_70_100_to_1_100":float(np.median(r70)),
  "median_ratio_48_52_to_1_100":float(np.median(rline))}

def make_windows(trials,total_samples):
 out=[]
 g=int(round(GUARD_TRIAL_SEC*SFREQ));rec=int(round(GUARD_RECORD_SEC*SFREQ))
 for t in trials:
  left=max(0,math.ceil((int(t["source_start_sample"])+GUARD_TRIAL_SEC*SFREQ_IN)/4))
  right=min(total_samples,math.floor((int(t["source_end_sample_exclusive"])-GUARD_TRIAL_SEC*SFREQ_IN)/4))
  # Physical edge guards apply only when the candidate interval approaches the recording boundary.
  left=max(left,rec);right=min(right,total_samples-rec)
  for dur,win,step in ((4,S4,S4),):
   for idx,start in enumerate(range(left,right-win+1,step)):
    out.append({**t,"duration_sec":dur,"window_index":idx,"start":start,"end":start+win,
     "window_class":"fast_core_4s","temporal_support_pass":True})
  if int(t["load"])==13:
   for idx,start in enumerate(range(left,right-S20+1,S20)):
    out.append({**t,"duration_sec":20,"window_index":idx,"start":start,"end":start+S20,
     "window_class":"full_v3_20s","temporal_support_pass":True})
 return out

def reref(seg):
 x=np.asarray(seg,dtype=np.float64).copy()
 x-=x.mean(axis=0,keepdims=True)
 return x

def features(window,labels,subject,trial,start,end,source_identity,branch,temporal):
 qc={"source_is_continuous":True,"timestamps_uniform":True,"input_samples_finite":bool(np.isfinite(window).all()),
  "gap_free":True,"bad_interval_free":None,"within_recording_bounds":True,
  "effective_filter_support_valid":bool(temporal),"effective_filter_support_status":"empirical_trial_guard_2s_and_recording_edge_guard_4s",
  "measurement_qualified":False}
 return compute_pipeline_window_measurements(window,labels,sample_rate_hz=SFREQ,
  window_start_sec=start/SFREQ,window_end_sec=end/SFREQ,
  segment_id=f"{subject}_task-memory_{trial['trial_id']}",source_identity=source_identity,
  input_branch=branch,support_qc=qc,sequence_complexity_reference_count=32,activity_block_sec=2.0)

def compare(old,new,features):
 vals=[]
 for key in features:
  try:a=float(old[key]);b=float(new.get(key))
  except (KeyError,TypeError,ValueError):continue
  if math.isfinite(a) and math.isfinite(b):vals.append(abs(a-b))
 if not vals:return {"compared_value_count":0,"max_abs_difference":None,"pass":False}
 md=max(vals)
 return {"compared_value_count":len(vals),"max_abs_difference":md,"pass":bool(md<=1e-10)}

def main():
 started=time.perf_counter();OUT.mkdir(parents=True,exist_ok=False);mne.set_log_level("ERROR")
 olddir=ARTICLE/"outputs"/"bench_002_pilot_v2_fast_gate_fix_20261009"
 oldfast=pd.read_csv(olddir/"fast_core_4s_window_values.csv")
 oldv3=pd.read_csv(olddir/"v3_window_values.csv")
 prior=json.loads((olddir/"run_manifest.json").read_text(encoding="utf-8"))
 source_hashes=prior.get("input_file_sha256",{})
 descriptor_by_subject={};trial_rows=[];qc_rows=[];qc_by_key={};measurement_rows=[];parity=[]
 jsonl=OUT/"measurements.jsonl"
 for subj in SUBJECTS:
  eeg=DATA/subj/"eeg";setp=eeg/f"{subj}_task-memory_eeg.set";chp=eeg/f"{subj}_task-memory_channels.tsv";evp=eeg/f"{subj}_task-memory_events.tsv"
  labels,_=bench.load_labels(chp);eegsrc=bench.read_set(setp,labels,scale=1e-6)
  trials,_=bench.parse_trials(evp,subj,eegsrc.shape[1]); total_source=eegsrc.shape[1]
  info=mne.create_info(ch_names=labels,sfreq=SFREQ_IN,ch_types=["eeg"]*len(labels),verbose="ERROR")
  raw=mne.io.RawArray(eegsrc,info,copy="auto",verbose="ERROR");del eegsrc
  raw.resample(SFREQ,n_jobs=1,verbose="ERROR")
  if raw.n_times!=total_source//4:raise ValueError(f"{subj}: unexpected resample grid")
  windows=make_windows(trials,raw.n_times)
  # Build surfaces and window QC before notch/bandpass.
  label_i={x.casefold():i for i,x in enumerate(labels)}
  core_missing=[x for x in CORE19_CHANNELS if x.casefold() not in label_i]
  if core_missing:raise ValueError(f"{subj}: missing Core19 channels {core_missing}")
  surfaces=[("core19",list(CORE19_CHANNELS),np.asarray([label_i[x.casefold()] for x in CORE19_CHANNELS],dtype=int)),
            ("native",labels,np.arange(len(labels),dtype=int))]
  rawdata=raw._data
  total_window_count=0
  for surface,slabels,idxs in surfaces:
   for w in windows:
    seg=reref(rawdata[idxs,w["start"]:w["end"]])
    if seg.shape!=(len(slabels),w["end"]-w["start"]):raise ValueError("QC window shape mismatch")
    q=signal_qc(seg,len(slabels))
    row={"subject":subj,"surface":surface,"trial_id":w["trial_id"],"condition":w["condition"],"load":w["load"],
     "window_class":w["window_class"],"duration_sec":w["duration_sec"],"window_index":w["window_index"],
     "window_start_sample_250hz":w["start"],"window_end_sample_250hz_exclusive":w["end"],
     "effective_filter_support_pass":True,"source_bad_annotations_available":False,
     "source_bad_interval_free":None,"channel_status_available":False,"measurement_qualified":False,**q}
    qc_rows.append(row);qc_by_key[(subj,surface,w["trial_id"],w["window_class"],w["window_index"])]=row;total_window_count+=1
  # Original MNE chain unchanged after the QC copy; processing remains recording-continuous.
  raw.notch_filter(freqs=[50.0],picks="eeg",n_jobs=1,verbose="ERROR")
  raw.filter(l_freq=1.0,h_freq=45.0,picks="eeg",n_jobs=1,verbose="ERROR")
  filtered=raw._data
  branch_template={"branch_id":"mnps_bench_002_mne_common_preprocessing_v1_guarded_windows",
   "reference_mode":"average_over_surface","filter_band_hz":[1.0,45.0],"amplitude_unit":"volts","reference_status":"verified",
   "effective_filter_support":"trial_boundary_2s; physical_recording_edge_4s"}
  source_identity=source_hashes.get(str(setp),f"{setp}#sha_not_rehashed_this_run")
  for surface,slabels,idxs in surfaces:
   for w in windows:
    win=reref(filtered[idxs,w["start"]:w["end"]])
    branch={**branch_template,"reference_set_sha256":bench.label_hash(slabels,ordered=False),"channel_set_sha256":bench.label_hash(slabels,ordered=False)}
    result=features(win,slabels,subj,w,w["start"],w["end"],source_identity,branch,w["temporal_support_pass"])
    vals=bench.v3_values(result)
    q=qc_by_key[(subj,surface,w["trial_id"],w["window_class"],w["window_index"])]
    mrow={"subject":subj,"surface":surface,"trial_id":w["trial_id"],"condition":w["condition"],"load":int(w["load"]),
     "window_class":w["window_class"],"duration_sec":int(w["duration_sec"]),"window_index":int(w["window_index"]),
     "window_start_sample_250hz":int(w["start"]),"window_end_sample_250hz_exclusive":int(w["end"]),
     "measurement_qualified":False,"source_bad_interval_free":None,"signal_qc_pass":q["hard_qc_pass"],
     "signal_qc_review_required":q["spectral_review_required"],"effective_filter_support_pass":True,
     **{k:vals.get(k) for k in (FAST_FEATURES if w["duration_sec"]==4 else V3_FEATURES)}}
    measurement_rows.append(mrow)
    with jsonl.open("a",encoding="utf-8") as f:f.write(json.dumps(bench.clean_json({"measurement":mrow,"qc":q,"result":result}),ensure_ascii=False,allow_nan=False)+"\n")
    if len(measurement_rows)%200==0:print(f"{subj}: completed measurement windows={len(measurement_rows)}",flush=True)
   # Fixed-window parity: one first historical window per subject/cell, for both conditions/loads and surfaces.
   for cond in ("control","memory"):
    for load in (5,9,13):
     t=next(x for x in trials if x["condition"]==cond and int(x["load"])==load)
     left=(int(t["source_start_sample"])+3)//4
     oldrow=oldfast[(oldfast.subject==subj)&(oldfast.surface==surface)&(oldfast.trial_id==t["trial_id"])&(oldfast.window_index==0)]
     if len(oldrow):
      w=reref(filtered[idxs,left:left+S4]); res=features(w,slabels,subj,t,left,left+S4,source_identity,branch_template,False); vals=bench.v3_values(res)
      comp=compare(oldrow.iloc[0].to_dict(),vals,FAST_FEATURES)
      parity.append({"subject":subj,"surface":surface,"condition":cond,"load":load,"window_class":"fast_core_4s_fixed_grid","start_sample_250hz":left,**comp})
    t=next(x for x in trials if x["condition"]==cond and int(x["load"])==13)
    left=(int(t["source_start_sample"])+3)//4
    oldrow=oldv3[(oldv3.subject==subj)&(oldv3.surface==surface)&(oldv3.trial_id==t["trial_id"])&(oldv3.window_index==0)]
    if len(oldrow):
     w=reref(filtered[idxs,left:left+S20]);res=features(w,slabels,subj,t,left,left+S20,source_identity,branch_template,False);vals=bench.v3_values(res)
     comp=compare(oldrow.iloc[0].to_dict(),vals,V3_FEATURES)
     parity.append({"subject":subj,"surface":surface,"condition":cond,"load":13,"window_class":"full_v3_20s_fixed_grid","start_sample_250hz":left,**comp})
  del raw,filtered,rawdata
  # Distinct source trial support rows per participant, condition, load, surface and realization.
  for surface in ("core19","native"):
   sq=[r for r in qc_rows if r["subject"]==subj and r["surface"]==surface]
   for t in trials:
    for cls,dur in (("fast_core_4s",4),("full_v3_20s",20)):
     if cls=="full_v3_20s" and int(t["load"])!=13:continue
     q=[r for r in sq if r["trial_id"]==t["trial_id"] and r["window_class"]==cls]
     eligible=[r for r in q if r["effective_filter_support_pass"] and r["hard_qc_pass"]]
     trial_rows.append({"subject":subj,"surface":surface,"trial_id":t["trial_id"],"condition":t["condition"],"load":int(t["load"]),
      "window_class":cls,"duration_sec":dur,"source_annotation_status":"unknown_no_usable_annotation",
      "nominal_trial_count":1,"nominal_window_count":len(q),"temporal_support_window_count":sum(r["effective_filter_support_pass"] for r in q),
      "hard_qc_pass_window_count":sum(r["hard_qc_pass"] for r in q),"spectral_review_window_count":sum(bool(r["spectral_review_required"]) for r in q),
      "eligible_window_count":len(eligible),"eligible_trial":bool(eligible),"measurement_qualified":False})
  print(f"{subj}: windows={total_window_count}; finished",flush=True)
 # Write auditable per-window and per-trial outputs.
 pd.DataFrame(qc_rows).to_csv(OUT/"window_signal_qc.csv",index=False)
 pd.DataFrame(measurement_rows).to_csv(OUT/"guarded_window_measurements.csv",index=False)
 pd.DataFrame(trial_rows).to_csv(OUT/"trial_support_by_cell.csv",index=False)
 pd.DataFrame(parity).to_csv(OUT/"fixed_window_parity.csv",index=False)
 qdf=pd.DataFrame(qc_rows);tdf=pd.DataFrame(trial_rows)
 balance=[]
 groupcols=["subject","surface","condition","load","window_class","duration_sec"]
 for key,g in tdf.groupby(groupcols):
  q=g
  balance.append({**dict(zip(groupcols,key)),"planned_trials":len(q),"eligible_trials":int(q.eligible_trial.sum()),
   "eligible_trial_rate":float(q.eligible_trial.mean()),"temporal_windows":int(q.temporal_support_window_count.sum()),
   "hard_qc_pass_windows":int(q.hard_qc_pass_window_count.sum()),"spectral_review_windows":int(q.spectral_review_window_count.sum()),
   "pilot_gate_minimum_trials":4,"pilot_support_gate_pass":int(q.eligible_trial.sum())>=4})
 bdf=pd.DataFrame(balance);bdf.to_csv(OUT/"participant_condition_balance.csv",index=False)
 qcsummary=(qdf.groupby(["surface","condition","load","window_class","duration_sec"],as_index=False)
  .agg(window_count=("hard_qc_pass","size"),hard_qc_pass_windows=("hard_qc_pass","sum"),spectral_review_windows=("spectral_review_required","sum"),
   median_max_abs_uv=("max_abs_uv","median"),median_max_ptp_uv=("max_ptp_uv","median"),median_max_step_uv=("max_step_uv","median")))
 qcsummary.to_csv(OUT/"signal_qc_summary.csv",index=False)
 # Participant-level memory-control support and QC contrasts, computed only after condition-blind flags exist.
 paired=[]
 for surf in ("core19","native"):
  for load in (5,9,13):
   for cls,dur in (("fast_core_4s",4),("full_v3_20s",20)):
    if cls=="full_v3_20s" and load!=13:continue
    for subj in SUBJECTS:
     rows=[r for r in balance if r["subject"]==subj and r["surface"]==surf and r["load"]==load and r["window_class"]==cls]
     by={r["condition"]:r for r in rows}
     if all(c in by for c in ("control","memory")):
      paired.append({"subject":subj,"surface":surf,"load":load,"window_class":cls,
       "control_planned_trials":by["control"]["planned_trials"],"memory_planned_trials":by["memory"]["planned_trials"],
       "control_eligible_trials":by["control"]["eligible_trials"],"memory_eligible_trials":by["memory"]["eligible_trials"],
       "eligible_trial_count_difference_memory_minus_control":by["memory"]["eligible_trials"]-by["control"]["eligible_trials"],
       "eligible_rate_difference_memory_minus_control":by["memory"]["eligible_trial_rate"]-by["control"]["eligible_trial_rate"],
       "control_spectral_review_windows":by["control"]["spectral_review_windows"],"memory_spectral_review_windows":by["memory"]["spectral_review_windows"]})
 pd.DataFrame(paired).to_csv(OUT/"participant_condition_balance_paired.csv",index=False)
 parity_ok=bool(parity) and all(r["pass"] for r in parity)
 gate=bool(len(bdf)>0 and bdf.pilot_support_gate_pass.all())
 manifest={"schema":"mnps.trial_support_002_replay.v1","created_utc":datetime.now(timezone.utc).isoformat(),
  "dataset":"OpenNeuro ds003838 v1.0.6","participants":list(SUBJECTS),"trial_guard_seconds":GUARD_TRIAL_SEC,"recording_edge_guard_seconds":GUARD_RECORD_SEC,
  "source_bad_interval_status":"unknown_no_usable_bad_interval_annotations_in_all_65_EEG_eligible_metadata_inventory",
  "channel_status_available":False,"measurement_qualified":False,"preprocessing":"MNE 1.6.1; same continuous resample/notch/bandpass chain as BENCH-002",
  "window_count":len(measurement_rows),"signal_qc_window_count":len(qc_rows),"participant_cell_count":len(bdf),
  "pilot_support_gate_pass_all_cells":gate,"fixed_window_parity_pass_all":parity_ok,
  "fixed_window_parity_max_abs_difference":float(max((r["max_abs_difference"] for r in parity if r["max_abs_difference"] is not None),default=float("nan"))),
  "prior_run_manifest":str(olddir/"run_manifest.json"),"prior_run_manifest_sha256":hashlib.sha256((olddir/"run_manifest.json").read_bytes()).hexdigest(),
  "input_file_identity_reference":"Prior BENCH-002 manifest SHA256 entries; .set payloads were read for extraction but not rehashed in this run.",
  "full_cohort_run":False,"classifier_fit":False,"elapsed_seconds":time.perf_counter()-started}
 (OUT/"run_manifest.json").write_text(json.dumps(bench.clean_json(manifest),indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
 print(json.dumps(manifest,indent=2,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
