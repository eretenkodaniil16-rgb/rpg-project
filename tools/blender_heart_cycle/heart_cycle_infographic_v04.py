from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_model as model
import heart_cycle_phase_rig_render_v03 as phase_render
import heart_cycle_phase_rig_v03 as rig
from heart_cycle_data import FPS, PHASES, TOTAL_FRAMES, phase_ranges


INFOGRAPHIC_REVISION = "heart_cycle_infographic_v04"
MODEL_REVISION = "heart_cutaway_v02_phase_rig_v03_infographic_v04"
DEFAULT_BLEND_NAME = f"{MODEL_REVISION}.blend"


VALVE_STATE_RU = {
    "open": "открыты",
    "closed": "закрыты",
    "closing": "закрываются",
}


def _arguments() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(
        description="Build the Russian educational compositor for the v03 heart rig."
    )
    parser.add_argument("--output-root", default=str(SCRIPT_DIR / "output"))
    parser.add_argument("--blend-name", default=DEFAULT_BLEND_NAME)
    parser.add_argument("--render-preview", action="store_true")
    parser.add_argument("--render-animation", action="store_true")
    parser.add_argument("--resolution", type=int, default=1080)
    return parser.parse_args(argv)


def _load_cyrillic_font() -> bpy.types.VectorFont | None:
    candidates = (
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    )
    for path in candidates:
        if path.is_file():
            return bpy.data.fonts.load(str(path), check_existing=True)
    return None


def _ui_material(
    name: str,
    color: tuple[float, float, float, float],
    *,
    strength: float = 1.0,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError(f"Material has no Principled BSDF: {name}")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.72
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = color
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = strength
    return material


def _parent_local(
    obj: bpy.types.Object,
    parent: bpy.types.Object,
    location: tuple[float, float, float],
) -> bpy.types.Object:
    obj.parent = parent
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, 0.0)
    return obj


def _camera_plane(
    name: str,
    camera: bpy.types.Object,
    collection: bpy.types.Collection,
    location: tuple[float, float, float],
    scale: tuple[float, float],
    material: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=2.0)
    plane = bpy.context.object
    plane.name = name
    model._move_to_collection(plane, collection)
    _parent_local(plane, camera, location)
    plane.scale = (scale[0], scale[1], 1.0)
    plane.data.materials.append(material)
    plane["infographic_role"] = "panel"
    return plane


def _camera_text(
    name: str,
    body: str,
    camera: bpy.types.Object,
    collection: bpy.types.Collection,
    location: tuple[float, float, float],
    size: float,
    material: bpy.types.Material,
    font: bpy.types.VectorFont | None,
    *,
    align_x: str = "LEFT",
    line_spacing: float = 0.92,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name=f"{name}_font", type="FONT")
    curve.body = body
    curve.align_x = align_x
    curve.align_y = "TOP_BASELINE"
    curve.size = size
    curve.space_line = line_spacing
    curve.extrude = 0.0005
    curve.resolution_u = 4
    if font is not None:
        curve.font = font
    curve.materials.append(material)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    _parent_local(obj, camera, location)
    obj["infographic_role"] = "text"
    return obj


def _wrap_description(lines: Iterable[str], width: int = 43) -> str:
    wrapped: list[str] = []
    for line in lines:
        pieces = textwrap.wrap(line, width=width, break_long_words=False)
        if not pieces:
            continue
        wrapped.append("• " + pieces[0])
        wrapped.extend("  " + piece for piece in pieces[1:])
    return "\n".join(wrapped)


def _phase_title(phase_title: str) -> str:
    lines = textwrap.wrap(phase_title, width=27, break_long_words=False)
    return "\n".join(lines)


def _set_phase_visibility(
    objects: Iterable[bpy.types.Object],
    start: int,
    end: int,
) -> None:
    objects = tuple(objects)
    for obj in objects:
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_viewport", frame=1)
        obj.keyframe_insert(data_path="hide_render", frame=1)
        if start > 1:
            obj.hide_viewport = True
            obj.hide_render = True
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


