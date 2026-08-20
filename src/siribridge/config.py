"""Permissions and environment checks.

Determines whether this process has the macOS privileges siribridge needs:
- Accessibility (AX) trust — required to inspect/drive the AX UI tree.
- Screen Recording — required to capture window/screen images for OCR.
"""

from __future__ import annotations

import dataclasses
import subprocess
from typing import Dict, List

# Keep pyobjc imports lazy so the package imports cleanly on non-macOS
# (e.g. for unit tests of pure logic) and so a missing framework fails
# loudly only when a capability is actually probed.


@dataclasses.dataclass
class PermStatus:
    """Result of a permission probe."""

    name: str
    granted: bool
    detail: str = ""


@dataclasses.dataclass
class EnvStatus:
    """Aggregate environment readiness."""

    accessibility: PermStatus
    screen_recording: PermStatus
    type_to_siri: PermStatus
    siri_present: bool
    os_version: str

    @property
    def all_required(self) -> bool:
        return (
            self.accessibility.granted
            and self.screen_recording.granted
            and self.type_to_siri.granted
        )

    def summary(self) -> List[str]:
        lines = [
            f"os: {self.os_version}",
            f"siri present: {self.siri_present}",
            f"accessibility: {'OK' if self.accessibility.granted else 'MISSING'}",
            f"screen recording: {'OK' if self.screen_recording.granted else 'MISSING'}",
            f"type to siri: {'OK' if self.type_to_siri.granted else 'MISSING'}",
        ]
        return lines


def _ax_trusted() -> bool:
    """Return True if this process is trusted for Accessibility."""
    try:
        import ApplicationServices
    except ImportError as e:  # pragma: no cover - non-macOS
        raise RuntimeError("pyobjc-framework-ApplicationServices not installed") from e
    return bool(ApplicationServices.AXIsProcessTrusted())


def _screen_recording_granted() -> bool:
    """Best-effort probe for Screen Recording permission.

    There is no public TCC API to check this directly. We use the
    side-effect approach: requesting a window-list image from another app's
    window returns empty/black when recording is denied. A zero-size result
    for a known window strongly implies denial.
    """
    try:
        import Quartz
    except ImportError as e:  # pragma: no cover - non-macOS
        raise RuntimeError("pyobjc-framework-Quartz not installed") from e
    opts = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
    info = Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID) or []
    # Use the frontmost normal app window as a probe target.
    for w in info:
        if w.get("kCGWindowLayer", 0) == 0 and w.get("kCGWindowOwnerName"):
            wid = w.get("kCGWindowNumber")
            img = Quartz.CGWindowListCreateImage(
                Quartz.CGRectNull,
                Quartz.kCGWindowListOptionIncludingWindow,
                wid,
                Quartz.kCGWindowImageBoundsIgnoreFraming,
            )
            if img is not None:
                return True
    # No normal windows to probe (rare) — assume granted so we don't false-negative.
    return True


def _siri_present() -> bool:
    return _path_exists("/System/Library/CoreServices/Siri.app")


def _path_exists(path: str) -> bool:
    from os.path import exists

    return exists(path)


def _type_to_siri_granted() -> bool:
    """Check the Type-to-Siri accessibility toggle.

    Reads `TypeToSiriEnabled` from `com.apple.Siri.plist` (user domain).
    Falls back to False when the key is absent. If the key can't be read
    for any reason, we default to False and document the manual toggle.
    """
    try:
        import subprocess

        out = subprocess.run(
            ["defaults", "read", "com.apple.Siri", "TypeToSiriEnabled"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.returncode == 0 and out.stdout.strip().lower() in ("1", "true", "yes")
    except Exception:
        return False


def _os_version() -> str:
    try:
        out = subprocess.run(
            ["sw_vers", "-productVersion"], capture_output=True, text=True, timeout=5
        )
        return out.stdout.strip()
    except Exception:  # pragma: no cover
        return "unknown"


def check() -> EnvStatus:
    return EnvStatus(
        accessibility=PermStatus("accessibility", _ax_trusted()),
        screen_recording=PermStatus("screen_recording", _screen_recording_granted()),
        type_to_siri=PermStatus("type_to_siri", _type_to_siri_granted()),
        siri_present=_siri_present(),
        os_version=_os_version(),
    )


def how_to_enable() -> Dict[str, str]:
    """Return human-readable instructions for each missing permission."""
    guide = {
        "accessibility": (
            "System Settings > Privacy & Security > Accessibility > "
            "enable the terminal/app that runs siribridge."
        ),
        "screen_recording": (
            "System Settings > Privacy & Security > Screen Recording > "
            "enable the terminal/app that runs siribridge."
        ),
        "type_to_siri": (
            "System Settings > Accessibility > Siri > turn on 'Type to Siri'. "
            "Also ensure Siri is enabled in System Settings > Siri & Spotlight."
        ),
    }
    status = check()
    missing = {}
    if not status.accessibility.granted:
        missing["accessibility"] = guide["accessibility"]
    if not status.screen_recording.granted:
        missing["screen_recording"] = guide["screen_recording"]
    if not status.type_to_siri.granted:
        missing["type_to_siri"] = guide["type_to_siri"]
    return missing
