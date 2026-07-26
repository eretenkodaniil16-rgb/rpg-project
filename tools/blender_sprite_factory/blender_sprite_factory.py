from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import bpy
    from mathutils import Vector
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Этот файл запускается только встроенным Python Blender. "
        "Используйте 02_RUN_BLENDER_SPRITE_PILOT.cmd."
    ) from exc

from factory_config import (
    CONTACT_SHEET_BACKGROUND_HEX,
    FactoryConfig,
    MaterialSlot,
    load_factory_config,
    validate_required_files,
)
from pixel_geometry import alpha_bbox, anchor_rgba_to_baseline


RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
MODULE_PROPERTY = "sprite_module_id"
SIDE_PROPERTY = "physical_side"
MATERIAL_PROPERTY = "material_slot_id"


@dataclass(frozen=True)
class FrameArtifact:
    animation_id: str
    direction: str
    frame_number: int
    output_path: Path
    sprite_width: int
    sprite_height: int
    baseline_y: int


@dataclass(frozen=True)
class FramingCalibration:
    scale: float
    source_center_x: float


@dataclass
class BuildContext:
    config: FactoryConfig
    rig: bpy.types.Object
    materials: dict[str, bpy.types.Material]
    module_collections: dict[str, bpy.types.Collection]


def main() -> int:
    args = _parse_args(_script_arguments())
    repo_root = Path(args.repo_root).resolve()
    config_path = _resolve_cli_path(repo_root, args.config)
    config = load_factory_config(config_path, repo_root)
    config.assert_blender_version(tuple(bpy.app.version))
    missing = validate_required_files(config)
    if missing:
        formatted = "\n".join(f"- {config.relative_to_repo(path)}" for path in missing)
        raise FileNotFoundError(f"Reference pack или texture slots неполны:\n{formatted}")

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id должен содержать только буквы, цифры, '.', '_' и '-'")
    run_dir = (config.run_root / run_id).resolve()
    _assert_within(config.run_root, run_dir, "run directory")
    run_dir.mkdir(parents=True, exist_ok=False)

    context = build_scene(config)
    source_dir = run_dir / "source"
    source_dir.mkdir()
    blend_path = source_dir / f"{config.character_id}_proxy_v01.blend"
    _set_idle_down(context)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)

    artifacts: list[FrameArtifact] = []
    contact_sheet: Path | None = None
    if args.mode == "all":
        artifacts = render_pilot(context, run_dir)
        contact_sheet = _write_contact_sheet(config, artifacts, run_dir / "contact_sheet.png")
        _set_idle_down(context)
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)

    manifest_path = _write_run_manifest(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    print(f"BLENDER_SPRITE_FACTORY_RESULT={manifest_path}")
    return 0


def build_scene(config: FactoryConfig) -> BuildContext:
    _clear_scene()
    scene = bpy.context.scene
    scene.name = f"{config.character_id}_sprite_factory"
    scene["character_id"] = config.character_id
    scene["factory_schema_version"] = config.schema_version
    scene["factory_stage"] = config.stage
    scene["master_reference"] = config.relative_to_repo(config.master_reference)
    scene["large_pauldron_physical_side"] = "left"
    scene["small_pauldron_physical_side"] = "right"
    scene["model_forward_axis"] = "-Y"
    scene["model_up_axis"] = "+Z"

    root_collection = _new_collection("SPRITE_FACTORY")
    rig_collection = _new_collection("RIG", root_collection)
    modules_root = _new_collection("MODULES", root_collection)
    _new_collection("REFERENCES", root_collection)
    render_collection = _new_collection("RENDER", root_collection)

    module_collections = {
        module_id: _new_collection(f"MOD_{module_id}", modules_root)
        for module_id in config.required_modules
    }
    materials = {
        slot_id: _create_material(slot)
        for slot_id, slot in config.material_slots.items()
    }
    rig = _create_rig(config, rig_collection)
    context = BuildContext(
        config=config,
        rig=rig,
        materials=materials,
        module_collections=module_collections,
    )

    _build_body(context)
    _build_head_and_hair(context)
    _build_armor(context)
    _build_arms(context)
    _build_legs(context)
    _build_accessories(context)
    _create_actions(context)
    _create_camera_and_lights(context, render_collection)
    _configure_render(scene, config)
    _validate_built_scene(context)
    return context


def render_pilot(context: BuildContext, run_dir: Path) -> list[FrameArtifact]:
    config = context.config
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    raw_dir.mkdir()
    frame_dir.mkdir()
    artifacts: list[FrameArtifact] = []

    idle_action = bpy.data.actions[f"{config.character_id}_idle"]
    _assign_action(context.rig, idle_action)
    down_calibration: FramingCalibration | None = None
    for direction in ("down", "left", "right", "up"):
        context.rig.rotation_euler[2] = math.radians(config.directions[direction])
        artifact, calibration = _render_frame(
            context,
            animation_id="idle",
            direction=direction,
            frame_number=1,
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=f"{config.character_id}_idle_{direction}_proxy_v01.png",
            fixed_scale=(down_calibration.scale if down_calibration else None),
            fixed_center_x=None,
        )
        artifacts.append(artifact)
        if direction == "down":
            down_calibration = calibration

    if down_calibration is None:
        raise RuntimeError("Не удалось откалибровать idle_down")

    walk_action = bpy.data.actions[f"{config.character_id}_walk_down"]
    _assign_action(context.rig, walk_action)
    context.rig.rotation_euler[2] = math.radians(config.directions["down"])
    for frame_number in config.animations["walk_down"]["frames"]:
        artifact, _ = _render_frame(
            context,
            animation_id="walk_down",
            direction="down",
            frame_number=int(frame_number),
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=(
                f"{config.character_id}_walk_down_f{int(frame_number):02d}_proxy_v01.png"
            ),
            fixed_scale=down_calibration.scale,
            fixed_center_x=down_calibration.source_center_x,
        )
        artifacts.append(artifact)
    return artifacts


def _build_body(context: BuildContext) -> None:
    _register(
        context,
        _box("body_pelvis", (0.0, 0.0, 2.10), (1.10, 0.62, 0.46), context.materials["leather_dark"], 0.08),
        "body_base",
        "pelvis",
    )
    _register(
        context,
        _frustum(
            "body_ribcage",
            (0.0, 0.0, 2.95),
            radius_bottom=0.61,
            radius_top=0.78,
            depth=1.35,
            vertices=8,
            material=context.materials["chainmail"],
        ),
        "body_base",
        "chest",
    )
    _register(
        context,
        _cylinder_between(
            "body_neck",
            (-0.01, 0.0, 3.64),
            (-0.01, 0.0, 3.98),
            0.19,
            8,
            context.materials["skin"],
        ),
        "body_base",
        "neck",
    )


def _build_head_and_hair(context: BuildContext) -> None:
    _register(
        context,
        _ellipsoid(
            "head_base",
            (0.0, -0.02, 4.29),
            (0.47, 0.42, 0.62),
            context.materials["skin"],
            segments=12,
            rings=8,
        ),
        "head",
        "head",
    )
    _register(
        context,
        _frustum(
            "head_nose",
            (0.0, -0.44, 4.25),
            radius_bottom=0.09,
            radius_top=0.035,
            depth=0.25,
            vertices=4,
            material=context.materials["skin"],
            rotation=(math.radians(90.0), 0.0, 0.0),
        ),
        "head",
        "head",
    )
    _register(
        context,
        _ellipsoid(
            "hair_cap",
            (0.0, 0.01, 4.61),
            (0.53, 0.47, 0.42),
            context.materials["hair"],
            segments=12,
            rings=7,
        ),
        "hair",
        "head",
    )
    locks = (
        ("hair_lock_front_left", (0.19, -0.39, 4.39), (0.16, 0.12, 0.42)),
        ("hair_lock_front_center", (-0.02, -0.43, 4.43), (0.15, 0.11, 0.35)),
        ("hair_lock_front_right", (-0.22, -0.36, 4.39), (0.18, 0.13, 0.39)),
        ("hair_lock_side_left", (0.42, -0.06, 4.33), (0.13, 0.16, 0.40)),
        ("hair_lock_side_right", (-0.42, -0.05, 4.34), (0.13, 0.16, 0.39)),
    )
    for name, location, scale in locks:
        _register(
            context,
            _ellipsoid(
                name,
                location,
                scale,
                context.materials["hair"],
                segments=8,
                rings=5,
            ),
            "hair",
            "head",
        )


def _build_armor(context: BuildContext) -> None:
    _register(
        context,
        _box(
            "armor_chest",
            (0.0, -0.18, 3.05),
            (1.30, 0.44, 1.08),
            context.materials["leather_mid"],
            0.10,
        ),
        "torso_armor",
        "chest",
    )
    _register(
        context,
        _box(
            "armor_strap_left_to_right",
            (0.08, -0.43, 3.08),
            (0.13, 0.08, 1.43),
            context.materials["leather_dark"],
            0.025,
            rotation=(0.0, math.radians(29.0), 0.0),
        ),
        "torso_armor",
        "chest",
    )
    _register(
        context,
        _frustum(
            "chainmail_skirt",
            (0.0, 0.0, 1.78),
            radius_bottom=0.67,
            radius_top=0.50,
            depth=0.78,
            vertices=10,
            material=context.materials["chainmail"],
        ),
        "chainmail",
        "pelvis",
    )
    _register(
        context,
        _frustum(
            "belt",
            (0.0, -0.01, 2.28),
            radius_bottom=0.61,
            radius_top=0.61,
            depth=0.16,
            vertices=10,
            material=context.materials["leather_dark"],
        ),
        "torso_armor",
        "pelvis",
    )
    _register(
        context,
        _torus(
            "scarf_wrap",
            (0.0, -0.01, 3.76),
            major_radius=0.49,
            minor_radius=0.16,
            material=context.materials["scarf"],
        ),
        "scarf",
        "neck",
    )
    _register(
        context,
        _frustum(
            "scarf_front",
            (0.0, -0.41, 3.48),
            radius_bottom=0.29,
            radius_top=0.48,
            depth=0.66,
            vertices=3,
            material=context.materials["scarf"],
            rotation=(0.0, 0.0, math.radians(180.0)),
        ),
        "scarf",
        "chest",
    )


def _build_arms(context: BuildContext) -> None:
    for side, sign in (("L", 1.0), ("R", -1.0)):
        upper_start = (0.68 * sign, 0.0, 3.43)
        elbow = (0.95 * sign, -0.02, 2.78)
        wrist = (1.00 * sign, -0.15, 2.18)
        hand = (1.00 * sign, -0.18, 1.96)
        upper = _cylinder_between(
            f"arm_upper_{side}",
            upper_start,
            elbow,
            0.22,
            8,
            context.materials["chainmail"],
        )
        _register(context, upper, "arms", f"upper_arm.{side}", side.lower())
        forearm_material = context.materials["silver"] if side == "L" else context.materials["dark_steel"]
        forearm = _cylinder_between(
            f"arm_forearm_{side}",
            elbow,
            wrist,
            0.20,
            8,
            forearm_material,
        )
        _register(context, forearm, "arms", f"forearm.{side}", side.lower())
        glove = _ellipsoid(
            f"arm_hand_{side}",
            hand,
            (0.20, 0.18, 0.23),
            context.materials["leather_dark"],
            segments=8,
            rings=5,
        )
        _register(context, glove, "arms", f"hand.{side}", side.lower())

    for index, (location, scale) in enumerate(
        (
            ((0.76, 0.0, 3.50), (0.47, 0.44, 0.34)),
            ((0.87, -0.02, 3.39), (0.43, 0.40, 0.28)),
            ((0.95, -0.03, 3.29), (0.35, 0.35, 0.23)),
        ),
        start=1,
    ):
        pauldron = _ellipsoid(
            f"pauldron_left_plate_{index:02d}",
            location,
            scale,
            context.materials["silver"],
            segments=10,
            rings=6,
        )
        _register(context, pauldron, "pauldron_left_large", "upper_arm.L", "left")

    right_pauldron = _ellipsoid(
        "pauldron_right_small",
        (-0.76, 0.0, 3.43),
        (0.37, 0.37, 0.28),
        context.materials["dark_steel"],
        segments=10,
        rings=6,
    )
    _register(
        context,
        right_pauldron,
        "pauldron_right_small",
        "upper_arm.R",
        "right",
    )


def _build_legs(context: BuildContext) -> None:
    for side, sign in (("L", 1.0), ("R", -1.0)):
        hip = (0.34 * sign, 0.0, 2.03)
        knee = (0.34 * sign, -0.01, 1.18)
        ankle = (0.34 * sign, -0.04, 0.48)
        thigh = _cylinder_between(
            f"leg_thigh_{side}",
            hip,
            knee,
            0.25,
            8,
            context.materials["leather_dark"],
        )
        _register(context, thigh, "legs", f"thigh.{side}", side.lower())
        shin_material = context.materials["silver"] if side == "L" else context.materials["boots"]
        shin = _cylinder_between(
            f"leg_shin_{side}",
            knee,
            ankle,
            0.23,
            8,
            shin_material,
        )
        _register(context, shin, "legs", f"shin.{side}", side.lower())
        knee_pad = _ellipsoid(
            f"leg_knee_{side}",
            knee,
            (0.28, 0.24, 0.19),
            context.materials["silver"] if side == "L" else context.materials["dark_steel"],
            segments=8,
            rings=5,
        )
        _register(context, knee_pad, "legs", f"shin.{side}", side.lower())
        boot = _box(
            f"boot_{side}",
            (0.34 * sign, -0.18, 0.22),
            (0.44, 0.72, 0.40),
            context.materials["boots"],
            0.07,
        )
        _register(context, boot, "boots", f"foot.{side}", side.lower())


def _build_accessories(context: BuildContext) -> None:
    cloth_specs = (
        ("L", 0.42, "cloth.L"),
        ("C", 0.0, "cloth.C"),
        ("R", -0.42, "cloth.R"),
    )
    for side, x_position, bone_name in cloth_specs:
        cloth = _frustum(
            f"back_cloth_{side}",
            (x_position, 0.29, 1.55),
            radius_bottom=0.24,
            radius_top=0.34,
            depth=1.62,
            vertices=3,
            material=context.materials["scarf"],
            rotation=(0.0, 0.0, math.radians(180.0)),
        )
        _register(context, cloth, "back_cloth", bone_name, side.lower())

    scabbard = _cylinder_between(
        "sword_scabbard",
        (0.60, 0.16, 2.57),
        (0.93, 0.19, 0.76),
        0.11,
        8,
        context.materials["dark_steel"],
    )
    _register(context, scabbard, "sword_scabbard", "pelvis", "left")
    sword_grip = _cylinder_between(
        "sword_grip",
        (0.60, 0.16, 2.56),
        (0.52, 0.15, 2.98),
        0.09,
        8,
        context.materials["boots"],
    )
    _register(context, sword_grip, "sword_scabbard", "pelvis", "left")
    sword_guard = _box(
        "sword_guard",
        (0.55, 0.15, 2.64),
        (0.43, 0.12, 0.10),
        context.materials["silver"],
        0.02,
        rotation=(0.0, math.radians(-10.0), 0.0),
    )
    _register(context, sword_guard, "sword_scabbard", "pelvis", "left")

    pouch = _box(
        "pouch_right",
        (-0.68, -0.34, 2.02),
        (0.48, 0.30, 0.58),
        context.materials["leather_mid"],
        0.08,
    )
    _register(context, pouch, "pouch", "pelvis", "right")
    pouch_flap = _box(
        "pouch_right_flap",
        (-0.68, -0.51, 2.16),
        (0.46, 0.07, 0.20),
        context.materials["leather_dark"],
        0.03,
    )
    _register(context, pouch_flap, "pouch", "pelvis", "right")


def _create_rig(config: FactoryConfig, collection: bpy.types.Collection) -> bpy.types.Object:
    armature_data = bpy.data.armatures.new(f"{config.character_id}_rig")
    rig = bpy.data.objects.new(f"RIG_{config.character_id}", armature_data)
    collection.objects.link(rig)
    rig.show_in_front = True
    rig.rotation_mode = "XYZ"
    rig["character_id"] = config.character_id
    rig["physical_left_axis"] = "+X"
    rig["physical_right_axis"] = "-X"

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bone_specs = (
        ("root", (0.0, 0.0, 0.0), (0.0, 0.0, 0.35), None),
        ("pelvis", (0.0, 0.0, 1.75), (0.0, 0.0, 2.30), "root"),
        ("spine", (0.0, 0.0, 2.15), (0.0, 0.0, 3.02), "pelvis"),
        ("chest", (0.0, 0.0, 2.88), (0.0, 0.0, 3.62), "spine"),
        ("neck", (0.0, 0.0, 3.60), (0.0, 0.0, 3.98), "chest"),
        ("head", (0.0, 0.0, 3.92), (0.0, 0.0, 4.72), "neck"),
        ("upper_arm.L", (0.66, 0.0, 3.45), (0.96, -0.02, 2.79), "chest"),
        ("forearm.L", (0.96, -0.02, 2.79), (1.00, -0.15, 2.18), "upper_arm.L"),
        ("hand.L", (1.00, -0.15, 2.18), (1.00, -0.18, 1.91), "forearm.L"),
        ("upper_arm.R", (-0.66, 0.0, 3.45), (-0.96, -0.02, 2.79), "chest"),
        ("forearm.R", (-0.96, -0.02, 2.79), (-1.00, -0.15, 2.18), "upper_arm.R"),
        ("hand.R", (-1.00, -0.15, 2.18), (-1.00, -0.18, 1.91), "forearm.R"),
        ("thigh.L", (0.34, 0.0, 2.08), (0.34, -0.01, 1.18), "pelvis"),
        ("shin.L", (0.34, -0.01, 1.18), (0.34, -0.04, 0.48), "thigh.L"),
        ("foot.L", (0.34, -0.04, 0.48), (0.34, -0.44, 0.18), "shin.L"),
        ("thigh.R", (-0.34, 0.0, 2.08), (-0.34, -0.01, 1.18), "pelvis"),
        ("shin.R", (-0.34, -0.01, 1.18), (-0.34, -0.04, 0.48), "thigh.R"),
        ("foot.R", (-0.34, -0.04, 0.48), (-0.34, -0.44, 0.18), "shin.R"),
        ("cloth.L", (0.42, 0.21, 2.24), (0.42, 0.31, 0.75), "pelvis"),
        ("cloth.C", (0.0, 0.21, 2.24), (0.0, 0.32, 0.68), "pelvis"),
        ("cloth.R", (-0.42, 0.21, 2.24), (-0.42, 0.31, 0.75), "pelvis"),
    )
    edit_bones: dict[str, bpy.types.EditBone] = {}
    for bone_name, head, tail, parent_name in bone_specs:
        bone = armature_data.edit_bones.new(bone_name)
        bone.head = head
        bone.tail = tail
        bone.use_connect = False
        if parent_name:
            bone.parent = edit_bones[parent_name]
        edit_bones[bone_name] = bone
    bpy.ops.object.mode_set(mode="POSE")
    for pose_bone in rig.pose.bones:
        pose_bone.rotation_mode = "XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)
    return rig


def _create_actions(context: BuildContext) -> None:
    config = context.config
    idle_channels = {
        'pose.bones["pelvis"].location': {2: [(1, 0.0)]},
        'pose.bones["chest"].location': {2: [(1, 0.0)]},
        'pose.bones["thigh.L"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["thigh.R"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["shin.L"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["shin.R"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["upper_arm.L"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["upper_arm.R"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["cloth.L"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["cloth.C"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["cloth.R"].rotation_euler': {0: [(1, 0.0)]},
    }
    idle_action = _new_action(
        f"{config.character_id}_idle",
        context.rig,
        idle_channels,
        animation_id="idle",
        fps=int(config.animations["idle"]["fps"]),
    )

    left_thigh = (18.0, 8.0, -10.0, -18.0, -8.0, 10.0)
    right_thigh = tuple(-value for value in left_thigh)
    left_shin = (-4.0, -10.0, -16.0, 6.0, 22.0, 10.0)
    right_shin = tuple(left_shin[(index + 3) % 6] for index in range(6))
    left_arm = tuple(-value * 0.42 for value in left_thigh)
    right_arm = tuple(-value for value in left_arm)
    bob = (0.0, -0.045, 0.01, 0.0, -0.045, 0.01)
    cloth_swing = (-3.0, -1.0, 2.0, 3.0, 1.0, -2.0)
    frames = tuple(int(value) for value in config.animations["walk_down"]["frames"])

    walk_channels = {
        'pose.bones["chest"].location': {2: _pairs(frames, bob)},
        'pose.bones["thigh.L"].rotation_euler': {0: _degree_pairs(frames, left_thigh)},
        'pose.bones["thigh.R"].rotation_euler': {0: _degree_pairs(frames, right_thigh)},
        'pose.bones["shin.L"].rotation_euler': {0: _degree_pairs(frames, left_shin)},
        'pose.bones["shin.R"].rotation_euler': {0: _degree_pairs(frames, right_shin)},
        'pose.bones["upper_arm.L"].rotation_euler': {0: _degree_pairs(frames, left_arm)},
        'pose.bones["upper_arm.R"].rotation_euler': {0: _degree_pairs(frames, right_arm)},
        'pose.bones["cloth.L"].rotation_euler': {0: _degree_pairs(frames, cloth_swing)},
        'pose.bones["cloth.C"].rotation_euler': {
            0: _degree_pairs(frames, tuple(value * 0.55 for value in cloth_swing))
        },
        'pose.bones["cloth.R"].rotation_euler': {
            0: _degree_pairs(frames, tuple(-value for value in cloth_swing))
        },
    }
    walk_action = _new_action(
        f"{config.character_id}_walk_down",
        context.rig,
        walk_channels,
        animation_id="walk_down",
        fps=int(config.animations["walk_down"]["fps"]),
    )
    idle_action.use_fake_user = True
    walk_action.use_fake_user = True
    _assign_action(context.rig, idle_action)


def _new_action(
    name: str,
    rig: bpy.types.Object,
    channels: dict[str, dict[int, list[tuple[int, float]]]],
    animation_id: str,
    fps: int,
) -> bpy.types.Action:
    action = bpy.data.actions.new(name)
    action["animation_id"] = animation_id
    action["fps"] = fps
    action["loop"] = True
    slot = action.slots.new(id_type="OBJECT", name=rig.name)
    layer = action.layers.new("Base")
    strip = layer.strips.new(type="KEYFRAME")
    channelbag = strip.channelbag(slot, ensure=True)
    for data_path, indexed_values in channels.items():
        for index, values in indexed_values.items():
            fcurve = channelbag.fcurves.new(data_path, index=index)
            points = fcurve.keyframe_points
            points.add(len(values))
            for point, (frame, value) in zip(points, values):
                point.co = (float(frame), float(value))
                point.interpolation = "CONSTANT"
    return action


def _create_camera_and_lights(
    context: BuildContext,
    collection: bpy.types.Collection,
) -> None:
    config = context.config
    camera_data = bpy.data.cameras.new("CAM_gameplay_ortho")
    camera = bpy.data.objects.new("CAM_gameplay_ortho", camera_data)
    collection.objects.link(camera)
    distance = float(config.camera["horizontal_distance_units"])
    elevation = math.radians(float(config.camera["elevation_degrees"]))
    target_height = float(config.camera["target_height_units"])
    camera.location = (0.0, -distance, target_height + math.tan(elevation) * distance)
    target = Vector((0.0, 0.0, target_height))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = float(config.camera["orthographic_scale"])
    camera_data.lens = 50.0
    camera["elevation_degrees"] = float(config.camera["elevation_degrees"])
    camera["projection_contract"] = "top_down_3_4"
    bpy.context.scene.camera = camera

    key = _new_light("LGT_key", "AREA", (-4.5, -6.0, 11.5), 760.0, 5.0, collection)
    key.rotation_euler = _look_at_rotation(key.location, (0.0, 0.0, 2.5))
    fill = _new_light("LGT_fill", "AREA", (5.0, -2.0, 7.5), 280.0, 4.0, collection)
    fill.rotation_euler = _look_at_rotation(fill.location, (0.0, 0.0, 2.7))
    rim = _new_light("LGT_rim", "AREA", (0.0, 5.0, 9.0), 420.0, 3.0, collection)
    rim.rotation_euler = _look_at_rotation(rim.location, (0.0, 0.0, 2.8))


def _configure_render(scene: bpy.types.Scene, config: FactoryConfig) -> None:
    engine_items = scene.render.bl_rna.properties["engine"].enum_items
    engines = {item.identifier for item in engine_items}
    if "BLENDER_EEVEE_NEXT" in engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in engines:
        scene.render.engine = "BLENDER_EEVEE"
    elif "BLENDER_WORKBENCH" in engines:
        scene.render.engine = "BLENDER_WORKBENCH"
    else:
        raise RuntimeError(f"Не найден поддерживаемый realtime render engine: {sorted(engines)}")

    scene.render.resolution_x = int(config.camera["render_width"])
    scene.render.resolution_y = int(config.camera["render_height"])
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = bool(config.camera["transparent_background"])
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    scene.render.use_file_extension = True
    scene.render.fps = int(config.animations["walk_down"]["fps"])
    scene.frame_start = 1
    scene.frame_end = 6
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    world = bpy.data.worlds.new("WORLD_sprite_factory")
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.015, 0.012, 0.010, 1.0)
        background.inputs["Strength"].default_value = 0.28
    scene.world = world