def _set_constant_visibility_interpolation(objects: Iterable[bpy.types.Object]) -> None:
    for obj in objects:
        animation = obj.animation_data
        if animation is None or animation.action is None:
            continue
        for fcurve in animation.action.fcurves:
            if "hide_" not in fcurve.data_path:
                continue
            for point in fcurve.keyframe_points:
                point.interpolation = "CONSTANT"


def _shift_heart_to_right(build: model.HeartBuild) -> bpy.types.Object:
    controls = build.collections["controls"]
    offset = bpy.data.objects.new("CTRL_InfographicHeartOffset", None)
    offset.empty_display_type = "PLAIN_AXES"
    offset.empty_display_size = 0.6
    controls.objects.link(offset)

    movable_collections = {
        build.collections[key]
        for key in ("anatomy", "chambers", "valves", "vessels", "flow", "controls")
    }
    for obj in list(bpy.data.objects):
        if obj is offset or obj.parent is not None:
            continue
        if not any(collection in movable_collections for collection in obj.users_collection):
            continue
        matrix = obj.matrix_world.copy()
        obj.parent = offset
        obj.matrix_world = matrix
    offset.location.x = 1.35
    offset["infographic_role"] = "heart_offset"
    return offset


def _build_infographic(build: model.HeartBuild) -> tuple[bpy.types.Object, ...]:
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None:
        raise RuntimeError("Heart scene has no active camera")
    render_collection = build.collections["render"]
    font = _load_cyrillic_font()

    panel_material = _ui_material("M_InfoPanel", (0.018, 0.035, 0.072, 1.0), strength=0.35)
    accent_material = _ui_material("M_InfoAccent", (0.15, 0.57, 1.00, 1.0), strength=1.8)
    text_material = _ui_material("M_InfoText", (0.93, 0.96, 1.00, 1.0), strength=1.35)
    muted_material = _ui_material("M_InfoMuted", (0.63, 0.72, 0.84, 1.0), strength=0.95)

    _shift_heart_to_right(build)

    created: list[bpy.types.Object] = []
    created.append(
        _camera_plane(
            "Infographic_PhasePanel",
            camera,
            render_collection,
            (-0.41, -0.045, -2.60),
            (0.35, 0.35),
            panel_material,
        )
    )
    created.append(
        _camera_plane(
            "Infographic_AccentBar",
            camera,
            render_collection,
            (-0.742, -0.045, -2.575),
            (0.008, 0.35),
            accent_material,
        )
    )
    created.append(
        _camera_text(
            "Infographic_Title",
            "СЕРДЕЧНЫЙ ЦИКЛ",
            camera,
            render_collection,
            (0.0, 0.365, -2.56),
            0.052,
            text_material,
            font,
            align_x="CENTER",
        )
    )
    created.append(
        _camera_text(
            "Infographic_Subtitle",
            "9 фаз по В. М. Покровскому · 15-секундная учебная петля",
            camera,
            render_collection,
            (0.0, 0.310, -2.56),
            0.020,
            muted_material,
            font,
            align_x="CENTER",
        )
    )

    phase_objects: list[bpy.types.Object] = []
    for phase, start, end in phase_ranges():
        duration_text = f"Длительность: {phase.duration_seconds_real:.2f} с".replace(".", ",")
        av_state = VALVE_STATE_RU.get(phase.av_valves, phase.av_valves)
        semilunar_state = VALVE_STATE_RU.get(
            phase.semilunar_valves, phase.semilunar_valves
        )
        group = (
            _camera_text(
                f"Info_PhaseIndex_{phase.index:02d}",
                f"ФАЗА {phase.index} ИЗ 9",
                camera,
                render_collection,
                (-0.705, 0.247, -2.55),
                0.019,
                accent_material,
                font,
            ),
            _camera_text(
                f"Info_PhaseTitle_{phase.index:02d}",
                _phase_title(phase.title_ru),
                camera,
                render_collection,
                (-0.705, 0.207, -2.55),
                0.034,
                text_material,
                font,
                line_spacing=0.86,
            ),
            _camera_text(
                f"Info_PhaseBody_{phase.index:02d}",
                _wrap_description(phase.description_ru),
                camera,
                render_collection,
                (-0.705, 0.105, -2.55),
                0.0195,
                text_material,
                font,
                line_spacing=0.88,
            ),
            _camera_text(
                f"Info_PhaseDuration_{phase.index:02d}",
                duration_text,
                camera,
                render_collection,
                (-0.705, -0.230, -2.55),
                0.021,
                accent_material,
                font,
            ),
            _camera_text(
                f"Info_PhaseValves_{phase.index:02d}",
                (
                    f"АВ-клапаны: {av_state}\n"
                    f"Полулунные: {semilunar_state}"
                ),
                camera,
                render_collection,
                (-0.705, -0.278, -2.55),
                0.0185,
                muted_material,
                font,
                line_spacing=0.90,
            ),
        )
        _set_phase_visibility(group, start, end)
        phase_objects.extend(group)
        created.extend(group)

    _set_constant_visibility_interpolation(phase_objects)
    scene["infographic_revision"] = INFOGRAPHIC_REVISION
    scene["infographic_language"] = "ru"
    scene["infographic_layout"] = "title_top; phase_panel_left; cutaway_heart_right"
    scene.frame_set(1)
    return tuple(created)


