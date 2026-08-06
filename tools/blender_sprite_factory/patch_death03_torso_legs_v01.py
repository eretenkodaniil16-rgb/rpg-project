from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "tools/blender_sprite_factory/death_down_keyposes_profile_v01.py"
BUILDER = ROOT / "tools/blender_sprite_factory/death_down_keyposes_builder_v01.py"
ADAPTER = ROOT / "tools/blender_sprite_factory/blender_sprite_factory_death_down_keyposes_v01.py"
TEST = ROOT / "tools/blender_sprite_factory/tests/test_death_down_keyposes_v01.py"
DOC = ROOT / "docs/HUMAN_WARRIOR_DEATH_DOWN_KEYPOSES_V01.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"{label}: expected one regex match, found {count}")
    return updated


def patch_profile() -> None:
    text = PROFILE.read_text(encoding="utf-8")
    death_03 = '''DEATH_03_BASE_POSES_V01 = (
    DeathDownPoseDeltaV01(frame=1, phase="guard"),
    DeathDownPoseDeltaV01(
        frame=2,
        phase="balance_break",
        pelvis_x=-0.010,
        pelvis_y=0.015,
        pelvis_z=-0.035,
        pelvis_roll_z_degrees=-4.0,
        spine_pitch_x_degrees=8.0,
        chest_yaw_z_degrees=-10.0,
        head_pitch_x_degrees=12.0,
        head_yaw_z_degrees=5.0,
        thigh_left_x_degrees=-8.0,
        thigh_right_x_degrees=-11.0,
        shin_left_x_degrees=12.0,
        shin_right_x_degrees=15.0,
        upper_arm_left_x_degrees=-7.0,
        upper_arm_left_y_degrees=6.0,
        upper_arm_left_z_degrees=-22.0,
        forearm_left_x_degrees=13.0,
        forearm_left_z_degrees=-12.0,
        upper_arm_right_x_degrees=-5.0,
        upper_arm_right_y_degrees=-6.0,
        upper_arm_right_z_degrees=24.0,
        forearm_right_x_degrees=15.0,
        forearm_right_z_degrees=14.0,
        cloth_left_x_degrees=3.0,
        cloth_center_x_degrees=2.0,
        cloth_right_x_degrees=4.0,
    ),
    DeathDownPoseDeltaV01(
        frame=3,
        phase="knee_drop",
        pelvis_x=-0.080,
        pelvis_y=0.040,
        pelvis_z=-0.220,
        pelvis_roll_z_degrees=-18.0,
        spine_pitch_x_degrees=12.0,
        chest_yaw_z_degrees=-22.0,
        head_pitch_x_degrees=18.0,
        head_yaw_z_degrees=10.0,
        thigh_left_x_degrees=-38.0,
        thigh_right_x_degrees=-44.0,
        shin_left_x_degrees=56.0,
        shin_right_x_degrees=63.0,
        foot_left_x_degrees=-15.0,
        foot_right_x_degrees=-18.0,
        upper_arm_left_x_degrees=-18.0,
        upper_arm_left_y_degrees=13.0,
        upper_arm_left_z_degrees=-47.0,
        forearm_left_x_degrees=30.0,
        forearm_left_z_degrees=-27.0,
        hand_left_x_degrees=14.0,
        upper_arm_right_x_degrees=-15.0,
        upper_arm_right_y_degrees=-13.0,
        upper_arm_right_z_degrees=49.0,
        forearm_right_x_degrees=32.0,
        forearm_right_z_degrees=29.0,
        hand_right_x_degrees=16.0,
        cloth_left_x_degrees=10.0,
        cloth_center_x_degrees=8.0,
        cloth_right_x_degrees=12.0,
    ),
    DeathDownPoseDeltaV01(
        frame=4,
        phase="ground_impact",
        pelvis_x=-0.200,
        pelvis_y=0.080,
        pelvis_z=-0.520,
        pelvis_roll_z_degrees=-48.0,
        spine_pitch_x_degrees=18.0,
        chest_yaw_z_degrees=-34.0,
        head_pitch_x_degrees=24.0,
        head_yaw_z_degrees=16.0,
        thigh_left_x_degrees=-62.0,
        thigh_right_x_degrees=-53.0,
        shin_left_x_degrees=82.0,
        shin_right_x_degrees=73.0,
        foot_left_x_degrees=-31.0,
        foot_right_x_degrees=-25.0,
        upper_arm_left_x_degrees=-34.0,
        upper_arm_left_y_degrees=22.0,
        upper_arm_left_z_degrees=-69.0,
        forearm_left_x_degrees=47.0,
        forearm_left_z_degrees=-42.0,
        hand_left_x_degrees=24.0,
        hand_left_z_degrees=-16.0,
        upper_arm_right_x_degrees=-28.0,
        upper_arm_right_y_degrees=-21.0,
        upper_arm_right_z_degrees=72.0,
        forearm_right_x_degrees=49.0,
        forearm_right_z_degrees=44.0,
        hand_right_x_degrees=26.0,
        hand_right_z_degrees=17.0,
        cloth_left_x_degrees=22.0,
        cloth_center_x_degrees=17.0,
        cloth_right_x_degrees=25.0,
    ),
    DeathDownPoseDeltaV01(
        frame=5,
        phase="final",
        pelvis_x=-0.260,
        pelvis_y=0.100,
        pelvis_z=-0.640,
        pelvis_roll_z_degrees=-67.0,
        spine_pitch_x_degrees=24.0,
        chest_yaw_z_degrees=-42.0,
        head_pitch_x_degrees=31.0,
        head_yaw_z_degrees=21.0,
        thigh_left_x_degrees=-78.0,
        thigh_right_x_degrees=-69.0,
        shin_left_x_degrees=89.0,
        shin_right_x_degrees=84.0,
        foot_left_x_degrees=-39.0,
        foot_right_x_degrees=-34.0,
        upper_arm_left_x_degrees=-45.0,
        upper_arm_left_y_degrees=28.0,
        upper_arm_left_z_degrees=-81.0,
        forearm_left_x_degrees=58.0,
        forearm_left_z_degrees=-52.0,
        hand_left_x_degrees=31.0,
        hand_left_z_degrees=-22.0,
        upper_arm_right_x_degrees=-39.0,
        upper_arm_right_y_degrees=-27.0,
        upper_arm_right_z_degrees=84.0,
        forearm_right_x_degrees=61.0,
        forearm_right_z_degrees=55.0,
        hand_right_x_degrees=34.0,
        hand_right_z_degrees=23.0,
        cloth_left_x_degrees=31.0,
        cloth_center_x_degrees=24.0,
        cloth_right_x_degrees=35.0,
    ),
)
'''
    text = regex_once(
        text,
        r"DEATH_03_BASE_POSES_V01 = \(\n.*?\n\)\n\n\n(?=HUMAN_WARRIOR_M01_DEATH_DOWN_KEYPOSES_V01)",
        death_03 + "\n\n",
        "death_03 pose block",
    )
    text = replace_once(
        text,
        'revision="death_03_base_down_keyposes_v01_pass01",',
        'revision="death_03_base_down_keyposes_v01_pass02_waist_separation",',
        "death_03 revision",
    )
    text = replace_once(
        text,
        'fall_side="character_left_back_spiral",',
        'fall_side="torso_right_legs_left_split",',
        "death_03 fall side",
    )
    text = replace_once(
        text,
        'gore_mode="left_forearm_detachment",\n        detached_part_id="left_forearm_and_hand",',
        'gore_mode="waist_torso_legs_separation",\n        detached_part_id="upper_torso_and_lower_body",',
        "death_03 gore identity",
    )
    text = replace_once(
        text,
        '''    if profile.gore_mode == "left_forearm_detachment":
        if profile.detached_part_id != "left_forearm_and_hand":
            raise ValueError("death_03 detached part contract drifted")
        if profile.detachment_frame not in profile.frame_order:
            raise ValueError("death_03 detachment frame is invalid")
''',
        '''    if profile.gore_mode == "waist_torso_legs_separation":
        if profile.detached_part_id != "upper_torso_and_lower_body":
            raise ValueError("death_03 torso/legs contract drifted")
        if profile.detachment_frame not in profile.frame_order:
            raise ValueError("death_03 separation frame is invalid")
''',
        "death_03 profile validation",
    )
    PROFILE.write_text(text, encoding="utf-8")


