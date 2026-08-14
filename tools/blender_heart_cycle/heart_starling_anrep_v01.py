from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_animation_export_v07 as export_v07
import heart_cycle_ecg_minute_v09 as minute
import heart_cycle_model as model
from heart_cycle_data import FPS, TOTAL_FRAMES as SOURCE_FRAMES, phase_ranges

REVISION = "heart_starling_anrep_v01"
MODEL_REVISION = f"{export_v07.MODEL_REVISION}_starling_anrep_v01"
DURATION_SECONDS = 105.0
TOTAL_FRAMES = int(FPS * DURATION_SECONDS)
FRAME_DIR = "starling_anrep_frames"
FRAME_PREFIX = "starling_anrep_"
BLEND_NAME = f"{MODEL_REVISION}.blend"
VIDEO_NAME = "heart_starling_anrep_v01_720p15_review.mp4"

SCENES = (
    ("intro", 0.0, 8.0, "Саморегуляция сердца"),
    ("baseline", 8.0, 15.0, "Исходный сердечный цикл"),
    ("frank_starling", 15.0, 50.0, "Закон Франка—Старлинга"),
    ("transition", 50.0, 60.0, "От преднагрузки к постнагрузке"),
    ("anrep", 60.0, 90.0, "Закон Анрепа"),
    ("comparison", 90.0, 102.0, "Два механизма саморегуляции"),
    ("outro", 102.0, 105.0, "Итог"),
)

infographic = minute.infographic


def sec(value: float) -> int:
    return max(1, min(TOTAL_FRAMES, int(round(value * FPS)) + 1))


def span(start: float, end: float) -> tuple[int, int]:
    return sec(start), min(TOTAL_FRAMES, int(round(end * FPS)))


def arguments() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(description="Build the 1:45 Frank-Starling + Anrep teaching video.")
    parser.add_argument("--output-root", default=str(SCRIPT_DIR / "output_starling_anrep_v01"))
    parser.add_argument("--resolution", type=int, default=720)
    parser.add_argument("--frame-start", type=int, default=1)
    parser.add_argument("--frame-end", type=int, default=TOTAL_FRAMES)
    parser.add_argument("--sample-step", type=int, default=2)
    parser.add_argument("--render-samples", type=int, default=64)
    parser.add_argument("--render-animation", action="store_true")
    parser.add_argument("--save-blend", action="store_true")
    return parser.parse_args(argv)


def validate(args: argparse.Namespace) -> None:
    if args.resolution < 360:
        raise ValueError("resolution must be >= 360")
    if not 1 <= args.frame_start <= args.frame_end <= TOTAL_FRAMES:
        raise ValueError(f"frame range must stay inside 1..{TOTAL_FRAMES}")
    if args.sample_step < 1 or FPS % args.sample_step:
        raise ValueError(f"sample-step must divide {FPS}")
    if args.render_samples < 1:
        raise ValueError("render-samples must be positive")


def hide_legacy_ui() -> None:
    for obj in bpy.data.objects:
        if obj.name.startswith(("Info_", "ECG_", "Minute_")):
            obj.animation_data_clear()
            obj.hide_viewport = True
            obj.hide_render = True


def repeat_base_cycle() -> None:
    """Repeat the approved slowed 15 s cardiac-cycle rig through 105 s."""
    for action in bpy.data.actions:
        for fcurve in action.fcurves:
            if not fcurve.keyframe_points:
                continue
            xs = [point.co.x for point in fcurve.keyframe_points]
            if min(xs) >= 1.0 and max(xs) <= SOURCE_FRAMES + 0.5:
                if not any(mod.type == "CYCLES" for mod in fcurve.modifiers):
                    modifier = fcurve.modifiers.new(type="CYCLES")
                    modifier.mode_before = "REPEAT"
                    modifier.mode_after = "REPEAT"
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.fps = FPS


def wrap_control(build: model.HeartBuild, key: str, name: str) -> bpy.types.Object:
    child = build.controls[key]
    world = child.matrix_world.copy()
    parent = bpy.data.objects.new(name, None)
    parent.empty_display_type = "CIRCLE"
    parent.empty_display_size = 0.34
    parent.location = child.matrix_world.translation
    build.collections["controls"].objects.link(parent)
    child.parent = parent
    child.matrix_world = world
    return parent


