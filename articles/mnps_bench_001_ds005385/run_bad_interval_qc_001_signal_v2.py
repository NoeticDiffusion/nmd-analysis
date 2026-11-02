from __future__ import annotations
import hashlib,json,math,sys,time
from datetime import datetime,timezone
from pathlib import Path
import h5py,mne,numpy as np,pandas as pd
from scipy.signal import welch
ARTICLE=Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
DATA=Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
V1=ARTICLE/"outputs"/"trial_support_002_replay_v1_20261009"
OLD=ARTICLE/"outputs"/"bench_002_pilot_v2_fast_gate_fix_20261009"
OUT=ARTICLE/"outputs"/"trial_support_002_replay_v2_1_20261009"
SUBJECTS=("sub-032","sub-033","sub-034","sub-035","sub-036","sub-038")
SFREQ=250.0; THRESHOLD_TRIALS=4
sys.path.insert(0,str(ARTICLE));import run_bench_002_pilot_v1 as bench
from mndm.mnps.v3_1.realizations import CORE19_CHANNELS

def bpower(p,f,lo,hi):
 m=(f>=lo)&(f<=hi)
 if np.count_nonzero(m)<2:return np.full(p.shape[0],np.nan)
 return np.trapz(p[:,m],f[m],axis=1)
def qc_window(seg,n_channels):
 uv=np.asarray(seg,dtype=np.float64)*1e6
 finite=bool(np.isfinite(uv).all())
 if not finite:
  return {"hard_nonfinite":True,"flat_channel_count":None,"extreme_centered_abs_channel_count":None,"extreme_ptp_channel_count":None,"large_step_channel_count":None,
   "max_abs_uncentered_uv":None,"median_abs_channel_offset_uv":None,"max_abs_channel_offset_uv":None,"max_abs_centered_uv":None,"max_ptp_uv":None,"max_step_uv":None,
   "hard_qc_pass":False,"spectral_review_required":None,"high30_45_review_channels":None,"high70_100_review_channels":None,"line48_52_review_channels":None}
 offsets=np.median(uv,axis=1);centered=uv-offsets[:,None]
 p2p=np.ptp(uv,axis=1);abscenter=np.max(np.abs(centered),axis=1);steps=np.max(np.abs(np.diff(uv,axis=1)),axis=1)
 flat=p2p<=0.5;absbad=abscenter>500.0;ptpbad=p2p>1000.0;stepbad=steps>200.0
 nper=min(500,uv.shape[1]);f,p=welch(uv,fs=SFREQ,window="hann",nperseg=nper,noverlap=nper//2,detrend="constant",scaling="density",axis=1)
 p1_45=bpower(p,f,1,45);p30=bpower(p,f,30,45);p1_100=bpower(p,f,1,100);p70=bpower(p,f,70,100);p48=bpower(p,f,48,52)
 with np.errstate(divide="ignore",invalid="ignore"):
  r30=np.divide(p30,p1_45,out=np.zeros_like(p30),where=p1_45>0);r70=np.divide(p70,p1_100,out=np.zeros_like(p70),where=p1_100>0);rl=np.divide(p48,p1_100,out=np.zeros_like(p48),where=p1_100>0)
 c30=int(np.count_nonzero(r30>0.80));c70=int(np.count_nonzero(r70>0.20));cl=int(np.count_nonzero(rl>0.50));minimum=int(math.ceil((5/19)*n_channels))
 hard=not(bool(flat.any()) or bool(absbad.any()) or bool(ptpbad.any()) or bool(stepbad.any()))
 return {"hard_nonfinite":False,"flat_channel_count":int(flat.sum()),"extreme_centered_abs_channel_count":int(absbad.sum()),
  "extreme_ptp_channel_count":int(ptpbad.sum()),"large_step_channel_count":int(stepbad.sum()),
  "max_abs_uncentered_uv":float(np.max(np.abs(uv))),"median_abs_channel_offset_uv":float(np.median(np.abs(offsets))),
  "max_abs_channel_offset_uv":float(np.max(np.abs(offsets))),"max_abs_centered_uv":float(abscenter.max()),"max_ptp_uv":float(p2p.max()),"max_step_uv":float(steps.max()),
  "hard_qc_pass":bool(hard),"spectral_review_min_channels":minimum,"high30_45_review_channels":c30,"high70_100_review_channels":c70,"line48_52_review_channels":cl,
  "spectral_review_required":bool(c30>=minimum or c70>=minimum or cl>=minimum),
  "median_ratio_30_45_to_1_45":float(np.median(r30)),"median_ratio_70_100_to_1_100":float(np.median(r70)),"median_ratio_48_52_to_1_100":float(np.median(rl))}
def main():
 started=time.perf_counter();OUT.mkdir(parents=True,exist_ok=False);mne.set_log_level("ERROR")
 oldqc=pd.read_csv(V1/"window_signal_qc.csv");oldmeas=pd.read_csv(V1/"guarded_window_measurements.csv")
 oldsupport=pd.read_csv(OLD/"trial_support.csv");trial_base=pd.read_csv(V1/"trial_support_by_cell.csv")
 qrows=[]
 for subject in SUBJECTS:
  eeg=DATA/subject/"eeg";setp=eeg/f"{subject}_task-memory_eeg.set";chp=eeg/f"{subject}_task-memory_channels.tsv"
  labels,_=bench.load_labels(chp);source=bench.read_set(setp,labels,scale=1e-6)
  info=mne.create_info(ch_names=labels,sfreq=1000.0,ch_types=["eeg"]*len(labels),verbose="ERROR")
  raw=mne.io.RawArray(source,info,copy="auto",verbose="ERROR");del source
  raw.resample(SFREQ,n_jobs=1,verbose="ERROR")
  label_i={x.casefold():i for i,x in enumerate(labels)}
  surfaces=[("core19",list(CORE19_CHANNELS),np.asarray([label_i[x.casefold()] for x in CORE19_CHANNELS],dtype=int)),
   ("native",labels,np.arange(len(labels),dtype=int))]
  data=raw._data
  part=oldqc[oldqc.subject==subject]
  for surface,slabels,idxs in surfaces:
   rows=part[part.surface==surface]
   for _,r in rows.iterrows():
    left=int(r.window_start_sample_250hz);right=int(r.window_end_sample_250hz_exclusive)
    seg=np.asarray(data[idxs,left:right],dtype=np.float64).copy();seg-=seg.mean(axis=0,keepdims=True)
    status=qc_window(seg,len(slabels))
    base_row=r.to_dict();base_row.update(status);base_row["qc_version"]="v2_channel_median_centered_amplitude"
    base_row["signal_qc_pass"]=status["hard_qc_pass"];base_row["source_bad_annotations_available"]=False
    base_row["source_bad_interval_free"]=None;base_row["channel_status_available"]=False;base_row["measurement_qualified"]=False
    qrows.append(base_row)
  del raw,data
  print(subject,"QC windows",len(part),flush=True)
 qdf=pd.DataFrame(qrows)
 if len(qdf)!=6480:raise ValueError(f"expected 6480 v2 QC rows, got {len(qdf)}")
 key=["subject","surface","trial_id","window_class","window_index"]
 flags=qdf[key+["hard_qc_pass","spectral_review_required","max_abs_uncentered_uv","median_abs_channel_offset_uv","max_abs_centered_uv"]]
 meas=oldmeas.merge(flags,on=key,how="left",validate="one_to_one",suffixes=("","_v2"))
 if meas.hard_qc_pass.isna().any():raise ValueError("QC merge missing measurements")
 meas["signal_qc_pass_v2"]=meas.hard_qc_pass.astype(bool);meas["signal_qc_review_required_v2"]=meas.spectral_review_required.astype(bool)
 # Build cell support with historical nominal and new guarded counts explicitly separated.
 oldmap={}
 for _,r in oldsupport.iterrows():
  dur=4 if str(r.surface) else 4
  oldmap[(r.subject,r.surface,r.trial_id,4)]=int(r.fast_core_four_second_window_count)
  oldmap[(r.subject,r.surface,r.trial_id,20)]=int(r.twenty_second_window_count)
 trows=[]
 for _,b in trial_base.iterrows():
  dur=int(b.duration_sec);cls=b.window_class
  q=qdf[(qdf.subject==b.subject)&(qdf.surface==b.surface)&(qdf.trial_id==b.trial_id)&(qdf.window_class==cls)]
  passed=q[q.hard_qc_pass]
  trows.append({"subject":b.subject,"surface":b.surface,"trial_id":b.trial_id,"condition":b.condition,"load":int(b.load),"window_class":cls,"duration_sec":dur,
   "historical_nominal_window_count":oldmap[(b.subject,b.surface,b.trial_id,dur)],"guarded_temporal_window_count":len(q),
   "hard_qc_pass_window_count":int(q.hard_qc_pass.sum()),"spectral_review_window_count":int(q.spectral_review_required.sum()),
   "eligible_window_count":len(passed),"eligible_trial":bool(len(passed)>0),"source_annotation_status":"unknown_no_usable_annotation",
   "source_bad_interval_free":None,"measurement_qualified":False})
 tdf=pd.DataFrame(trows)
 group=["subject","surface","condition","load","window_class","duration_sec"]
 bal=[]
 for k,g in tdf.groupby(group,sort=True):
  bal.append({**dict(zip(group,k)),"planned_trials":len(g),"eligible_trials":int(g.eligible_trial.sum()),"eligible_trial_rate":float(g.eligible_trial.mean()),
   "historical_nominal_windows":int(g.historical_nominal_window_count.sum()),"guarded_temporal_windows":int(g.guarded_temporal_window_count.sum()),
   "hard_qc_pass_windows":int(g.hard_qc_pass_window_count.sum()),"spectral_review_windows":int(g.spectral_review_window_count.sum()),
   "pilot_gate_minimum_trials":THRESHOLD_TRIALS,"pilot_support_gate_pass":int(g.eligible_trial.sum())>=THRESHOLD_TRIALS})
 bdf=pd.DataFrame(bal);paired=[]
 for surface in ("core19","native"):
  for load in (5,9,13):
   for cls,dur in (("fast_core_4s",4),("full_v3_20s",20)):
    if cls=="full_v3_20s" and load!=13:continue
    for subject in SUBJECTS:
     z=bdf[(bdf.subject==subject)&(bdf.surface==surface)&(bdf.load==load)&(bdf.window_class==cls)].set_index("condition")
     if not all(c in z.index for c in ("control","memory")):continue
     c=z.loc["control"];m=z.loc["memory"]
     paired.append({"subject":subject,"surface":surface,"load":load,"window_class":cls,
      "control_planned_trials":int(c.planned_trials),"memory_planned_trials":int(m.planned_trials),
      "control_eligible_trials":int(c.eligible_trials),"memory_eligible_trials":int(m.eligible_trials),
      "eligible_trial_count_difference_memory_minus_control":int(m.eligible_trials-c.eligible_trials),
      "eligible_trial_rate_difference_memory_minus_control":float(m.eligible_trial_rate-c.eligible_trial_rate),
      "control_spectral_review_windows":int(c.spectral_review_windows),"memory_spectral_review_windows":int(m.spectral_review_windows),
      "control_spectral_review_rate":float(c.spectral_review_windows/max(1,c.guarded_temporal_windows)),
      "memory_spectral_review_rate":float(m.spectral_review_windows/max(1,m.guarded_temporal_windows))})
 pdf=pd.DataFrame(paired)
 qsum=(qdf.groupby(["surface","condition","load","window_class","duration_sec"],as_index=False)
  .agg(window_count=("hard_qc_pass","size"),hard_qc_pass_windows=("hard_qc_pass","sum"),spectral_review_windows=("spectral_review_required","sum"),
   median_abs_uncentered_uv=("max_abs_uncentered_uv","median"),median_abs_dc_offset_uv=("median_abs_channel_offset_uv","median"),
   median_max_abs_centered_uv=("max_abs_centered_uv","median"),median_max_ptp_uv=("max_ptp_uv","median"),median_max_step_uv=("max_step_uv","median")))
 for df,name in ((qdf,"window_signal_qc_v2.csv"),(meas,"guarded_window_measurements_v2.csv"),(tdf,"trial_support_by_cell_v2.csv"),(bdf,"participant_condition_balance_v2.csv"),(pdf,"participant_condition_balance_paired_v2.csv"),(qsum,"signal_qc_summary_v2.csv")):
  df.to_csv(OUT/name,index=False)
 oldmanifest=json.loads((V1/"run_manifest.json").read_text(encoding="utf-8"));passed=bool(bdf.pilot_support_gate_pass.all())
 parity=pd.read_csv(V1/"fixed_window_parity.csv");
 if len(parity)!=96 or not parity["pass"].all():raise ValueError("fixed-window parity failure inherited from v1")
 manifest={"schema":"mnps.trial_support_002_replay.v2","created_utc":datetime.now(timezone.utc).isoformat(),
  "dataset":"OpenNeuro ds003838 v1.0.6","participants":list(SUBJECTS),"qc_policy":"BAD-INTERVAL-QC-001 amendment v2: median-centered max amplitude; other hard limits unchanged",
  "trial_guard_seconds":2.0,"recording_edge_guard_seconds":4.0,"window_count":len(meas),"signal_qc_window_count":len(qdf),
  "signal_qc_hard_pass_count":int(qdf.hard_qc_pass.sum()),"signal_qc_hard_pass_rate":float(qdf.hard_qc_pass.mean()),
  "spectral_review_window_count":int(qdf.spectral_review_required.sum()),"participant_cell_count":len(bdf),"pilot_support_gate_pass_all_cells":passed,
  "fixed_window_parity_pass_all":True,"fixed_window_parity_row_count":len(parity),"fixed_window_parity_max_abs_difference":float(parity.max_abs_difference.max()),
  "source_bad_interval_status":"unknown_no_usable_annotations_in_65_EEG_eligible_participant_scan","measurement_qualified":False,
  "feature_values_recomputed":False,"feature_values_source":"unchanged 6,480-window v1 guarded extraction; only QC status rejoined",
  "v1_manifest_sha256":hashlib.sha256((V1/"run_manifest.json").read_bytes()).hexdigest(),
  "full_cohort_run":False,"classifier_fit":False,"elapsed_seconds":time.perf_counter()-started}
 (OUT/"run_manifest.json").write_text(json.dumps(bench.clean_json(manifest),indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
 print(json.dumps(manifest,indent=2,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
