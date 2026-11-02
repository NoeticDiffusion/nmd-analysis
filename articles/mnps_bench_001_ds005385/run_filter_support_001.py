from __future__ import annotations
import csv, hashlib, json, math, re
from datetime import datetime, timezone
from pathlib import Path
import h5py
import mne
import numpy as np

DATA = Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
ARTICLE = Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
OUT = ARTICLE / "outputs" / "filter_support_001_pilot_v1_20261009"
SUBJECTS = ("sub-032", "sub-033", "sub-034", "sub-035", "sub-036", "sub-038")
SFREQ_IN, SFREQ_OUT = 1000.0, 250.0
GUARDS = (0,1,2,3,3.296,4,5,6,7,8,10,12,15,20)
TRIAL_RE = re.compile(r"\b(?P<cond>control|memory)\s+(?P<pos>\d+)\s*/\s*(?P<load>\d+)\b", re.I)
CORE19 = {"Fp1","Fp2","F7","F3","Fz","F4","F8","T7","C3","Cz","C4","T8","P7","P3","Pz","P4","P8","O1","O2"}

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""): h.update(b)
    return h.hexdigest()

def event_trials(path):
    out=[]; cur=None
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            m=TRIAL_RE.search(str(row.get("trial_type","")))
            if not m: continue
            d={"condition":m.group("cond").lower(),"pos":int(m.group("pos")),"load":int(m.group("load")),"sample":int(float(row["sample"]))}
            if d["pos"]==1:
                if cur is not None: raise ValueError("nested trial start")
                cur={"condition":d["condition"],"load":d["load"],"digits":[]}
            if cur is None or (d["condition"],d["load"])!=(cur["condition"],cur["load"]): raise ValueError("broken digit sequence")
            cur["digits"].append(d)
            if d["pos"]==d["load"]:
                ds=cur["digits"]
                if [x["pos"] for x in ds] != list(range(1,cur["load"]+1)): raise ValueError("bad positions")
                out.append({"condition":cur["condition"],"load":cur["load"],"start":ds[0]["sample"],"last":ds[-1]["sample"],"end":ds[-1]["sample"]+3000})
                cur=None
    if cur is not None: raise ValueError("unterminated trial")
    return out

def make_signals(n, boundary, orient):
    arr=np.zeros((4,n),dtype=np.float64)
    if orient=="trial_start":
        idx=boundary-1
        burst_start=boundary-1000
    elif orient=="trial_end":
        idx=boundary
        burst_start=boundary
    elif orient=="recording_start":
        idx=0
        burst_start=0
    elif orient=="recording_end":
        idx=n-1
        burst_start=n-1000
    else: raise ValueError(orient)
    if idx<0 or idx>=n: raise ValueError(f"injection index outside recording {orient}: {idx}/{n}")
    arr[0,idx]=100e-6
    nburst=min(1000,n-burst_start)
    if nburst<=0: raise ValueError("no burst samples")
    w=np.hanning(1000)[:nburst]
    t=np.arange(nburst)/SFREQ_IN
    for ch,freq in enumerate((10.,30.,80.),start=1):
        arr[ch,burst_start:burst_start+nburst]=100e-6*w*np.sin(2*np.pi*freq*t)
    wave_rms=[100e-6,*(float(np.sqrt(np.mean(x*x))) for x in arr[1:,burst_start:burst_start+nburst])]
    return arr, idx, burst_start, wave_rms

def process(arr):
    info=mne.create_info([f"QC{i}" for i in range(arr.shape[0])],sfreq=SFREQ_IN,ch_types=["eeg"]*arr.shape[0],verbose="ERROR")
    raw=mne.io.RawArray(arr,info,copy="auto",verbose="ERROR")
    raw.resample(SFREQ_OUT,n_jobs=1,verbose="ERROR")
    a=np.asarray(raw.get_data(),dtype=np.float64).copy()
    raw.notch_filter(freqs=[50.0],picks="eeg",n_jobs=1,verbose="ERROR")
    b=np.asarray(raw.get_data(),dtype=np.float64).copy()
    raw.filter(l_freq=1.0,h_freq=45.0,picks="eeg",n_jobs=1,verbose="ERROR")
    c=np.asarray(raw.get_data(),dtype=np.float64).copy()
    del raw
    return {"resample":a,"notch":b,"bandpass":c}

