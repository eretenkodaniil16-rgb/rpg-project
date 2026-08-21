from __future__ import annotations

"""Mechanistic teaching insets for Frank-Starling and Anrep.

Frank-Starling:
  15-28 s — atrium/ventricle cutaway with increased filling.
  28-50 s — sarcomere cartoon: a larger fraction of myosin heads becomes
             attached to actin with physiological stretch (length-dependent
             activation; not creation of new heads).

Anrep:
  60-90 s — aortic cross-section with elevated pressure/filling and a pressure
             vector opposing ventricular ejection. The 3D aorta is enlarged
             moderately as a didactic pressure cue, not as a literal statement
             that aortic dilation is the cause of increased afterload.
"""

import math
import bpy

REVISION = "heart_starling_anrep_mechanism_insets_v03"


def _ellipse_points(cx: float, cy: float, rx: float, ry: float, n: int = 64):
    points = []
    for i in range(n + 1):
        a = 2.0 * math.pi * i / n
        points.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return tuple(points)


def _camera_disk(app, name, camera, collection, loc, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=36, ring_count=18, radius=1.0)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    app.model._move_to_collection(obj, collection)
    app.infographic._parent_local(obj, camera, loc)
    return obj


def _line(app, name, camera, collection, points, material, bevel=0.0025):
    return app.minute._curve_object(name, camera, collection, tuple(points), material, bevel=bevel)


def _visibility(app, objects, start_s: float, end_s: float):
    app.set_visibility(objects, *app.span(start_s, end_s))
    app.minute._set_constant_visibility(objects)


def _key_scale(obj, frame: int, xyz):
    obj.scale = xyz
    obj.keyframe_insert(data_path="scale", frame=frame)


def _build_filling_cutaway(app, build):
    camera = bpy.context.scene.camera
    collection = build.collections["render"]
    font = app.infographic._load_cyrillic_font()

    panel = app.minute._make_material("M_FS_CutawayPanel_v03", (0.008, 0.022, 0.050, 1.0), 0.40)
    wall = app.minute._make_material("M_FS_CutawayWall_v03", (0.88, 0.46, 0.42, 1.0), 1.15)
    blood = app.minute._make_material("M_FS_CutawayBlood_v03", (0.74, 0.055, 0.045, 1.0), 1.00)
    arrow = app.minute._make_material("M_FS_CutawayArrow_v03", (0.22, 0.82, 1.00, 1.0), 2.0)
    text = app.minute._make_material("M_FS_CutawayText_v03", (0.95, 0.98, 1.00, 1.0), 1.25)
    accent = app.minute._make_material("M_FS_CutawayAccent_v03", (0.24, 0.80, 1.00, 1.0), 2.2)

    made = []
    made.append(app.infographic._camera_plane(
        "FS_Cutaway_Panel_v03", camera, collection,
        (0.43, -0.105, -2.59), (0.235, 0.135), panel,
    ))
    made.append(app.infographic._camera_text(
        "FS_Cutaway_Title_v03", "↑ НАПОЛНЕНИЕ СЕРДЦА", camera, collection,
        (0.225, -0.010, -2.47), 0.026, accent, font,
    ))
    made.append(app.infographic._camera_text(
        "FS_Cutaway_Label_v03", "↑ венозный возврат  →  ↑ КДО", camera, collection,
        (0.225, -0.205, -2.47), 0.0185, text, font,
    ))

    atrium_center = (0.345, -0.075)
    vent_center = (0.435, -0.145)
    made.append(_line(app, "FS_Cutaway_AtriumWall_v03", camera, collection,
                      _ellipse_points(*atrium_center, 0.060, 0.043), wall, 0.0030))
    made.append(_line(app, "FS_Cutaway_VentricleWall_v03", camera, collection,
                      _ellipse_points(*vent_center, 0.095, 0.067), wall, 0.0032))

    atrial_blood = _camera_disk(app, "FS_Cutaway_AtrialBlood_v03", camera, collection,
                                (atrium_center[0], atrium_center[1], -2.505),
                                (0.040, 0.027, 0.003), blood)
    ventricular_blood = _camera_disk(app, "FS_Cutaway_VentricularBlood_v03", camera, collection,
                                     (vent_center[0], vent_center[1], -2.505),
                                     (0.058, 0.039, 0.003), blood)
    made.extend((atrial_blood, ventricular_blood))

    # Inflow from pulmonary venous side into atrium, then through AV valve.
    made.append(_line(app, "FS_Cutaway_Inflow_v03", camera, collection,
                      ((0.225, -0.065), (0.285, -0.065), (0.315, -0.073)), arrow, 0.0035))
    made.append(_line(app, "FS_Cutaway_AVFlow_v03", camera, collection,
                      ((0.365, -0.108), (0.395, -0.125)), arrow, 0.0035))
    made.append(app.infographic._camera_text(
        "FS_Cutaway_InflowLabel_v03", "больше крови", camera, collection,
        (0.225, -0.045, -2.47), 0.0165, arrow, font,
    ))

    # Animate chamber blood fill; this is the inset equivalent of increased EDV.
    f15, f21, f27 = app.sec(15), app.sec(21), app.sec(27)
    _key_scale(atrial_blood, f15, (0.030, 0.020, 0.003))
    _key_scale(atrial_blood, f21, (0.046, 0.031, 0.003))
    _key_scale(atrial_blood, f27, (0.050, 0.034, 0.003))
    _key_scale(ventricular_blood, f15, (0.048, 0.032, 0.003))
    _key_scale(ventricular_blood, f21, (0.062, 0.042, 0.003))
    _key_scale(ventricular_blood, f27, (0.077, 0.052, 0.003))

    _visibility(app, made, 15.0, 28.0)
    return tuple(made)


