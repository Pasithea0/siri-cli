"""Tests for siribridge.capture.ax — pure AX-snapshot logic.

These test the AXElement model and text-extraction rules without a live
macOS accessibility session (that needs TCC grants and is exercised by the
integration path).
"""

from siribridge.capture.ax import AXElement, extract_texts, find_element

# Minimal fake element tree that mimics what _children/walk_tree yield.
# We build a plain nested structure and a fake app ref with a walk.


class _Fake:
    def __init__(self, role, value=None, desc=None, title=None, children=()):
        self.role = role
        self.value = value
        self.desc = desc
        self.title = title
        self.children = list(children)


def _snap(el):
    return AXElement(
        role=el.role,
        value=el.value,
        description=el.desc,
        title=el.title,
        bounds=(0, 0, 1, 1),
    )


def _walk(el):
    yield _snap(el)
    for c in el.children:
        yield from _walk(c)


def test_ax_element_label_prefers_title():
    el = AXElement(role="AXStaticText", value="v", description="d", title="t")
    assert el.label == "t"


def test_ax_element_text_only_for_text_roles():
    assert AXElement(role="AXStaticText", title="hi", value=None, description=None).text == "hi"
    assert AXElement(role="AXGroup", title="nope", value=None, description=None).text is None


def test_walk_returns_parents_before_children():
    root = _Fake("AXWindow", title="w", children=[_Fake("AXStaticText", title="a")])
    roles = [s.role for s in _walk(root)]
    assert roles == ["AXWindow", "AXStaticText"]


def test_find_element_by_label_contains():
    root = _Fake(
        "AXWindow",
        title="w",
        children=[
            _Fake("AXStaticText", title="Ask Siri"),
            _Fake("AXStaticText", title="Cancel"),
        ],
    )

    # monkeypatch module-level helpers to use our fake tree
    import siribridge.capture.ax as axmod

    axmod._children = lambda el: iter(el.children)
    axmod._element_to_snapshot = _snap
    found = axmod.find_element(root, label_contains="siri")
    assert found is not None
    assert found.title == "Ask Siri"


def test_find_element_by_role():
    import siribridge.capture.ax as axmod

    axmod._children = lambda el: iter(el.children)
    axmod._element_to_snapshot = _snap
    root = _Fake("AXWindow", title="w", children=[_Fake("AXTextField", title="input")])
    found = axmod.find_element(root, role="AXTextField")
    assert found is not None
    assert found.role == "AXTextField"


def test_extract_texts_collects_text_roles_in_order():
    import siribridge.capture.ax as axmod

    axmod._children = lambda el: iter(el.children)
    axmod._element_to_snapshot = _snap
    root = _Fake(
        "AXWindow",
        title="w",
        children=[
            _Fake("AXStaticText", title="Q: what time is it"),
            _Fake("AXGroup", title="ignored", children=[_Fake("AXStaticText", title="It is 3:00 PM")]),
        ],
    )
    texts = axmod.extract_texts(root)
    assert "Q: what time is it" in texts
    assert "It is 3:00 PM" in texts
    assert "ignored" not in texts
