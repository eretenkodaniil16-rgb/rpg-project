from __future__ import annotations

import math
import random

import bpy

from blender_helpers import (
    cube,
    cylinder,
    ease,
    key_location,
    key_rotation,
    key_scale,
    look_at,
    material,
    polyline,
    text,
    torus,
    uv_sphere,
    visibility_window,
)
from synapse_data import PHASES, SOURCE_NOTE, TOTAL_FRAMES, sec_to_frame

SEED = 774


def build_materials():
    return {
        "pre": material("Presynaptic membrane", (0.63, 0.26, 0.08, 1), roughness=0.48),
        "pre_light": material("Active zone", (0.95, 0.55, 0.17, 1), roughness=0.35),
        "post": material("Postsynaptic membrane", (0.47, 0.19, 0.06, 1), roughness=0.50),
        "vesicle": material("Synaptic vesicle", (0.62, 0.20, 0.72, 1), roughness=0.32),
        "nt": material(
            "Neurotransmitter",
            (0.77, 0.05, 0.48, 1),
            roughness=0.25,
            emission=(0.33, 0.0, 0.12, 1),
            emission_strength=1.8,
        ),
        "ca": material(
            "Calcium",
            (0.03, 0.37, 0.95, 1),
            roughness=0.20,
            emission=(0.0, 0.12, 0.8, 1),
            emission_strength=2.4,
        ),
        "channel": material("Voltage-gated calcium channel", (0.03, 0.43, 0.84, 1), roughness=0.25, metallic=0.12),
        "iono": material("Ionotropic receptor", (0.95, 0.30, 0.05, 1), roughness=0.30),
        "meta": material("Metabotropic receptor", (0.02, 0.58, 0.60, 1), roughness=0.30),
        "ion": material(
            "Postsynaptic ion",
            (0.22, 0.75, 0.95, 1),
            roughness=0.20,
            emission=(0.02, 0.32, 0.8, 1),
            emission_strength=1.5,
        ),
        "messenger": material(
            "Second messenger",
            (0.95, 0.68, 0.05, 1),
            roughness=0.22,
            emission=(0.55, 0.23, 0.0, 1),
            emission_strength=1.2,
        ),
        "mito": material("Mitochondrion", (0.69, 0.14, 0.48, 1), roughness=0.38),
        "uptake": material("Reuptake transporter", (0.15, 0.65, 0.28, 1), roughness=0.31),
        "enzyme": material("Enzyme", (0.73, 0.72, 0.20, 1), roughness=0.35),
        "white": material(
            "Text white",
            (0.96, 0.97, 1.0, 1),
            roughness=0.80,
            emission=(0.45, 0.48, 0.58, 1),
            emission_strength=0.55,
        ),
        "muted": material("Text muted", (0.58, 0.64, 0.72, 1), roughness=0.80),
        "red": material(
            "Action potential",
            (1.0, 0.03, 0.02, 1),
            roughness=0.18,
            emission=(1.0, 0.01, 0.0, 1),
            emission_strength=6.0,
        ),
        "dark": material("Dark panel", (0.015, 0.025, 0.05, 1), roughness=0.70),
    }


def build_anatomy(m):
    uv_sphere("Presynaptic terminal", (0, 0.2, 3.7), (6.6, 2.25, 3.05), m["pre"])
    cylinder("Axon", (0.0, 0.2, 9.0), 1.45, 7.4, m["pre"], vertices=48)
    cube("Active zone", (0.0, -2.26, 0.86), (2.3, 0.10, 0.11), m["pre_light"], bevel=0.06)
    uv_sphere("Postsynaptic neuron", (0, 0.25, -4.1), (7.2, 2.4, 2.85), m["post"])

    text("Label pre", "ПРЕСИНАПТИЧЕСКАЯ ТЕРМИНАЛЬ", (-7.7, -5.0, 5.6), 0.34, m["white"], align="LEFT")
    text("Label cleft", "СИНАПТИЧЕСКАЯ ЩЕЛЬ", (-7.7, -5.0, -0.2), 0.30, m["white"], align="LEFT")
    text("Label post", "ПОСТСИНАПТИЧЕСКИЙ НЕЙРОН", (-7.7, -5.0, -5.5), 0.34, m["white"], align="LEFT")

    for i, (x, z, angle) in enumerate([(-3.6, 4.5, -0.25), (3.6, 4.3, 0.35), (4.7, 2.3, -0.5)]):
        mito = uv_sphere(f"Mitochondrion {i+1}", (x, -2.32, z), (0.82, 0.28, 0.43), m["mito"], segments=32, rings=16)
        mito.rotation_euler[1] = angle
        for j in range(3):
            bar = cube(
                f"Crista {i+1}-{j+1}",
                (x - 0.28 + j * 0.27, -2.62, z),
                (0.06, 0.03, 0.22),
                m["vesicle"],
                bevel=0.02,
            )
            bar.rotation_euler[1] = angle