def key_scale(obj: bpy.types.Object, frame: int, xyz: tuple[float, float, float]) -> None:
    obj.scale = xyz
    obj.keyframe_insert(data_path="scale", frame=frame)


def phase_frame(slug: str, where: str = "start") -> int:
    for phase, start, end in phase_ranges():
        if phase.slug == slug:
            if where == "start":
                return start
            if where == "end":
                return end
            return start + (end - start) // 2
    raise KeyError(slug)


def cf(cycle_start: int, source_frame: int) -> int:
    return cycle_start + source_frame - 1


def smooth_scale(obj: bpy.types.Object) -> None:
    if not obj.animation_data or not obj.animation_data.action:
        return
    for curve in obj.animation_data.action.fcurves:
        if curve.data_path == "scale":
            for point in curve.keyframe_points:
                point.interpolation = "BEZIER"
                point.easing = "AUTO"


def animate_frank_starling(left: bpy.types.Object, right: bpy.types.Object) -> None:
    """Heterometric response: increased ED size and greater subsequent shortening."""
    neutral = (1.0, 1.0, 1.0)
    rapid = phase_frame("rapid_ejection")
    ejection_end = phase_frame("slow_ejection", "end")
    filling = phase_frame("rapid_filling")
    slow_fill = phase_frame("slow_filling")
    for obj in (left, right):
        key_scale(obj, 1, neutral)
        key_scale(obj, sec(15), neutral)

    # First increased-preload beat, 15-30 s.
    a = sec(15)
    key_scale(left, a, (1.060, 1.035, 1.070)); key_scale(right, a, (1.035, 1.020, 1.040))
    key_scale(left, cf(a, rapid), (0.945, 0.940, 0.950)); key_scale(right, cf(a, rapid), (0.970, 0.965, 0.975))
    key_scale(left, cf(a, ejection_end), (0.965, 0.960, 0.970)); key_scale(right, cf(a, ejection_end), (0.985, 0.980, 0.985))
    key_scale(left, cf(a, filling), (1.035, 1.020, 1.040)); key_scale(right, cf(a, filling), (1.020, 1.012, 1.025))
    key_scale(left, cf(a, slow_fill), (1.060, 1.035, 1.070)); key_scale(right, cf(a, slow_fill), (1.035, 1.020, 1.040))

    # Second beat makes the relation visibly stronger, 30-45 s.
    b = sec(30)
    key_scale(left, b, (1.080, 1.050, 1.090)); key_scale(right, b, (1.045, 1.025, 1.050))
    key_scale(left, cf(b, rapid), (0.925, 0.915, 0.935)); key_scale(right, cf(b, rapid), (0.965, 0.955, 0.970))
    key_scale(left, cf(b, ejection_end), (0.950, 0.940, 0.955)); key_scale(right, cf(b, ejection_end), (0.980, 0.972, 0.982))
    key_scale(left, cf(b, filling), (1.050, 1.030, 1.060)); key_scale(right, cf(b, filling), (1.025, 1.015, 1.030))
    key_scale(left, cf(b, slow_fill), (1.080, 1.050, 1.090)); key_scale(right, cf(b, slow_fill), (1.045, 1.025, 1.050))

    key_scale(left, sec(50), (1.060, 1.035, 1.070)); key_scale(right, sec(50), (1.030, 1.018, 1.035))
    key_scale(left, sec(56), neutral); key_scale(right, sec(56), neutral)
    key_scale(left, sec(60), neutral); key_scale(right, sec(60), neutral)
    smooth_scale(left); smooth_scale(right)


