import json, sys
from pathlib import Path
import h5py, numpy as np, pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.stage_dependency_audit import audit

def make_h5(tmp_path):
    p=tmp_path/'x.h5'
    with h5py.File(p,'w') as h:
        h['epoch_id']=np.arange(3); h['time']=[0.,1.,2.]; h['window_start']=[0.,1.,2.]; h['window_end']=[1.,2.,3.]; h['labels/stage']=[0,8,2]
    return p

POLICY = Path(__file__).resolve().parents[1] / 'stage_dependency_policy_20260910.json'

def test_descriptive_unknown_and_code8(tmp_path, monkeypatch):
    p=make_h5(tmp_path); policy=POLICY
    mod=type(sys)('nmd_analysis.signal_support'); mod.__file__=__file__; mod.read_signal_support=lambda p:{'status':'legacy_missing','reference_fit_population':{'status':'unknown'}}; monkeypatch.setitem(sys.modules,'nmd_analysis.signal_support',mod)
    r=audit([p],policy,tmp_path/'out'); s=r['sources'][0]
    assert s['code8_source_quality_rows']==1 and s['qualified_increment_count'] is None

def test_malformed_reader_fails_with_diagnostic(tmp_path, monkeypatch):
    p=make_h5(tmp_path); policy=POLICY
    mod=type(sys)('nmd_analysis.signal_support'); mod.__file__=__file__; mod.read_signal_support=lambda p:{'status':'malformed'}; monkeypatch.setitem(sys.modules,'nmd_analysis.signal_support',mod)
    with pytest.raises(RuntimeError): audit([p],policy,tmp_path/'out')
    assert (tmp_path/'out'/'stage_dependency_audit.json').exists()
