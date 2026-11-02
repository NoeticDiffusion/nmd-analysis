import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nmd_analysis.signal_support_audit import audit_signal_support


def _h5(tmp_path):
    p = tmp_path / "x.h5"
    p.write_bytes(b"synthetic-h5")
    return p


def test_legacy_reader_status_is_explicit_unknown(tmp_path, monkeypatch):
    module = types.ModuleType("nmd_analysis.signal_support")
    module.read_signal_support = lambda path: {"status": "legacy_missing"}
    monkeypatch.setitem(sys.modules, "nmd_analysis.signal_support", module)
    report = audit_signal_support([_h5(tmp_path)], tmp_path / "out")
    assert report["sources"][0]["status"] == "legacy_missing"
    assert report["subject_pooling"] == "not_performed"


def test_existing_output_is_rejected(tmp_path, monkeypatch):
    module = types.ModuleType("nmd_analysis.signal_support")
    module.read_signal_support = lambda path: {"status": "unknown"}
    monkeypatch.setitem(sys.modules, "nmd_analysis.signal_support", module)
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(FileExistsError):
        audit_signal_support([_h5(tmp_path)], out)


def test_malformed_reader_report_fails_and_writes_diagnostic(tmp_path, monkeypatch):
    module = types.ModuleType("nmd_analysis.signal_support")
    module.read_signal_support = lambda path: {"status": "bad_status"}
    monkeypatch.setitem(sys.modules, "nmd_analysis.signal_support", module)
    out = tmp_path / "out"
    with pytest.raises(RuntimeError):
        audit_signal_support([_h5(tmp_path)], out)
    assert (out / "signal_support_audit.json").exists()


def test_future_status_is_rejected(tmp_path, monkeypatch):
    module = types.ModuleType("nmd_analysis.signal_support")
    module.read_signal_support = lambda path: {"status": "error"}
    monkeypatch.setitem(sys.modules, "nmd_analysis.signal_support", module)
    with pytest.raises(RuntimeError):
        audit_signal_support([_h5(tmp_path)], tmp_path / "out")


def test_recorded_requires_valid_reader_validation(tmp_path, monkeypatch):
    module = types.ModuleType("nmd_analysis.signal_support")
    module.read_signal_support = lambda path: {"status": "recorded", "validation": {"status": "invalid_or_unavailable"}}
    monkeypatch.setitem(sys.modules, "nmd_analysis.signal_support", module)
    with pytest.raises(RuntimeError):
        audit_signal_support([_h5(tmp_path)], tmp_path / "out")
