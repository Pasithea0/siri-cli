"""Tests for siribridge.driver.siriai — the macOS 27 Siri AI backend."""

import pytest

from siribridge import config
from siribridge.driver import siriai
from siribridge.driver.base import PermissionsError


def _perm(granted):
    return type("PermStatus", (), {"granted": granted})()


def _healthy(**overrides):
    d = {
        "accessibility": True,
        "screen_recording": True,
        "type_to_siri": True,
        "siri_present": True,
        "os_version": "27.0",
    }
    d.update(overrides)
    return type(
        "EnvStatus",
        (),
        {
            "accessibility": _perm(d["accessibility"]),
            "screen_recording": _perm(d["screen_recording"]),
            "type_to_siri": _perm(d["type_to_siri"]),
            "siri_present": d["siri_present"],
            "os_version": d["os_version"],
            "all_required": all([d["accessibility"], d["screen_recording"], d["type_to_siri"]]),
        },
    )()


def test_filter_keeps_conversation_drops_chrome():
    texts = [
        "Today",
        "Yesterday",
        "what time is it",
        "what time is it",
        "It's 10:36 AM.",
        "It's 10:36 AM.",
        "About This Mac",
        "Show “Mail.app” in Finder",
        "New Conversation",
        "0.0",
        "Copy",
    ]
    out = siriai.SiriAiBackend._filter_conversation_text(texts)
    assert out is not None
    # Dedupe: repeated lines collapse to one.
    assert out.count("what time is it") == 1
    assert out.count("It's 10:36 AM.") == 1
    assert "Today" not in out
    assert "About This Mac" not in out
    assert "Show " not in out
    assert "New Conversation" not in out
    assert "0.0" not in out
    assert "Copy" not in out


def test_filter_returns_none_if_all_noise():
    out = siriai.SiriAiBackend._filter_conversation_text(
        ["Today", "About This Mac", "0.0", "New Conversation"]
    )
    assert out is None


def test_health_not_ready_without_accessibility(monkeypatch):
    backend = siriai.SiriAiBackend()
    monkeypatch.setattr(config, "check", lambda: _healthy(accessibility=False))
    assert backend.health()["ready"] is False


def test_ask_raises_permissions_without_accessibility(monkeypatch):
    backend = siriai.SiriAiBackend()
    monkeypatch.setattr(config, "check", lambda: _healthy(accessibility=False))
    with pytest.raises(PermissionsError):
        backend.ask("hi")