def animate_anrep(left: bpy.types.Object) -> None:
    """Homeometric response: afterload step, transient weak ejection, delayed inotropy."""
    neutral = (1.0, 1.0, 1.0)
    rapid = phase_frame("rapid_ejection")
    ejection_end = phase_frame("slow_ejection", "end")
    filling = phase_frame("rapid_filling")

    # Challenge beat, 60-75 s: ED scale unchanged, emptying initially impaired.
    a = sec(60)
    key_scale(left, a, neutral)
    key_scale(left, cf(a, rapid), (1.040, 1.035, 1.045))
    key_scale(left, cf(a, ejection_end), (1.030, 1.025, 1.035))
    key_scale(left, cf(a, filling), neutral)
    key_scale(left, sec(75), neutral)

    # Adapted beat, 75-90 s: same ED scale, stronger shortening after delay.
    b = sec(75)
    key_scale(left, b, neutral)
    key_scale(left, cf(b, rapid), (0.945, 0.935, 0.950))
    key_scale(left, cf(b, ejection_end), (0.965, 0.955, 0.970))
    key_scale(left, cf(b, filling), neutral)
    key_scale(left, sec(90), neutral)
    smooth_scale(left)


def reference_torso(build: model.HeartBuild) -> tuple[bpy.types.Object, ...]:
    """Opening context from the user's turntable: stylised torso proportions, not a face scan."""
    material = model._material("M_UserReferenceTorso_v01", (0.18, 0.23, 0.30, 0.12), roughness=0.72)
    bsdf = material.node_tree.nodes.get("Principled BSDF") if material.node_tree else None
    if bsdf is not None and "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 0.13
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    parts: list[bpy.types.Object] = []
    for name, location, scale in (
        ("UserReference_Torso_v01", (0.0, 0.78, 4.10), (3.0, 1.18, 3.55)),
        ("UserReference_Head_v01", (0.0, 0.72, 8.05), (1.05, 0.84, 1.22)),
    ):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, location=location, scale=scale)
        obj = bpy.context.object; obj.name = name; obj.data.materials.append(material)
        model._move_to_collection(obj, build.collections["anatomy"]); parts.append(obj)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.72, depth=1.0, location=(0.0, 0.74, 6.95))
    neck = bpy.context.object; neck.name = "UserReference_Neck_v01"; neck.data.materials.append(material)
    model._move_to_collection(neck, build.collections["anatomy"]); parts.append(neck)
    minute._set_visibility_interval(parts, *span(0, 8)); minute._set_constant_visibility(parts)
    return tuple(parts)


def afterload_ring(build: model.HeartBuild) -> bpy.types.Object:
    material = model._material("M_AfterloadRing_v01", (0.95, 0.16, 0.04, 1.0), roughness=0.25, emission=(0.92, 0.05, 0.01, 1.0))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.50, minor_radius=0.055, major_segments=56, minor_segments=12, location=(0.50, 0.24, 5.82))
    ring = bpy.context.object; ring.name = "Afterload_AorticPressureRing_v01"; ring.data.materials.append(material)
    model._move_to_collection(ring, build.collections["render"])
    minute._set_visibility_interval((ring,), *span(60, 90)); minute._set_constant_visibility((ring,))
    for frame, scale in ((sec(60), 0.88), (sec(64), 1.15), (sec(75), 1.05), (sec(90), 1.12)):
        ring.scale = (scale, scale, scale); ring.keyframe_insert(data_path="scale", frame=frame)
    return ring


