"""Tests for siri_cli.driver.siriai — the macOS 27 Siri AI backend."""

import pytest

from siri_cli import config
from siri_cli.driver import siriai
from siri_cli.driver.base import PermissionsError


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


def test_wait_for_response_skips_bare_query_echo(monkeypatch):
    # Siri AI shows only the echoed query for ~2 s, then a status line,
    # then the answer. The echo alone must not count as a settled response.
    backend = siriai.SiriAiBackend()
    frames = iter(
        ["what's on my calendar"] * 8
        + ["what's on my calendar\nSearching events"] * 2
        + ["what's on my calendar\nYou have one event tomorrow."] * 10
    )
    monkeypatch.setattr(backend, "_extract_response_text", lambda pid: next(frames))
    monkeypatch.setattr(siriai.time, "sleep", lambda s: None)
    out = backend._wait_for_response(1, siriai.time.monotonic() + 5, "what's on my calendar")
    assert out == "what's on my calendar\nYou have one event tomorrow."


def test_wait_for_response_waits_through_long_status_line(monkeypatch):
    # "Searching emails" can hold well past the stability window.
    backend = siriai.SiriAiBackend()
    frames = iter(
        ["check mail"] * 3
        + ["check mail\nSearching emails"] * 20
        + ["check mail\nNo new messages today."] * 10
    )
    monkeypatch.setattr(backend, "_extract_response_text", lambda pid: next(frames))
    monkeypatch.setattr(siriai.time, "sleep", lambda s: None)
    out = backend._wait_for_response(1, siriai.time.monotonic() + 5, "check mail")
    assert out == "check mail\nNo new messages today."


@pytest.mark.parametrize(
    "line, is_status",
    [
        ("Searching events", True),
        ("Searching emails", True),
        ("Looking up the weather", True),
        ("Checking your calendar", True),
        ("Checking in at 3 PM is fine.", False),
        ("Searching the web found nothing useful, sorry about that.", False),
        ("It's 1:46 PM.", False),
    ],
)
def test_status_line_regex(line, is_status):
    assert bool(siriai._STATUS_LINE_RE.match(line)) is is_status