def build_vesicles(m):
    reserve = [(-3.7, 3.6), (-2.4, 5.2), (-1.1, 3.9), (1.8, 4.9), (3.3, 3.5), (4.1, 5.4)]
    for i, (x, z) in enumerate(reserve):
        uv_sphere(f"Reserve vesicle {i+1}", (x, -2.43, z), (0.72, 0.22, 0.72), m["vesicle"], segments=32, rings=16)
        for j in range(6):
            angle = 2 * math.pi * j / 6
            uv_sphere(
                f"Reserve NT {i+1}-{j+1}",
                (x + 0.34 * math.cos(angle), -2.70, z + 0.34 * math.sin(angle)),
                (0.11, 0.06, 0.11),
                m["nt"],
                segments=18,
                rings=9,
            )

    active = uv_sphere("Active synaptic vesicle", (0.6, -2.45, 3.2), (0.86, 0.24, 0.86), m["vesicle"], segments=40, rings=20)
    key_location(active, sec_to_frame(0), (0.6, -2.45, 3.2))
    key_location(active, sec_to_frame(13), (0.6, -2.45, 3.2))
    key_location(active, sec_to_frame(17.5), (0.2, -2.45, 1.25))
    key_scale(active, sec_to_frame(17.5), (1, 1, 1))
    key_scale(active, sec_to_frame(20.0), (1.25, 1.0, 0.16))
    key_scale(active, sec_to_frame(21.0), (0.01, 0.01, 0.01))
    ease(active)

    for j in range(10):
        angle = 2 * math.pi * j / 10
        radius = 0.42 if j else 0.0
        nt = uv_sphere(
            f"Active vesicle NT {j+1}",
            (0.6 + radius * math.cos(angle), -2.72, 3.2 + radius * math.sin(angle)),
            (0.12, 0.06, 0.12),
            m["nt"],
            segments=18,
            rings=9,
        )
        key_location(nt, sec_to_frame(13), nt.location)
        key_location(nt, sec_to_frame(17.5), (0.2 + radius * math.cos(angle), -2.72, 1.25 + radius * math.sin(angle)))
        key_scale(nt, sec_to_frame(19.0), (1, 1, 1))
        key_scale(nt, sec_to_frame(20.5), (0.01, 0.01, 0.01))
        ease(nt)


def build_calcium(m, rng):
    channel_x = (-2.0, 2.0)
    for idx, x in enumerate(channel_x):
        cylinder(f"Ca channel {idx+1} A", (x - 0.20, -2.48, 0.95), 0.17, 0.95, m["channel"], vertices=24)
        cylinder(f"Ca channel {idx+1} B", (x + 0.20, -2.48, 0.95), 0.17, 0.95, m["channel"], vertices=24)
        gate = cube(f"Ca gate {idx+1}", (x, -2.70, 0.92), (0.23, 0.07, 0.07), m["channel"], bevel=0.03)
        key_rotation(gate, sec_to_frame(0), (0, 0, 0))
        key_rotation(gate, sec_to_frame(8.0), (0, 0, 0))
        key_rotation(gate, sec_to_frame(9.0), (0, math.radians(70), 0))
        key_rotation(gate, sec_to_frame(13.0), (0, math.radians(70), 0))
        key_rotation(gate, sec_to_frame(15.0), (0, 0, 0))
        ease(gate)

    for i in range(22):
        x0 = channel_x[i % 2] + rng.uniform(-0.55, 0.55)
        z0 = rng.uniform(-0.25, 0.45)
        ion = uv_sphere(f"Ca2+ {i+1:02d}", (x0, -2.75, z0), (0.13, 0.08, 0.13), m["ca"], segments=16, rings=8)
        start_s = 8.4 + (i % 7) * 0.28 + rng.uniform(0.0, 0.18)
        end_s = start_s + 2.4 + rng.uniform(-0.3, 0.4)
        visibility_window(ion, sec_to_frame(start_s), sec_to_frame(14.2), TOTAL_FRAMES)
        key_location(ion, sec_to_frame(start_s), (x0, -2.75, z0))
        key_location(ion, sec_to_frame(end_s), (x0 + rng.uniform(-0.9, 0.9), -2.65, rng.uniform(1.8, 3.2)))
        key_scale(ion, sec_to_frame(13.5), (1, 1, 1))
        key_scale(ion, sec_to_frame(15.0), (0.01, 0.01, 0.01))
        ease(ion)


