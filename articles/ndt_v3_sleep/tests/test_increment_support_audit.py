import csv
from pathlib import Path
import numpy as np
import pytest
from src.increment_support_audit import audit_rows, build_pool

def make_h5():
    class Dataset:
        def __init__(self,a): self.a=np.asarray(a)
        def __getitem__(self,k): return self.a
    class F:
        def __init__(self): self.d={'/epoch_id':np.arange(4),'/window_start':np.array([0.,30,60,90]),'/window_end':np.array([30.,60,90,120]),'/time':np.array([15.,45,75,105]),'/labels/stage':np.array([0,0,8,1]),'/row_source/raw_file':np.array([b'a']*4),'/coords_3d_subject_anchored/values':np.ones((4,3))}
        def __getitem__(self,k): return Dataset(self.d[k])
    return F()

def row(**kw):
    d={'query_epoch_id':'0','query_index':'0','query_stage_code':'0','query_stage_unknown':'0','query_window_start':'0','query_window_end':'30','selection_index':'0','source_epoch_id':'0','source_index':'0','source_stage_code':'0','source_stage_unknown':'0','source_window_start':'0','source_window_end':'30','target_epoch_id':'1','target_index':'1','target_stage_code':'0','target_stage_unknown':'0','target_window_start':'30','target_window_end':'60','distance_squared':'1','dt_sec':'30','kth_distance_tie_ambiguous':'0'}; d.update({k:str(v) for k,v in kw.items()}); return d

def test_gap_and_unknown_are_visible_and_not_eligible():
    out=audit_rows([row(), row(query_epoch_id='1',query_index='1',query_window_start='30',query_window_end='60',source_epoch_id='1',source_index='1',source_stage_code='0',source_stage_unknown='0',target_epoch_id='2',target_index='2',target_stage_code='8',target_stage_unknown='1',target_window_start='60',target_window_end='90',source_window_start='30',source_window_end='60')], make_h5(),30,.05)
    assert out[0]['structurally_admissible']==1 and out[0]['same_known_stage']==1
    assert out[1]['same_known_stage']==0

def test_dt_limit_and_nonfinite_endpoint_fail_closed():
    f=make_h5(); f.d['/coords_3d_subject_anchored/values'][1,0]=np.nan
    out=audit_rows([row(dt_sec='32')],f,30,.05)
    assert out[0]['structurally_admissible']==0
    assert out[0]['dt_exact']==0 and out[0]['finite_endpoints']==0

def test_nonconsecutive_and_non_touching_fail():
    f=make_h5(); f.d['/window_start'][1]=31
    out=audit_rows([row(target_epoch_id='2',target_index='2',target_stage_code='8',target_stage_unknown='1',target_window_start='60',target_window_end='90')],f,30,.05)
    assert out[0]['source_target_consecutive']==0 and out[0]['touching_windows']==0

def test_build_pool_contains_all_three_adjacent_pairs_and_unknown():
    pool = build_pool(make_h5(), 30, .05)
    assert len(pool) == 3
    assert [r['source_stage_h5'] for r in pool] == [0, 0, 8]
    assert pool[1]['touches_code8'] == 1
    assert pool[2]['touches_code8'] == 1

def test_build_pool_exposes_gap_rawfile_and_nonfinite_failures():
    f = make_h5()
    f.d['/window_start'][2] = 61
    f.d['/row_source/raw_file'][2] = b'other'
    f.d['/coords_3d_subject_anchored/values'][3, 1] = np.nan
    pool = build_pool(f, 30, .05)
    assert pool[1]['structurally_admissible'] == 0
    assert pool[2]['structurally_admissible'] == 0
    assert pool[2]['finite_endpoints'] == 0
