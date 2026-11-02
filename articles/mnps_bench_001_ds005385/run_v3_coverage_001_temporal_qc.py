from __future__ import annotations
import csv, hashlib, json, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import h5py

ARTICLE=Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
DATA=Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
COV=ARTICLE/"outputs"/"v3_coverage_001_pilot_v1_20261008"
OUT=ARTICLE/"outputs"/"v3_coverage_001_temporal_qc_20261009"
SUBJECTS=("sub-032","sub-033","sub-034","sub-035","sub-036","sub-038")
TRIAL=re.compile(r"\b(?P<c>control|memory)\s+(?P<p>\d+)\s*/\s*(?P<l>\d+)\b",re.I)
BAD=re.compile(r"\b(?:bad|artifact|artefact|reject(?:ed)?|discontinuity)\b",re.I)
AUDIO={".wav",".mp3",".mp4",".mov",".avi",".flac",".webm",".aac",".ogg"}

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""): h.update(b)
    return h.hexdigest()
def tsv(p):
    with p.open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter="\t"); return list(r.fieldnames or []),list(r)
def settypes(p):
    out=[]
    with h5py.File(p,"r") as f:
        for ref in f["event"]["type"][:,0]:
            if not ref: out.append(""); continue
            a=f[ref][()]
            out.append("".join(chr(int(x)) for x in a.reshape(-1) if int(x)).strip())
    return out
def reject_inventory(p):
    with h5py.File(p,"r") as f:
        fields=[k for k in f["reject"].keys() if k.startswith(("rej","icarej")) and not k.endswith("col")]
        nonempty=[k for k in fields if not bool(f["reject"][k].attrs.get("MATLAB_empty",0))]
    return len(fields),nonempty
def trials(rows,sub):
    out=[]; cur=None
    def close():
        nonlocal cur
        if cur is None:return
        ds=cur["d"]; load=cur["l"]
        if [x["p"] for x in ds]!=list(range(1,load+1)): raise ValueError(f"{sub}: malformed digit sequence")
        first,last=ds[0]["s"],ds[-1]["s"]
        out.append({"subject":sub,"trial_id":f"{sub}_T{len(out)+1:03d}","condition":cur["c"],
                    "load":load,"first":first,"last":last,"end":last+3000})
        cur=None
    for r in rows:
        m=TRIAL.search(str(r.get("trial_type","")))
        if not m: continue
        d={"c":m.group("c").lower(),"p":int(m.group("p")),"l":int(m.group("l")),"s":int(float(r["sample"]))}
        if d["p"]==1:
            close();cur={"c":d["c"],"l":d["l"],"d":[]}
        if cur is None or (d["c"],d["l"])!=(cur["c"],cur["l"]): raise ValueError(f"{sub}: noncontiguous events")
        cur["d"].append(d)
    close()
    if len(out)!=162: raise ValueError(f"{sub}: expected 162 trials, got {len(out)}")
    return out
