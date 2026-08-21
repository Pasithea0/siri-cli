"""Tests for siri_cli.driver.typetosiri — the Type-to-Siri backend.

Live UI interaction is not exercised here (needs a real Siri session); we
unit-test the permission gating, health reporting, and the ask() flow using
an injected get_response_text callable so settle-detection runs against a
stable fake response.
"""

import pytest

from siri_cli.driver import typetosiri
from siri_cli.driver.base import PermissionsError


def _perm(granted):
    return type("PermStatus", (), {"granted": granted})()


def _healthy_status(**overrides):
    defaults = {
        "accessibility": True,
        "screen_recording": True,
        "type_to_siri": True,
        "siri_present": True,
        "os_version": "26.5.2",
    }
    defaults.update(overrides)
    return type(
        "EnvStatus",
        (),
        {
            "accessibility": _perm(defaults["accessibility"]),
            "screen_recording": _perm(defaults["screen_recording"]),
            "type_to_siri": _perm(defaults["type_to_siri"]),
            "siri_present": defaults["siri_present"],
            "os_version": defaults["os_version"],
            "all_required": (
                defaults["accessibility"]
                and defaults["screen_recording"]
                and defaults["type_to_siri"]
            ),
        },
    )()


def test_health_reports_ready(monkeypatch):
    backend = typetosiri.TypeToSiriBackend()
    monkeypatch.setattr(typetosiri.config, "check", lambda: _healthy_status())
    h = backend.health()
    assert h["ready"] is True
    assert h["name"] == "typetosiri"


def test_health_not_ready_when_missing_accessibility(monkeypatch):
    backend = typetosiri.TypeToSiriBackend()
    monkeypatch.setattr(
        typetosiri.config, "check", lambda: _healthy_status(accessibility=False)
    )
    assert backend.health()["ready"] is False


def test_ask_raises_permissions_error_without_accessibility(monkeypatch):
    backend = typetosiri.TypeToSiriBackend()
    monkeypatch.setattr(
        typetosiri.config, "check", lambda: _healthy_status(accessibility=False)
    )
    with pytest.raises(PermissionsError):
        backend.ask("what time is it")


def test_ask_raises_permissions_error_without_type_to_siri(monkeypatch):
    backend = typetosiri.TypeToSiriBackend()
    monkeypatch.setattr(
        typetosiri.config, "check", lambda: _healthy_status(type_to_siri=False)
    )
    with pytest.raises(PermissionsError):
        backend.ask("what time is it")


def test_ask_returns_response_with_injected_text(monkeypatch):
    backend = typetosiri.TypeToSiriBackend(
        get_response_text=lambda: "It is 3:00 PM",
        settle_kwargs={"stable_required": 2, "min_latency_s": 0},
    )
    monkeypatch.setattr(typetosiri.config, "check", lambda: _healthy_status())
    # Stub the send-path subprocess calls to no-ops.
    monkeypatch.setattr(typetosiri, "_press_hotkey", lambda h: None)
    monkeypatch.setattr(typetosiri.TypeToSiriBackend, "_send_query", lambda self, q: None)

    resp = backend.ask("what time is it", timeout_s=10)
    assert resp.text == "It is 3:00 PM"
    assert resp.backend == "typetosiri"
    assert resp.capture_mode == "ax"
    assert resp.elapsed_ms >= 0


def test_extract_falls_back_to_ocr_when_ax_empty(monkeypatch):
    """When AX returns nothing, the OCR path is used."""
    backend = typetosiri.TypeToSiriBackend()

    # Simulate: no Siri pid found (AX path skipped entirely) -> OCR used.
    monkeypatch.setattr(typetosiri.TypeToSiriBackend, "_find_siri_pid", lambda self: None)
    monkeypatch.setattr(
        typetosiri.TypeToSiriBackend, "_extract_response_text_ocr", lambda self: "It is 4 PM"
    )
    assert backend._extract_response_text() == "It is 4 PM"


def test_extract_uses_ax_when_text_present(monkeypatch):
    backend = typetosiri.TypeToSiriBackend()
    monkeypatch.setattr(typetosiri.TypeToSiriBackend, "_find_siri_pid", lambda self: 999)
    monkeypatch.setattr(
        typetosiri.ax, "extract_texts", lambda app_ref: ["AX answer"]
    )
    monkeypatch.setattr(
        typetosiri.TypeToSiriBackend, "_extract_response_text_ocr", lambda self: "OCR answer"
    )
    assert backend._extract_response_text() == "AX answer"
