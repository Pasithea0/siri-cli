"""Siri AI backend (macOS 27).

Drives the new "Siri AI.app" — a real, AX-accessible chat application (unlike
the macOS 26 NC overlay whose AX tree was empty). The app exposes:

- A conversation-history sidebar (Today / Yesterday / ... rows with text).
- A "New Conversation" button to start a fresh thread.
- A composer/input field once a conversation is active.
- Rendered Siri responses as readable AX text (AXUnknown/AXStaticText).

The response-capture loop the whole project targets finally works here:
summon -> start conversation -> type query -> submit -> settle-detect ->
read response from the AX tree.
"""

from __future__ import annotations

import subprocess
import time
from typing import Optional

from . import base
from ..capture import ax

_SIRI_AI_APP = "/System/Applications/Siri AI.app"
_SIRI_AI_PID_CMD = ["pgrep", "-f", "Siri AI.app/Contents/MacOS/Siri AI"]


class SiriAiBackend(base.BridgeBackend):
    """Backend that drives the new Siri AI app on macOS 27."""

    name = "siriai"

    def __init__(
        self,
        *,
        settle_kwargs: Optional[dict] = None,
        submit_delay_s: float = 0.5,
    ):
        self._settle_kwargs = settle_kwargs or {}
        self.submit_delay_s = submit_delay_s

    # -- health -----------------------------------------------------------

    def health(self) -> dict:
        from .. import config

        status = config.check()
        return {
            "name": self.name,
            "accessibility": status.accessibility.granted,
            "siri_ai_present": self._find_pid() is not None,
            "siri_ai_app": _SIRI_AI_APP,
            "ready": status.accessibility.granted and self._find_pid() is not None,
        }

    # -- public API -------------------------------------------------------

    def ask(self, query: str, timeout_s: float = 30.0) -> base.SiriResponse:
        health = self.health()
        if not health["accessibility"]:
            raise base.PermissionsError("accessibility")
        if not health["siri_ai_present"]:
            raise base.SurfaceError("Siri AI app is not running")

        start = time.monotonic()
        pid = self._find_pid()
        if pid is None:
            raise base.SurfaceError("Siri AI app is not running")
        # NOTE: we do NOT osascript-activate here. `tell app to activate`
        # steals focus from the composer so subsequent keystrokes don't land.
        # Pressing "New Conversation" already brings the app forward and
        # focuses the composer.
        self._start_new_conversation(pid)
        self._type_and_submit(query)

        # Poll for the conversation response. Skip None (chrome-only) results;
        # return the first non-empty response text that stops changing.
        app = ax.app_for_pid(pid)
        last: Optional[str] = None
        stable = 0
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            texts = self._extract_response_text(pid)
            if texts:
                if texts == last:
                    stable += 1
                    if stable >= 2:  # two identical reads = settled
                        break
                else:
                    stable = 0
                last = texts
            time.sleep(0.5)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        if not last:
            raise base.CaptureError("Timed out waiting for Siri AI response")
        return base.SiriResponse(
            text=last,
            backend=self.name,
            elapsed_ms=elapsed_ms,
            capture_mode="ax",
            raw=last,
        )

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _find_pid() -> Optional[int]:
        try:
            out = subprocess.run(_SIRI_AI_PID_CMD, capture_output=True, text=True, timeout=5)
            lines = [l.strip() for l in out.stdout.splitlines() if l.strip()]
            return int(lines[0]) if lines else None
        except Exception:
            return None

    def _ensure_active(self, pid: int) -> None:
        """Bring the Siri AI app to the foreground."""
        subprocess.run(
            ["osascript", "-e", f'tell application "Siri AI" to activate'],
            capture_output=True, text=True, timeout=5,
        )
        time.sleep(0.5)

    def _start_new_conversation(self, pid: int) -> None:
        """Click the 'New Conversation' button in the AX tree."""
        app = ax.app_for_pid(pid)
        el = ax.find_element(app, label_contains="New Conversation")
        if el is not None:
            # Perform the AXPress action on the matching element.
            self._press_by_label(pid, "New Conversation")
        time.sleep(0.6)

    def _press_by_label(self, pid: int, label: str) -> None:
        """Find an element by label and perform AXPress."""
        import ApplicationServices as a

        app = a.AXUIElementCreateApplication(pid)
        self._find_and_press(app, label)

    def _find_and_press(self, el, label: str, depth: int = 0) -> bool:
        import ApplicationServices as a

        if depth > 25:
            return False
        err_r, role = a.AXUIElementCopyAttributeValue(el, "AXRole", None)
        role = str(role) if err_r == 0 else ""
        # Only press AXButton elements (the toolbar "New Conversation" button);
        # sidebar text rows also carry the label but aren't actionable.
        if role == "AXButton":
            for attr in ("AXTitle", "AXValue", "AXDescription", "AXLabel"):
                err, val = a.AXUIElementCopyAttributeValue(el, attr, None)
                if err == 0 and val is not None and label.lower() in str(val).lower():
                    a.AXUIElementPerformAction(el, "AXPress")
                    return True
        err_c, children = a.AXUIElementCopyAttributeValue(el, "AXChildren", None)
        if err_c == 0 and children is not None:
            for c in children:
                if self._find_and_press(c, label, depth + 1):
                    return True
        return False

    def _type_and_submit(self, query: str) -> None:
        """Type into the composer and submit via AX (no focus dependency).

        Sets the composer AXTextField's AXValue directly and calls its
        AXConfirm action. This avoids `System Events` keystrokes, which only
        land if the Siri AI app happens to be frontmost — unreliable when an
        agent/terminal is in the foreground.
        """
        import ApplicationServices as a

        app = a.AXUIElementCreateApplication(self._find_pid())
        field = self._find_composer(app)
        if field is None:
            # Fallback: try keystrokes (works when the app is frontmost).
            self._type_and_submit_keystroke(query)
            return

        # Set the composer's value to the query.
        err = a.AXUIElementSetAttributeValue(field, "AXValue", query)
        if err != 0:
            raise base.CaptureError(f"Failed to set composer value (err {err})")
        time.sleep(self.submit_delay_s)
        # Submit via AXConfirm.
        a.AXUIElementPerformAction(field, "AXConfirm")

    def _find_composer(self, app) -> Optional[object]:
        """Return the composer AXTextField, or None."""
        import ApplicationServices as a

        def walk(el, depth=0):
            if depth > 20:
                return None
            err_r, role = a.AXUIElementCopyAttributeValue(el, "AXRole", None)
            if err_r == 0 and str(role) == "AXTextField":
                act_err, actions = a.AXUIElementCopyActionNames(el, None)
                if act_err == 0 and "AXConfirm" in list(actions):
                    return el
            err_c, ch = a.AXUIElementCopyAttributeValue(el, "AXChildren", None)
            if err_c == 0 and ch:
                for c in ch:
                    r = walk(c, depth + 1)
                    if r is not None:
                        return r
            return None

        return walk(app)

    def _type_and_submit_keystroke(self, query: str) -> None:
        """Fallback: type via System Events keystroke (needs app frontmost)."""
        subprocess.run(
            ["osascript", "-e", f'tell application "System Events" to keystroke {query!r}'],
            capture_output=True, text=True, timeout=5,
        )
        time.sleep(self.submit_delay_s)
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to key code 36'],
            capture_output=True, text=True, timeout=5,
        )  # Return

    def _extract_response_text(self, pid: int) -> Optional[str]:
        """Read the response from the Siri AI conversation area.

        Walks only the app's AX windows (not the process-level menu bar /
        Finder menus) and keeps the conversation text. Falls back to the
        full process tree if no window is found.
        """
        app = ax.app_for_pid(pid)
        texts: list[str] = []
        windows = self._windows(app)
        if windows:
            for w in windows:
                texts.extend(ax.extract_texts(w))
        else:
            texts = ax.extract_texts(app)
        if not texts:
            return None
        return self._filter_conversation_text(texts)

    @staticmethod
    def _windows(app) -> list:
        """Return the app's AXWindow elements (excluding the menu bar)."""
        import ApplicationServices as a

        err, children = a.AXUIElementCopyAttributeValue(app, "AXChildren", None)
        if err != 0 or children is None:
            return []
        result = []
        for c in children:
            err_r, role = a.AXUIElementCopyAttributeValue(c, "AXRole", None)
            if err_r == 0 and str(role) == "AXWindow":
                result.append(c)
        return result

    @staticmethod
    def _filter_conversation_text(texts: list[str]) -> Optional[str]:
        """Keep conversation content; drop chrome, menus, and duplicate lines.

        Also collapses the UI's repeated rendering (the query and answer
        often appear twice) and drops one-off button labels like "Copy".
        """
        noise_prefixes = (
            "About This Mac", "System Information", "System Settings…",
            "App Store", "Recent Items", "Applications",
            "Show “", "Clear Menu", "Force Quit", "Sleep", "Restart",
            "Shut Down", "Lock Screen", "Log Out", "About Siri",
        )
        noise_exact = {
            "Today", "Yesterday", "Previous 7 Days", "Previous 30 Days",
            "New Conversation", "Search", "0.0", "No Conversation Selected",
            "Copy", "Like", "Share", "Dismiss",
        }
        keep: list[str] = []
        for t in texts:
            s = " ".join(t.split())  # collapse whitespace
            if not s:
                continue
            if s in noise_exact:
                continue
            if s.startswith(noise_prefixes):
                continue
            # Skip a line that's identical to the previous kept line
            # (the app often renders the query/answer twice).
            if keep and s == keep[-1]:
                continue
            keep.append(s)
        if not keep:
            return None
        return "\n".join(keep)