def build_action_potential(m):
    pulse = torus("Action potential pulse", (0, -2.7, 9.7), 1.56, 0.16, m["red"], rotation=(math.pi / 2, 0, 0))
    visibility_window(pulse, sec_to_frame(3.7), sec_to_frame(8.5), TOTAL_FRAMES)
    key_location(pulse, sec_to_frame(4.0), (0, -2.7, 10.6))
    key_location(pulse, sec_to_frame(7.3), (0, -2.7, 4.9))
    key_scale(pulse, sec_to_frame(4.0), (1, 1, 1))
    key_scale(pulse, sec_to_frame(7.8), (1.55, 1.55, 1.55))
    ease(pulse)

    cube("AP graph panel", (-5.4, -5.4, 8.6), (2.1, 0.05, 1.35), m["dark"], bevel=0.12)
    graph = [
        (-6.9, -5.55, 8.0), (-6.3, -5.55, 8.0), (-6.0, -5.55, 8.2),
        (-5.75, -5.55, 9.5), (-5.45, -5.55, 9.95), (-5.15, -5.55, 8.6),
        (-4.8, -5.55, 8.05), (-4.0, -5.55, 8.0),
    ]
    polyline("Action potential graph", graph, 0.045, m["red"])
    text("AP label", "ПОТЕНЦИАЛ ДЕЙСТВИЯ", (-5.4, -5.65, 10.25), 0.25, m["white"])
    marker = uv_sphere("AP graph marker", (-6.9, -5.72, 8.0), (0.10, 0.04, 0.10), m["red"], segments=16, rings=8)
    visibility_window(marker, sec_to_frame(3.7), sec_to_frame(8.5), TOTAL_FRAMES)
    key_location(marker, sec_to_frame(4.0), (-6.9, -5.72, 8.0))
    key_location(marker, sec_to_frame(7.8), (-4.0, -5.72, 8.0))
    ease(marker)


def build_receptors(m):
    for i, x in enumerate([-3.4, -1.6, 0.3]):
        cylinder(f"Ionotropic {i+1} L", (x - 0.22, -2.62, -1.42), 0.16, 1.05, m["iono"], vertices=24)
        cylinder(f"Ionotropic {i+1} R", (x + 0.22, -2.62, -1.42), 0.16, 1.05, m["iono"], vertices=24)
        gate = cube(f"Ionotropic gate {i+1}", (x, -2.80, -1.17), (0.22, 0.06, 0.06), m["iono"], bevel=0.02)
        key_rotation(gate, sec_to_frame(27.0), (0, 0, 0))
        key_rotation(gate, sec_to_frame(28.0), (0, math.radians(70), 0))
        key_rotation(gate, sec_to_frame(35.0), (0, math.radians(70), 0))
        key_rotation(gate, sec_to_frame(38.5), (0, 0, 0))
        ease(gate)

    for j in range(7):
        x = 3.05 + (j - 3) * 0.16
        z = -1.35 + 0.10 * math.sin(j)
        cylinder(f"Metabotropic helix {j+1}", (x, -2.64, z), 0.085, 1.15, m["meta"], vertices=18)
    text("Ionotropic label", "ИОНОТРОПНЫЙ", (-1.7, -5.0, -2.3), 0.25, m["white"])
    text("Metabotropic label", "МЕТАБОТРОПНЫЙ", (3.1, -5.0, -2.3), 0.25, m["white"])


