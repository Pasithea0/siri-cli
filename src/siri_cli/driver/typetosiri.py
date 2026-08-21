"""Type-to-Siri backend.

Drives the macOS Type-to-Siri overlay (macOS 26's SiriNCService surface):

1. Summon — press the Type-to-Siri hotkey (Fn+Space by default).
2. Send — type the query and press Return.
3. Settle — poll the response area via AX until the text is stable.
4. Capture — extract the response text from the AX tree (Vision OCR as
   fallback for rich cards).

Because Siri is not scriptable via any public API, this uses the
Accessibility (AX) APIs directly via pyobjc — the same mechanism CuaDriver
uses. It runs standalone (no Hermes dependency).
"""

from __future__ import annotations

import subprocess
import time
from typing import Callable, Optional

from . import base
from .. import config
from ..capture import ax
from ..capture import ocr

# Siri summon hotkey. On this machine Siri is bound to double-press Command
# (keycode 55 = left Command), per KeyboardShortcutSAE params (32,55). A
# single Command+Space is Raycast here, so we use the double-Command summon.
_DOUBLE_CMD = "double-cmd"

# Fallback: open Siri via its launcher app if hotkey summon is unreliable.
_SIRI_APP = "/System/Library/CoreServices/Siri.app"


def _press_hotkey(hotkey: str) -> None:
    """Press a hotkey via osascript keystroke (works with AX trust)."""
    if hotkey == _DOUBLE_CMD:
        # Double-press Command (keycode 55) quickly -> summons Siri overlay.
        for _ in range(2):
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to key code 55'],
                capture_output=True,
                text=True,
                timeout=5,
            )
        return
    # Fallback: plain space keycode.
    subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to key code 49'],
        capture_output=True,
        text=True,
        timeout=5,
    )


class TypeToSiriBackend(base.BridgeBackend):
    """Backend that drives the Type-to-Siri overlay."""

    name = "typetosiri"

    def __init__(
        self,
        *,
        hotkey: str = _DOUBLE_CMD,
        settle_kwargs: Optional[dict] = None,
        get_response_text: Optional[Callable[[], Optional[str]]] = None,
    ):
        self.hotkey = hotkey
        self._settle_kwargs = settle_kwargs or {}
        # Overridable for testing: a function returning the current response text.
        self._get_response_text = get_response_text

    # -- health -----------------------------------------------------------

    def health(self) -> dict:
        status = config.check()
        return {
            "name": self.name,
            "accessibility": status.accessibility.granted,
            "screen_recording": status.screen_recording.granted,
            "type_to_siri": status.type_to_siri.granted,
            "siri_present": status.siri_present,
            "ready": status.all_required,
        }

    # -- public API -------------------------------------------------------

    def ask(self, query: str, timeout_s: float = 30.0) -> base.SiriResponse:
        health = self.health()
        if not health["accessibility"]:
            raise base.PermissionsError("accessibility")
        if not health["type_to_siri"]:
            raise base.PermissionsError("type_to_siri")

        start = time.monotonic()
        self._summon()
        self._send_query(query)

        # Capture: settle-detect then extract.
        from ..state import wait_for_settle

        def poll():
            if self._get_response_text is not None:
                return self._get_response_text()
            return self._extract_response_text()

        settled = wait_for_settle(
            poll,
            max_wait_s=timeout_s,
            **self._settle_kwargs,
        )

        elapsed_ms = int((time.monotonic() - start) * 1000)
        if not settled:
            raise base.CaptureError("Timed out waiting for Siri response to settle")

        return base.SiriResponse(
            text=settled,
            backend=self.name,
            elapsed_ms=elapsed_ms,
            capture_mode="ax",
            raw=settled,
        )

    # -- send path --------------------------------------------------------

    def _summon(self) -> None:
        """Bring up the Type-to-Siri overlay."""
        _press_hotkey(self.hotkey)
        time.sleep(1.0)  # let the overlay appear

    def _send_query(self, query: str) -> None:
        """Type the query and submit."""
        subprocess.run(
            ["osascript", "-e", f'tell application "System Events" to keystroke {query!r}'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to key code 36'],
            capture_output=True,
            text=True,
            timeout=5,
        )  # Return key

    # -- capture path -----------------------------------------------------

    def _extract_response_text(self) -> Optional[str]:
        """Read the current response text from the Siri overlay.

        On macOS 26 the SiriNCService AX tree is empty, so we first try the
        AX tree (macOS 27 Siri app) then fall back to screen-region OCR of
        the overlay area.
        """
        # 1) Try AX (works on surfaces that expose an AX tree).
        pid = self._find_siri_pid()
        if pid is not None:
            app_ref = ax.app_for_pid(pid)
            texts = ax.extract_texts(app_ref)
            if texts:
                return "\n".join(texts)

        # 2) Fall back to OCR of the top-left overlay region.
        return self._extract_response_text_ocr()

    def _extract_response_text_ocr(self) -> Optional[str]:
        """OCR the screen region where the Siri overlay renders.

        The Type-to-Siri prompt renders near the top of the screen. We scan
        the top band; on macOS 27 (Siri app) this may need a different
        region, which is configurable.
        """
        # Overlay region: top-left band of the display.
        w, h = ocr.screen_size()
        # The prompt is a relatively small centered box near the top; scan
        # the top 45% of the screen for text.
        region_h = int(h * 0.45)
        return ocr.extract_text_from_region(0, 0, w, region_h)

    @staticmethod
    def _find_siri_pid() -> Optional[int]:
        """Return the pid of the Siri/SiriNCService process, if running."""
        try:
            out = subprocess.run(
                ["pgrep", "-f", "SiriNCService"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = [l.strip() for l in out.stdout.splitlines() if l.strip()]
            return int(lines[0]) if lines else None
        except Exception:
            return None
