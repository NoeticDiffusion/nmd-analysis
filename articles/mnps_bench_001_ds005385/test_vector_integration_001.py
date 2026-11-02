"""Focused checks of forecasting mathematics and support eligibility."""
import importlib.util
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("integration", Path(__file__).with_name("run_vector_integration_001.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def traces():
    fast = [{"start":e-4,"end":e,"value":[.1,.2,.3,.4],"conventional":[1.]*6} for e in range(8,161,4)]
    context = [{"start":e-20,"end":e,"value":[.2,.3,.4,.5],"conventional":[1.]*6} for e in range(112,157,4)]
    return {"p":{"fast":fast,"context":context}}


def test_common_rows_and_support():
    rows,excluded = runner.build_rows(traces())
    assert not excluded
    assert sum(r["horizon"]==1 for r in rows)==8
    assert sum(r["horizon"]==2 for r in rows)==7
    assert all(r["history"].shape==(24,4) for r in rows)
    assert rows[0]["origin"] == 128


def test_missing_target_or_history_does_not_zero_fill():
    trace = traces()
    trace["p"]["fast"][-2]["value"] = None
    rows,excluded = runner.build_rows(trace)
    assert excluded and all(np.isfinite(r["history"]).all() for r in rows)
    assert not any(r["origin"]==152 and r["horizon"]==2 for r in rows)


def test_gap_and_out_of_span_context_excluded():
    trace = traces()
    trace["p"]["fast"][10]["start"] += 1
    rows,excluded = runner.build_rows(trace)
    assert any(r["reason"]=="noncontiguous_time_grid" for r in excluded)
    trace = traces()
    trace["p"]["context"][0]["start"] = 0
    rows,excluded = runner.build_rows(trace)
    assert any(r["reason"]=="context_outside_common_history_support" for r in excluded)


def test_ar_known_linear_relationship_and_training_only_scaling():
    rng = np.random.default_rng(7)
    x = rng.normal(size=(1000,1))
    y = .72*x + .13
    test = np.array([[-3.],[2.],[900.]])
    pred = runner.ridge(x,y,test,alpha=0)
    np.testing.assert_allclose(pred,.72*test+.13,atol=1e-10)
    pred_single = runner.ridge(x,y,test[:1],alpha=0)
    np.testing.assert_allclose(pred_single,pred[:1],atol=1e-12)


def test_candidate_local_null_and_named_AR_median():
    result = {"measurements":[{"candidate_id":c,"computed":True,"valid":True,"value":[1.,4.,2.] if c=="M3" else .2} for c in runner.CONTEXT_IDS]}
    assert runner.vector(result,runner.CONTEXT_IDS)[0]==2
    result["measurements"][0]["computed"] = False
    assert runner.vector(result,runner.CONTEXT_IDS) is None


def test_actual_coordinatewise_AR_forecast_recovers_synthetic_case():
    rng = np.random.default_rng(11)
    factors = np.array([.55,.70,.80,.90])
    offset = np.array([.05,.10,.15,.20])
    rows = []
    for _ in range(410):
        history = rng.normal(size=(24,4))
        current = history[-1]
        rows.append({"history":history,"current":current,"target":factors*current+offset,
                     "context":rng.normal(size=4),"wrong":rng.normal(size=4),
                     "conventional":rng.normal(size=6)})
    predictions = runner.fit_models(rows[:400],rows[400:])
    target = np.stack([r["target"] for r in rows[400:]])
    np.testing.assert_allclose(predictions["A1_AR1"],target,atol=.01)
    np.testing.assert_allclose(predictions["A2_AR2"],target,atol=.01)
    assert runner.rmse(predictions["A1_AR1"]-target) < runner.rmse(predictions["A0_persistence"]-target)/20