def stats(seg, stimulus_peak, stimulus_rms, car):
    if seg.size==0: return {"n":0,"max_uv":None,"rms_uv":None,"max_peak_ratio":None,"rms_stimulus_ratio":None,"pass":False}
    v=np.asarray(seg,dtype=np.float64)*car*1e6
    peak=float(np.max(np.abs(v))); rms=float(np.sqrt(np.mean(v*v)))
    return {"n":int(v.size),"max_uv":peak,"rms_uv":rms,"max_peak_ratio":peak/(stimulus_peak*1e6),
            "rms_stimulus_ratio":rms/(stimulus_rms*1e6),
            "pass":bool(peak<=1e-4*stimulus_peak*1e6 and rms<=1e-4*stimulus_rms*1e6)}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    leakage=[]; guards=[]; recall=[]; hashes={}; event_cases=[]
    # Resolve actual recording lengths from the MATLAB v7.3 array shape only; do not load EEG samples.
    for sub in SUBJECTS:
        eeg=DATA/sub/"eeg"; evp=eeg/f"{sub}_task-memory_events.tsv"; setp=eeg/f"{sub}_task-memory_eeg.set"
        trials=event_trials(evp)
        t13=[t for t in trials if t["load"]==13]
        chosen={cond:next(t for t in t13 if t["condition"]==cond) for cond in ("control","memory")}
        with h5py.File(setp,"r") as h:
            n=int(h["data"].shape[0]); nc=int(h["data"].shape[1])
        if nc!=63: raise ValueError(f"{sub}: expected 63 channels, got {nc}")
        for cond,t in chosen.items():
            if t["end"]>n: raise ValueError(f"event outside data {sub} {cond}")
            event_cases.append((sub,cond,t,n,evp,setp))
        hashes[str(evp)]=sha(evp); hashes[str(setp)]=sha(setp)
    # Each boundary case is one-channel-equivalent; four perturbations are processed together.
    for sub,cond,t,n,evp,setp in event_cases:
        for orient,boundary in (("trial_start",t["start"]),("trial_end",t["end"])):
            arr,inj,bst,wave_rms=make_signals(n,boundary,orient)
            stages=process(arr)
            boundary_out=int(round(boundary*SFREQ_OUT/SFREQ_IN))
            start_out=int(round(t["start"]*SFREQ_OUT/SFREQ_IN)); end_out=int(round(t["end"]*SFREQ_OUT/SFREQ_IN))
            # Nominal historical load-13 full-v3 window: first digit through +20 s.
            full_end=min(start_out+20*int(SFREQ_OUT),end_out)
            if orient=="trial_end":
                gap_samples=max(0,boundary_out-full_end)
                actual_idx=np.arange(start_out,full_end,dtype=int)
                for stage,data in stages.items():
                    for k,name in enumerate(("impulse_100uV","burst_10Hz","burst_30Hz","burst_80Hz")):
                        car=18/19
                        record=stats(data[k,actual_idx],100e-6,wave_rms[k],car)
                        recall.append({"subject":sub,"condition":cond,"stage":stage,"waveform":name,
                                       "window_start_sample_250hz":start_out,"window_end_sample_250hz_exclusive":full_end,
                                       "recall_boundary_sample_250hz":boundary_out,"gap_seconds":gap_samples/SFREQ_OUT,
                                       **record})
            for gi,g in enumerate(GUARDS):
                gsample=int(math.ceil(g*SFREQ_OUT-1e-12))
                if orient=="trial_start":
                    left=boundary_out+gsample; right=min(boundary_out+20*int(SFREQ_OUT),end_out)
                else:
                    left=max(boundary_out-20*int(SFREQ_OUT),start_out); right=boundary_out-gsample
                for stage,data in stages.items():
                    for k,name in enumerate(("impulse_100uV","burst_10Hz","burst_30Hz","burst_80Hz")):
                        car=18/19
                        rec=stats(data[k,left:right],100e-6,wave_rms[k],car)
                        guards.append({"subject":sub,"condition":cond,"boundary":orient,"guard_seconds":g,
                                       "stage":stage,"waveform":name,"sample_start_250hz":left,"sample_end_250hz_exclusive":right,**rec})
            # Summary maxima across unguarded, trial-local 20-second neighborhood for stage curves.
            for stage,data in stages.items():
                for k,name in enumerate(("impulse_100uV","burst_10Hz","burst_30Hz","burst_80Hz")):
                    leakage.append({"subject":sub,"condition":cond,"boundary":orient,"stage":stage,"waveform":name,
                                    "source_injection_sample":inj,"source_burst_start_sample":bst,"source_recording_samples":n,
                                    "source_sfreq_hz":SFREQ_IN,"target_boundary_sample_250hz":boundary_out,
                                    "source_input_rms_uv":wave_rms[k]*1e6,"core19_average_reference_max_effect_factor":18/19})
            print(f"completed {sub} {cond} {orient}",flush=True)
            del arr,stages
    # Summarize all-cases operational guard, using complete-chain stage only.
    gb=[r for r in guards if r["stage"]=="bandpass"]
    guard_summary=[]
    operational=None
    for g in GUARDS:
        rows=[r for r in gb if r["guard_seconds"]==g]
        nonempty=[r for r in rows if r["n"]>0]
        passed=bool(rows) and len(nonempty)==len(rows) and all(r["pass"] for r in rows)
        guard_summary.append({"guard_seconds":g,"case_count":len(rows),"nonempty_case_count":len(nonempty),"all_cases_pass":passed,
                              "max_peak_ratio":max((r["max_peak_ratio"] for r in nonempty),default=None),
                              "max_rms_stimulus_ratio":max((r["rms_stimulus_ratio"] for r in nonempty),default=None)})
        if operational is None and passed: operational=g
    def write_csv(path,rows):
        if not rows:return
        with path.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write_csv(OUT/"guard_grid_all_cases.csv",guards)
    write_csv(OUT/"recall_window_leakage.csv",recall)
    with (OUT/"guard_summary.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(guard_summary[0]));w.writeheader();w.writerows(guard_summary)
    report={"schema":"mnps.filter_support_001_pilot.v1","created_utc":datetime.now(timezone.utc).isoformat(),
            "dataset":"OpenNeuro ds003838 v1.0.6","participants":list(SUBJECTS),"target_trial_count":len(event_cases),
            "boundary_case_count":len(event_cases)*2,"stimulus_count_per_boundary":4,"mne_version":mne.__version__,
            "mne_resample":{"method":"frequency-domain FFT","window":"boxcar","npad":"auto","pad":"reflect_limited"},
            "notch":{"frequency_hz":50,"method":"FIR zero-phase Hamming firwin","length_samples":825,"sfreq_hz":250},
            "bandpass":{"low_hz":1,"high_hz":45,"method":"FIR zero-phase Hamming firwin","length_samples":825,"sfreq_hz":250},
            "combined_fir_half_support_seconds":3.296,"fft_resampling_finite_support":False,
            "stimuli":{"impulse_peak_uv":100,"bursts_hz":[10,30,80],"burst_duration_seconds":1,"window":"Hann","peak_uv":100},
            "tolerance_fraction":1e-4,"core19_average_reference":"single-channel perturbation projected through 19-channel average reference; max response factor 18/19",
            "operational_guard_seconds":operational,"no_finite_guard_within_grid":operational is None,
            "guard_summary":guard_summary,"source_hashes":hashes,
            "trial_end_window_leakage_rows":len(recall),"full_cohort_run":False,"classifier_fit":False}
    (OUT/"run_manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"operational_guard_seconds":operational,"guard_summary":guard_summary,"output":str(OUT)},indent=2),flush=True)
if __name__=="__main__":main()
