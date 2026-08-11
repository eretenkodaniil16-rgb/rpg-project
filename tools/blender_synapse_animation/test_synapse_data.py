from synapse_data import (
    DURATION_SECONDS,
    FPS,
    PHASES,
    TOTAL_FRAMES,
    phase_for_second,
    sec_to_frame,
)


def test_contract_is_45_seconds_at_30_fps():
    assert DURATION_SECONDS == 45
    assert FPS == 30
    assert TOTAL_FRAMES == 1350


def test_phase_timeline_is_contiguous():
    assert PHASES[0]["start_s"] == 0.0
    assert PHASES[-1]["end_s"] == 45.0
    for left, right in zip(PHASES, PHASES[1:]):
        assert left["end_s"] == right["start_s"]


def test_frame_conversion_edges():
    assert sec_to_frame(0.0) == 1
    assert sec_to_frame(1.0) == 31
    assert sec_to_frame(45.0) == 1350


def test_phase_lookup_boundaries():
    assert phase_for_second(0)["id"] == "rest"
    assert phase_for_second(8.0)["id"] == "calcium_entry"
    assert phase_for_second(44.9)["id"] == "recovery"