def _augment_manifest(path: Path) -> Path:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["model_revision"] = MODEL_REVISION
    payload["infographic_revision"] = INFOGRAPHIC_REVISION
    payload["infographic"] = {
        "language": "ru",
        "title": "Сердечный цикл",
        "subtitle": "9 фаз по В. М. Покровскому",
        "layout": {
            "title": "top",
            "phase_card": "left",
            "cutaway_heart": "right",
        },
        "phase_fields": [
            "index",
            "title_ru",
            "description_ru",
            "duration_seconds_real",
            "av_valves",
            "semilunar_valves",
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _render_infographic_phase_previews(output_root: Path) -> tuple[Path, ...]:
    scene = bpy.context.scene
    preview_root = output_root / "infographic_phase_previews"
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


def build_model(resolution: int) -> model.HeartBuild:
    build = phase_render.build_model_once(resolution)
    _build_infographic(build)
    scene = bpy.context.scene
    scene["model_revision"] = MODEL_REVISION
    scene["phase_rig_revision"] = rig.PHASE_RIG_REVISION
    scene["infographic_revision"] = INFOGRAPHIC_REVISION
    return build


def main() -> int:
    args = _arguments()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    build_model(args.resolution)
    blend_path = output_root / args.blend_name
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    manifest_path = _augment_manifest(
        rig._augment_manifest(rig._BASE_WRITE_MANIFEST(output_root, blend_path))
    )

    scene = bpy.context.scene
    preview_paths: tuple[Path, ...] = ()
    if args.render_preview:
        scene.frame_set(1)
        scene.render.filepath = str(output_root / "heart_cycle_infographic_preview.png")
        bpy.ops.render.render(write_still=True)
        preview_paths = _render_infographic_phase_previews(output_root)
    if args.render_animation:
        frame_root = output_root / "infographic_frames"
        frame_root.mkdir(exist_ok=True)
        scene.render.filepath = str(frame_root / "heart_cycle_infographic_")
        bpy.ops.render.render(animation=True)

    print(f"HEART_CYCLE_BLEND={blend_path}")
    print(f"HEART_CYCLE_MANIFEST={manifest_path}")
    if preview_paths:
        print(f"HEART_CYCLE_INFOGRAPHIC_PREVIEWS={len(preview_paths)}")
    return 0


model.build_model = build_model


if __name__ == "__main__":
    raise SystemExit(main())