def _render_frame(
    context: BuildContext,
    animation_id: str,
    direction: str,
    frame_number: int,
    raw_dir: Path,
    frame_dir: Path,
    output_name: str,
    fixed_scale: float | None,
    fixed_center_x: float | None,
) -> tuple[FrameArtifact, FramingCalibration]:
    scene = bpy.context.scene
    scene.frame_set(frame_number)
    bpy.context.view_layer.update()
    raw_path = raw_dir / output_name.replace(".png", "_raw.png")
    output_path = frame_dir / output_name
    scene.render.filepath = str(raw_path)
    bpy.ops.render.render(write_still=True)
    width, height, calibration = _normalize_render(
        raw_path,
        output_path,
        context.config,
        fixed_scale=fixed_scale,
        fixed_center_x=fixed_center_x,
    )
    artifact = FrameArtifact(
        animation_id=animation_id,
        direction=direction,
        frame_number=frame_number,
        output_path=output_path,
        sprite_width=width,
        sprite_height=height,
        baseline_y=context.config.technical.baseline_y,
    )
    return artifact, calibration


def _normalize_render(
    raw_path: Path,
    output_path: Path,
    config: FactoryConfig,
    fixed_scale: float | None,
    fixed_center_x: float | None,
) -> tuple[int, int, FramingCalibration]:
    source = bpy.data.images.load(str(raw_path), check_existing=False)
    try:
        source_width, source_height = (int(value) for value in source.size)
        source_pixels = tuple(source.pixels[:])
        alpha_threshold = max(0.08, config.technical.alpha_threshold / 255.0)
        bbox = alpha_bbox(source_pixels, source_width, source_height, alpha_threshold)
        if bbox is None:
            raise RuntimeError(f"Render не содержит видимого силуэта: {raw_path}")
        min_x, min_y, max_x, max_y = bbox
        bbox_width = max_x - min_x + 1
        bbox_height = max_y - min_y + 1
        scale = fixed_scale or (
            config.technical.pilot_sprite_height / max(1, bbox_height)
        )
        if scale <= 0.0:
            raise RuntimeError("Некорректный коэффициент framing calibration")
        source_center_x = (
            fixed_center_x
            if fixed_center_x is not None
            else (min_x + max_x + 1) * 0.5
        )
        calibration = FramingCalibration(
            scale=scale,
            source_center_x=source_center_x,
        )
        canvas_width = config.technical.canvas_width
        canvas_height = config.technical.canvas_height
        target_min_y = canvas_height - 1 - config.technical.baseline_y
        target_center_x = canvas_width * 0.5

        palette = [_hex_to_linear_rgb(value) for value in config.quantization_palette]
        output_pixels = [0.0] * (canvas_width * canvas_height * 4)
        for target_y in range(canvas_height):
            source_y = round(
                min_y + (target_y - target_min_y + 0.5) / scale - 0.5
            )
            if not 0 <= source_y < source_height:
                continue
            for target_x in range(canvas_width):
                source_x = round(
                    source_center_x
                    + (target_x - target_center_x + 0.5) / scale
                    - 0.5
                )
                if not 0 <= source_x < source_width:
                    continue
                source_index = (source_y * source_width + source_x) * 4
                alpha = source_pixels[source_index + 3]
                if alpha < 0.5:
                    continue
                rgb = (
                    source_pixels[source_index],
                    source_pixels[source_index + 1],
                    source_pixels[source_index + 2],
                )
                quantized = min(palette, key=lambda candidate: _color_distance(rgb, candidate))
                destination_index = (target_y * canvas_width + target_x) * 4
                output_pixels[destination_index] = quantized[0]
                output_pixels[destination_index + 1] = quantized[1]
                output_pixels[destination_index + 2] = quantized[2]
                output_pixels[destination_index + 3] = 1.0

        try:
            output_pixels, normalized_bbox = anchor_rgba_to_baseline(
                output_pixels,
                canvas_width,
                canvas_height,
                config.technical.baseline_y,
                0.5,
            )
        except ValueError as exc:
            raise RuntimeError(
                f"Не удалось привязать силуэт к baseline: {raw_path}: {exc}"
            ) from exc
        normalized_min_x, normalized_min_y, normalized_max_x, normalized_max_y = (
            normalized_bbox
        )
        normalized_width = normalized_max_x - normalized_min_x + 1
        normalized_height = normalized_max_y - normalized_min_y + 1
        normalized_baseline_y = canvas_height - 1 - normalized_min_y
        if normalized_baseline_y != config.technical.baseline_y:
            raise RuntimeError(
                f"Baseline drift: {normalized_baseline_y} вместо "
                f"{config.technical.baseline_y}"
            )
        if normalized_width > config.technical.max_sprite_width:
            raise RuntimeError(
                f"Силуэт шириной {normalized_width}px превышает "
                f"{config.technical.max_sprite_width}px"
            )

        image = bpy.data.images.new(
            f"normalized_{output_path.stem}",
            width=canvas_width,
            height=canvas_height,
            alpha=True,
            float_buffer=False,
        )
        try:
            image.pixels[:] = output_pixels
            image.file_format = "PNG"
            image.filepath_raw = str(output_path)
            image.save()
        finally:
            bpy.data.images.remove(image)
        return normalized_width, normalized_height, calibration
    finally:
        bpy.data.images.remove(source)


