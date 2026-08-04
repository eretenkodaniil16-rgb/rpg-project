from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path(__file__).with_name("heart_cycle_animation_export_v07.py").read_text(
    encoding="utf-8"
)


def test_animation_export_v07_source_parses() -> None:
    ast.parse(SOURCE)


def test_review_profile_preserves_fifteen_second_duration() -> None:
    assert 'ANIMATION_EXPORT_REVISION = "heart_cycle_animation_export_v07"' in SOURCE
    assert 'parser.add_argument("--sample-step", type=int, default=2)' in SOURCE
    assert "return FPS // sample_step" in SOURCE
    assert "len(range(1, TOTAL_FRAMES + 1, sample_step))" in SOURCE
    assert '"duration_seconds": frame_count / output_fps' in SOURCE
    assert '"duration_seconds": TOTAL_FRAMES / FPS' in SOURCE


def test_mp4_export_settings_are_explicit() -> None:
    required_tokens = (
        'scene.render.image_settings.file_format = "FFMPEG"',
        'scene.render.ffmpeg.format = "MPEG4"',
        'scene.render.ffmpeg.codec = "H264"',
        'scene.render.ffmpeg.audio_codec = "NONE"',
        'scene.render.ffmpeg.constant_rate_factor = "MEDIUM"',
        'DEFAULT_VIDEO_NAME = "heart_cycle_review_v07.mp4"',
    )
    for token in required_tokens:
        assert token in SOURCE


def test_full_quality_profile_remains_available() -> None:
    assert '"full_quality_profile"' in SOURCE
    assert '"sample_step": 1' in SOURCE
    assert '"output_fps": FPS' in SOURCE
    assert '"output_frame_count": TOTAL_FRAMES' in SOURCE
    assert '"loop_seam"' in SOURCE


def test_invalid_sampling_cannot_change_duration_silently() -> None:
    assert "if FPS % args.sample_step != 0:" in SOURCE
    assert "must divide the authored" in SOURCE
    assert "if args.sample_step < 1:" in SOURCE