def _build_sarcomere_inset(app, build):
    camera = bpy.context.scene.camera
    collection = build.collections["render"]
    font = app.infographic._load_cyrillic_font()

    panel = app.minute._make_material("M_FS_SarcomerePanel_v03", (0.008, 0.022, 0.050, 1.0), 0.40)
    actin = app.minute._make_material("M_FS_Actin_v03", (0.18, 0.78, 1.00, 1.0), 2.0)
    myosin = app.minute._make_material("M_FS_Myosin_v03", (0.95, 0.38, 0.16, 1.0), 2.0)
    inactive = app.minute._make_material("M_FS_BridgeInactive_v03", (0.45, 0.50, 0.58, 1.0), 0.9)
    active = app.minute._make_material("M_FS_BridgeActive_v03", (1.00, 0.76, 0.13, 1.0), 2.6)
    text = app.minute._make_material("M_FS_SarcomereText_v03", (0.95, 0.98, 1.00, 1.0), 1.25)

    made = []
    made.append(app.infographic._camera_plane(
        "FS_Sarcomere_Panel_v03", camera, collection,
        (0.43, -0.105, -2.59), (0.235, 0.135), panel,
    ))
    made.append(app.infographic._camera_text(
        "FS_Sarcomere_Title_v03", "САРКОМЕР: БОЛЬШЕ СВЯЗАННЫХ МОСТИКОВ", camera, collection,
        (0.205, -0.010, -2.47), 0.0215, active, font,
    ))

    # Two actin filaments and a central myosin thick filament.
    made.append(_line(app, "FS_ActinTop_v03", camera, collection,
                      ((0.225, -0.067), (0.635, -0.067)), actin, 0.0030))
    made.append(_line(app, "FS_ActinBottom_v03", camera, collection,
                      ((0.225, -0.148), (0.635, -0.148)), actin, 0.0030))
    made.append(_line(app, "FS_MyosinCore_v03", camera, collection,
                      ((0.305, -0.108), (0.555, -0.108)), myosin, 0.0050))

    # Myosin heads are always present. Their attachment state changes.
    head_xs = (0.325, 0.355, 0.390, 0.425, 0.460, 0.495, 0.530)
    for i, x in enumerate(head_xs, 1):
        target_y = -0.067 if i % 2 else -0.148
        # short head/lever arm, visible throughout inset
        made.append(_line(app, f"FS_MyosinHead_{i}_v03", camera, collection,
                          ((x, -0.108), (x + 0.012, -0.092 if i % 2 else -0.124)), myosin, 0.0025))

    # Baseline attached bridges: 3. Additional bridges appear progressively.
    bridge_objects = []
    bridge_specs = [
        (0.337, -0.092, -0.067),
        (0.402, -0.124, -0.148),
        (0.472, -0.092, -0.067),
        (0.367, -0.124, -0.148),
        (0.437, -0.092, -0.067),
        (0.507, -0.124, -0.148),
        (0.542, -0.092, -0.067),
    ]
    for i, (x, y0, y1) in enumerate(bridge_specs, 1):
        mat = active if i <= 3 else inactive
        obj = _line(app, f"FS_CrossBridge_{i}_v03", camera, collection,
                    ((x, y0), (x + 0.010, y1)), mat, 0.0028)
        bridge_objects.append(obj)
        made.append(obj)

    made.append(app.infographic._camera_text(
        "FS_Sarcomere_Caption_v03",
        "растяжение → ↑ длина-зависимая активация\n↑ чувствительность миофиламентов к Ca²⁺",
        camera, collection, (0.215, -0.188, -2.47), 0.0168, text, font, line_spacing=0.90,
    ))

    # Make the 4 additional bridges become active sequentially. We do this by
    # swapping their material slots at keyed frames via hide/show duplicates.
    for idx in range(3, 7):
        original = bridge_objects[idx]
        original.hide_render = True
        original.hide_viewport = True
        # active duplicate at same geometry/local transform
        dup = original.copy()
        dup.data = original.data.copy()
        dup.name = original.name + "_Active"
        collection.objects.link(dup)
        dup.data.materials.clear()
        dup.data.materials.append(active)
        dup.parent = original.parent
        dup.matrix_parent_inverse = original.matrix_parent_inverse.copy()
        dup.location = original.location.copy()
        dup.rotation_euler = original.rotation_euler.copy()
        dup.scale = original.scale.copy()
        start = 31.0 + (idx - 3) * 3.0
        _visibility(app, (dup,), start, 50.0)
        made.append(dup)

    _visibility(app, made[:len(made) - 4], 28.0, 50.0)
    return tuple(made)


