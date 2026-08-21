"""Tests for siribridge.state — settle-detection logic."""

from siribridge.state import SettleDetector, wait_for_settle


def test_settles_after_stable_samples():
    d = SettleDetector(stable_required=3, min_latency_s=0)
    t = 0.0
    # Stream grows twice (each resets the stable counter), then stabilizes.
    d.sample("It", t); t += 1
    d.sample("It is", t); t += 1
    # First identical sample of the final text sets stable_count=1.
    d.sample("It is 3:00", t); t += 1
    assert d.sample("It is 3:00", t) is False  # stable count 2
    t += 1
    assert d.sample("It is 3:00", t) is True   # stable count 3 -> settled


def test_growing_stream_resets_stability():
    d = SettleDetector(stable_required=3, min_latency_s=0)
    t = 0.0
    d.sample("a", t); t += 1
    d.sample("ab", t); t += 1
    d.sample("abc", t); t += 1  # keeps changing, stable stays 1
    d.sample("abcd", t); t += 1  # stable 1 (first "abcd")
    assert d.sample("abcd", t) is False  # stable count 2
    assert d.sample("abcd", t) is True   # stable count 3 -> settled


def test_min_latency_enforced():
    d = SettleDetector(stable_required=1, min_latency_s=5.0)
    t = 0.0
    assert d.sample("done", t) is False  # not enough latency yet
    assert d.sample("done", t) is False
    t = 6.0
    assert d.sample("done", t) is True


def test_wait_for_settle_returns_final_text():
    calls = {"n": 0}

    def poll():
        calls["n"] += 1
        return "It is 3:00 PM" if calls["n"] >= 3 else f"partial-{calls['n']}"

    # Emit growing then a stable final text; need 2 consecutive identical
    # samples to settle (not 1, which would settle on the first poll).
    text = wait_for_settle(
        poll,
        stable_required=2,
        min_latency_s=0,
        max_wait_s=10,
        poll_interval_s=0.001,
    )
    assert text == "It is 3:00 PM"


def test_wait_for_settle_timeout_returns_last_text():
    def poll():
        return "stuck"

    text = wait_for_settle(
        poll,
        stable_required=5,          # never reaches 5 in time
        min_latency_s=0,
        max_wait_s=0.05,            # quick timeout
        poll_interval_s=0.001,
    )
    assert text == "stuck"
