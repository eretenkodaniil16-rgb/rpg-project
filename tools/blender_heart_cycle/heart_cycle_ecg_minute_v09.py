from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_animation_export_v07 as export_v07
import heart_cycle_model as model
from heart_cycle_data import FPS, PHASES, TOTAL_FRAMES as SOURCE_TOTAL_FRAMES, phase_ranges


MINUTE_REVISION = "heart_cycle_ecg_minute_v09"
MODEL_REVISION = f"{export_v07.MODEL_REVISION}_ecg_minute_v09"
MINUTE_SECONDS = 60.0
TOTAL_FRAMES = int(FPS * MINUTE_SECONDS)
INTRO_FRAMES = 150
OUTRO_FRAMES = 150
CORE_START = INTRO_FRAMES + 1
CORE_END = TOTAL_FRAMES - OUTRO_FRAMES
CORE_FRAMES = CORE_END - CORE_START + 1
DEFAULT_FRAME_DIRECTORY = "minute_frames"
DEFAULT_FRAME_PREFIX = "heart_cycle_ecg_"
DEFAULT_BLEND_NAME = f"{MODEL_REVISION}.blend"
DEFAULT_VIDEO_NAME = "heart_cycle_ecg_minute_v09_review.mp4"

presentation = export_v07.presentation
infographic = presentation.infographic


PHASE_ELECTRICAL_LABELS = {
    1: "P: деполяризация предсердий",
    2: "QRS: деполяризация желудочков",
    3: "QRS → ST: начало механической систолы желудочков",
    4: "ST: желудочки деполяризованы · быстрое изгнание",
    5: "ST: желудочки деполяризованы · медленное изгнание",
    6: "T: начинается реполяризация желудочков",
    7: "T: реполяризация и расслабление желудочков",
    8: "TP: электрическая диастола · быстрое наполнение",
    9: "TP: электрическая диастола · медленное наполнение",
}


def _arguments() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(
        description=(
            "Build the one-minute ECG + cardiac mechanics teaching video from the "
            "approved Blender heart-cycle model."
        )
    )
    parser.add_argument("--output-root", default=str(SCRIPT_DIR / "output_minute_v09"))
    parser.add_argument("--resolution", type=int, default=720)
    parser.add_argument("--frame-start", type=int, default=1)
    parser.add_argument("--frame-end", type=int, default=TOTAL_FRAMES)
    parser.add_argument("--sample-step", type=int, default=2)
    parser.add_argument("--render-samples", type=int, default=96)
    parser.add_argument("--render-animation", action="store_true")
    parser.add_argument("--save-blend", action="store_true")
    return parser.parse_args(argv)


def _validate_arguments(args: argparse.Namespace) -> None:
    if args.resolution < 360:
        raise ValueError("resolution must be at least 360p")
    if not 1 <= args.frame_start <= TOTAL_FRAMES:
        raise ValueError(f"frame-start must be between 1 and {TOTAL_FRAMES}")
    if not 1 <= args.frame_end <= TOTAL_FRAMES:
        raise ValueError(f"frame-end must be between 1 and {TOTAL_FRAMES}")
    if args.frame_end < args.frame_start:
        raise ValueError("frame-end must not precede frame-start")
    if args.sample_step < 1 or FPS % args.sample_step != 0:
        raise ValueError(f"sample-step must be a positive divisor of {FPS}")
    if args.render_samples < 1:
        raise ValueError("render-samples must be positive")


def _map_source_frame(frame: float) -> float:
    if SOURCE_TOTAL_FRAMES <= 1:
        return float(CORE_START)
    alpha = (float(frame) - 1.0) / float(SOURCE_TOTAL_FRAMES - 1)
    return CORE_START + alpha * float(CORE_END - CORE_START)