def starling_graph(camera: bpy.types.Object, collection: bpy.types.Collection) -> tuple[bpy.types.Object, ...]:
    panel = minute._make_material("M_FSPanel_v01", (0.010, 0.025, 0.055, 1.0), 0.32)
    axis = minute._make_material("M_FSAxis_v01", (0.55, 0.68, 0.82, 1.0), 1.0)
    curve = minute._make_material("M_FSCurve_v01", (0.18, 0.78, 1.00, 1.0), 2.3)
    point = minute._make_material("M_FSPoint_v01", (1.00, 0.70, 0.10, 1.0), 3.0)
    font = infographic._load_cyrillic_font(); made: list[bpy.types.Object] = []
    x0, x1, y0, y1 = -0.70, -0.27, -0.165, -0.035
    made.append(infographic._camera_plane("FS_GraphPanel_v01", camera, collection, (-0.47, -0.095, -2.59), (0.285, 0.115), panel))
    made.append(minute._curve_object("FS_AxisX_v01", camera, collection, ((x0, y0), (x1, y0)), axis, bevel=0.0018))
    made.append(minute._curve_object("FS_AxisY_v01", camera, collection, ((x0, y0), (x0, y1)), axis, bevel=0.0018))
    pts = []
    for i in range(72):
        t = i / 71.0; x = x0 + (x1 - x0) * t
        n = (1 - math.exp(-2.2 * t)) / (1 - math.exp(-2.2)); y = y0 + 0.012 + (y1 - y0 - 0.020) * n; pts.append((x, y))
    made.append(minute._curve_object("FS_Curve_v01", camera, collection, pts, curve, bevel=0.0030))
    made.append(infographic._camera_text("FS_XLabel_v01", "КДО / преднагрузка →", camera, collection, (x0, y0 - 0.030, -2.48), 0.0135, axis, font))
    made.append(infographic._camera_text("FS_YLabel_v01", "↑ УО / сила", camera, collection, (x0 - 0.005, y1 + 0.012, -2.48), 0.0135, axis, font))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.010)
    marker = bpy.context.object; marker.name = "FS_CurveMarker_v01"; marker.data.materials.append(point); model._move_to_collection(marker, collection)
    infographic._parent_local(marker, camera, (pts[18][0], pts[18][1], -2.46))
    for frame, index in ((sec(15), 18), (sec(30), 43), (sec(45), 61)):
        marker.location = (pts[index][0], pts[index][1], -2.46); marker.keyframe_insert(data_path="location", frame=frame)
    made.append(marker); minute._set_visibility_interval(made, *span(15, 50)); minute._set_constant_visibility(made)
    return tuple(made)


