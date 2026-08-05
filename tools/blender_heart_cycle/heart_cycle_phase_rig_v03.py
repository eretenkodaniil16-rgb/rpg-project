from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_build as anatomy_v02
import heart_cycle_model as model
from heart_cycle_data import FPS, PHASES, TOTAL_FRAMES, phase_ranges


PHASE_RIG_REVISION = "heart_cycle_phase_rig_v03"
MODEL_REVISION = "heart_cutaway_v02_phase_rig_v03"
model.MODEL_REVISION = MODEL_REVISION

_PREVIOUS_BUILD_MODEL = model.build_model
_BASE_WRITE_MANIFEST = model._write_manifest


@dataclass(frozen=True)
class BoundaryState:
    left_atrium_scale: tuple[float, float, float]
    right_atrium_scale: tuple[float, float, float]
    left_ventricle_scale: tuple[float, float, float]
    right_ventricle_scale: tuple[float, float, float]
    av_open_fraction: float
    semilunar_open_fraction: float
    left_atrial_pressure: float
    right_atrial_pressure: float
    left_ventricular_pressure: float
    right_ventricular_pressure: float
    aortic_pressure: float
    pulmonary_artery_pressure: float
    ventricular_volume_fraction: float
    atrial_volume_fraction: float


# State 0 is also state 9, making the 450-frame sequence loop without a jump.
BOUNDARY_STATES: tuple[BoundaryState, ...] = (
    BoundaryState(
        (1.00, 1.00, 1.00),
        (1.00, 1.00, 1.00),
        (1.00, 1.00, 1.00),
        (1.00, 1.00, 1.00),
        1.00,
        0.00,
        8.0,
        5.0,
        5.0,
        2.0,
        80.0,
        15.0,
        1.00,
        0.92,
    ),
    BoundaryState(
        (0.91, 0.86, 0.92),
        (0.90, 0.85, 0.91),
        (1.015, 1.010, 1.010),
        (1.020, 1.012, 1.008),
        1.00,
        0.00,
        6.0,
        4.0,
        11.0,
        7.0,
        80.0,
        15.0,
        1.00,
        0.74,
    ),
    BoundaryState(
        (0.96, 0.96, 0.97),
        (0.96, 0.96, 0.97),
        (0.975, 0.925, 1.108),
        (0.970, 0.900, 1.145),
        0.00,
        0.00,
        7.0,
        5.0,
        68.0,
        14.0,
        80.0,
        15.0,
        1.00,
        0.78,
    ),
    BoundaryState(
        (0.985, 0.985, 0.985),
        (0.985, 0.985, 0.985),
        (0.955, 0.895, 1.170),
        (0.950, 0.865, 1.218),
        0.00,
        0.00,
        8.0,
        6.0,
        82.0,
        20.0,
        80.0,
        15.0,
        1.00,
        0.83,
    ),
    BoundaryState(
        (1.015, 1.020, 1.015),
        (1.020, 1.025, 1.018),
        (0.885, 0.825, 0.875),
        (0.900, 0.790, 0.900),
        0.00,
        1.00,
        10.0,
        7.0,
        122.0,
        26.0,
        118.0,
        24.0,
        0.72,
        0.90,
    ),
    BoundaryState(
        (1.045, 1.055, 1.040),
        (1.050, 1.060, 1.045),
        (0.850, 0.790, 0.835),
        (0.875, 0.760, 0.865),
        0.00,
        0.82,
        12.0,
        8.0,
        92.0,
        18.0,
        96.0,
        18.0,
        0.56,
        1.00,
    ),
    BoundaryState(
        (1.055, 1.065, 1.050),
        (1.060, 1.070, 1.055),
        (0.900, 0.845, 0.890),
        (0.915, 0.820, 0.910),
        0.00,
        0.00,
        13.0,
        9.0,
        72.0,
        12.0,
        82.0,
        16.0,
        0.56,
        1.00,
    ),
    BoundaryState(
        (1.060, 1.070, 1.055),
        (1.065, 1.075, 1.060),
        (0.975, 0.925, 1.108),
        (0.970, 0.900, 1.145),
        0.00,
        0.00,
        12.0,
        8.0,
        5.0,
        2.0,
        80.0,
        15.0,
        0.56,
        1.00,
    ),
    BoundaryState(
        (0.965, 0.955, 0.970),
        (0.960, 0.950, 0.965),
        (1.030, 1.035, 1.025),
        (1.035, 1.040, 1.020),
        1.00,
        0.00,
        7.0,
        5.0,
        4.0,
        2.0,
        80.0,
        15.0,
        0.84,
        0.72,
    ),
    BoundaryState(
        (1.00, 1.00, 1.00),
        (1.00, 1.00, 1.00),
        (1.00, 1.00, 1.00),
        (1.00, 1.00, 1.00),
        1.00,
        0.00,
        8.0,
        5.0,
        5.0,
        2.0,
        80.0,
        15.0,
        1.00,
        0.92,
    ),
)


