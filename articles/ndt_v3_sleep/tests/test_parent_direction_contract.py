import copy
import pytest
from src.compare_parent_stage_direction import COORDS, contrasts

def fixture():
    return {"scientific_qualification": "not_assessed", "representations": {
        rep: {"summary": [{"coordinate": f"mnps_{rep}_{name}", "stage_code": stage, "n": 3,
                            "median": 1.0 if stage == 0 else -1.0}
                           for name in names for stage in (0, 2)]}
        for rep, names in COORDS.items()}}

def test_all_coordinates_and_fixed_subtraction_direction():
    result=contrasts(fixture())
    assert len(result)==12
    assert all(r["n2_minus_wake_median"]==-2.0 and r["direction"]==-1 for r in result.values())

def test_empty_stage_is_unsupported_not_zero():
    s=fixture(); s["representations"]["3d"]["summary"][1].update(n=0,median=None)
    result=contrasts(s)[("3d","mnps_3d_m")]
    assert result["direction"] is None and result["n2_minus_wake_median"] is None

def test_zero_difference_and_duplicate_or_invalid_denominator():
    s=fixture(); s["representations"]["3d"]["summary"][1]["median"]=1.0
    assert contrasts(s)[("3d","mnps_3d_m")]["direction"]==0
    bad=copy.deepcopy(s);bad["representations"]["3d"]["summary"].append(bad["representations"]["3d"]["summary"][0])
    with pytest.raises(ValueError,match="duplicate"):contrasts(bad)
    s["representations"]["3d"]["summary"][0]["n"]=True
    with pytest.raises(ValueError,match="denominator"):contrasts(s)