def patch_builder() -> None:
    text = BUILDER.read_text(encoding="utf-8")
    replacement = '''_GORE_UPPER_CUT_CAP = "death03_upper_waist_cut_cap"
_GORE_LOWER_CUT_CAP = "death03_lower_waist_cut_cap"
_GORE_UPPER_BODY_BONES = frozenset(
    {
        "spine",
        "chest",
        "neck",
        "head",
        "upper_arm.L",
        "upper_arm.R",
        "forearm.L",
        "forearm.R",
        "hand.L",
        "hand.R",
    }
)


def _set_hidden(obj: factory.bpy.types.Object, hidden: bool) -> None:
    obj.hide_render = hidden
    obj.hide_viewport = hidden


def _create_gore_modules_v01(context: factory.BuildContext) -> None:
    required_names = (_GORE_UPPER_CUT_CAP, _GORE_LOWER_CUT_CAP)
    if any(factory.bpy.data.objects.get(name) is not None for name in required_names):
        raise RuntimeError("death_03 waist gore modules already exist")

    upper_cap = factory._ellipsoid(
        _GORE_UPPER_CUT_CAP,
        (0.0, -0.01, 2.38),
        (0.30, 0.22, 0.095),
        context.materials["scarf"],
        segments=10,
        rings=5,
    )
    factory._register(context, upper_cap, "torso_armor", "spine")
    upper_cap["death_gore_module"] = True
    upper_cap["gore_role"] = "upper_torso_cut_surface"
    upper_cap["detached_part_id"] = "upper_torso_and_lower_body"
    _set_hidden(upper_cap, True)

    lower_cap = factory._ellipsoid(
        _GORE_LOWER_CUT_CAP,
        (0.0, -0.01, 2.31),
        (0.32, 0.23, 0.10),
        context.materials["scarf"],
        segments=10,
        rings=5,
    )
    factory._register(context, lower_cap, "torso_armor", "pelvis")
    lower_cap["death_gore_module"] = True
    lower_cap["gore_role"] = "lower_body_cut_surface"
    lower_cap["detached_part_id"] = "upper_torso_and_lower_body"
    _set_hidden(lower_cap, True)
'''
    text = regex_once(
        text,
        r'_GORE_ORIGINAL_FOREARM = .*?\n\n\n(?=def create_death_down_keypose_actions_v01)',
        replacement + "\n\n\n",
        "builder gore module block",
    )
    BUILDER.write_text(text, encoding="utf-8")