FLOW_PROFILES: dict[str, tuple[tuple[str, ...], float, float]] = {
    "atrial_systole": (("red_av", "blue_av"), 0.88, 0.38),
    "asynchronous_contraction": ((), 0.0, 0.0),
    "isometric_contraction": ((), 0.0, 0.0),
    "rapid_ejection": (("red_eject", "blue_eject"), 1.22, 0.92),
    "slow_ejection": (("red_eject", "blue_eject"), 0.78, 0.32),
    "protodiastolic_period": (("red_reverse", "blue_reverse"), 0.58, 0.10),
    "isometric_relaxation": ((), 0.0, 0.0),
    "rapid_filling": (("red_av", "blue_av"), 1.16, 0.78),
    "slow_filling": (("red_av", "blue_av"), 0.52, 0.18),
}


PRESSURE_CHANNELS = (
    "left_atrial_pressure_mmHg",
    "right_atrial_pressure_mmHg",
    "left_ventricular_pressure_mmHg",
    "right_ventricular_pressure_mmHg",
    "aortic_pressure_mmHg",
    "pulmonary_artery_pressure_mmHg",
    "ventricular_volume_fraction",
    "atrial_volume_fraction",
    "av_valve_open_fraction",
    "semilunar_valve_open_fraction",
    "phase_index",
)


def _arguments() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(description="Build the v03 physiological heart phase rig.")
    parser.add_argument("--output-root", default=str(SCRIPT_DIR / "output"))
    parser.add_argument("--blend-name", default=f"{MODEL_REVISION}.blend")
    parser.add_argument("--render-preview", action="store_true")
    parser.add_argument("--render-animation", action="store_true")
    parser.add_argument("--resolution", type=int, default=1080)
    return parser.parse_args(argv)


def _set_scale(control: bpy.types.Object, scale: tuple[float, float, float], frame: int) -> None:
    control.scale = scale
    control.keyframe_insert(data_path="scale", frame=frame)


def _set_custom_property(owner: bpy.types.ID, name: str, value: float, frame: int) -> None:
    owner[name] = float(value)
    owner.keyframe_insert(data_path=f'["{name}"]', frame=frame)


def _leaflet_baseline(leaflet: bpy.types.Object) -> tuple[float, float, float]:
    key = "phase_rig_base_rotation"
    if key not in leaflet:
        leaflet[key] = tuple(float(value) for value in leaflet.rotation_euler)
    return tuple(float(value) for value in leaflet[key])


def _set_valve_open_fraction(
    leaflets: Iterable[bpy.types.Object],
    fraction: float,
    frame: int,
    *,
    semilunar: bool,
) -> None:
    maximum = math.radians(44.0 if semilunar else 31.0)
    fraction = max(0.0, min(1.0, float(fraction)))
    for index, leaflet in enumerate(leaflets):
        base = _leaflet_baseline(leaflet)
        sign = -1.0 if index % 2 else 1.0
        leaflet.rotation_euler = (
            base[0] + sign * maximum * fraction,
            base[1],
            base[2],
        )
        leaflet.keyframe_insert(data_path="rotation_euler", frame=frame)
        leaflet["open_fraction"] = fraction
        leaflet.keyframe_insert(data_path='["open_fraction"]', frame=frame)


def _all_flow_objects(build: model.HeartBuild) -> tuple[bpy.types.Object, ...]:
    return tuple(obj for group in build.flow_groups.values() for obj in group)


def _set_flow_visibility(objects: Iterable[bpy.types.Object], visible: bool, frame: int) -> None:
    for obj in objects:
        obj.hide_viewport = not visible
        obj.hide_render = not visible
        obj.keyframe_insert(data_path="hide_viewport", frame=frame)
        obj.keyframe_insert(data_path="hide_render", frame=frame)


def _set_flow_intensity(objects: Iterable[bpy.types.Object], intensity: float, frame: int) -> None:
    intensity = max(0.01, float(intensity))
    for obj in objects:
        if "phase_rig_base_scale" not in obj:
            obj["phase_rig_base_scale"] = tuple(float(value) for value in obj.scale)
        base = tuple(float(value) for value in obj["phase_rig_base_scale"])
        if obj.type == "CURVE":
            scale = (base[0] * intensity, base[1] * intensity, base[2])
        else:
            scale = tuple(value * intensity for value in base)
        obj.scale = scale
        obj.keyframe_insert(data_path="scale", frame=frame)
        obj["flow_intensity"] = intensity
        obj.keyframe_insert(data_path='["flow_intensity"]', frame=frame)


