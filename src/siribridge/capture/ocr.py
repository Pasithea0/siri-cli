"""Vision OCR capture for rich Siri cards and the macOS 26 overlay.

On macOS 26 the SiriNCService overlay exposes an EMPTY Accessibility tree,
so the response cannot be read via AX. Instead we capture the screen
region where the overlay renders and run Apple Vision OCR on it.

This is the capture fallback the plan anticipated; on macOS 27 the Siri app
should expose a proper AX tree and AX becomes the primary path again.
"""

from __future__ import annotations

import dataclasses
from typing import List, Optional

import Quartz

_TEXT_ROLES = None  # placeholder for symmetry; OCR has no roles


@dataclasses.dataclass
class OCRResult:
    """One recognized text observation."""

    text: str
    confidence: float = 0.0
    bounding_box: Optional[tuple[float, float, float, float]] = None


def capture_region(
    x: int, y: int, width: int, height: int
) -> Optional[object]:
    """Capture a screen region as a CGImage. Returns None on failure."""
    try:
        rect = Quartz.CGRectMake(x, y, width, height)
        img = Quartz.CGWindowListCreateImage(
            rect,
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
            Quartz.kCGWindowImageDefault,
        )
        return img
    except Exception:
        return None


def _ocr_cgimage(cgimg) -> List[OCRResult]:
    """Run Apple Vision OCR on a CGImage; returns ordered observations."""
    import Vision

    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cgimg, {})
    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    # Returns (success_bool, error_or_None). Ignore the tuple; read results.
    handler.performRequests_error_([request], None)
    results = request.results() or []
    out: List[OCRResult] = []
    for obs in results:
        cands = obs.topCandidates_(1)
        if cands and len(cands):
            conf = float(cands[0].confidence())
            out.append(OCRResult(text=str(cands[0].string()), confidence=conf))
    return out


def ocr_region(x: int, y: int, width: int, height: int) -> List[OCRResult]:
    """Capture a screen region and OCR it. Returns [] on any failure."""
    img = capture_region(x, y, width, height)
    if img is None:
        return []
    return _ocr_cgimage(img)


def extract_text_from_region(x: int, y: int, width: int, height: int) -> Optional[str]:
    """OCR a region and return joined text (newline-separated), or None."""
    results = ocr_region(x, y, width, height)
    if not results:
        return None
    return "\n".join(r.text for r in results)


def screen_size() -> tuple[int, int]:
    """Return (width, height) of the main display in points."""
    frame = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    return int(frame.size.width), int(frame.size.height)