def _mapped_phase_ranges() -> tuple[tuple[object, int, int], ...]:
    result = []
    for phase, start, end in phase_ranges():
        mapped_start = int(round(_map_source_frame(start)))
        mapped_end = int(round(_map_source_frame(end)))
        result.append((phase, mapped_start, mapped_end))
    result[0] = (result[0][0], CORE_START, result[0][2])
    result[-1] = (result[-1][0], result[-1][1], CORE_END)
    for idx in range(1, len(result)):
        phase, start, end = result[idx]
        prev = result[idx - 1]
        if start <= prev[2]:
            start = prev[2] + 1
        result[idx] = (phase, start, end)
    return tuple(result)


def _retime_existing_animation() -> None:
    """Stretch the approved 15 s authored rig into the 50 s teaching core."""
    for action in bpy.data.actions:
        for fcurve in action.fcurves:
            for point in fcurve.keyframe_points:
                original_x = float(point.co.x)
                if 1.0 <= original_x <= float(SOURCE_TOTAL_FRAMES):
                    new_x = _map_source_frame(original_x)
                    delta = new_x - original_x
                    point.co.x = new_x
                    point.handle_left.x += delta
                    point.handle_right.x += delta
            fcurve.update()

    scene = bpy.context.scene
    for marker in scene.timeline_markers:
        if 1 <= marker.frame <= SOURCE_TOTAL_FRAMES:
            marker.frame = int(round(_map_source_frame(marker.frame)))

    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.fps = FPS
    scene.render.fps_base = 1.0


def _make_material(name: str, color: tuple[float, float, float, float], strength: float) -> bpy.types.Material:
    return infographic._ui_material(name, color, strength=strength)


def _curve_object(
    name: str,
    camera: bpy.types.Object,
    collection: bpy.types.Collection,
    points: Iterable[tuple[float, float]],
    material: bpy.types.Material,
    *,
    z: float = -2.49,
    bevel: float = 0.0026,
) -> bpy.types.Object:
    pts = tuple(points)
    curve_data = bpy.data.curves.new(name=f"{name}_curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 1
    curve_data.bevel_depth = bevel
    curve_data.bevel_resolution = 2
    curve_data.materials.append(material)
    spline = curve_data.splines.new("POLY")
    spline.points.add(len(pts) - 1)
    for idx, (x, y) in enumerate(pts):
        spline.points[idx].co = (x, y, 0.0, 1.0)
    obj = bpy.data.objects.new(name, curve_data)
    collection.objects.link(obj)
    infographic._parent_local(obj, camera, (0.0, 0.0, z))
    obj["infographic_role"] = "ecg_curve"
    return obj


def _ecg_value(t: float) -> float:
    """Stylised teaching ECG waveform, normalized to roughly +/-1."""
    if t < 0.08:
        return 0.0
    if t < 0.18:
        u = (t - 0.08) / 0.10
        return 0.36 * math.sin(math.pi * u)
    if t < 0.255:
        return 0.0
    if t < 0.285:
        u = (t - 0.255) / 0.03
        return -0.28 * math.sin(math.pi * u)
    if t < 0.315:
        u = (t - 0.285) / 0.03
        return 1.00 * math.sin(math.pi * u)
    if t < 0.355:
        u = (t - 0.315) / 0.04
        return -0.55 * math.sin(math.pi * u)
    if t < 0.60:
        return 0.0
    if t < 0.78:
        u = (t - 0.60) / 0.18
        return 0.50 * math.sin(math.pi * u)
    return 0.0


def _ecg_xy(t: float) -> tuple[float, float]:
    x0, x1 = -0.705, -0.115
    baseline_y = 0.205
    amplitude = 0.042
    return (x0 + (x1 - x0) * t, baseline_y + amplitude * _ecg_value(t))


def _segment_points(t0: float, t1: float, samples: int = 72) -> tuple[tuple[float, float], ...]:
    return tuple(_ecg_xy(t0 + (t1 - t0) * i / (samples - 1)) for i in range(samples))


def _set_visibility_interval(objects: Iterable[bpy.types.Object], start: int, end: int) -> None:
    for obj in objects:
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=1)
        obj.keyframe_insert(data_path="hide_render", frame=1)
        if start > 1:
            obj.keyframe_insert(data_path="hide_viewport", frame=start - 1)
            obj.keyframe_insert(data_path="hide_render", frame=start - 1)
        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_viewport", frame=start)
        obj.keyframe_insert(data_path="hide_render", frame=start)
        obj.keyframe_insert(data_path="hide_viewport", frame=end)
        obj.keyframe_insert(data_path="hide_render", frame=end)
        if end < TOTAL_FRAMES:
            obj.hide_viewport = True
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_viewport", frame=end + 1)
            obj.keyframe_insert(data_path="hide_render", frame=end + 1)


