"""Tests for siribridge.config — permissions & environment checks.

Pure-logic tests only; the pyobjc probes are exercised by the live
`check()` path and integration tests, not here (they need a real macOS
session + TCC grants).
"""

import importlib

import pytest

import siribridge.config as config


def _make_status(
    ax: bool = True, sr: bool = True, tts: bool = True, siri: bool = True
) -> config.EnvStatus:
    return config.EnvStatus(
        accessibility=config.PermStatus("accessibility", ax),
        screen_recording=config.PermStatus("screen_recording", sr),
        type_to_siri=config.PermStatus("type_to_siri", tts),
        siri_present=siri,
        os_version="26.5.2",
    )


def test_all_required_true_when_all_granted():
    assert _make_status().all_required is True


def test_all_required_false_when_any_missing():
    assert _make_status(ax=False).all_required is False
    assert _make_status(sr=False).all_required is False
    assert _make_status(tts=False).all_required is False


def test_summary_lists_each_capability():
    lines = _make_status().summary()
    assert any("accessibility" in l for l in lines)
    assert any("screen recording" in l for l in lines)
    assert any("type to siri" in l for l in lines)
    assert any("os:" in l for l in lines)
    assert any("siri present:" in l for l in lines)


def test_how_to_enable_reports_nothing_when_ready(monkeypatch):
    monkeypatch.setattr(config, "check", lambda: _make_status())
    assert config.how_to_enable() == {}


def test_how_to_enable_lists_missing_perms(monkeypatch):
    monkeypatch.setattr(config, "check", lambda: _make_status(ax=False, tts=False))
    missing = config.how_to_enable()
    assert set(missing.keys()) == {"accessibility", "type_to_siri"}
    assert "Privacy & Security" in missing["accessibility"]
    assert "Type to Siri" in missing["type_to_siri"]


def test_module_imports_without_pyobjc():
    """Package must import cleanly even if pyobjc is absent (lazy imports)."""
    importlib.reload(config)
    assert hasattr(config, "check")


def test_type_to_siri_reads_enabled_key(monkeypatch):
    """Reads TypeToSiriEnabled=true from com.apple.Siri."""
    import subprocess

    class _Res:
        returncode = 0
        stdout = "true"

    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _Res()
    )
    assert config._type_to_siri_granted() is True


def test_type_to_siri_false_when_disabled(monkeypatch):
    import subprocess

    class _Res:
        returncode = 0
        stdout = "0"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Res())
    assert config._type_to_siri_granted() is False


def test_type_to_siri_false_on_error(monkeypatch):
    import subprocess

    def boom(*a, **k):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", boom)
    assert config._type_to_siri_granted() is False
