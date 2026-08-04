from heart_cycle_data import FPS, PHASES, TOTAL_FRAMES, phase_ranges


def test_timeline_is_15_seconds() -> None:
    assert TOTAL_FRAMES == 450
    assert TOTAL_FRAMES / FPS == 15.0


def test_nine_phases_cover_entire_timeline() -> None:
    ranges = phase_ranges()
    assert len(ranges) == 9
    assert ranges[0][1] == 1
    assert ranges[-1][2] == TOTAL_FRAMES
    assert sum(phase.frame_count for phase in PHASES) == TOTAL_FRAMES


def test_real_cycle_is_point_eight_seconds() -> None:
    assert abs(sum(phase.duration_seconds_real for phase in PHASES) - 0.8) < 1e-9
