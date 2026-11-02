"""Independent preprimary tests; all stochastic seeds are nonprimary."""
import copy
import os
from pathlib import Path
import sys
import numpy as np
import pytest
from scipy.integrate import cumulative_trapezoid, quad

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nmd_analysis.dynamical_families import trans_adapter_benchmark as base
from nmd_analysis.dynamical_families import trans_adapter_convergence as conv

def packet(paths,labels):
    lengths=np.array([len(p) for p in paths])
    return {'reaction':np.concatenate(paths).astype(float),'offsets':np.r_[0,np.cumsum(lengths)].astype(np.int64),'terminal_labels':np.array(labels,dtype=np.int64),'path_starts':np.array([p[0] for p in paths]),'dt':base.DT,'horizon':(max(lengths)-1)*base.DT,'n_steps':int(max(lengths)-1),'n_paths':len(paths),'D':.2}

def fixture():
    x=np.repeat(np.clip(np.linspace(-1,1,65),-.999999,.999999),32)
    y=x+(x-x**3)*base.DT+np.tile([-1.,1.],len(x)//2)*np.sqrt(.4*base.DT)
    labels=np.where(y<=-1,0,np.where(y>=1,1,-1))
    return packet(list(zip(x,y)),labels)

def oracle(grid):
    f=lambda x: np.exp((x**4/4-x*x/2)/.2)
    denominator=quad(f,-1,1,epsabs=1e-12)[0]
    return np.array([quad(f,-1,x,epsabs=1e-12)[0]/denominator for x in grid])

def test_partition_additivity_and_no_cross_path_increment():
    paths=[[-.9,-1.03],[.9,1.04],[0,.1,.2]]
    whole=conv.chunk_statistics(packet(paths,[0,1,-1]))
    a=conv.chunk_statistics(packet(paths[:2],[0,1]))
    b=conv.chunk_statistics(packet(paths[2:],[-1]))
    joined=conv.merge_statistics([a,b])
    for key in ['support','drift_sum','oracle_drift_sum']:
        np.testing.assert_allclose(joined[key],whole[key],rtol=0,atol=1e-12)
    assert np.sum(whole['support'])==4
    assert whole['n_A']==whole['n_B']==whole['n_unresolved']==1

def test_streaming_matches_unchanged_adapter():
    ingest=os.environ.get('NMD_INGEST_ROOT')
    if not ingest: pytest.skip('NMD_INGEST_ROOT required')
    p=fixture()
    streamed=conv.fit_statistics(conv.chunk_statistics(p))
    actual=base.fit_adapter(p,ingest_root=ingest)
    assert streamed['computation_status']==actual['computation_status']=='computed'
    np.testing.assert_array_equal(streamed['support'],actual['grid_support_count'])
    np.testing.assert_allclose(streamed['drift'],actual['drift_estimate_grid'],atol=2e-6,rtol=0)
    np.testing.assert_allclose(streamed['q_grid'],actual['q_grid'],atol=2e-7,rtol=0)

@pytest.mark.parametrize('grid_size',[65,129,257])
def test_known_drift_quadrature_is_separate_and_accurate(grid_size):
    x=np.linspace(-1,1,grid_size)
    q=conv.integrate_drift(x-x**3,x)
    assert q[0]==0 and q[-1]==1 and np.all(np.diff(q)>0)
    assert np.max(abs(q-oracle(x)))<.001

@pytest.mark.parametrize('paths,labels',[
    ([[.9,1.02,-1.02]],[0]),([[0,np.nan]],[-1]),([[0,.2]],[255]),
    ([[-.9,-1.02]],[256]),([[0,1.02]],[-1])])
def test_malformed_packet_refused(paths,labels):
    with pytest.raises(ValueError): conv.chunk_statistics(packet(paths,labels))

def test_gap_refused_before_streaming():
    p=base.pack_training(packet([[0,.1,.2]],[-1]))
    p['time'][1]+=base.DT/2
    with pytest.raises(ValueError): conv.chunk_statistics(p)

def test_missing_support_remains_unavailable():
    p=fixture(); pairs=p['reaction'].reshape(-1,2)
    keep=np.abs(pairs[:,0])>.01
    fit=conv.fit_statistics(conv.chunk_statistics(packet(pairs[keep],p['terminal_labels'][keep])))
    assert fit['computation_status']=='insufficient_support' and fit['q_grid'] is None

def test_no_transitions_remains_not_testable():
    fit=conv.fit_statistics(conv.chunk_statistics(packet([[0,.1]]*32,[-1]*32)))
    assert fit['computation_status']=='not_testable' and fit['q_grid'] is None

def test_occupancy_diagnostic_decomposition_is_algebraic():
    fit=conv.fit_statistics(conv.chunk_statistics(fixture()))
    x=np.linspace(-1,1,65); truth=oracle(x); grid_q=conv.integrate_drift(x-x**3,x)
    q=np.array(fit['q_grid']); occupancy=np.array(fit['occupancy_q_grid'])
    np.testing.assert_allclose((q-occupancy)+(occupancy-grid_q)+(grid_q-truth),q-truth,atol=1e-15,rtol=0)

def test_small_seed_simulation_preserves_overshoot_statistics():
    p=base.simulate_paths(np.resize([-.999,.999],32),seed=1002,horizon=16*base.DT)
    s=conv.chunk_statistics(p)
    assert sum(s['support'])==len(p['reaction'])-32
    assert s['n_A']+s['n_B']>0
    assert np.any(np.abs(p['reaction'][p['offsets'][1:]-1])>1)

def summary_rows():
    fitted=conv.fit_statistics(conv.chunk_statistics(fixture()))
    rows=[]
    for rep in range(16):
        for size in [512,2048,8192]:
            row=copy.deepcopy(fitted)
            row.update(rep=rep,n_paths=size)
            if size==512: row['equivalence']={'equivalent':True}
            rows.append(row)
    return rows

def test_recovery_precedence_and_missing_equivalence():
    rows=summary_rows()
    assert conv.summarize_convergence(rows)['recovery_decision']=='PASS'
    rows[2].update(status='insufficient_support',computation_status='insufficient_support',q_grid=None,query_predictions=None,query_errors=None)
    assert conv.summarize_convergence(rows)['recovery_decision']=='INCONCLUSIVE'
    rows[5]['query_errors']=np.full(5,.06)
    rows[5]['query_predictions']=np.array(rows[5]['query_truth'])+.06
    assert conv.summarize_convergence(rows)['recovery_decision']=='FAIL'
    rows=summary_rows(); rows[0]['equivalence']['equivalent']=False
    assert conv.summarize_convergence(rows)['recovery_decision']!='PASS'

@pytest.mark.parametrize('bad',[np.full(5,np.nan),np.zeros(6)])
def test_malformed_query_errors_cannot_pass(bad):
    rows=summary_rows();rows[2]['query_errors']=bad
    try: result=conv.summarize_convergence(rows)
    except ValueError: return
    assert result['recovery_decision']!='PASS'

def test_duplicate_chunks_and_repetitions_refused():
    s=conv.chunk_statistics(fixture());s.update(rep=0,chunk=0)
    with pytest.raises(ValueError): conv.merge_statistics([s,s])
    rows=summary_rows();rows.append(copy.deepcopy(rows[0]))
    with pytest.raises(ValueError): conv.summarize_convergence(rows)

def test_tiny_packet_status_matches_original(ingest_root=None):
    ingest=os.environ.get('NMD_INGEST_ROOT')
    if not ingest: pytest.skip('NMD_INGEST_ROOT required')
    p=packet([[0,.1]],[-1])
    a=conv.fit_statistics(conv.chunk_statistics(p)); b=base.fit_adapter(p,ingest_root=ingest)
    assert (a['computation_status'],a['failure_reason'])==(b['computation_status'],b['failure_reason'])

def test_failed_equivalence_keeps_raw_violation_but_blocks_qualification():
    rows=summary_rows()
    rows[0]['equivalence']['equivalent']=False
    rows[2]['query_errors']=np.full(5,.06)
    rows[2]['query_predictions']=np.array(rows[2]['query_truth'])+.06
    result=conv.summarize_convergence(rows)
    assert result['raw_recovery_screen_decision']=='FAIL'
    assert result['numerical_equivalence_decision']=='FAIL'
    assert result['recovery_decision']=='INCONCLUSIVE'