def _write_contact_sheet(
    config: FactoryConfig,
    artifacts: list[FrameArtifact],
    output_path: Path,
) -> Path:
    columns = 6
    rows = 3
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = columns * tile_width
    height = rows * tile_height
    background = _hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    idle_by_direction = {
        item.direction: item
        for item in artifacts
        if item.animation_id == "idle"
    }
    idle_directions = ("down", "left", "right", "up")
    missing_idle = [
        direction for direction in idle_directions if direction not in idle_by_direction
    ]
    if missing_idle:
        raise RuntimeError(
            f"Contact sheet не получил idle-направления: {missing_idle}"
        )
    proxy_idle_paths = tuple(
        idle_by_direction[direction].output_path for direction in idle_directions
    )
    approved_idle_paths = tuple(
        config.idle_reference_root
        / f"{config.character_id}_idle_{direction}.png"
        for direction in idle_directions
    )
    walk_paths = tuple(
        item.output_path
        for item in sorted(
            (
                artifact
                for artifact in artifacts
                if artifact.animation_id == "walk_down"
            ),
            key=lambda artifact: artifact.frame_number,
        )
    )
    rows_data = (proxy_idle_paths, approved_idle_paths, walk_paths)
    for row_index, row_paths in enumerate(rows_data):
        for column_index, image_path in enumerate(row_paths):
            image = bpy.data.images.load(str(image_path), check_existing=False)
            try:
                tile_pixels = tuple(image.pixels[:])
                destination_row = rows - 1 - row_index
                _copy_tile(
                    pixels,
                    width,
                    tile_pixels,
                    tile_width,
                    tile_height,
                    column_index * tile_width,
                    destination_row * tile_height,
                )
            finally:
                bpy.data.images.remove(image)

    contact_sheet = bpy.data.images.new(
        "human_warrior_m01_pilot_contact_sheet",
        width=width,
        height=height,
        alpha=True,
        float_buffer=False,
    )
    try:
        contact_sheet.pixels[:] = pixels
        contact_sheet.file_format = "PNG"
        contact_sheet.filepath_raw = str(output_path)
        contact_sheet.save()
    finally:
        bpy.data.images.remove(contact_sheet)
    return output_path