def build_transmitter(m, rng):
    targets = [-3.4, -1.6, 0.3, 3.05]
    for i in range(42):
        angle = rng.uniform(0, 2 * math.pi)
        radius = rng.uniform(0.0, 0.42)
        start = (0.20 + radius * math.cos(angle), -2.86, 0.65 + radius * math.sin(angle))
        nt = uv_sphere(f"Released NT {i+1:02d}", start, (0.12, 0.06, 0.12), m["nt"], segments=16, rings=8)
        appear_s = 19.4 + (i % 9) * 0.20 + rng.uniform(0.0, 0.20)
        bind_s = 25.0 + (i % 8) * 0.48 + rng.uniform(0.0, 0.35)
        target_x = targets[i % 4] + rng.uniform(-0.25, 0.25)
        mid = (start[0] + rng.uniform(-1.5, 1.5), -2.88, -0.15 + rng.uniform(-0.35, 0.35))
        end = (target_x, -2.88, -0.82 + rng.uniform(-0.12, 0.12))
        visibility_window(nt, sec_to_frame(appear_s), sec_to_frame(40.7), TOTAL_FRAMES)
        key_scale(nt, sec_to_frame(appear_s), (0.01, 0.01, 0.01))
        key_scale(nt, sec_to_frame(appear_s + 0.25), (1, 1, 1))
        key_location(nt, sec_to_frame(appear_s), start)
        key_location(nt, sec_to_frame((appear_s + bind_s) * 0.5), mid)
        key_location(nt, sec_to_frame(bind_s), end)
        if i % 3 == 0:
            key_location(nt, sec_to_frame(39.6), (5.0 + rng.uniform(-0.2, 0.2), -2.88, 0.8))
        elif i % 3 == 1:
            key_location(nt, sec_to_frame(39.6), (rng.choice((-1, 1)) * rng.uniform(6.2, 8.0), -2.88, -0.2))
        else:
            key_scale(nt, sec_to_frame(37.0), (1, 1, 1))
            key_scale(nt, sec_to_frame(39.2), (0.01, 0.01, 0.01))
        key_scale(nt, sec_to_frame(40.5), (0.01, 0.01, 0.01))
        ease(nt)


def build_postsynaptic_response(m, rng):
    receptors = [-3.4, -1.6, 0.3]
    for i in range(22):
        x = receptors[i % 3] + rng.uniform(-0.08, 0.08)
        ion = uv_sphere(f"Post ion {i+1:02d}", (x, -2.88, -0.55), (0.10, 0.05, 0.10), m["ion"], segments=14, rings=7)
        start = 29.0 + (i % 6) * 0.25
        visibility_window(ion, sec_to_frame(start), sec_to_frame(36.2), TOTAL_FRAMES)
        key_location(ion, sec_to_frame(start), (x, -2.88, -0.55))
        key_location(ion, sec_to_frame(start + 2.2), (x + rng.uniform(-0.25, 0.25), -2.88, -3.0))
        ease(ion)

    gprotein = uv_sphere("G protein", (3.1, -2.75, -2.15), (0.34, 0.12, 0.24), m["messenger"], segments=22, rings=11)
    visibility_window(gprotein, sec_to_frame(29.5), sec_to_frame(36.5), TOTAL_FRAMES)
    key_location(gprotein, sec_to_frame(30.0), (3.1, -2.75, -2.15))
    key_location(gprotein, sec_to_frame(32.5), (4.0, -2.75, -2.7))
    ease(gprotein)

    for i in range(15):
        msg = uv_sphere(f"Second messenger {i+1:02d}", (4.0, -2.80, -2.7), (0.085, 0.04, 0.085), m["messenger"], segments=14, rings=7)
        start = 31.8 + i * 0.16
        visibility_window(msg, sec_to_frame(start), sec_to_frame(37.0), TOTAL_FRAMES)
        key_location(msg, sec_to_frame(start), (4.0, -2.80, -2.7))
        key_location(msg, sec_to_frame(start + 2.2), (rng.uniform(2.3, 5.8), -2.80, rng.uniform(-5.0, -3.2)))
        ease(msg)


