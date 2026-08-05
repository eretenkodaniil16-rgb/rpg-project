from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_animation_export_v07 as export_v07
from heart_cycle_data import FPS, TOTAL_FRAMES


FINAL_EXPORT_REVISION = "heart_cycle_final_export_v08"
MODEL_REVISION = f"{export_v07.MODEL_REVISION}_final_v08"
DEFAULT_FRAME_DIRECTORY = "final_frames"
DEFAULT_FRAME_PREFIX = "heart_cycle_final_"


def _arguments() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(
        description=(
            "Render one lossless PNG shard of the native 450-frame heart-cycle "
            "timeline for final 1080p assembly."
        )
    )
    parser.add_argument("--output-root", default=str(SCRIPT_DIR / "output_final_v08"))
    parser.add_argument("--frame-start", type=int, required=True)
    parser.add_argument("--frame-end", type=int, required=True)
    parser.add_argument("--animation-resolution", type=int, default=1080)
    parser.add_argument("--sample-step", type=int, default=1)
    parser.add_argument("--render-samples", type=int, default=128)
    parser.add_argument("--save-blend", action="store_true")
    return parser.parse_args(argv)


def _validate_arguments(args: argparse.Namespace) -> None:
    if not 1 <= args.frame_start <= TOTAL_FRAMES:
        raise ValueError(f"frame-start must be between 1 and {TOTAL_FRAMES}")
    if not 1 <= args.frame_end <= TOTAL_FRAMES:
        raise ValueError(f"frame-end must be between 1 and {TOTAL_FRAMES}")
    if args.frame_end < args.frame_start:
        raise ValueError("frame-end must not precede frame-start")
    if args.animation_resolution < 720:
        raise ValueError("Final animation resolution must be at least 720p")
    if args.sample_step < 1:
        raise ValueError("sample-step must be at least 1")
    if FPS % args.sample_step != 0:
        raise ValueError(f"sample-step must divide the authored {FPS} FPS timeline")
    if args.render_samples < 1:
        raise ValueError("render-samples must be positive")


def _expected_frames(args: argparse.Namespace) -> tuple[int, ...]:
    return tuple(range(args.frame_start, args.frame_end + 1, args.sample_step))


def _configure_quality(scene: bpy.types.Scene, args: argparse.Namespace, frame_root: Path) -> None:
    scene.frame_start = args.frame_start
    scene.frame_end = args.frame_end
    scene.frame_step = args.sample_step
    scene.render.fps = FPS // args.sample_step
    scene.render.fps_base = 1.0
    scene.render.resolution_x = int(args.animation_resolution * 16 / 9)
    scene.render.resolution_y = args.animation_resolution
    scene.render.resolution_percentage = 100
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    scene.render.use_placeholder = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 12
    scene.render.filepath = str(frame_root / DEFAULT_FRAME_PREFIX)

    # Blender has changed the EEVEE sampling RNA across releases. Apply the
    # highest supported render-sample property without making v08 version-fragile.
    eevee = getattr(scene, "eevee", None)
    applied_sampling_property = "engine_default"
    if eevee is not None:
        for attribute in ("taa_render_samples", "taa_samples"):
            if hasattr(eevee, attribute):
                setattr(eevee, attribute, args.render_samples)
                applied_sampling_property = attribute
                break

    scene["final_export_revision"] = FINAL_EXPORT_REVISION
    scene["final_export_width"] = scene.render.resolution_x
    scene["final_export_height"] = scene.render.resolution_y
    scene["final_export_fps"] = scene.render.fps
    scene["final_export_frame_start"] = args.frame_start
    scene["final_export_frame_end"] = args.frame_end
    scene["final_export_sample_step"] = args.sample_step
    scene["final_export_render_samples"] = args.render_samples
    scene["final_export_sampling_property"] = applied_sampling_property
    scene["final_export_intermediate"] = "lossless PNG sequence"


def _validate_output(frame_root: Path, expected_frames: tuple[int, ...]) -> tuple[Path, ...]:
    expected_paths = tuple(
        frame_root / f"{DEFAULT_FRAME_PREFIX}{frame:04d}.png" for frame in expected_frames
    )
    missing = tuple(path for path in expected_paths if not path.is_file())
    if missing:
        raise RuntimeError(f"Missing final render frames: {missing[:5]}")
    empty = tuple(path for path in expected_paths if path.stat().st_size <= 0)
    if empty:
        raise RuntimeError(f"Empty final render frames: {empty[:5]}")
    return expected_paths


def _write_shard_manifest(
    output_root: Path,
    args: argparse.Namespace,
    rendered_frames: tuple[Path, ...],
) -> Path:
    width = int(args.animation_resolution * 16 / 9)
    payload = {
        "final_export_revision": FINAL_EXPORT_REVISION,
        "model_revision": MODEL_REVISION,
        "source_timeline": {
            "frame_start": 1,
            "frame_end": TOTAL_FRAMES,
            "fps": FPS,
            "frame_count": TOTAL_FRAMES,
            "duration_seconds": TOTAL_FRAMES / FPS,
        },
        "shard": {
            "frame_start": args.frame_start,
            "frame_end": args.frame_end,
            "sample_step": args.sample_step,
            "rendered_frame_count": len(rendered_frames),
        },
        "quality": {
            "width": width,
            "height": args.animation_resolution,
            "fps": FPS // args.sample_step,
            "intermediate_format": "PNG RGB 8-bit lossless",
            "render_samples_requested": args.render_samples,
            "source_is_native_blender_render": True,
            "upscaled_from_preview": False,
        },
        "first_frame": rendered_frames[0].name,
        "last_frame": rendered_frames[-1].name,
    }
    path = output_root / f"heart_cycle_final_v08_shard_{args.frame_start:04d}_{args.frame_end:04d}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    args = _arguments()
    _validate_arguments(args)

    output_root = Path(args.output_root).resolve()
    frame_root = output_root / DEFAULT_FRAME_DIRECTORY
    frame_root.mkdir(parents=True, exist_ok=True)

    export_v07.build_model(args.animation_resolution)
    scene = bpy.context.scene
    scene["model_revision"] = MODEL_REVISION
    _configure_quality(scene, args, frame_root)

    if args.save_blend:
        blend_path = output_root / f"{MODEL_REVISION}.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
        print(f"HEART_CYCLE_FINAL_BLEND={blend_path}")

    scene.frame_set(args.frame_start)
    bpy.ops.render.render(animation=True)

    rendered_frames = _validate_output(frame_root, _expected_frames(args))
    manifest_path = _write_shard_manifest(output_root, args, rendered_frames)

    print(f"HEART_CYCLE_FINAL_REVISION={FINAL_EXPORT_REVISION}")
    print(f"HEART_CYCLE_FINAL_FRAME_ROOT={frame_root}")
    print(f"HEART_CYCLE_FINAL_FRAME_COUNT={len(rendered_frames)}")
    print(f"HEART_CYCLE_FINAL_MANIFEST={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
