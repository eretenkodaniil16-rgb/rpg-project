from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_model as model
import heart_cycle_phase_rig_v03 as rig


def _no_base_animation(_build: model.HeartBuild) -> None:
    """Keep the v02 geometry build, but defer all keyframes to phase rig v03."""


def build_model_once(resolution: int) -> model.HeartBuild:
    active_animate = model._animate
    model._animate = _no_base_animation
    try:
        build = rig._PREVIOUS_BUILD_MODEL(resolution)
    finally:
        model._animate = active_animate

    scene = bpy.context.scene
    for marker in list(scene.timeline_markers):
        scene.timeline_markers.remove(marker)

    rig._animate_phase_rig(build)
    scene["model_revision"] = rig.MODEL_REVISION
    scene["phase_rig_revision"] = rig.PHASE_RIG_REVISION
    return build


def main() -> int:
    args = rig._arguments()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    build_model_once(args.resolution)
    blend_path = output_root / args.blend_name
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    manifest_path = rig._augment_manifest(
        rig._BASE_WRITE_MANIFEST(output_root, blend_path)
    )

    scene = bpy.context.scene
    preview_paths: tuple[Path, ...] = ()
    if args.render_preview:
        scene.frame_set(1)
        scene.render.filepath = str(output_root / "heart_cutaway_preview.png")
        bpy.ops.render.render(write_still=True)
        preview_paths = rig._render_phase_previews(output_root)
    if args.render_animation:
        frame_root = output_root / "frames"
        frame_root.mkdir(exist_ok=True)
        scene.render.filepath = str(frame_root / "heart_cycle_")
        bpy.ops.render.render(animation=True)

    print(f"HEART_CYCLE_BLEND={blend_path}")
    print(f"HEART_CYCLE_MANIFEST={manifest_path}")
    if preview_paths:
        print(f"HEART_CYCLE_PHASE_PREVIEWS={len(preview_paths)}")
    return 0


model.build_model = build_model_once


if __name__ == "__main__":
    raise SystemExit(main())
