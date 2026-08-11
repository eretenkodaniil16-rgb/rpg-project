from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from blender_helpers import clear_scene
from synapse_data import DURATION_SECONDS, FPS, PHASES, SOURCE_NOTE, TOTAL_FRAMES
from synapse_layout_v01 import apply_teaching_layout
from synapse_scene_v01 import SEED, build_synapse_scene


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="artifacts/synapse_v01")
    parser.add_argument("--frame-start", type=int, default=1)
    parser.add_argument("--frame-end", type=int, default=TOTAL_FRAMES)
    parser.add_argument("--resolution", type=int, default=1080)
    parser.add_argument("--render-samples", type=int, default=64)
    parser.add_argument("--save-blend", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    return parser.parse_args(argv)


def configure_scene(resolution: int, render_samples: int) -> None:
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.render.resolution_percentage = 100
    scene.render.resolution_y = int(resolution)
    scene.render.resolution_x = int(round(resolution * 16 / 9))
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        pass
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = render_samples
    scene.world.color = (0.006, 0.011, 0.025)
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass


def build(args: argparse.Namespace) -> None:
    clear_scene()
    configure_scene(args.resolution, args.render_samples)
    build_synapse_scene()
    apply_teaching_layout()


def write_manifest(output_root: Path, args: argparse.Namespace) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "contract": "chemical-synapse-v01",
        "blender_version": bpy.app.version_string,
        "duration_seconds": DURATION_SECONDS,
        "fps": FPS,
        "total_frames": TOTAL_FRAMES,
        "resolution": [int(round(args.resolution * 16 / 9)), args.resolution],
        "frame_start": max(1, args.frame_start),
        "frame_end": min(TOTAL_FRAMES, args.frame_end),
        "render_samples": args.render_samples,
        "seed": SEED,
        "phases": PHASES,
        "source_note": SOURCE_NOTE,
        "scale_note": "The synaptic cleft and molecular actors are enlarged schematically for educational visibility; geometry is not spatially to scale.",
    }
    (output_root / "synapse_v01_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def render_range(output_root: Path, frame_start: int, frame_end: int) -> None:
    start = max(1, int(frame_start))
    end = min(TOTAL_FRAMES, int(frame_end))
    if start > end:
        raise ValueError(f"Invalid frame range: {start}..{end}")
    frames = output_root / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    for frame in range(start, end + 1):
        scene.frame_set(frame)
        scene.render.filepath = str(frames / f"synapse_{frame:04d}.png")
        bpy.ops.render.render(write_still=True)


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_root).resolve()
    build(args)
    write_manifest(output_root, args)
    if args.save_blend:
        output_root.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(
            filepath=str(output_root / "chemical_synapse_neurotransmitter_v01.blend")
        )
    if not args.build_only:
        render_range(output_root, args.frame_start, args.frame_end)


if __name__ == "__main__":
    main()