def _apply_boundary_state(build: model.HeartBuild, state: BoundaryState, frame: int) -> None:
    _set_scale(build.controls["left_atrium"], state.left_atrium_scale, frame)
    _set_scale(build.controls["right_atrium"], state.right_atrium_scale, frame)
    _set_scale(build.controls["left_ventricle"], state.left_ventricle_scale, frame)
    _set_scale(build.controls["right_ventricle"], state.right_ventricle_scale, frame)

    for name in ("Mitral", "Tricuspid"):
        _set_valve_open_fraction(
            build.valve_leaflets[name],
            state.av_open_fraction,
            frame,
            semilunar=False,
        )
    for name in ("Aortic", "Pulmonary"):
        _set_valve_open_fraction(
            build.valve_leaflets[name],
            state.semilunar_open_fraction,
            frame,
            semilunar=True,
        )

    scene = bpy.context.scene
    pressure_values = {
        "left_atrial_pressure_mmHg": state.left_atrial_pressure,
        "right_atrial_pressure_mmHg": state.right_atrial_pressure,
        "left_ventricular_pressure_mmHg": state.left_ventricular_pressure,
        "right_ventricular_pressure_mmHg": state.right_ventricular_pressure,
        "aortic_pressure_mmHg": state.aortic_pressure,
        "pulmonary_artery_pressure_mmHg": state.pulmonary_artery_pressure,
        "ventricular_volume_fraction": state.ventricular_volume_fraction,
        "atrial_volume_fraction": state.atrial_volume_fraction,
        "av_valve_open_fraction": state.av_open_fraction,
        "semilunar_valve_open_fraction": state.semilunar_open_fraction,
    }
    for channel, value in pressure_values.items():
        _set_custom_property(scene, channel, value, frame)


def _set_interpolation() -> None:
    for action in bpy.data.actions:
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                if "hide_" in fcurve.data_path or "phase_index" in fcurve.data_path:
                    keyframe.interpolation = "CONSTANT"
                else:
                    keyframe.interpolation = "BEZIER"
                    keyframe.easing = "AUTO"


