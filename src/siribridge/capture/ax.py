"""AX tree extraction via pyobjc's ApplicationServices.

Walks the macOS Accessibility (AX) UI tree for a process and extracts
text/values within a region, so a Siri/Spotlight response can be read out
of the rendered UI.

Lazy-imports ApplicationServices so the package still imports cleanly in
pure-logic unit tests on any platform.
"""

from __future__ import annotations

import dataclasses
from typing import Iterator, List, Optional

# Roles that carry user-visible text we care about.
_TEXT_ROLES = {
    "AXStaticText",
    "AXTextField",
    "AXTextArea",
    "AXButton",
    "AXLink",
    "AXHeading",
    "AXCell",
    "AXValueIndicator",
    "AXMenuItem",
    "AXLabel",
}


@dataclasses.dataclass
class AXElement:
    """Minimal snapshot of an AX element."""

    role: str
    value: Optional[str]
    description: Optional[str]
    title: Optional[str]
    # Native point coords: [x, y, w, h]
    bounds: Optional[tuple[int, int, int, int]] = None

    @property
    def label(self) -> Optional[str]:
        """Best human-readable text for the element."""
        return self.title or self.value or self.description

    @property
    def text(self) -> Optional[str]:
        """Element text if this role carries visible text."""
        if self.role in _TEXT_ROLES:
            return self.label
        return None


def _get_attr(el, attr: str):
    """Safely read an AX attribute; returns None on failure."""
    import ApplicationServices as ax

    err, val = ax.AXUIElementCopyAttributeValue(el, attr, None)
    if err != 0:  # kAXErrorSuccess
        return None
    return val


def _get_attr_text(el, attr: str) -> Optional[str]:
    """Read an attribute and coerce to str/None."""
    val = _get_attr(el, attr)
    if val is None:
        return None
    s = str(val)
    return s if s else None


def _element_bounds(el) -> Optional[tuple[int, int, int, int]]:
    """Read kAXPosition + kAXSize into an (x, y, w, h) tuple."""
    pos = _get_attr(el, "AXPosition")
    size = _get_attr(el, "AXSize")
    if pos is None or size is None:
        return None
    try:
        x, y = float(pos.x), float(pos.y)
        w, h = float(size.width), float(size.height)
        return int(x), int(y), int(w), int(h)
    except Exception:  # pragma: no cover - pyobjc CGPoint/CGSize edge cases
        return None


def _element_to_snapshot(el) -> AXElement:
    return AXElement(
        role=_get_attr_text(el, "AXRole") or "",
        value=_get_attr_text(el, "AXValue"),
        description=_get_attr_text(el, "AXDescription"),
        title=_get_attr_text(el, "AXTitle"),
        bounds=_element_bounds(el),
    )


def _children(el) -> Iterator:
    """Iterate direct AX children of an element."""
    import ApplicationServices as ax

    err, arr = ax.AXUIElementCopyAttributeValue(el, "AXChildren", None)
    if err != 0 or arr is None:
        return
    try:
        for child in arr:
            yield child
    except TypeError:  # pragma: no cover - non-iterable
        return


def walk_tree(el) -> Iterator[AXElement]:
    """Depth-first walk yielding AXElement snapshots (parents before children)."""
    yield _element_to_snapshot(el)
    for child in _children(el):
        yield from walk_tree(child)


def find_element(
    app_ref, *,
    role: Optional[str] = None,
    label_contains: Optional[str] = None,
    max_depth: int = 40,
) -> Optional[AXElement]:
    """Find the first element matching role/label in an app's AX tree.

    `app_ref` is the result of `ApplicationServices.AXUIElementCreateApplication(pid)`.
    """
    found = None

    def _walk(el, depth):
        nonlocal found
        if found is not None or depth > max_depth:
            return
        snap = _element_to_snapshot(el)
        if role and snap.role != role:
            pass  # still recurse
        elif label_contains and snap.label and label_contains.lower() in snap.label.lower():
            found = snap
            return
        elif role and not label_contains and snap.role == role:
            found = snap
            return
        for child in _children(el):
            _walk(child, depth + 1)
            if found is not None:
                return

    _walk(app_ref, 0)
    return found


def extract_texts(app_ref, *, max_depth: int = 40, limit: int = 500) -> List[str]:
    """Collect user-visible text from an app's AX tree, in tree order."""
    texts: List[str] = []
    count = 0

    def _walk(el, depth):
        nonlocal count
        if depth > max_depth or count >= limit:
            return
        snap = _element_to_snapshot(el)
        t = snap.text
        if t:
            texts.append(t)
            count += 1
        for child in _children(el):
            _walk(child, depth + 1)

    _walk(app_ref, 0)
    return texts


def app_for_pid(pid: int):
    """Create an AXUIElement for the given pid."""
    import ApplicationServices as ax

    return ax.AXUIElementCreateApplication(pid)


def is_trusted() -> bool:
    """True if this process is AX-trusted."""
    import ApplicationServices as ax

    return bool(ax.AXIsProcessTrusted())