def build_clearance(m):
    for dx in (-0.18, 0.18):
        cylinder(f"Reuptake transporter {dx}", (5.0 + dx, -2.55, 0.82), 0.15, 1.0, m["uptake"], vertices=24)
    text("Reuptake label", "ОБРАТНЫЙ ЗАХВАТ", (5.0, -5.0, 1.8), 0.23, m["white"])

    for i, (x, z) in enumerate([(-5.0, -0.15), (-4.2, -0.55), (4.4, -0.25)]):
        enzyme = uv_sphere(f"Enzyme {i+1}", (x, -2.85, z), (0.26, 0.09, 0.18), m["enzyme"], segments=18, rings=9)
        visibility_window(enzyme, sec_to_frame(34.5), sec_to_frame(41.0), TOTAL_FRAMES)


def build_cards(m):
    for i, phase in enumerate(PHASES):
        start = sec_to_frame(phase["start_s"])
        end = sec_to_frame(phase["end_s"] - 1 / 30)
        title_obj = text(f"Phase title {i+1}", phase["title"], (0.0, -5.2, 10.5), 0.48, m["white"])
        caption_obj = text(f"Phase caption {i+1}", phase["caption"], (0.0, -5.2, -7.2), 0.25, m["white"])
        visibility_window(title_obj, start, end, TOTAL_FRAMES)
        visibility_window(caption_obj, start, end, TOTAL_FRAMES)

    text("Source note", SOURCE_NOTE, (0.0, -5.2, -8.0), 0.18, m["muted"])
    polyline("Timeline", [(-6.4, -5.25, -8.6), (6.4, -5.25, -8.6)], 0.025, m["muted"])
    playhead = uv_sphere("Timeline playhead", (-6.4, -5.35, -8.6), (0.09, 0.04, 0.09), m["red"], segments=16, rings=8)
    key_location(playhead, 1, (-6.4, -5.35, -8.6))
    key_location(playhead, TOTAL_FRAMES, (6.4, -5.35, -8.6))
    ease(playhead)


def build_camera_and_lights():
    camera_keys = [
        (sec_to_frame(0), (0.0, -28.5, 2.0), (0.0, -0.5, 1.0)),
        (sec_to_frame(12.0), (0.0, -28.5, 2.0), (0.0, -0.5, 1.0)),
        (sec_to_frame(19.0), (0.0, -25.8, 0.8), (0.0, -0.5, 0.4)),
        (sec_to_frame(24.0), (0.0, -25.8, 0.8), (0.0, -0.5, 0.4)),
        (sec_to_frame(31.0), (0.0, -27.2, 0.0), (0.0, -0.5, -0.5)),
        (sec_to_frame(41.0), (0.0, -28.5, 2.0), (0.0, -0.5, 1.0)),
        (TOTAL_FRAMES, (0.0, -28.5, 2.0), (0.0, -0.5, 1.0)),
    ]
    bpy.ops.object.camera_add(location=camera_keys[0][1])
    camera = bpy.context.object
    camera.name = "Teaching camera"
    camera.data.lens = 56
    bpy.context.scene.camera = camera
    for frame, location, target in camera_keys:
        camera.location = location
        look_at(camera, target)
        camera.keyframe_insert(data_path="location", frame=frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    ease(camera)

    lights = [
        ("Key light", "AREA", (-5.5, -11.0, 9.0), 1050, 7.0, (0, 0, 1)),
        ("Fill light", "AREA", (6.5, -8.0, 1.5), 700, 6.0, (0, 0, 0)),
        ("Rim light", "AREA", (0.0, 2.5, 8.0), 900, 5.0, (0, 0, 2.0)),
    ]
    for name, kind, location, energy, size, target in lights:
        bpy.ops.object.light_add(type=kind, location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.size = size
        look_at(light, target)


def build_synapse_scene():
    rng = random.Random(SEED)
    m = build_materials()
    build_anatomy(m)
    build_vesicles(m)
    build_calcium(m, rng)
    build_action_potential(m)
    build_receptors(m)
    build_transmitter(m, rng)
    build_postsynaptic_response(m, rng)
    build_clearance(m)
    build_cards(m)
    build_camera_and_lights()
    bpy.context.scene.frame_set(1)