def _write_run_manifest(
    context: BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    config = context.config
    payload = {
        "schema_version": 1,
        "pipeline_id": "blender_sprite_factory",
        "stage": config.stage,
        "character_id": config.character_id,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "blender_version": bpy.app.version_string,
        "factory_config": config.relative_to_repo(config.manifest_path),
        "factory_config_sha256": hashlib.sha256(config.manifest_path.read_bytes()).hexdigest(),
        "source_blend": blend_path.relative_to(run_dir).as_posix(),
        "contact_sheet": (
            contact_sheet.relative_to(run_dir).as_posix() if contact_sheet else None
        ),
        "contact_sheet_review": {
            "background_color": CONTACT_SHEET_BACKGROUND_HEX,
            "rows_top_to_bottom": [
                "proxy_idle",
                "approved_idle_reference",
                "proxy_walk_down",
            ],
        },
        "technical_contract": {
            "canvas_width": config.technical.canvas_width,
            "canvas_height": config.technical.canvas_height,
            "sprite_height": config.technical.pilot_sprite_height,
            "max_sprite_width": config.technical.max_sprite_width,
            "baseline_y": config.technical.baseline_y,
            "camera_elevation_degrees": config.camera["elevation_degrees"],
            "camera_projection": config.camera["projection"],
            "binary_alpha": True,
            "mirrored_directions": False,
        },
        "physical_sides": config.physical_sides,
        "materials_status": config.materials_status,
        "frames": [
            {
                "animation_id": artifact.animation_id,
                "direction": artifact.direction,
                "frame_number": artifact.frame_number,
                "path": artifact.output_path.relative_to(run_dir).as_posix(),
                "sprite_width": artifact.sprite_width,
                "sprite_height": artifact.sprite_height,
                "baseline_y": artifact.baseline_y,
            }
            for artifact in artifacts
        ],
    }
    manifest_path = run_dir / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _create_material(slot: MaterialSlot) -> bpy.types.Material:
    material = bpy.data.materials.new(f"MAT_{slot.slot_id}")
    material.diffuse_color = (*_hex_rgb_normalized(slot.base_color), 1.0)
    material.use_nodes = True
    material["material_slot_id"] = slot.slot_id
    material["texture_source"] = str(slot.texture_path)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(slot.texture_path), check_existing=True)
    texture.interpolation = "Closest"
    texture.extension = "REPEAT"
    shader.inputs["Base Color"].default_value = (*_hex_rgb_normalized(slot.base_color), 1.0)
    shader.inputs["Roughness"].default_value = slot.roughness
    if slot.slot_id in {"silver", "dark_steel", "chainmail"}:
        shader.inputs["Metallic"].default_value = 0.68
    else:
        shader.inputs["Metallic"].default_value = 0.0
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def _register(
    context: BuildContext,
    obj: bpy.types.Object,
    module_id: str,
    bone_name: str,
    physical_side: str | None = None,
) -> bpy.types.Object:
    if module_id not in context.module_collections:
        raise KeyError(f"Неизвестный module_id: {module_id}")
    _move_to_collection(obj, context.module_collections[module_id])
    _parent_to_bone(obj, context.rig, bone_name)
    obj[MODULE_PROPERTY] = module_id
    if physical_side:
        obj[SIDE_PROPERTY] = physical_side
    if obj.data and getattr(obj.data, "materials", None) and obj.data.materials:
        material = obj.data.materials[0]
        obj[MATERIAL_PROPERTY] = str(material.get("material_slot_id", ""))
    obj["factory_generated"] = True
    return obj