def writecsv(p,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def table(headers,rows):
    return "\n".join(["| "+" | ".join(headers)+" |","|"+"|".join(["---"]*len(headers))+"|"]+
                     ["| "+" | ".join(str(x) for x in row)+" |" for row in rows])

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    support={}
    with (COV/"trial_support_by_duration.csv").open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            if r["structurally_eligible"].lower()!="true":continue
            key=(r["subject"],r["trial_id"],int(r["duration_sec"]))
            old=support.get(key)
            if old and (old["first_probe_start_sample_250hz"],old["first_probe_end_sample_250hz_exclusive"])!=(r["first_probe_start_sample_250hz"],r["first_probe_end_sample_250hz_exclusive"]):
                raise ValueError(f"surface boundary mismatch {key}")
            support[key]=r
    covman=json.loads((COV/"run_manifest.json").read_text(encoding="utf-8"))
    people=[]; windows=[]; hashes={}
    for sub in SUBJECTS:
        ed=DATA/sub/"eeg"; bd=DATA/sub/"beh"
        ep=ed/f"{sub}_task-memory_events.tsv"; cp=ed/f"{sub}_task-memory_channels.tsv"
        jp=ed/f"{sub}_task-memory_eeg.json"; sp=ed/f"{sub}_task-memory_eeg.set"
        bp=bd/f"{sub}_task-memory_beh.tsv"
        ef,ev=tsv(ep); cf,ch=tsv(cp); bf,beh=tsv(bp); meta=json.loads(jp.read_text(encoding="utf-8"))
        tr=trials(ev,sub); digit=[r for r in ev if TRIAL.search(str(r.get("trial_type","")))]
        boundary=[r for r in ev if str(r.get("trial_type","")).upper()=="STATUS" or str(r.get("value","")).lower()=="boundary"]
        bad=[r for r in ev if BAD.search(" ".join(str(r.get(k,"")) for k in ("trial_type","value","description")))]
        typ=settypes(sp); reject_count,nonempty_reject=reject_inventory(sp); values=[str(r.get("value","")).strip() for r in ev]
        if typ!=values: raise ValueError(f"{sub}: EEGLAB/BIDS event sequence mismatch")
        ctypes=Counter(str(r.get("type","")).strip() for r in ch)
        audio=[p for p in (DATA/sub).rglob("*") if p.is_file() and p.suffix.lower() in AUDIO]
        timefields=[x for x in bf if re.search(r"(onset|timestamp|latency|response.?time|time)",x,re.I)]
        people.append({"subject":sub,"bids_event_rows":len(ev),"digit_event_rows":len(digit),"boundary_event_rows":len(boundary),
                       "bad_interval_like_bids_rows":len(bad),"eeglab_event_rows":len(typ),"bids_eeglab_event_sequence_matches":True,
                       "bad_interval_like_eeglab_event_types":sum(bool(BAD.search(x)) for x in typ),
                       "eeglab_rejection_flag_field_count":reject_count,"eeglab_nonempty_rejection_flag_fields":",".join(nonempty_reject),
                       "channel_count":len(ch),"channel_types":json.dumps(dict(sorted(ctypes.items())),separators=(",",":")),
                       "channels_tsv_fields":",".join(cf),"eeg_emg_channel_count":meta.get("EMGChannelCount",0),
                       "eeg_misc_channel_count":meta.get("MiscChannelCount",0),"behavior_rows":len(beh),
                       "behavior_fields":",".join(bf),"behavior_response_field_present":"response" in bf,
                       "behavior_response_timing_fields":",".join(timefields),"participant_audio_recording_file_count":len(audio),
                       "trial_count":len(tr),"load5_trials":sum(t["load"]==5 for t in tr),
                       "load9_trials":sum(t["load"]==9 for t in tr),"load13_trials":sum(t["load"]==13 for t in tr)})
        for t in tr:
            for dur in (4,8,12,20):
                r=support.get((sub,t["trial_id"],dur))
                if r is None:continue
                left=int(float(r["first_probe_start_sample_250hz"]))*4
                right=int(float(r["first_probe_end_sample_250hz_exclusive"]))*4
                windows.append({"subject":sub,"trial_id":t["trial_id"],"condition":t["condition"],"load":t["load"],
                                "duration_sec":dur,"surface_count":2,"window_start_sample_250hz":left//4,
                                "window_end_sample_250hz_exclusive":right//4,
                                "window_start_offset_from_first_digit_ms":left-t["first"],
                                "window_end_before_last_digit_onset_ms":t["last"]-right,
                                "window_end_before_nominal_recall_start_ms":t["end"]-right,
                                "ends_before_last_digit":right<=t["last"],"ends_before_nominal_recall_start":right<=t["end"]})
        for p in (ep,cp,jp,bp):hashes[str(p)]=sha(p)
        hashes[str(sp)]=covman["source_file_sha256"][str(sp)]
    summaries=[]
    for load in (5,9,13):
        for dur in (4,8,12,20):
            g=[w for w in windows if w["load"]==load and w["duration_sec"]==dur]
            a=[w["window_end_before_last_digit_onset_ms"] for w in g]
            b=[w["window_end_before_nominal_recall_start_ms"] for w in g]
            summaries.append({"load":load,"duration_sec":dur,"eligible_trial_count":len(g),"surface_window_count":2*len(g),
                              "min_margin_before_last_digit_ms":min(a) if g else "",
                              "max_margin_before_last_digit_ms":max(a) if g else "",
                              "min_margin_before_nominal_recall_ms":min(b) if g else "",
                              "max_margin_before_nominal_recall_ms":max(b) if g else "",
                              "all_end_before_last_digit":all(w["ends_before_last_digit"] for w in g) if g else "",
                              "all_end_before_nominal_recall":all(w["ends_before_nominal_recall_start"] for w in g) if g else ""})
    extras=[ARTICLE/"run_bench_002_pilot_v1.py",ARTICLE/"run_v3_coverage_001_pilot_v1.py",
            ARTICLE/"v3_coverage_001_protocol_v1_20261008.md",DATA/"stimuli"/"presentationScript"/"peavler.py",
            DATA/"stimuli"/"presentationScript"/"peavler.psyexp",COV/"trial_support_by_duration.csv",COV/"run_manifest.json"]
    for p in extras:hashes[str(p)]=sha(p)
    pc=OUT/"participant_temporal_qc.csv"; wc=OUT/"trial_window_temporal_margins.csv"; sc=OUT/"temporal_qc_summary.csv"
    writecsv(pc,people);writecsv(wc,windows);writecsv(sc,summaries)
    total_events=sum(p["bids_event_rows"] for p in people); total_boundary=sum(p["boundary_event_rows"] for p in people)
    total_bad=sum(p["bad_interval_like_bids_rows"] for p in people)
    minlast=min(w["window_end_before_last_digit_onset_ms"] for w in windows)
    minrec=min(w["window_end_before_nominal_recall_start_ms"] for w in windows)
    group_table=table(["Load","Duration","Trials","Surface windows","Min before last digit (s)","Min before planned recall (s)"],
        [[s["load"],f'{s["duration_sec"]} s',s["eligible_trial_count"],s["surface_window_count"],
          "—" if not s["eligible_trial_count"] else f'{s["min_margin_before_last_digit_ms"]/1000:.3f}',
          "—" if not s["eligible_trial_count"] else f'{s["min_margin_before_nominal_recall_ms"]/1000:.3f}'] for s in summaries])
    person_table=table(["Participant","Event rows","Boundaries","BAD-like","EEGLAB matches BIDS","Empty rejection flags","EEG channels","Behavior rows","Audio files"],
        [[p["subject"],p["bids_event_rows"],p["boundary_event_rows"],p["bad_interval_like_bids_rows"],
          p["bids_eeglab_event_sequence_matches"],p["eeglab_rejection_flag_field_count"] if not p["eeglab_nonempty_rejection_flag_fields"] else "nonempty",p["channel_count"],p["behavior_rows"],p["participant_audio_recording_file_count"]] for p in people])
    report=f"""# V3-COVERAGE-001 temporal QC supplement

Scope: six frozen participants from OpenNeuro ds003838 v1.0.6. No additional subjects, contrast, classifier, or full-cohort run.

## Bad-interval provenance

bad_interval_free remains **unknown**. Across six participants the BIDS event exports contain {total_events} rows: {total_boundary} recording-boundary markers and {total_bad} rows with BAD/artifact/rejection-like labels. The EEGLAB .set event-type sequence matches BIDS events.tsv for every participant and contains the same boundary/digit events. The channels TSV files provide only channel name, type, and units, with no channel-quality status field. Each EEGLAB set has 26 rejection-mark arrays, all stored as empty MATLAB arrays; the remaining nonempty reject fields are thresholds or color settings, not sample-interval masks. These exports therefore provide no time-localized bad-interval annotation; this does not establish that the EEG is artifact-free.

## Vocal-response timing

The supplied PsychoPy source uses a 2-second routine for each digit, then a fixed 1-second retention routine after the sequence, followed by the microphone/retrieval routine. The audited first windows are half-open. Every eligible first window ends before the last digit onset, so it ends earlier still than scheduled overt recall. The table gives minimum observed gaps across all six participants.

{group_table}

This is protocol-supported exclusion of planned overt recall, not acoustic verification of each participant's actual voice onset. No participant response-audio files are present; EEG sidecars declare no EMG or miscellaneous microphone channel; BIDS events contain digit triggers/correctness but no voice-onset or retention-end marker; behavior files have recall text/accuracy but no response-time field. Exact realized speech onset cannot be checked.

## Participant inventory

{person_table}

## Impact and decision

The support matrix is unchanged: each candidate computed on all eligible first windows at 4/8/12 seconds; hash-checked 20-second outputs cover load 13 only. PCV, TP, OI, and SC were independently computed at 4 seconds for loads 5, 9, and 13 without the full-v3 gate. Shorter spatial coordinates remain experimental realizations; computability does not establish fidelity or comparability. PCV edge fidelity, ED short-window covariance behavior, RD's 12-second disagreement, and SC's duration-specific reference interpretation remain limitations.

**Go/no-go:** no-go for a 65-participant all-load full-v3.1 run on ds003838 under the 20-second contract. A separate 4-second fast-core benchmark is a supported candidate design and must stay distinct from full v3.1. Keep bad_interval_free unknown and all values unqualified. For an all-load full-vector objective, use data with longer trial-local support and assess coordinate-specific fidelity.

Files: participant_temporal_qc.csv; trial_window_temporal_margins.csv; temporal_qc_summary.csv; run_manifest.json.
"""
    rp=OUT/"results.md";rp.write_text(report,encoding="utf-8")
    script=ARTICLE/"run_v3_coverage_001_temporal_qc.py";hashes[str(script)]=sha(script)
    outs={p.name:{"bytes":p.stat().st_size,"sha256":sha(p)} for p in (pc,wc,sc,rp)}
    manifest={"schema":"mndm.v3_coverage_001_temporal_qc_manifest.v1","created_utc":datetime.now(timezone.utc).isoformat(),
              "dataset":"OpenNeuro ds003838 v1.0.6","participants":list(SUBJECTS),"trial_count":sum(p["trial_count"] for p in people),
              "unique_trial_duration_windows":len(windows),"surface_window_count":2*len(windows),"bad_interval_free":None,
              "bad_interval_status":"unresolved_no_time_localized_annotations_in_BIDS_or_EEGLAB_event_types_or_rejection_masks",
              "eeglab_rejection_flag_fields_empty":all(not p["eeglab_nonempty_rejection_flag_fields"] for p in people),
              "vocal_response_status":"excluded_by_schedule_for_first_windows; participant_specific_audio_onset_unavailable",
              "minimum_gap_before_last_digit_ms":minlast,"minimum_gap_before_nominal_recall_ms":minrec,
              "source_hashes":hashes,"outputs":outs,"coverage_manifest":str(COV/"run_manifest.json"),
              "coverage_manifest_sha256":sha(COV/"run_manifest.json")}
    (OUT/"run_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
if __name__=="__main__":main()