def _set_constant_visibility(objects: Iterable[bpy.types.Object]) -> None:
    for obj in objects:
        animation = obj.animation_data
        if animation is None or animation.action is None:
            continue
        for fcurve in animation.action.fcurves:
            if "hide_" not in fcurve.data_path:
                continue
            for key in fcurve.keyframe_points:
                key.interpolation = "CONSTANT"


def _hide_legacy_phase_cards_during_intro_outro() -> None:
    phase_objects = tuple(obj for obj in bpy.data.objects if obj.name.startswith("Info_Phase"))
    for obj in phase_objects:
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=1)
        obj.keyframe_insert(data_path="hide_render", frame=1)
        obj.keyframe_insert(data_path="hide_viewport", frame=INTRO_FRAMES)
        obj.keyframe_insert(data_path="hide_render", frame=INTRO_FRAMES)
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=CORE_END + 1)
        obj.keyframe_insert(data_path="hide_render", frame=CORE_END + 1)
    _set_constant_visibility(phase_objects)


def _build_ecg_overlay(build: model.HeartBuild) -> tuple[bpy.types.Object, ...]:
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None:
        raise RuntimeError("Heart scene has no active camera")
    collection = build.collections["render"]
    font = infographic._load_cyrillic_font()

    panel_mat = _make_material("M_ECGPanel_v09", (0.010, 0.025, 0.055, 1.0), 0.30)
    grid_mat = _make_material("M_ECGGrid_v09", (0.12, 0.23, 0.37, 1.0), 0.50)
    trace_mat = _make_material("M_ECGTrace_v09", (0.74, 0.82, 0.93, 1.0), 1.10)
    p_mat = _make_material("M_ECGP_v09", (1.00, 0.58, 0.04, 1.0), 2.20)
    qrs_mat = _make_material("M_ECGQRS_v09", (1.00, 0.16, 0.18, 1.0), 2.50)
    t_mat = _make_material("M_ECGT_v09", (0.12, 0.48, 1.00, 1.0), 2.30)
    text_mat = _make_material("M_ECGText_v09", (0.94, 0.97, 1.00, 1.0), 1.30)
    muted_mat = _make_material("M_ECGMuted_v09", (0.56, 0.68, 0.83, 1.0), 0.95)
    accent_mat = _make_material("M_ECGCursor_v09", (0.32, 0.78, 1.00, 1.0), 3.20)

    created: list[bpy.types.Object] = []
    panel = infographic._camera_plane(
        "ECG_BottomPanel_v09",
        camera,
        collection,
        (-0.41, 0.205, -2.60),
        (0.35, 0.070),
        panel_mat,
    )
    created.append(panel)

    for i in range(17):
        x = -0.74 + i * 0.0425
        created.append(
            infographic._camera_plane(
                f"ECG_GridV_{i:02d}", camera, collection, (x, 0.205, -2.575), (0.00055, 0.061), grid_mat
            )
        )
    for i in range(5):
        y = 0.157 + i * 0.024
        created.append(
            infographic._camera_plane(
                f"ECG_GridH_{i:02d}", camera, collection, (-0.41, y, -2.575), (0.335, 0.00055), grid_mat
            )
        )

    created.append(_curve_object("ECG_Trace_v09", camera, collection, _segment_points(0.0, 1.0, 220), trace_mat))
    created.append(_curve_object("ECG_P_v09", camera, collection, _segment_points(0.075, 0.19, 48), p_mat, bevel=0.0030))
    created.append(_curve_object("ECG_QRS_v09", camera, collection, _segment_points(0.25, 0.37, 64), qrs_mat, bevel=0.0032))
    created.append(_curve_object("ECG_T_v09", camera, collection, _segment_points(0.59, 0.79, 64), t_mat, bevel=0.0030))

    created.extend(
        (
            infographic._camera_text("ECG_LabelP_v09", "P", camera, collection, (-0.612, 0.250, -2.49), 0.022, p_mat, font),
            infographic._camera_text("ECG_LabelQRS_v09", "QRS", camera, collection, (-0.500, 0.250, -2.49), 0.020, qrs_mat, font),
            infographic._camera_text("ECG_LabelT_v09", "T", camera, collection, (-0.255, 0.250, -2.49), 0.022, t_mat, font),
            infographic._camera_text(
                "ECG_Scale_v09", "ЭКГ: электрические события", camera, collection, (-0.705, 0.142, -2.49), 0.014, muted_mat, font
            ),
        )
    )

    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.009)
    cursor = bpy.context.object
    cursor.name = "ECG_Cursor_v09"
    model._move_to_collection(cursor, collection)
    cursor.data.materials.append(accent_mat)
    infographic._parent_local(cursor, camera, (*_ecg_xy(0.0), -2.47))
    cursor.hide_viewport = True
    cursor.hide_render = True
    cursor.keyframe_insert(data_path="hide_viewport", frame=1)
    cursor.keyframe_insert(data_path="hide_render", frame=1)
    cursor.keyframe_insert(data_path="hide_viewport", frame=INTRO_FRAMES)
    cursor.keyframe_insert(data_path="hide_render", frame=INTRO_FRAMES)
    cursor.hide_viewport = False
    cursor.hide_render = False
    cursor.keyframe_insert(data_path="hide_viewport", frame=CORE_START)
    cursor.keyframe_insert(data_path="hide_render", frame=CORE_START)

    samples = 90
    for idx in range(samples):
        t = idx / (samples - 1)
        frame = int(round(CORE_START + t * (CORE_END - CORE_START)))
        x, y = _ecg_xy(t)
        cursor.location = (x, y, -2.47)
        cursor.keyframe_insert(data_path="location", frame=frame)
    cursor.keyframe_insert(data_path="hide_viewport", frame=CORE_END)
    cursor.keyframe_insert(data_path="hide_render", frame=CORE_END)
    cursor.hide_viewport = True
    cursor.hide_render = True
    cursor.keyframe_insert(data_path="hide_viewport", frame=CORE_END + 1)
    cursor.keyframe_insert(data_path="hide_render", frame=CORE_END + 1)
    if cursor.animation_data is not None and cursor.animation_data.action is not None:
        for fcurve in cursor.animation_data.action.fcurves:
            for key in fcurve.keyframe_points:
                key.interpolation = "CONSTANT" if "hide_" in fcurve.data_path else "LINEAR"
    created.append(cursor)

    phase_labels: list[bpy.types.Object] = []
    for phase, start, end in _mapped_phase_ranges():
        label = infographic._camera_text(
            f"ECG_PhaseElectrical_{phase.index:02d}_v09",
            PHASE_ELECTRICAL_LABELS[phase.index],
            camera,
            collection,
            (-0.705, 0.120, -2.49),
            0.0165,
            text_mat,
            font,
        )
        _set_visibility_interval((label,), start, end)
        phase_labels.append(label)
        created.append(label)
    _set_constant_visibility(phase_labels)

    return tuple(created)