def patch_adapter() -> None:
    text = ADAPTER.read_text(encoding="utf-8")
    text = regex_once(
        text,
        r'from death_down_keyposes_builder_v01 import \(\n.*?\n\)\n',
        '''from death_down_keyposes_builder_v01 import (
    _GORE_LOWER_CUT_CAP,
    _GORE_UPPER_BODY_BONES,
    _GORE_UPPER_CUT_CAP,
    create_death_down_keypose_actions_v01,
)
''',
        "adapter builder imports",
    )
    gore_helpers = '''def _reset_gore_state() -> None:
    for name in (_GORE_UPPER_CUT_CAP, _GORE_LOWER_CUT_CAP):
        _set_hidden(_required_object(name), True)


def _apply_gore_state(profile: object, frame_number: int) -> None:
    _reset_gore_state()
    if profile.gore_mode != "waist_torso_legs_separation":
        return
    if profile.detachment_frame is None or frame_number < profile.detachment_frame:
        return
    _set_hidden(_required_object(_GORE_UPPER_CUT_CAP), False)
    _set_hidden(_required_object(_GORE_LOWER_CUT_CAP), False)


def _upper_body_offset(frame_number: int) -> tuple[float, float, float]:
    if frame_number == 4:
        return (0.58, -0.12, 0.10)
    if frame_number == 5:
        return (0.86, -0.18, 0.04)
    return (0.0, 0.0, 0.0)


def _detach_upper_body(
    context: factory.BuildContext,
    frame_number: int,
) -> tuple[tuple[object, object, str, str, object], ...]:
    offset = factory.Vector(_upper_body_offset(frame_number))
    if offset.length == 0.0:
        return ()

    states: list[tuple[object, object, str, str, object]] = []
    for obj in tuple(factory.bpy.data.objects):
        if obj.parent != context.rig or obj.parent_type != "BONE":
            continue
        if obj.parent_bone not in _GORE_UPPER_BODY_BONES:
            continue
        if obj.hide_render:
            continue
        parent = obj.parent
        parent_type = obj.parent_type
        parent_bone = obj.parent_bone
        world_matrix = obj.matrix_world.copy()
        states.append((obj, parent, parent_type, parent_bone, world_matrix))
        moved_matrix = world_matrix.copy()
        moved_matrix.translation += offset
        obj.parent = None
        obj.parent_type = "OBJECT"
        obj.parent_bone = ""
        obj.matrix_world = moved_matrix
    if not states:
        raise RuntimeError("death_03 upper-body object set is empty")
    factory.bpy.context.view_layer.update()
    return tuple(states)


def _restore_upper_body(
    states: tuple[tuple[object, object, str, str, object], ...],
) -> None:
    for obj, parent, parent_type, parent_bone, world_matrix in states:
        obj.parent = parent
        obj.parent_type = parent_type
        obj.parent_bone = parent_bone
        obj.matrix_world = world_matrix
    if states:
        factory.bpy.context.view_layer.update()
'''
    text = regex_once(
        text,
        r'def _reset_gore_state\(\) -> None:\n.*?\n\n\n(?=def render_death_down_keyposes_v01)',
        gore_helpers + "\n\n\n",
        "adapter gore helpers",
    )
    old_render = '''                factory.bpy.context.scene.frame_set(frame_number)
                factory.bpy.context.view_layer.update()
                _apply_gore_state(profile, frame_number)
                artifact, _ = factory._render_frame(
                    context,
                    animation_id=profile.animation_id,
                    direction="down",
                    frame_number=frame_number,
                    raw_dir=raw_dir,
                    frame_dir=frame_dir,
                    output_name=(
                        f"{config.character_id}_{profile.animation_id}_"
                        f"f{frame_number:02d}_proxy_{revision}.png"
                    ),
                    fixed_scale=down_calibration.scale,
                    fixed_center_x=down_calibration.source_center_x,
                )
                artifacts.append(artifact)
'''
    new_render = '''                factory.bpy.context.scene.frame_set(frame_number)
                factory.bpy.context.view_layer.update()
                _apply_gore_state(profile, frame_number)
                split_states: tuple[tuple[object, object, str, str, object], ...] = ()
                if (
                    profile.gore_mode == "waist_torso_legs_separation"
                    and profile.detachment_frame is not None
                    and frame_number >= profile.detachment_frame
                ):
                    split_states = _detach_upper_body(context, frame_number)
                try:
                    artifact, _ = factory._render_frame(
                        context,
                        animation_id=profile.animation_id,
                        direction="down",
                        frame_number=frame_number,
                        raw_dir=raw_dir,
                        frame_dir=frame_dir,
                        output_name=(
                            f"{config.character_id}_{profile.animation_id}_"
                            f"f{frame_number:02d}_proxy_{revision}.png"
                        ),
                        fixed_scale=down_calibration.scale,
                        fixed_center_x=down_calibration.source_center_x,
                    )
                    artifacts.append(artifact)
                finally:
                    _restore_upper_body(split_states)
'''
    text = replace_once(text, old_render, new_render, "adapter render split")
    old_check = '''            if profile.gore_mode == "left_forearm_detachment":
                for item in frames:
                    if item.frame_number < int(profile.detachment_frame):
                        continue
                    component_sizes = _opaque_component_sizes(item.output_path)
                    visible_components = [
                        size for size in component_sizes if size >= 8
                    ]
                    if len(visible_components) < 2:
                        raise RuntimeError(
                            "death_03 detached limb is not visually separated: "
                            f"f{item.frame_number:02d}={component_sizes}"
                        )
'''
    new_check = '''            if profile.gore_mode == "waist_torso_legs_separation":
                for item in frames:
                    if item.frame_number < int(profile.detachment_frame):
                        continue
                    component_sizes = _opaque_component_sizes(item.output_path)
                    major_components = [
                        size for size in component_sizes if size >= 120
                    ]
                    if (
                        len(major_components) < 2
                        or major_components[1] < major_components[0] * 0.20
                    ):
                        raise RuntimeError(
                            "death_03 torso and legs are not visually separated: "
                            f"f{item.frame_number:02d}={component_sizes}"
                        )
'''
    text = replace_once(text, old_check, new_check, "adapter component contract")
    ADAPTER.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    text = TEST.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''        self.assertEqual(death_03.gore_mode, "left_forearm_detachment")
        self.assertEqual(death_03.detached_part_id, "left_forearm_and_hand")
        self.assertEqual(death_03.detachment_frame, 4)
        self.assertLess(death_03.poses[-1].spine_pitch_x_degrees, -80.0)
        self.assertGreater(death_03.poses[-1].pelvis_roll_z_degrees, 80.0)
