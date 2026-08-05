from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path(__file__).with_name("heart_cycle_final_export_v08.py").read_text(
    encoding="utf-8"
)


def test_final_export_v08_source_parses() -> None:
    ast.parse(SOURCE)


def test_native_1080p_full_timeline_contract_is_locked() -> None:
    required_tokens = (
        'FINAL_EXPORT_REVISION = "heart_cycle_final_export_v08"',
        'parser.add_argument("--animation-resolution", type=int, default=1080)',
        'parser.add_argument("--sample-step", type=int, default=1)',
        'parser.add_argument("--render-samples", type=int, default=128)',
        '"source_is_native_blender_render": True',
        '"upscaled_from_preview": False',
        '"frame_count": TOTAL_FRAMES',
        '"fps": FPS',
    )
    for token in required_tokens:
        assert token in SOURCE


def test_sharded_rendering_preserves_original_frame_numbers() -> None:
    assert 'parser.add_argument("--frame-start", type=int, required=True)' in SOURCE
    assert 'parser.add_argument("--frame-end", type=int, required=True)' in SOURCE
    assert 'f"{DEFAULT_FRAME_PREFIX}{frame:04d}.png"' in SOURCE
    assert "range(args.frame_start, args.frame_end + 1, args.sample_step)" in SOURCE


def test_lossless_png_intermediate_and_validation_are_locked() -> None:
    assert 'scene.render.image_settings.file_format = "PNG"' in SOURCE
    assert 'scene.render.image_settings.color_mode = "RGB"' in SOURCE
    assert 'scene.render.image_settings.color_depth = "8"' in SOURCE
    assert '"intermediate_format": "PNG RGB 8-bit lossless"' in SOURCE
    assert "Missing final render frames" in SOURCE
    assert "Empty final render frames" in SOURCE


def test_eevee_sampling_is_version_tolerant() -> None:
    assert '("taa_render_samples", "taa_samples")' in SOURCE
    assert 'applied_sampling_property = "engine_default"' in SOURCE
