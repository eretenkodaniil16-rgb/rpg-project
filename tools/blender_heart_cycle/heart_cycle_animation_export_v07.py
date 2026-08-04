from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_model as model
import heart_cycle_presentation_polish_v06 as presentation
from heart_cycle_data import FPS, TOTAL_FRAMES


ANIMATION_EXPORT_REVISION = "heart_cycle_animation_export_v07"
MODEL_REVISION = f"{presentation.MODEL_REVISION}_animation_v07"
DEFAULT_BLEND_NAME = f"{MODEL_REVISION}.blend"
DEFAULT_VIDEO_NAME = "heart_cycle_review_v07.mp4"
DEFAULT_GIF_NAME = "heart_cycle_review_v07.gif"


def _arguments() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(
        description="Build v06 and export the complete 15-second heart-cycle animation."
    )
    parser.add_argument("--output-root", default=str(SCRIPT_DIR / "output"))
    parser.add_argument("--blend-name", default=DEFAULT_BLEND_NAME)
    parser.add_argument("--video-name", default=DEFAULT_VIDEO_NAME)
    parser.add_argument("--render-preview", action="store_true")
    parser.add_argument("--render-animation", action="store_true")
    parser.add_argument("--resolution", type=int, default=720)
    parser.add_argument("--animation-resolution", type=int, default=360)
    parser.add_argument("--sample-step", type=int, default=2)
    parser.add_argument("--video-bitrate", type=int, default=4500)
    return parser.parse_args(argv)


def _validate_export_arguments(args: argparse.Namespace) -> None:
    if args.resolution < 240:
        raise ValueError("Preview resolution must be at least 240 pixels high")
    if args.animation_resolution < 240:
        raise ValueError("Animation resolution must be at least 240 pixels high")
    if args.sample_step < 1:
        raise ValueError("Animation sample step must be at least 1")
    if FPS % args.sample_step != 0:
        raise ValueError(
            f"Sample step {args.sample_step} must divide the authored {FPS} FPS timeline"
        )
    if args.video_bitrate < 1000:
        raise ValueError("Video bitrate must be at least 1000 kbit/s")


def _output_fps(sample_step: int) -> int:
    return FPS // sample_step


def _output_frame_count(sample_step: int) -> int:
    return len(range(1, TOTAL_FRAMES + 1, sample_step))


def _configure_animation_export(
    output_root: Path,
    *,
    video_name: str,
    animation_resolution: int,
    sample_step: int,
    video_bitrate: int,
) -> Path:
    scene = bpy.context.scene
    output_fps = _output_fps(sample_step)

    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.frame_step = sample_step
    scene.render.fps = output_fps
    scene.render.fps_base = 1.0
    scene.render.resolution_x = int(animation_resolution * 16 / 9)
    scene.render.resolution_y = animation_resolution
    scene.render.resolution_percentage = 100
    scene.render.use_file_extension = True
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.gopsize = output_fps * 2
    scene.render.ffmpeg.video_bitrate = video_bitrate

    video_path = output_root / video_name
    scene.render.filepath = str(video_path)
    scene["animation_export_revision"] = ANIMATION_EXPORT_REVISION
    scene["animation_source_fps"] = FPS
    scene["animation_output_fps"] = output_fps
    scene["animation_sample_step"] = sample_step
    scene["animation_output_frame_count"] = _output_frame_count(sample_step)
    scene["animation_duration_seconds"] = TOTAL_FRAMES / FPS
    return video_path


def _resolve_rendered_video(path: Path) -> Path:
    candidates = (
        path,
        path.with_suffix(".mp4"),
        Path(f"{path}.mp4"),
    )
    for candidate in candidates:
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    raise RuntimeError(f"Blender did not create the expected MP4 file: {path}")


def _render_preview(output_root: Path) -> tuple[Path, tuple[Path, ...]]:
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    scene.frame_step = 1
    scene.render.fps = FPS
    scene.render.resolution_x = int(scene.render.resolution_y * 16 / 9)
    scene.frame_set(1)

    preview_path = output_root / "heart_cycle_infographic_preview.png"
    scene.render.filepath = str(preview_path)
    bpy.ops.render.render(write_still=True)
    phase_paths = presentation.infographic._render_infographic_phase_previews(output_root)
    return preview_path, phase_paths