''',
        '''        self.assertEqual(death_03.gore_mode, "waist_torso_legs_separation")
        self.assertEqual(death_03.detached_part_id, "upper_torso_and_lower_body")
        self.assertEqual(death_03.detachment_frame, 4)
        self.assertLess(death_03.poses[-1].pelvis_x, -0.20)
        self.assertLess(death_03.poses[-1].pelvis_roll_z_degrees, -60.0)
        self.assertGreater(death_03.poses[-1].spine_pitch_x_degrees, 20.0)
''',
        "tests death_03 profile",
    )
    text = replace_once(
        text,
        '''        self.assertIn("death03_detached_forearm_L", source)
        self.assertIn("death03_left_elbow_stump", source)
''',
        '''        self.assertIn("death03_upper_waist_cut_cap", source)
        self.assertIn("death03_lower_waist_cut_cap", source)
        self.assertIn("_GORE_UPPER_BODY_BONES", source)
''',
        "tests builder gore modules",
    )
    text = replace_once(
        text,
        '''        self.assertIn("_apply_gore_state", source)
        self.assertIn("_opaque_component_sizes", source)
        self.assertIn("detached limb is not visually separated", source)
        self.assertIn("left_forearm_detachment", source)
''',
        '''        self.assertIn("_apply_gore_state", source)
        self.assertIn("_detach_upper_body", source)
        self.assertIn("_restore_upper_body", source)
        self.assertIn("_opaque_component_sizes", source)
        self.assertIn("torso and legs are not visually separated", source)
        self.assertIn("waist_torso_legs_separation", source)
