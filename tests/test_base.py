"""Tests for siribridge.driver.base — response/error types."""

from siribridge.driver.base import (
    CaptureError,
    PermissionsError,
    SiriError,
    SiriResponse,
    SurfaceError,
)


def test_siri_response_defaults():
    r = SiriResponse(text="42", backend="typetosiri")
    assert r.elapsed_ms == 0
    assert r.images == []
    assert r.capture_mode is None
    assert r.raw is None


def test_siri_error_retryable_default_false():
    e = SiriError("boom")
    assert e.retryable is False


def test_permissions_error_sets_missing():
    e = PermissionsError("accessibility")
    assert e.missing == "accessibility"
    assert e.retryable is False
    assert "accessibility" in str(e)


def test_surface_error_retryable_default_true():
    assert SurfaceError("nope").retryable is True


def test_capture_error_retryable_default_true():
    assert CaptureError("nope").retryable is True


def test_errors_subclass_sirierror():
    assert issubclass(PermissionsError, SiriError)
    assert issubclass(SurfaceError, SiriError)
    assert issubclass(CaptureError, SiriError)
