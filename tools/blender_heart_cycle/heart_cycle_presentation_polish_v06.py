from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_layout_fix_v05 as layout_v05
import heart_cycle_model as model
from heart_cycle_data import TOTAL_FRAMES, phase_ranges


PRESENTATION_REVISION = "heart_cycle_presentation_polish_v06"
MODEL_REVISION = (
    "heart_cutaway_reference_layout_v05_phase_rig_v03_"
    "infographic_v04_presentation_v06"
)
DEFAULT_BLEND_NAME = f"{MODEL_REVISION}.blend"

rig = layout_v05.rig
infographic = layout_v05.infographic

_FLOW_VALIDATION: dict[str, object] = {}


def _key_visibility(
    objects: Iterable[bpy.types.Object],
    visible: bool,
    frame: int,
) -> None:
    for obj in objects:
        obj.hide_viewport = not visible
        obj.hide_render = not visible
        obj.keyframe_insert(data_path="hide_viewport", frame=frame)
        obj.keyframe_insert(data_path="hide_render", frame=frame)


def _repair_flow_visibility(build: model.HeartBuild) -> None:
    """Rebuild flow visibility without conflicting boundary keyframes.

    v03 inserted a second pass that hid the next phase's active flow group at
    the same frame where it had just been enabled. The later key won, so the
    arrows were absent from mid-phase renders. This pass writes one canonical
    visibility state for every group at every phase boundary.
    """

    ranges = phase_ranges()
    for phase, start, end in ranges:
        active_keys = set(rig.FLOW_PROFILES[phase.slug][0])
        for key, objects in build.flow_groups.items():
            visible = key in active_keys
            _key_visibility(objects, visible, start)
            _key_visibility(objects, visible, end)

        if end < TOTAL_FRAMES:
            next_phase = ranges[phase.index]
            next_active = set(rig.FLOW_PROFILES[next_phase[0].slug][0])
            for key, objects in build.flow_groups.items():
                _key_visibility(objects, key in next_active, end + 1)

    layout_v05._set_interpolation_blender_52()
    bpy.context.scene.frame_set(1)


def _animate_with_repaired_flow(build: model.HeartBuild) -> None:
    _BASE_ANIMATE(build)
    _repair_flow_visibility(build)


def _adjust_infographic_layout(build: model.HeartBuild) -> None:
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None:
        raise RuntimeError("Heart scene has no active camera")

    offset = bpy.data.objects.get("CTRL_InfographicHeartOffset")
    if offset is None:
        raise RuntimeError("Infographic heart offset control is missing")
    offset.location.x = 1.62
    offset.location.z = -0.12

    title = bpy.data.objects.get("Infographic_Title")
    subtitle = bpy.data.objects.get("Infographic_Subtitle")
    if title is None or subtitle is None:
        raise RuntimeError("Infographic title objects are missing")

    title.data.align_x = "LEFT"
    title.data.size = 0.045
    title.location = (-0.705, 0.360, -2.52)

    subtitle.data.align_x = "LEFT"
    subtitle.data.size = 0.0175
    subtitle.location = (-0.705, 0.318, -2.52)

    render_collection = build.collections["render"]
    panel_material = bpy.data.materials.get("M_InfoPanel")
    accent_material = bpy.data.materials.get("M_InfoAccent")
    if panel_material is None or accent_material is None:
        raise RuntimeError("Infographic materials are missing")

    header = infographic._camera_plane(
        "Infographic_HeaderPanel_v06",
        camera,
        render_collection,
        (-0.41, 0.337, -2.60),
        (0.35, 0.052),
        panel_material,
    )
    separator = infographic._camera_plane(
        "Infographic_HeaderSeparator_v06",
        camera,
        render_collection,
        (-0.41, 0.284, -2.57),
        (0.35, 0.0022),
        accent_material,
    )
    header["presentation_revision"] = PRESENTATION_REVISION
    separator["presentation_revision"] = PRESENTATION_REVISION

    scene["presentation_revision"] = PRESENTATION_REVISION
    scene["presentation_layout"] = (
        "header confined to left card; heart shifted right and slightly down"
    )


def _validate_flow_visibility(build: model.HeartBuild) -> dict[str, object]:
    failures: list[str] = []
    phase_results: list[dict[str, object]] = []

    for phase, start, end in phase_ranges():
        frame = start + (end - start) // 2
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        active_keys = set(rig.FLOW_PROFILES[phase.slug][0])
        visible_keys: list[str] = []

        for key, objects in build.flow_groups.items():
            visible = any(not obj.hide_render for obj in objects)
            if visible:
                visible_keys.append(key)
            expected = key in active_keys
            if visible != expected:
                failures.append(
                    f"phase {phase.index} {phase.slug}: {key} visible={visible}, expected={expected}"
                )

        phase_results.append(
            {
                "phase_index": phase.index,
                "phase_slug": phase.slug,
                "frame": frame,
                "expected_flow_groups": sorted(active_keys),
                "visible_flow_groups": sorted(visible_keys),
            }
        )

    bpy.context.scene.frame_set(1)
    if failures:
        raise RuntimeError("Flow visibility validation failed: " + "; ".join(failures))

    return {
        "status": "passed",
        "phase_count": len(phase_results),
        "phases": phase_results,
    }


_BASE_ANIMATE = rig._animate_phase_rig
rig._animate_phase_rig = _animate_with_repaired_flow

_BASE_BUILD_MODEL = layout_v05.build_model
_BASE_AUGMENT_MANIFEST = infographic._augment_manifest

infographic.MODEL_REVISION = MODEL_REVISION
infographic.DEFAULT_BLEND_NAME = DEFAULT_BLEND_NAME
model.MODEL_REVISION = MODEL_REVISION


def build_model(resolution: int) -> model.HeartBuild:
    global _FLOW_VALIDATION

    build = _BASE_BUILD_MODEL(resolution)
    _adjust_infographic_layout(build)
    _FLOW_VALIDATION = _validate_flow_visibility(build)

    scene = bpy.context.scene
    scene["model_revision"] = MODEL_REVISION
    scene["presentation_revision"] = PRESENTATION_REVISION
    scene["flow_visibility_validation"] = "passed"
    return build


def _augment_manifest(path: Path) -> Path:
    path = _BASE_AUGMENT_MANIFEST(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["model_revision"] = MODEL_REVISION
    payload["presentation_revision"] = PRESENTATION_REVISION
    payload["presentation"] = {
        "title_region": "left header card",
        "heart_offset_x": 1.62,
        "heart_offset_z": -0.12,
        "header_occlusion": "prevented",
        "flow_visibility": "canonical phase-boundary schedule",
    }
    payload["flow_visibility_validation"] = _FLOW_VALIDATION
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


infographic.build_model = build_model
infographic._augment_manifest = _augment_manifest
model.build_model = build_model


if __name__ == "__main__":
    raise SystemExit(infographic.main())