def _augment_manifest(
    path: Path,
    *,
    blend_path: Path,
    video_path: Path,
    args: argparse.Namespace,
    animation_rendered: bool,
) -> Path:
    payload = json.loads(path.read_text(encoding="utf-8"))
    output_fps = _output_fps(args.sample_step)
    frame_count = _output_frame_count(args.sample_step)
    payload["model_revision"] = MODEL_REVISION
    payload["animation_export_revision"] = ANIMATION_EXPORT_REVISION
    payload["animation_export"] = {
        "source_timeline": {
            "frame_start": 1,
            "frame_end": TOTAL_FRAMES,
            "fps": FPS,
            "frame_count": TOTAL_FRAMES,
            "duration_seconds": TOTAL_FRAMES / FPS,
        },
        "review_profile": {
            "sample_step": args.sample_step,
            "output_fps": output_fps,
            "output_frame_count": frame_count,
            "resolution": [int(args.animation_resolution * 16 / 9), args.animation_resolution],
            "duration_seconds": frame_count / output_fps,
            "video_codec": "H.264",
            "container": "MPEG-4",
            "video_bitrate_kbit_s": args.video_bitrate,
        },
        "full_quality_profile": {
            "sample_step": 1,
            "output_fps": FPS,
            "output_frame_count": TOTAL_FRAMES,
            "duration_seconds": TOTAL_FRAMES / FPS,
        },
        "files": {
            "blend": blend_path.name,
            "mp4": video_path.name,
            "gif": DEFAULT_GIF_NAME,
        },
        "rendered": animation_rendered,
        "gif_generation": "ffmpeg palette post-process in CI",
        "loop_seam": "frame 450 and frame 1 share the same physiological boundary state",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_model(resolution: int) -> model.HeartBuild:
    build = presentation.build_model(resolution)
    scene = bpy.context.scene
    scene["model_revision"] = MODEL_REVISION
    scene["animation_export_revision"] = ANIMATION_EXPORT_REVISION
    return build


def main() -> int:
    args = _arguments()
    _validate_export_arguments(args)

    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    build_model(args.resolution)

    preview_path: Path | None = None
    phase_paths: tuple[Path, ...] = ()
    if args.render_preview:
        preview_path, phase_paths = _render_preview(output_root)

    requested_video_path = _configure_animation_export(
        output_root,
        video_name=args.video_name,
        animation_resolution=args.animation_resolution,
        sample_step=args.sample_step,
        video_bitrate=args.video_bitrate,
    )

    blend_path = output_root / args.blend_name
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)

    rendered_video_path = requested_video_path
    if args.render_animation:
        bpy.context.scene.frame_set(1)
        bpy.ops.render.render(animation=True)
        rendered_video_path = _resolve_rendered_video(requested_video_path)

    manifest_path = presentation.rig._BASE_WRITE_MANIFEST(output_root, blend_path)
    manifest_path = presentation.rig._augment_manifest(manifest_path)
    manifest_path = presentation._augment_manifest(manifest_path)
    manifest_path = _augment_manifest(
        manifest_path,
        blend_path=blend_path,
        video_path=rendered_video_path,
        args=args,
        animation_rendered=args.render_animation,
    )

    print(f"HEART_CYCLE_BLEND={blend_path}")
    print(f"HEART_CYCLE_MANIFEST={manifest_path}")
    print(f"HEART_CYCLE_ANIMATION_PROFILE={_output_fps(args.sample_step)}fps/{args.animation_resolution}p")
    if preview_path is not None:
        print(f"HEART_CYCLE_PREVIEW={preview_path}")
        print(f"HEART_CYCLE_PHASE_PREVIEWS={len(phase_paths)}")
    if args.render_animation:
        print(f"HEART_CYCLE_MP4={rendered_video_path}")
    return 0


model.MODEL_REVISION = MODEL_REVISION
model.build_model = build_model


if __name__ == "__main__":
    raise SystemExit(main())