def _build_intro_outro(build: model.HeartBuild) -> tuple[bpy.types.Object, ...]:
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None:
        raise RuntimeError("Heart scene has no active camera")
    collection = build.collections["render"]
    font = infographic._load_cyrillic_font()

    card_mat = _make_material("M_MinuteCard_v09", (0.018, 0.035, 0.072, 1.0), 0.45)
    text_mat = _make_material("M_MinuteText_v09", (0.94, 0.97, 1.00, 1.0), 1.35)
    accent_mat = _make_material("M_MinuteAccent_v09", (0.15, 0.57, 1.00, 1.0), 2.0)
    muted_mat = _make_material("M_MinuteMuted_v09", (0.63, 0.72, 0.84, 1.0), 1.0)

    intro = (
        infographic._camera_plane("Minute_IntroCard_v09", camera, collection, (-0.41, 0.02, -2.54), (0.34, 0.21), card_mat),
        infographic._camera_text("Minute_IntroTitle_v09", "ЭКГ ↔ МЕХАНИКА", camera, collection, (-0.705, 0.18, -2.49), 0.036, text_mat, font),
        infographic._camera_text(
            "Minute_IntroBody_v09",
            "Один сердечный цикл:\nэлектрическое возбуждение → сокращение → расслабление → наполнение",
            camera,
            collection,
            (-0.705, 0.105, -2.49),
            0.021,
            text_mat,
            font,
            line_spacing=0.90,
        ),
        infographic._camera_text(
            "Minute_IntroHint_v09",
            "В следующих 50 секундах цикл замедлен для учебной визуализации.",
            camera,
            collection,
            (-0.705, -0.085, -2.49),
            0.0165,
            muted_mat,
            font,
        ),
    )
    _set_visibility_interval(intro, 1, INTRO_FRAMES)

    outro = (
        infographic._camera_plane("Minute_OutroCard_v09", camera, collection, (-0.41, 0.02, -2.54), (0.34, 0.21), card_mat),
        infographic._camera_text("Minute_OutroTitle_v09", "СВЯЗЬ ЭКГ И МЕХАНИКИ", camera, collection, (-0.705, 0.19, -2.49), 0.031, accent_mat, font),
        infographic._camera_text(
            "Minute_OutroBody_v09",
            "P → деполяризация и затем систола предсердий\n"
            "QRS → деполяризация и начало систолы желудочков\n"
            "T → реполяризация и переход к расслаблению желудочков",
            camera,
            collection,
            (-0.705, 0.105, -2.49),
            0.0195,
            text_mat,
            font,
            line_spacing=0.92,
        ),
        infographic._camera_text(
            "Minute_OutroHint_v09",
            "Механическое событие следует за электрическим с небольшой задержкой.",
            camera,
            collection,
            (-0.705, -0.105, -2.49),
            0.0165,
            muted_mat,
            font,
        ),
    )
    _set_visibility_interval(outro, CORE_END + 1, TOTAL_FRAMES)
    _set_constant_visibility((*intro, *outro))
    return (*intro, *outro)


