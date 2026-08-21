"""Bridge backend abstraction.

Defines the `BridgeBackend` interface and the `SiriResponse` result type
shared by all driver backends (Type-to-Siri now, Spotlight/Siri-AI later).
"""

from __future__ import annotations

import abc
import dataclasses
from typing import Optional


@dataclasses.dataclass
class SiriResponse:
    """A captured Siri response.

    Attributes:
        text: The extracted response text (primary deliverable).
        backend: Which backend produced it (e.g. "typetosiri", "spotlight").
        elapsed_ms: Round-trip time in milliseconds.
        images: Optional list of captured screenshot paths (for rich cards).
        capture_mode: Which capture path succeeded ("ax" or "ocr").
        raw: Optional raw AX/OCR text before cleanup, for debugging.
    """

    text: str
    backend: str
    elapsed_ms: int = 0
    images: list[str] = dataclasses.field(default_factory=list)
    capture_mode: Optional[str] = None
    raw: Optional[str] = None


class SiriError(Exception):
    """Base error for the bridge."""

    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class PermissionsError(SiriError):
    """Missing macOS permission (Accessibility / Screen Recording)."""

    def __init__(self, missing: str):
        super().__init__(f"Missing permission: {missing}", retryable=False)
        self.missing = missing


class SurfaceError(SiriError):
    """The Siri/Spotlight surface could not be summoned or focused."""

    def __init__(self, message: str, *, retryable: bool = True):
        super().__init__(message, retryable=retryable)


class CaptureError(SiriError):
    """The response could not be read out of the surface."""

    def __init__(self, message: str, *, retryable: bool = True):
        super().__init__(message, retryable=retryable)


class BridgeBackend(abc.ABC):
    """Interface for a backend that drives the Siri surface."""

    name: str = "base"

    @abc.abstractmethod
    def ask(self, query: str, timeout_s: float = 30.0) -> SiriResponse:
        """Send `query` to the surface and capture the response."""

    @abc.abstractmethod
    def health(self) -> dict:
        """Return a dict describing backend readiness."""

    def close(self) -> None:  # pragma: no cover - optional cleanup
        """Release any resources (overridden by backends that need it)."""
        return None