def _box(
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    material: bpy.types.Material,
    bevel: float,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        modifier = obj.modifiers.new("pixel_bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
    _assign_material(obj, material)
    return obj


def _ellipsoid(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material: bpy.types.Material,
    segments: int,
    rings: int,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        radius=1.0,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _flat_shade(obj)
    _assign_material(obj, material)
    return obj


def _frustum(
    name: str,
    location: tuple[float, float, float],
    radius_bottom: float,
    radius_top: float,
    depth: float,
    vertices: int,
    material: bpy.types.Material,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius_bottom,
        radius2=radius_top,
        depth=depth,
        end_fill_type="NGON",
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    _flat_shade(obj)
    _assign_material(obj, material)
    return obj


def _torus(
    name: str,
    location: tuple[float, float, float],
    major_radius: float,
    minor_radius: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_segments=12,
        minor_segments=4,
        location=location,
        major_radius=major_radius,
        minor_radius=minor_radius,
    )
    obj = bpy.context.object
    obj.name = name
    _flat_shade(obj)
    _assign_material(obj, material)
    return obj


def _cylinder_between(
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    vertices: int,
    material: bpy.types.Material,
) -> bpy.types.Object:
    start_vector = Vector(start)
    end_vector = Vector(end)
    direction = end_vector - start_vector
    midpoint = (start_vector + end_vector) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=direction.length,
        end_fill_type="NGON",
        location=midpoint,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    _flat_shade(obj)
    _assign_material(obj, material)
    return obj


def _new_light(
    name: str,
    light_type: str,
    location: tuple[float, float, float],
    energy: float,
    size: float,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    light_data = bpy.data.lights.new(name, type=light_type)
    light_data.energy = energy
    light_data.shape = "DISK"
    light_data.size = size
    light = bpy.data.objects.new(name, light_data)
    light.location = location
    collection.objects.link(light)
    return light


def _validate_built_scene(context: BuildContext) -> None:
    actual_bones = set(context.rig.data.bones.keys())
    missing_bones = sorted(set(context.config.required_bones).difference(actual_bones))
    if missing_bones:
        raise RuntimeError(f"Сцена не создала обязательные кости: {missing_bones}")
    actual_modules = {
        str(obj.get(MODULE_PROPERTY))
        for obj in bpy.data.objects
        if obj.get(MODULE_PROPERTY)
    }
    missing_modules = sorted(set(context.config.required_modules).difference(actual_modules))
    if missing_modules:
        raise RuntimeError(f"Сцена не создала обязательные модули: {missing_modules}")
    _assert_module_side("pauldron_left_large", "left")
    _assert_module_side("pauldron_right_small", "right")
    _assert_module_side("sword_scabbard", "left")
    _assert_module_side("pouch", "right")
    expected_actions = {
        f"{context.config.character_id}_idle",
        f"{context.config.character_id}_walk_down",
    }
    missing_actions = sorted(expected_actions.difference(bpy.data.actions.keys()))
    if missing_actions:
        raise RuntimeError(f"Сцена не создала обязательные Actions: {missing_actions}")


def _assert_module_side(module_id: str, expected_side: str) -> None:
    objects = [
        obj
        for obj in bpy.data.objects
        if obj.get(MODULE_PROPERTY) == module_id
    ]
    if not objects:
        raise RuntimeError(f"Модуль {module_id} пуст")
    wrong = [obj.name for obj in objects if obj.get(SIDE_PROPERTY) != expected_side]
    if wrong:
        raise RuntimeError(
            f"Модуль {module_id} потерял физическую сторону {expected_side}: {wrong}"
        )


def _assign_action(rig: bpy.types.Object, action: bpy.types.Action) -> None:
    animation_data = rig.animation_data_create()
    animation_data.action = action
    if action.slots:
        animation_data.action_slot = action.slots[0]


def _set_idle_down(context: BuildContext) -> None:
    _assign_action(
        context.rig,
        bpy.data.actions[f"{context.config.character_id}_idle"],
    )
    context.rig.rotation_euler = (
        0.0,
        0.0,
        math.radians(context.config.directions["down"]),
    )
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()


def _parent_to_bone(obj: bpy.types.Object, rig: bpy.types.Object, bone_name: str) -> None:
    if bone_name not in rig.data.bones:
        raise KeyError(f"В rig отсутствует кость {bone_name}")
    world_matrix = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_world = world_matrix


def _new_collection(
    name: str,
    parent: bpy.types.Collection | None = None,
) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(collection)
    else:
        parent.children.link(collection)
    return collection


def _move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for owner in tuple(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def _assign_material(obj: bpy.types.Object, material: bpy.types.Material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(material)


def _flat_shade(obj: bpy.types.Object) -> None:
    for polygon in obj.data.polygons:
        polygon.use_smooth = False


def _clear_scene() -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in tuple(bpy.data.collections):
        bpy.data.collections.remove(collection)
    for data_collection in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.armatures,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.materials,
        bpy.data.actions,
    ):
        for datablock in tuple(data_collection):
            data_collection.remove(datablock)


def _copy_tile(
    destination: list[float],
    destination_width: int,
    source: tuple[float, ...],
    source_width: int,
    source_height: int,
    offset_x: int,
    offset_y: int,
) -> None:
    for y in range(source_height):
        for x in range(source_width):
            source_index = (y * source_width + x) * 4
            destination_index = (
                (offset_y + y) * destination_width + offset_x + x
            ) * 4
            alpha = source[source_index + 3]
            if alpha <= 0.0:
                continue
            destination[destination_index : destination_index + 4] = source[
                source_index : source_index + 4
            ]


def _look_at_rotation(
    source: Iterable[float],
    target: Iterable[float],
) -> Any:
    direction = Vector(target) - Vector(source)
    return direction.to_track_quat("-Z", "Y").to_euler()


def _degree_pairs(
    frames: tuple[int, ...],
    degrees: tuple[float, ...],
) -> list[tuple[int, float]]:
    return _pairs(frames, tuple(math.radians(value) for value in degrees))


def _pairs(
    frames: tuple[int, ...],
    values: tuple[float, ...],
) -> list[tuple[int, float]]:
    if len(frames) != len(values):
        raise ValueError("Число кадров и значений Action не совпадает")
    return list(zip(frames, values))


def _hex_rgb_normalized(value: str) -> tuple[float, float, float]:
    raw = value.lstrip("#")
    return (
        int(raw[0:2], 16) / 255.0,
        int(raw[2:4], 16) / 255.0,
        int(raw[4:6], 16) / 255.0,
    )


def _hex_to_linear_rgb(value: str) -> tuple[float, float, float]:
    return tuple(_srgb_to_linear(component) for component in _hex_rgb_normalized(value))


def _srgb_to_linear(value: float) -> float:
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _color_distance(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
) -> float:
    return (
        (first[0] - second[0]) ** 2 * 0.30
        + (first[1] - second[1]) ** 2 * 0.59
        + (first[2] - second[2]) ** 2 * 0.11
    )


def _resolve_cli_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _assert_within(root: Path, path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} выходит за разрешённый каталог: {path}") from exc


def _script_arguments() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def _parse_args(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and render the Blender sprite pilot.")
    parser.add_argument(
        "--repo-root",
        default=str(SCRIPT_DIR.parents[1]),
    )
    parser.add_argument(
        "--config",
        default="tools/blender_sprite_factory/configs/human_warrior_m01.json",
    )
    parser.add_argument("--run-id")
    parser.add_argument("--mode", choices=("build", "all"), default="all")
    return parser.parse_args(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