''',
        "tests renderer split contract",
    )
    TEST.write_text(text, encoding="utf-8")


def patch_docs() -> None:
    DOC.write_text(
        '''# human_warrior_m01 — weapon-agnostic death down keyposes v01

## Цель

Подготовить три визуально различимых варианта смерти `human_warrior_m01` для
направления `down`, не привязанные к оружию.

Текущий PR содержит только key poses и Blender review-пайплайн. Runtime,
approved-атласы, случайный selector и остальные направления не подключаются.

## Варианты

### death_01_base

Утверждённое тяжёлое падение `pass02`. Геометрия движения сохранена; оружейный
слой скрыт.

### death_02_base

Фронтальное обрушение на противоположную сторону. Это самостоятельный motion,
а не зеркальная копия `death_01`.

### death_03_base

Разделение тела в области пояса:

- до `f03` персонаж проседает почти вертикально;
- на `f04` верхняя часть тела отделяется от таза и ног;
- туловище с головой и руками смещается вправо;
- таз и обе ноги падают отдельной массой влево;
- два крупных cut-cap закрывают поверхности разрыва;
- `f05` сохраняет две раздельные corpse-массы.

Мелкие отделённые части не используются. Это обеспечивает читаемость в
игровом размере `96×96` и делает `death_03` принципиально отличным от
`death_01`.

## Общий контракт

Каждый вариант содержит:

`guard → balance_break → knee_drop → ground_impact → final`

- 5 key poses;
- review-тайминг 8 FPS;
- `96×96 RGBA`;
- binary alpha;
- baseline `y=91`;
- non-loop;
- постоянный финальный corpse-state;
- оружие не отображается;
- mirroring, negative scale и root translation запрещены;
- appearance v03, head v22, proxy v25 и gameplay camera `down` сохранены.

## Контракт разделения death_03

Renderer временно отвязывает уже позированные объекты верхней части тела от rig,
сдвигает их как единую массу и после рендера восстанавливает исходное parenting.
Поэтому лицо, волосы, шарф, броня и физическая асимметрия не заменяются
упрощённым proxy.

Для `f04/f05` CI требует минимум две крупные раздельные alpha-компоненты. Вторая
масса должна составлять не менее 20% первой и содержать минимум 120 непрозрачных
пикселей. Маленький gore-prop не может формально пройти эту проверку.

## Следующий этап после ручного утверждения

1. добавить промежуточные кадры и собрать три полных `base_down` цикла;
2. зафиксировать финальные corpse-state кадры;
3. перенести варианты на `left/right/up` без зеркалирования;
4. отдельным integration PR добавить approved-атласы;
5. подключить случайный selector без немедленного повтора;
6. использовать fallback `death_01_base` и приоритет `death > hit`.
''',
        encoding="utf-8",
    )


def main() -> int:
    patch_profile()
    patch_builder()
    patch_adapter()
    patch_tests()
    patch_docs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