def text_cards(build: model.HeartBuild) -> tuple[bpy.types.Object, ...]:
    camera = bpy.context.scene.camera
    if camera is None: raise RuntimeError("Heart scene has no camera")
    collection = build.collections["render"]; font = infographic._load_cyrillic_font()
    card_mat = minute._make_material("M_LawCard_v01", (0.012, 0.028, 0.060, 1.0), 0.36)
    text = minute._make_material("M_LawText_v01", (0.94, 0.97, 1.00, 1.0), 1.30)
    muted = minute._make_material("M_LawMuted_v01", (0.60, 0.72, 0.85, 1.0), 1.0)
    blue = minute._make_material("M_LawBlue_v01", (0.18, 0.70, 1.00, 1.0), 2.2)
    orange = minute._make_material("M_LawOrange_v01", (1.00, 0.54, 0.08, 1.0), 2.3)
    green = minute._make_material("M_LawGreen_v01", (0.27, 0.90, 0.54, 1.0), 2.0)
    made: list[bpy.types.Object] = []

    def card(prefix: str, start: float, end: float, title: str, body: str, accent: bpy.types.Material) -> None:
        objects = (
            infographic._camera_plane(prefix + "_Panel", camera, collection, (-0.47, 0.105, -2.58), (0.285, 0.100), card_mat),
            infographic._camera_text(prefix + "_Title", title, camera, collection, (-0.715, 0.165, -2.47), 0.028, accent, font),
            infographic._camera_text(prefix + "_Body", body, camera, collection, (-0.715, 0.105, -2.47), 0.0165, text, font, line_spacing=0.91),
        )
        minute._set_visibility_interval(objects, *span(start, end)); minute._set_constant_visibility(objects); made.extend(objects)

    card("Law_Intro_v01", 0, 8, "САМОРЕГУЛЯЦИЯ СЕРДЦА", "Франк—Старлинг — адаптация к наполнению\nАнреп — адаптация к сопротивлению изгнанию", text)
    card("Law_Baseline_v01", 8, 15, "ИСХОДНЫЙ ЦИКЛ", "Обычное наполнение и обычная\nамплитуда сокращения желудочка.", muted)
    card("Law_FS1_v01", 15, 30, "ФРАНК—СТАРЛИНГ", "↑ венозный возврат → ↑ КДО\n↑ растяжение миокарда в диастолу\n→ более сильная следующая систола", blue)
    card("Law_FS2_v01", 30, 50, "ГЕТЕРОМЕТРИЧЕСКАЯ РЕГУЛЯЦИЯ", "В физиологических пределах:\n↑ начальная длина волокон → ↑ сила сокращения\n→ ↑ ударный объём", blue)
    card("Law_Transition_v01", 50, 60, "А ЕСЛИ РАСТЁТ ПОСТНАГРУЗКА?", "Наполнение оставляем примерно прежним,\nно повышаем давление, против которого\nлевый желудочек должен выбросить кровь.", orange)
    card("Law_Anrep1_v01", 60, 75, "АНРЕП: ШАГ ПОСТНАГРУЗКИ", "↑ давление в аорте / постнагрузка\n→ сначала изгнание затрудняется\n→ ударный объём временно уменьшается", orange)
    card("Law_Anrep2_v01", 75, 90, "АНРЕП: ОТСРОЧЕННЫЙ ОТВЕТ", "При сходной диастолической длине волокон\nсократимость постепенно возрастает\n→ выброс восстанавливается", orange)

    compare = (
        infographic._camera_plane("Law_ComparePanel_v01", camera, collection, (-0.41, 0.02, -2.59), (0.34, 0.215), card_mat),
        infographic._camera_text("Law_CompareTitle_v01", "ФРАНК—СТАРЛИНГ  vs  АНРЕП", camera, collection, (-0.705, 0.185, -2.47), 0.028, text, font),
        infographic._camera_text("Law_CompareLeft_v01", "ФРАНК—СТАРЛИНГ\n↑ преднагрузка\nменяется длина волокон\nгетерометрическая регуляция", camera, collection, (-0.705, 0.105, -2.47), 0.0175, blue, font, line_spacing=0.93),
        infographic._camera_text("Law_CompareRight_v01", "АНРЕП\n↑ постнагрузка\n↑ сократимость при сходной длине\nгомеометрическая регуляция", camera, collection, (-0.365, 0.105, -2.47), 0.0175, orange, font, line_spacing=0.93),
    )
    minute._set_visibility_interval(compare, *span(90, 102)); minute._set_constant_visibility(compare); made.extend(compare)
    outro = (
        infographic._camera_plane("Law_OutroPanel_v01", camera, collection, (-0.41, 0.02, -2.59), (0.34, 0.20), card_mat),
        infographic._camera_text("Law_OutroTitle_v01", "ОДНА ЦЕЛЬ — СТАБИЛЬНЫЙ ВЫБРОС", camera, collection, (-0.705, 0.145, -2.47), 0.029, green, font),
        infographic._camera_text("Law_OutroBody_v01", "Сердце приспосабливает насосную функцию\nи к объёму крови, и к нагрузке на изгнание.", camera, collection, (-0.705, 0.055, -2.47), 0.020, text, font),
    )
    minute._set_visibility_interval(outro, *span(102, 105)); minute._set_constant_visibility(outro); made.extend(outro)
    made.extend(starling_graph(camera, collection)); return tuple(made)


def animate_camera() -> None:
    camera = bpy.context.scene.camera
    if camera is None: return
    base_location = tuple(camera.location); base_lens = float(camera.data.lens)
    camera.location = (base_location[0], base_location[1] - 5.0, base_location[2] + 0.35); camera.data.lens = max(45.0, base_lens - 6.0)
    camera.keyframe_insert(data_path="location", frame=1); camera.data.keyframe_insert(data_path="lens", frame=1)
    camera.location = base_location; camera.data.lens = base_lens
    camera.keyframe_insert(data_path="location", frame=sec(8)); camera.data.keyframe_insert(data_path="lens", frame=sec(8))