def _update_header() -> None:
    title = bpy.data.objects.get("Infographic_Title")
    subtitle = bpy.data.objects.get("Infographic_Subtitle")
    if title is not None and hasattr(title.data, "body"):
        title.data.body = "ЭКГ И СЕРДЕЧНЫЙ ЦИКЛ"
        title.data.size = 0.032
    if subtitle is not None and hasattr(subtitle.data, "body"):
        subtitle.data.body = "Электрические и механические события одного сердечного цикла"
        subtitle.data.size = 0.0145

    for obj in bpy.data.objects:
        if obj.name.startswith("Info_PhaseIndex_"):
            obj.location.y = 0.095
            obj.data.size = 0.016
        elif obj.name.startswith("Info_PhaseTitle_"):
            obj.location.y = 0.065
            obj.data.size = 0.027
        elif obj.name.startswith("Info_PhaseBody_"):
            obj.location.y = -0.015
            obj.data.size = 0.0165
        elif obj.name.startswith("Info_PhaseDuration_"):
            obj.location.y = -0.205
            obj.data.size = 0.017
        elif obj.name.startswith("Info_PhaseValves_"):
            obj.location.y = -0.240
            obj.data.size = 0.0155


def _configure_render(scene: bpy.types.Scene, args: argparse.Namespace, frame_root: Path) -> None:
    scene.frame_start = args.frame_start
    scene.frame_end = args.frame_end
    scene.frame_step = args.sample_step
    scene.render.fps = FPS // args.sample_step
    scene.render.fps_base = 1.0
    scene.render.resolution_x = int(args.resolution * 16 / 9)
    scene.render.resolution_y = args.resolution
    scene.render.resolution_percentage = 100
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    scene.render.use_placeholder = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 14
    scene.render.filepath = str(frame_root / DEFAULT_FRAME_PREFIX)

    eevee = getattr(scene, "eevee", None)
    if eevee is not None:
        for attribute in ("taa_render_samples", "taa_samples"):
            if hasattr(eevee, attribute):
                setattr(eevee, attribute, args.render_samples)
                break