def _build_anrep_aorta_inset(app, build):
    camera = bpy.context.scene.camera
    collection = build.collections["render"]
    font = app.infographic._load_cyrillic_font()

    panel = app.minute._make_material("M_AnrepAortaPanel_v03", (0.035, 0.017, 0.010, 1.0), 0.42)
    wall = app.minute._make_material("M_AnrepAortaWall_v03", (0.96, 0.35, 0.14, 1.0), 2.0)
    blood = app.minute._make_material("M_AnrepAortaBlood_v03", (0.72, 0.035, 0.025, 1.0), 1.1)
    pressure = app.minute._make_material("M_AnrepPressure_v03", (1.00, 0.72, 0.10, 1.0), 2.6)
    text = app.minute._make_material("M_AnrepAortaText_v03", (0.98, 0.96, 0.93, 1.0), 1.25)

    made = []
    made.append(app.infographic._camera_plane(
        "Anrep_AortaPanel_v03", camera, collection,
        (0.43, -0.105, -2.59), (0.235, 0.135), panel,
    ))
    made.append(app.infographic._camera_text(
        "Anrep_AortaTitle_v03", "↑ ДАВЛЕНИЕ В АОРТЕ", camera, collection,
        (0.225, -0.010, -2.47), 0.027, pressure, font,
    ))

    center = (0.425, -0.110)
    made.append(_line(app, "Anrep_AortaWall_v03", camera, collection,
                      _ellipse_points(*center, 0.105, 0.075), wall, 0.0050))
    blood_disk = _camera_disk(app, "Anrep_AortaBlood_v03", camera, collection,
                              (center[0], center[1], -2.505),
                              (0.070, 0.050, 0.003), blood)
    made.append(blood_disk)

    # Pressure vectors directed against forward ejection.
    made.append(_line(app, "Anrep_PressureArrow_v03", camera, collection,
                      ((0.610, -0.110), (0.535, -0.110), (0.500, -0.110)), pressure, 0.0040))
    made.append(app.infographic._camera_text(
        "Anrep_PressureLabel_v03", "← ↑ постнагрузка", camera, collection,
        (0.510, -0.075, -2.47), 0.0190, pressure, font,
    ))
    made.append(app.infographic._camera_text(
        "Anrep_AortaCaption_v03", "большее наполнение + ↑ давление\nсначала выброс ЛЖ затруднён",
        camera, collection, (0.225, -0.195, -2.47), 0.0175, text, font, line_spacing=0.90,
    ))

    f60, f65, f75, f90 = app.sec(60), app.sec(65), app.sec(75), app.sec(90)
    _key_scale(blood_disk, f60, (0.060, 0.043, 0.003))
    _key_scale(blood_disk, f65, (0.078, 0.056, 0.003))
    _key_scale(blood_disk, f75, (0.082, 0.059, 0.003))
    _key_scale(blood_disk, f90, (0.080, 0.058, 0.003))

    _visibility(app, made, 60.0, 90.0)
    return tuple(made)


def _animate_main_aorta(app):
    """Moderate visible aortic calibre increase as a pressure cue."""
    aorta = bpy.data.objects.get("V02_Aorta")
    if aorta is None or aorta.type != "CURVE":
        return
    data = aorta.data
    base = float(data.bevel_depth)
    for time_s, factor in ((1.0, 1.00), (59.0, 1.00), (64.0, 1.20), (75.0, 1.18), (90.0, 1.20), (102.0, 1.00)):
        data.bevel_depth = base * factor
        data.keyframe_insert(data_path="bevel_depth", frame=app.sec(time_s))


def apply(build, app):
    _build_filling_cutaway(app, build)
    _build_sarcomere_inset(app, build)
    _build_anrep_aorta_inset(app, build)
    _animate_main_aorta(app)

    scene = bpy.context.scene
    scene["mechanism_insets_revision"] = REVISION
    scene["frank_starling_insets"] = "15-28s filling cutaway; 28-50s sarcomere/cross-bridge visualization"
    scene["anrep_inset"] = "60-90s aortic cross-section + pressure vector; 3D aorta +20% calibre cue"
    scene["physiology_note"] = (
        "Sarcomere inset depicts increased fraction/probability of attached cross-bridges with "
        "length-dependent activation, not creation of additional myosin heads. Aortic dilation "
        "is a didactic cue for elevated aortic pressure/afterload, not its causal definition."
    )