def configure_render(scene: bpy.types.Scene, args: argparse.Namespace, frame_root: Path) -> None:
    scene.frame_start = args.frame_start; scene.frame_end = args.frame_end; scene.frame_step = args.sample_step
    scene.render.fps = FPS // args.sample_step; scene.render.fps_base = 1.0
    scene.render.resolution_x = int(args.resolution * 16 / 9); scene.render.resolution_y = args.resolution; scene.render.resolution_percentage = 100
    scene.render.use_file_extension = True; scene.render.use_overwrite = True; scene.render.use_placeholder = False
    scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGB"; scene.render.image_settings.color_depth = "8"; scene.render.image_settings.compression = 14
    scene.render.filepath = str(frame_root / FRAME_PREFIX)
    eevee = getattr(scene, "eevee", None)
    if eevee is not None:
        for attr in ("taa_render_samples", "taa_samples"):
            if hasattr(eevee, attr): setattr(eevee, attr, args.render_samples); break


def write_manifest(root: Path, args: argparse.Namespace) -> Path:
    path = root / "heart_starling_anrep_v01_manifest.json"
    data = {
        "revision": REVISION,
        "model_revision": MODEL_REVISION,
        "source_model": export_v07.MODEL_REVISION,
        "timeline": {"fps_authored": FPS, "duration_seconds": DURATION_SECONDS, "frame_end": TOTAL_FRAMES,
                     "scenes": [{"slug": s, "start_seconds": a, "end_seconds": b, "title_ru": t} for s, a, b, t in SCENES]},
        "physiology": {
            "frank_starling": {"type": "heterometric autoregulation", "visual_chain_ru": "↑ венозный возврат → ↑ КДО → ↑ диастолическое растяжение → ↑ сила следующего сокращения → ↑ УО", "animation": "increased end-diastolic scale plus increased systolic shortening"},
            "anrep": {"type": "homeometric autoregulation", "visual_chain_ru": "↑ постнагрузка → временно ↓ изгнание → отсроченно ↑ сократимость → восстановление выброса", "animation": "unchanged diastolic scale, transient reduced emptying, delayed rise in contractility"},
        },
        "human_reference": {"source": "user-provided turntable video", "v01_scope": "stylised translucent torso proportions; detailed facial likeness deferred"},
        "render": {"frame_start": args.frame_start, "frame_end": args.frame_end, "sample_step": args.sample_step, "output_fps": FPS // args.sample_step, "resolution": [int(args.resolution * 16 / 9), args.resolution], "render_samples": args.render_samples},
        "files": {"blend": BLEND_NAME, "video_target": VIDEO_NAME, "frame_directory": FRAME_DIR},
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"); return path


def build_model(resolution: int) -> model.HeartBuild:
    build = export_v07.build_model(resolution)
    hide_legacy_ui(); repeat_base_cycle()
    left = wrap_control(build, "left_ventricle", "CTRL_Law_LeftVentricle_v01")
    right = wrap_control(build, "right_ventricle", "CTRL_Law_RightVentricle_v01")
    animate_frank_starling(left, right); animate_anrep(left)
    reference_torso(build); afterload_ring(build); text_cards(build); animate_camera()
    scene = bpy.context.scene
    scene["model_revision"] = MODEL_REVISION; scene["teaching_revision"] = REVISION; scene["duration_seconds"] = DURATION_SECONDS
    scene["frank_starling_mode"] = "heterometric"; scene["anrep_mode"] = "homeometric"; scene["human_reference"] = "stylised user-proportion torso from provided turntable"
    scene.frame_start = 1; scene.frame_end = TOTAL_FRAMES; scene.frame_set(1); return build


def main() -> int:
    args = arguments(); validate(args)
    root = Path(args.output_root).resolve(); root.mkdir(parents=True, exist_ok=True)
    frames = root / FRAME_DIR; frames.mkdir(parents=True, exist_ok=True)
    build_model(args.resolution); scene = bpy.context.scene; configure_render(scene, args, frames)
    blend = root / BLEND_NAME
    if args.save_blend: bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    if args.render_animation: scene.frame_set(args.frame_start); bpy.ops.render.render(animation=True)
    manifest = write_manifest(root, args)
    print(f"HEART_STARLING_ANREP_REVISION={REVISION}"); print(f"HEART_STARLING_ANREP_FRAME_ROOT={frames}")
    print(f"HEART_STARLING_ANREP_BLEND={blend}"); print(f"HEART_STARLING_ANREP_MANIFEST={manifest}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
