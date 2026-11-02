"""Independent structural check of the two nominated endpoints; no effect estimates."""
from pathlib import Path
from collections import Counter,defaultdict
from math import comb
import hashlib,json
import h5py,numpy as np

ROOT=Path('J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_ds004100_20260918_083008')
OUT=Path(__file__).resolve().parent
PRODUCTS={
 'one_step_lag1':'dynamical_families/one_step/v1/affine_one_step_map_level2',
 'one_step_lag2':'dynamical_families/one_step/v1/declared_lag_2/affine_one_step_map_level2',
 'iterated_one_step':'dynamical_families/one_step/v1/iterated_one_step_horizon_map_level4',
 'history_gain':'dynamical_families/history/v1/history_predictive_gain_level1',
 'history_operator':'dynamical_families/history/v1/history_conditioned_operator_level2',
 'drift_blocked':'dynamical_families/drift/v1/conditional_mean_rate_level1/blocked_crossfit',
}

def string(v):return v.decode() if isinstance(v,bytes) else str(v)
def scalar(g,k):return string(g[k][()]) if k in g else 'not_recorded'
def p_tail(k,n):return sum(comb(n,j) for j in range(k,n+1))/2**n
def holm(p):
    order=np.argsort(p);out=[0.]*len(p);running=0.
    for rank,idx in enumerate(order):
        running=max(running,(len(p)-rank)*p[idx]);out[idx]=min(1.,running)
    return out

def mask_h1(values,valid):
    if values.shape!=valid.shape or values.ndim!=1:raise ValueError('H1 native masks misaligned')
    return np.isfinite(values)&(valid==1)

def mask_h2(values,idx,pairs):
    if values.shape!=pairs.shape or values.ndim!=1:raise ValueError('H2 native arrays misaligned')
    if len(np.unique(idx))!=len(idx) or np.any(idx<0) or np.any(idx>=len(values)-1):raise ValueError('Invalid source indices')
    m=np.zeros(len(values),dtype=bool);m[idx]=True
    return m&np.isfinite(values)&(pairs>0)

def main():
    # A valid terminal H1 query is not excluded merely because no increment starts there.
    assert mask_h1(np.ones(4),np.ones(4)).sum()==4
    assert mask_h2(np.array([1.,1.,np.nan,np.nan]),np.array([0,1,2]),np.array([2,2,0,0])).sum()==2
    assert mask_h1(np.array([1.,np.nan,2.]),np.array([1,1,0])).sum()==1
    try:mask_h2(np.ones(3),np.array([0,0]),np.ones(3))
    except ValueError:pass
    else:raise AssertionError('Duplicate indices must fail')
    # Two hypotheses, including an unavailable p=1; ties stay in N.
    assert holm([.01,.04])==[.02,.04]
    assert holm([.01,1.])==[.02,1.]
    assert p_tail(8,20)>.05
    rows=[];subjects=defaultdict(lambda:defaultdict(set));status_counts=defaultdict(Counter);reach_steps=[]
    for p in sorted(ROOT.rglob('*.h5')):
        with h5py.File(p,'r') as f:
            n=len(f['time']);r={'file':str(p.relative_to(ROOT)),'subject':string(f.attrs['subject_id']),'task':string(f.attrs['task']),'n_time':n}
            g=f['dynamical_families/diffusion/v1'];s=g['series']
            valid=mask_h1(s['diffusion_effective_dimension'][:],s['valid'][:]);r['H1_valid_centers']=int(valid.sum())
            r['H1_status']=scalar(g,'computation_status');r['H1_support']=scalar(g,'support_status')
            r['H1_eligible']=r['H1_status']=='computed' and r['H1_support']=='sufficient' and valid.sum()>=30 and valid.sum()>=.5*n
            g=f['dynamical_families/amplification/v1/neighbor_gain_q90_level1'];s=g['series']
            valid=mask_h2(s['neighbor_gain_q90'][:],s['source_idx'][:],s['n_neighbor_pairs'][:]);r['H2_valid_centers']=int(valid.sum())
            r['H2_status']=scalar(g,'computation_status');r['H2_support']=scalar(g,'support_status')
            r['H2_eligible']=r['H2_status']=='computed' and r['H2_support']=='sufficient' and valid.sum()>=30 and valid.sum()>=.5*n
            for h in ['H1','H2']:
                r[h+'_eligible']=bool(r[h+'_eligible'])
                if r[h+'_eligible']:subjects[h][r['subject']].add(r['task'])
            r['nested_statuses']={k:scalar(f[path],'computation_status') if path in f else 'absent' for k,path in PRODUCTS.items()}
            for k,v in r['nested_statuses'].items():status_counts[k][v]+=1
            key='stochastic_reachability/v1/primary/n_propagator_steps'
            if key in f:reach_steps.append(int(f[key][()]))
            rows.append(r)
    summary={'files':len(rows),'structural_eligible_files':{h:sum(r[h+'_eligible'] for r in rows) for h in ['H1','H2']},
      'structural_paired_subjects':{h:sum({'ictal','interictal'}<=v for v in subjects[h].values()) for h in ['H1','H2']},
      'notes':'Numeric support only; source identity, feature signature and processed-contact/reference gates remain separate. No medians, effects or empirical p-values computed.',
      'synthetic_rule_checks':'PASS: masks, terminal query, duplicate rejection, Holm and ties',
      'nested_computation_status_counts':dict(status_counts),
      'primary_reachability_n_propagator_steps_range':[min(reach_steps),max(reach_steps)],
      'first_Holm_step_negative_count_required':{str(n):next(k for k in range(n+1) if p_tail(k,n)<=.025) for n in [20,30,55]},
      'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT/'endpoint_support_checks.json').write_text(json.dumps({'summary':summary,'rows':rows},indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
