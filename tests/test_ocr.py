"""Tests for siribridge.capture.ocr — OCR result model + fallback wiring.

The real Vision OCR needs a live screen + TCC grant, so we test the pure
pieces (OCRResult model, screen_size fallback, extract_text_from_region
join logic) by mocking the capture/OCR primitives.
"""

import pytest

from siribridge.capture import ocr


def test_ocr_result_defaults():
    r = ocr.OCRResult(text="hello")
    assert r.confidence == 0.0
    assert r.bounding_box is None


def test_screen_size_returns_tuple(monkeypatch):
    import Quartz

    class _Frame:
        size = type("S", (), {"width": 1512.0, "height": 982.0})()

    monkeypatch.setattr(Quartz, "CGDisplayBounds", lambda *a: _Frame())
    monkeypatch.setattr(Quartz, "CGMainDisplayID", lambda: 1)
    assert ocr.screen_size() == (1512, 982)


def test_extract_text_from_region_joins_lines(monkeypatch):
    monkeypatch.setattr(
        ocr,
        "ocr_region",
        lambda *a, **k: [ocr.OCRResult("line one"), ocr.OCRResult("line two")],
    )
    assert ocr.extract_text_from_region(0, 0, 100, 100) == "line one\nline two"


def test_extract_text_from_region_none_on_empty(monkeypatch):
    monkeypatch.setattr(ocr, "ocr_region", lambda *a, **k: [])
    assert ocr.extract_text_from_region(0, 0, 100, 100) is None


def test_capture_region_returns_none_on_error(monkeypatch):
    monkeypatch.setattr(ocr.Quartz, "CGWindowListCreateImage", lambda *a, **k: (_ for _ in ()).throw(Exception))
    assert ocr.capture_region(0, 0, 10, 10) is None


def test_ocr_region_returns_empty_on_capture_failure(monkeypatch):
    monkeypatch.setattr(ocr, "capture_region", lambda *a, **k: None)
    assert ocr.ocr_region(0, 0, 10, 10) == []