def _write_manifest(output_root: Path, args: argparse.Namespace) -> Path:
    path = output_root / "heart_cycle_ecg_minute_v09_manifest.json"
    phases = [
        {
            "index": phase.index,
            "slug": phase.slug,
            "title_ru": phase.title_ru,
            "frame_start": start,
            "frame_end": end,
            "electrical_label": PHASE_ELECTRICAL_LABELS[phase.index],
        }
        for phase, start, end in _mapped_phase_ranges()
    ]
    payload = {
        "revision": MINUTE_REVISION,
        "model_revision": MODEL_REVISION,
        "source_model": export_v07.MODEL_REVISION,
        "timeline": {
            "fps_authored": FPS,
            "duration_seconds": MINUTE_SECONDS,
            "frame_start": 1,
            "frame_end": TOTAL_FRAMES,
            "intro_frames": INTRO_FRAMES,
            "teaching_core": [CORE_START, CORE_END],
            "outro_frames": OUTRO_FRAMES,
            "source_15s_rig_retimed": True,
        },
        "render": {
            "frame_start": args.frame_start,
            "frame_end": args.frame_end,
            "sample_step": args.sample_step,
            "output_fps": FPS // args.sample_step,
            "resolution": [int(args.resolution * 16 / 9), args.resolution],
            "render_samples": args.render_samples,
            "intermediate": "PNG sequence",
        },
        "ecg": {
            "segments": ["P", "QRS", "T"],
            "moving_cursor": True,
            "phase_synchronized_labels": True,
        },
        "phases": phases,
        "files": {
            "blend": DEFAULT_BLEND_NAME,
            "video_target": DEFAULT_VIDEO_NAME,
            "frame_directory": DEFAULT_FRAME_DIRECTORY,
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_model(resolution: int) -> model.HeartBuild:
    build = export_v07.build_model(resolution)
    _retime_existing_animation()
    _update_header()
    _hide_legacy_phase_cards_during_intro_outro()
    _build_ecg_overlay(build)
    _build_intro_outro(build)

    scene = bpy.context.scene
    scene["model_revision"] = MODEL_REVISION
    scene["minute_revision"] = MINUTE_REVISION
    scene["minute_duration_seconds"] = MINUTE_SECONDS
    scene["ecg_overlay"] = "P/QRS/T with moving cursor"
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.frame_set(1)
    return build


def main() -> int:
    args = _arguments()
    _validate_arguments(args)

    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    frame_root = output_root / DEFAULT_FRAME_DIRECTORY
    frame_root.mkdir(parents=True, exist_ok=True)

    build_model(args.resolution)
    scene = bpy.context.scene
    _configure_render(scene, args, frame_root)

    blend_path = output_root / DEFAULT_BLEND_NAME
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)

    if args.render_animation:
        scene.frame_set(args.frame_start)
        bpy.ops.render.render(animation=True)

    manifest = _write_manifest(output_root, args)
    print(f"HEART_CYCLE_MINUTE_REVISION={MINUTE_REVISION}")
    print(f"HEART_CYCLE_MINUTE_FRAME_ROOT={frame_root}")
    print(f"HEART_CYCLE_MINUTE_BLEND={blend_path}")
    print(f"HEART_CYCLE_MINUTE_MANIFEST={manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
