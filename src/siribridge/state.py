"""Settle-detection state machine.

The novel part of the bridge: given a sequence of snapshots of the Siri
response area, decide when the response has *finished rendering* so we can
safely capture it. Handles the streaming/streaming-stop ambiguity.

Logic (all unit-testable, no UI):
- We poll the surface's captured text.
- If the text is unchanged across `stable_required` consecutive samples
  AND at least `min_latency_s` has elapsed since the query was submitted,
  we declare it settled.
- A growing stream resets the stable counter.
"""

from __future__ import annotations

import time
from typing import Optional


class SettleDetector:
    """Detects when a response stream has stopped changing."""

    def __init__(
        self,
        *,
        stable_required: int = 3,
        min_latency_s: float = 1.0,
        max_wait_s: float = 30.0,
        poll_interval_s: float = 0.25,
    ):
        self.stable_required = stable_required
        self.min_latency_s = min_latency_s
        self.max_wait_s = max_wait_s
        self.poll_interval_s = poll_interval_s
        self._reset()

    def _reset(self) -> None:
        self._stable_count = 0
        self._last_text: Optional[str] = None
        self._start_s: Optional[float] = None

    def sample(self, text: str, now_s: Optional[float] = None) -> bool:
        """Feed one snapshot; returns True once the stream is settled.

        `text` is the concatenated response text so far. `now_s` defaults
        to `time.monotonic()`.
        """
        if now_s is None:
            now_s = time.monotonic()

        if self._start_s is None:
            self._start_s = now_s

        if self._last_text is None or text != self._last_text:
            # First sample, or stream still growing.
            self._stable_count = 1
            self._last_text = text
        else:
            self._stable_count += 1
        return self._settled(now_s)

    def _settled(self, now_s: float) -> bool:
        if self._start_s is None:
            return False
        elapsed_s = now_s - self._start_s
        # Both required: enough consecutive identical samples AND enough time.
        return self._stable_count >= self.stable_required and elapsed_s >= self.min_latency_s


def wait_for_settle(
    poll,
    *,
    stable_required: int = 3,
    min_latency_s: float = 1.0,
    max_wait_s: float = 30.0,
    poll_interval_s: float = 0.25,
) -> Optional[str]:
    """Poll `poll()` (returns response text or None) until settled.

    Returns the final settled text, or None if it timed out. Pure and
    unit-testable — `poll` is any zero-arg callable.
    """
    detector = SettleDetector(
        stable_required=stable_required,
        min_latency_s=min_latency_s,
        max_wait_s=max_wait_s,
        poll_interval_s=poll_interval_s,
    )
    deadline = time.monotonic() + max_wait_s
    settled_text: Optional[str] = None

    while time.monotonic() < deadline:
        try:
            text = poll()
        except Exception:
            text = None
        if text:
            settled_text = text
            if detector.sample(text):
                return text
        time.sleep(poll_interval_s)
    return settled_text
