"""Read only source sidecars linked by H5 identities; no waveform or effect analysis."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import h5py
import numpy as np

BASE = Path(__file__).resolve().parent
H5_ROOT = Path('J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_ds004100_20260918_083008')
SOURCE = Path('K:/ExternalReceivedDatasets/openneuro/ds004100')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def txt(v):
    return v.decode() if isinstance(v,bytes) else str(v)

def read_tsv(p):
    with p.open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream,delimiter='\t'))

def main():
    rows=[]; hashes={}; groups=defaultdict(list)
    for p in sorted(H5_ROOT.rglob('*.h5')):
        with h5py.File(p,'r') as f:
            a={k:txt(f.attrs[k]) for k in ['subject_id','session','task','acq','run']}
            stem=f"{a['subject_id']}_{a['session']}_task-{a['task']}_{a['acq']}_{a['run']}"
            folder=SOURCE/a['subject_id']/a['session']/'ieeg'
            info=folder/(stem+'_ieeg.json'); channels=folder/(stem+'_channels.tsv'); events=folder/(stem+'_events.tsv')
            row={'h5':str(p.relative_to(H5_ROOT)),**a,
                 'source_ieeg_json':info.exists(),'source_channels_tsv':channels.exists(),
                 'source_events_tsv':events.exists(),'seizure_intervals':[],
                 'annotation_status':'not_recorded','nominal_seizure_contained_windows':None}
            for q in [info,channels,events]:
                if q.exists(): hashes[str(q.relative_to(SOURCE))]=sha(q)
            if info.exists():
                j=json.loads(info.read_text());row.update({k:j.get(k) for k in ['RecordingDuration','SamplingFrequency','iEEGReference','TaskName']})
                row['h5_window_end_within_source_duration']=bool(float(np.max(f['window_end'][:])) <= j.get('RecordingDuration',-1)+1e-6)
                excess=float(np.max(f['window_end'][:]))-j.get('RecordingDuration',-1)
                row['nominal_duration_excess_sec']=excess
                row['h5_end_within_one_source_sample']=bool(excess <= 1/float(j['SamplingFrequency'])+1e-6)
            if channels.exists():
                ch=read_tsv(channels);row['n_source_channels']=len(ch)
                sig=sorted((c.get('name'),c.get('type'),c.get('status')) for c in ch)
                row['channel_name_type_status_hash']=hashlib.sha256(json.dumps(sig).encode()).hexdigest()
                groups[(a['subject_id'],a['session'],a['acq'])].append(row['channel_name_type_status_hash'])
            if events.exists():
                ev=read_tsv(events);pending=None;intervals=[];valid=True
                for e in sorted(ev,key=lambda z:float(z['onset'])):
                    kind=e.get('trial_type','').lower().strip();t=float(e['onset'])
                    if kind=='sz onset':
                        if pending is not None:valid=False
                        pending=t
                    elif kind=='sz offset':
                        if pending is None or t<=pending:valid=False
                        else:intervals.append([pending,t])
                        pending=None
                valid=valid and pending is None and bool(intervals)
                row['annotation_status']='onset_offset_pairs' if valid else 'unresolved_event_structure'
                row['seizure_intervals']=intervals
                if valid:
                    start=f['window_start'][:];end=f['window_end'][:];mask=np.zeros(len(start),dtype=bool)
                    for lo,hi in intervals:mask|=(start>=lo)&(end<=hi)
                    row['nominal_seizure_contained_windows']=int(mask.sum())
            rows.append(row)
    metadata=SOURCE/'dataset_description.json';hashes[metadata.name]=sha(metadata)
    summary={'source':str(SOURCE),'h5_root':str(H5_ROOT),'n_files':len(rows),
        'source_version':json.loads(metadata.read_text()).get('DatasetDOI'),
        'source_file_counts':{k:sum(r[k] for r in rows) for k in ['source_ieeg_json','source_channels_tsv','source_events_tsv']},
        'event_status_by_label':{label:dict(Counter(r['annotation_status'] for r in rows if r['task']==label)) for label in ['ictal','interictal']},
        'channel_signature_groups':len(groups),'groups_with_multiple_channel_signatures':sum(len(set(v))>1 for v in groups.values()),
        'reference_values':dict(Counter(str(r.get('iEEGReference')) for r in rows)),
        'nominal_seizure_windows_ge30':sum((r['nominal_seizure_contained_windows'] or 0)>=30 for r in rows),
        'subjects_with_nominal_seizure_windows_ge30':len({r['subject_id'] for r in rows if (r['nominal_seizure_contained_windows'] or 0)>=30}),
        'source_task_matches':sum(r.get('TaskName')==r['task'] for r in rows),
        'h5_end_within_recording_duration':sum(r['h5_window_end_within_source_duration'] for r in rows),
        'h5_end_within_one_source_sample':sum(r['h5_end_within_one_source_sample'] for r in rows),
        'nominal_seizure_windows_range':[min(r['nominal_seizure_contained_windows'] for r in rows if r['nominal_seizure_contained_windows'] is not None),max(r['nominal_seizure_contained_windows'] for r in rows if r['nominal_seizure_contained_windows'] is not None)],
        'limitations':['Only sidecars read; no EDF waveforms opened','Filename/entity linkage, not a certified original-sample mapping','Nominal interval containment ignores unknown filter support and whole-recording estimator neighborhoods','Stable raw channel signatures do not establish preprocessing reference/retained contacts'],
        'script_sha256':sha(Path(__file__))}
    (BASE/'source_metadata_audit.json').write_text(json.dumps({'summary':summary,'rows':rows,'source_sidecar_sha256':hashes},indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