def _animate_phase_rig(build: model.HeartBuild) -> None:
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.fps = FPS
    scene["phase_rig_revision"] = PHASE_RIG_REVISION
    scene["phase_rig_model_revision"] = MODEL_REVISION

    all_flow = _all_flow_objects(build)
    phase_ranges_value = phase_ranges()

    # Clear pre-existing animation data if the function is re-run interactively.
    for obj in bpy.data.objects:
        obj.animation_data_clear()
    scene.animation_data_clear()

    for phase_offset, (phase, start, end) in enumerate(phase_ranges_value):
        start_state = BOUNDARY_STATES[phase_offset]
        end_state = BOUNDARY_STATES[phase_offset + 1]
        middle = start + max(1, (end - start) // 2)

        _apply_boundary_state(build, start_state, start)
        _apply_boundary_state(build, end_state, end)
        _set_custom_property(scene, "phase_index", phase.index, start)
        _set_custom_property(scene, "phase_index", phase.index, end)

        # During asynchronous contraction the right and left ventricular
        # controls enter tension a few frames apart, rather than scaling as one.
        if phase.slug == "asynchronous_contraction":
            right_frame = min(end, start + max(2, (end - start) // 3))
            left_frame = min(end, right_frame + 3)
            right_scale = tuple(
                start_state.right_ventricle_scale[index]
                + 0.46 * (
                    end_state.right_ventricle_scale[index]
                    - start_state.right_ventricle_scale[index]
                )
                for index in range(3)
            )
            left_scale = tuple(
                start_state.left_ventricle_scale[index]
                + 0.42 * (
                    end_state.left_ventricle_scale[index]
                    - start_state.left_ventricle_scale[index]
                )
                for index in range(3)
            )
            _set_scale(build.controls["right_ventricle"], right_scale, right_frame)
            _set_scale(build.controls["left_ventricle"], left_scale, left_frame)

        # Valve transitions occur inside the phase, not as an instantaneous
        # switch at a boundary.
        if phase.slug == "asynchronous_contraction":
            close_frame = start + int((end - start) * 0.68)
            for name in ("Mitral", "Tricuspid"):
                _set_valve_open_fraction(
                    build.valve_leaflets[name],
                    0.15,
                    close_frame,
                    semilunar=False,
                )
        elif phase.slug == "rapid_ejection":
            open_frame = start + max(2, int((end - start) * 0.16))
            for name in ("Aortic", "Pulmonary"):
                _set_valve_open_fraction(
                    build.valve_leaflets[name],
                    1.0,
                    open_frame,
                    semilunar=True,
                )
        elif phase.slug == "protodiastolic_period":
            close_frame = start + max(2, int((end - start) * 0.55))
            for name in ("Aortic", "Pulmonary"):
                _set_valve_open_fraction(
                    build.valve_leaflets[name],
                    0.10,
                    close_frame,
                    semilunar=True,
                )
        elif phase.slug == "rapid_filling":
            open_frame = start + max(2, int((end - start) * 0.18))
            for name in ("Mitral", "Tricuspid"):
                _set_valve_open_fraction(
                    build.valve_leaflets[name],
                    1.0,
                    open_frame,
                    semilunar=False,
                )

        active_keys, peak_intensity, end_intensity = FLOW_PROFILES[phase.slug]
        _set_flow_visibility(all_flow, False, start)
        active_objects = tuple(
            obj for key in active_keys for obj in build.flow_groups[key]
        )
        if active_objects:
            _set_flow_visibility(active_objects, True, start)
            _set_flow_visibility(active_objects, True, end)
            _set_flow_intensity(active_objects, 0.12, start)
            _set_flow_intensity(active_objects, peak_intensity, middle)
            _set_flow_intensity(active_objects, end_intensity, end)
        scene.timeline_markers.new(f"{phase.index:02d}_{phase.slug}", frame=start)

    # Explicitly close all inactive flow groups one frame after their phases.
    for phase, start, end in phase_ranges_value:
        active_keys = set(FLOW_PROFILES[phase.slug][0])
        next_frame = min(TOTAL_FRAMES, end + 1)
        for key, objects in build.flow_groups.items():
            if key not in active_keys:
                _set_flow_visibility(objects, False, next_frame)

    _set_interpolation()
    scene.frame_set(1)


def _augment_manifest(path: Path) -> Path:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["model_revision"] = MODEL_REVISION
    payload["anatomy_revision"] = anatomy_v02.ANATOMY_REVISION
    payload["phase_rig_revision"] = PHASE_RIG_REVISION
    payload["pressure_channels"] = list(PRESSURE_CHANNELS)
    payload["preview_frames"] = [
        {
            "phase_index": phase.index,
            "phase_slug": phase.slug,
            "frame": start + (end - start) // 2,
        }
        for phase, start, end in phase_ranges()
    ]
    payload["rig_notes"] = {
        "isovolumetric_phases": [
            "asynchronous_contraction",
            "isometric_contraction",
            "isometric_relaxation",
        ],
        "left_right_ventricular_deformation": "independent",
        "valve_opening": "continuous fraction",
        "flow_intensity": "phase-specific",
        "loop_seam": "frame 1 and frame 450 share the same boundary state",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_model_with_phase_rig(resolution: int) -> model.HeartBuild:
    build = _PREVIOUS_BUILD_MODEL(resolution)
    _animate_phase_rig(build)
    bpy.context.scene["model_revision"] = MODEL_REVISION
    bpy.context.scene["phase_rig_revision"] = PHASE_RIG_REVISION
    return build


def _render_phase_previews(output_root: Path) -> tuple[Path, ...]:
    scene = bpy.context.scene
    preview_root = output_root / "phase_previews"
    preview_root.mkdir(exist_ok=True)
    rendered: list[Path] = []
    for phase, start, end in phase_ranges():
        frame = start + (end - start) // 2
        scene.frame_set(frame)
        path = preview_root / f"phase_{phase.index:02d}_{phase.slug}_f{frame:03d}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(path)
    scene.frame_set(1)
    return tuple(rendered)


def main() -> int:
    args = _arguments()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    _build_model_with_phase_rig(args.resolution)
    blend_path = output_root / args.blend_name
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    manifest_path = _augment_manifest(_BASE_WRITE_MANIFEST(output_root, blend_path))

    scene = bpy.context.scene
    preview_paths: tuple[Path, ...] = ()
    if args.render_preview:
        scene.frame_set(1)
        scene.render.filepath = str(output_root / "heart_cutaway_preview.png")
        bpy.ops.render.render(write_still=True)
        preview_paths = _render_phase_previews(output_root)
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


model._animate = _animate_phase_rig
model.build_model = _build_model_with_phase_rig


if __name__ == "__main__":
    raise SystemExit(main())
