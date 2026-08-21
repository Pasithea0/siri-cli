"""Tests for the siribridge CLI entrypoint — argument dispatch."""

import pytest
from click.testing import CliRunner

from siribridge.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_no_args_prints_usage(runner):
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert 'siri "what time is it"' in result.output


def test_status_subcommand(runner, monkeypatch):
    from siribridge import config

    monkeypatch.setattr(config, "check", lambda: _ok_status())
    result = runner.invoke(main, ["status"])
    assert result.exit_code == 0
    assert "accessibility" in result.output


def test_health_subcommand(runner, monkeypatch):
    from siribridge import config

    monkeypatch.setattr(config, "check", lambda: _ok_status())
    result = runner.invoke(main, ["health"])
    assert result.exit_code == 0
    assert result.output.strip() == "ok"


def test_bare_query_dispatches_to_backend(runner, monkeypatch):
    """siri 'what time is it' should call the backend, not a subcommand."""
    calls = {}

    class _FakeBackend:
        def ask(self, query, timeout_s=30.0):
            calls["query"] = query
            from siribridge.driver.base import SiriResponse
            return SiriResponse(text="It is noon.", backend="fake", elapsed_ms=5)

    from siribridge.driver import siriai as siriai_mod
    monkeypatch.setattr(siriai_mod, "SiriAiBackend", lambda *a, **k: _FakeBackend())
    result = runner.invoke(main, ["what", "time", "is", "it"])
    assert result.exit_code == 0
    assert calls["query"] == "what time is it"
    assert "It is noon." in result.output


def test_quoted_query(runner, monkeypatch):
    calls = {}

    class _FakeBackend:
        def ask(self, query, timeout_s=30.0):
            calls["query"] = query
            from siribridge.driver.base import SiriResponse
            return SiriResponse(text="42", backend="fake", elapsed_ms=1)

    from siribridge.driver import siriai as siriai_mod
    monkeypatch.setattr(siriai_mod, "SiriAiBackend", lambda *a, **k: _FakeBackend())
    result = runner.invoke(main, ['"what is 6 times 7"'])
    assert result.exit_code == 0
    assert calls["query"] == '"what is 6 times 7"'
    assert "42" in result.output


def _ok_status():
    def _perm(g):
        return type("P", (), {"granted": g})()

    def _summary(self):
        return [
            "os: 27.0",
            "siri present: True",
            "accessibility: OK",
            "screen recording: OK",
            "type to siri: OK",
        ]

    return type(
        "E",
        (),
        {
            "accessibility": _perm(True),
            "screen_recording": _perm(True),
            "type_to_siri": _perm(True),
            "siri_present": True,
            "os_version": "27.0",
            "all_required": True,
            "summary": _summary,
        },
    )()
