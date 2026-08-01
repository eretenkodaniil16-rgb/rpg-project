from __future__ import annotations

from dataclasses import dataclass

from combat_idle_down_weapon_variants_profile_v09 import (
    load_weapon_stance_profile_v09,
)
from walk_down_profile_v03 import load_walk_down_profile_v03
from walk_left_profile_v01 import load_walk_left_profile_v01
from walk_right_profile_v01 import load_walk_right_profile_v01
from walk_up_profile_v02 import load_walk_up_profile_v02


ARMED_WALK_FRAME_ORDER = (1, 2, 3, 4, 5, 6)
ARMED_WALK_FPS = 8
ONEHAND_MAX_WEAPON_SWAY_DEGREES = 1.0
TWOHAND_MAX_WEAPON_SWAY_DEGREES = 3.5


@dataclass(frozen=True)
class ArmedWalkDirectionV15:
    direction: str
    source_action_id: str
    source_profile_revision: str
    source_animation_revision: str


@dataclass(frozen=True)
class ArmedWalkGripV15:
    grip_id: str
    display_name: str
    stance_variant_id: str
    stance_source_revision: str
    weapon_cycle_id: str
    action_prefix: str
    render_animation_prefix: str
    free_arm_swing_scale: float
    weapon_arm_step_offsets_degrees: tuple[float, ...]


@dataclass(frozen=True)
class WalkDirectionalWeaponProfileV15:
    character_id: str
    revision: str
    animation_revision: str
    fps: int
    loop: bool
    frame_order: tuple[int, ...]
    directions: tuple[ArmedWalkDirectionV15, ...]
    grips: tuple[ArmedWalkGripV15, ...]
    static_weapon_source_revision: str
    combat_idle_source_revision: str


HUMAN_WARRIOR_M01_WALK_DIRECTIONAL_WEAPON_V15 = (
    WalkDirectionalWeaponProfileV15(
        character_id="human_warrior_m01",
        revision="v15",
        animation_revision="v01",
        fps=ARMED_WALK_FPS,
        loop=True,
        frame_order=ARMED_WALK_FRAME_ORDER,
        directions=(
            ArmedWalkDirectionV15(
                direction="down",
                source_action_id="walk_down",
                source_profile_revision="v03",
                source_animation_revision="v04",
            ),
            ArmedWalkDirectionV15(
                direction="left",
                source_action_id="walk_left",
                source_profile_revision="v01",
                source_animation_revision="v01",
            ),
            ArmedWalkDirectionV15(
                direction="right",
                source_action_id="walk_right",
                source_profile_revision="v01",
                source_animation_revision="v01",
            ),
            ArmedWalkDirectionV15(
                direction="up",
                source_action_id="walk_up",
                source_profile_revision="v02",
                source_animation_revision="v02",
            ),
        ),
        grips=(
            ArmedWalkGripV15(
                grip_id="onehand_ready",
                display_name="Ходьба с одноручным мечом",
                stance_variant_id="onehand_ready",
                stance_source_revision="v09",
                weapon_cycle_id="onehand_ready",
                action_prefix="walk_onehand",
                render_animation_prefix="walk_onehand",
                free_arm_swing_scale=0.32,
                weapon_arm_step_offsets_degrees=(0.0, -0.6, 0.3, 0.0, -0.6, 0.3),
            ),
            ArmedWalkGripV15(
                grip_id="twohand_center_high",
                display_name="Ходьба с двуручным мечом",
                stance_variant_id="twohand_center_high",
                stance_source_revision="v06_exact_in_v09",
                weapon_cycle_id="twohand_center_high",
                action_prefix="walk_twohand",
                render_animation_prefix="walk_twohand",
                free_arm_swing_scale=0.0,
                weapon_arm_step_offsets_degrees=(
                    0.0,
                    -1.5,
                    -3.5,
                    0.0,
                    -1.5,
                    -3.5,
                ),
            ),
        ),
        static_weapon_source_revision="directional_weapon_v12_artist_approved",
        combat_idle_source_revision="directional_cycles_v14_artist_approved",
    )
)


def _source_profiles(character_id: str) -> dict[str, object]:
    return {
        "down": load_walk_down_profile_v03(character_id),
        "left": load_walk_left_profile_v01(character_id),
        "right": load_walk_right_profile_v01(character_id),
        "up": load_walk_up_profile_v02(character_id),
    }


def load_walk_directional_weapon_profile_v15(
    character_id: str,
) -> WalkDirectionalWeaponProfileV15:
    profile = HUMAN_WARRIOR_M01_WALK_DIRECTIONAL_WEAPON_V15
    if character_id != profile.character_id:
        raise KeyError(
            f"No armed directional walk v15 profile for character_id={character_id}"
        )
    if profile.revision != "v15" or profile.animation_revision != "v01":
        raise ValueError("Armed directional walk v15 identity drifted")
    if profile.fps != ARMED_WALK_FPS or not profile.loop:
        raise ValueError("Armed directional walk v15 must remain an 8 FPS loop")
    if profile.frame_order != ARMED_WALK_FRAME_ORDER:
        raise ValueError("Armed directional walk v15 frame order drifted")
    if tuple(item.direction for item in profile.directions) != (
        "down",
        "left",
        "right",
        "up",
    ):
        raise ValueError("Armed directional walk v15 direction order drifted")
    if tuple(item.grip_id for item in profile.grips) != (
        "onehand_ready",
        "twohand_center_high",
    ):
        raise ValueError("Armed directional walk v15 grip order drifted")
    if profile.static_weapon_source_revision != (
        "directional_weapon_v12_artist_approved"
    ):
        raise ValueError("Armed directional walk v15 lost approved weapon directions")
    if profile.combat_idle_source_revision != (
        "directional_cycles_v14_artist_approved"
    ):
        raise ValueError("Armed directional walk v15 lost approved combat idle source")

    source_profiles = _source_profiles(character_id)
    for item in profile.directions:
        source = source_profiles[item.direction]
        if source.animation_id != item.source_action_id:
            raise ValueError(
                f"Armed directional walk v15 source action drifted: {item.direction}"
            )
        if source.revision != item.source_profile_revision:
            raise ValueError(
                f"Armed directional walk v15 source profile drifted: {item.direction}"
            )
        if source.animation_revision != item.source_animation_revision:
            raise ValueError(
                f"Armed directional walk v15 source animation drifted: {item.direction}"
            )
        if source.fps != profile.fps or not source.loop:
            raise ValueError(
                f"Armed directional walk v15 source timing drifted: {item.direction}"
            )
        if tuple(pose.frame for pose in source.poses) != profile.frame_order:
            raise ValueError(
                f"Armed directional walk v15 source frames drifted: {item.direction}"
            )

    stances = load_weapon_stance_profile_v09(character_id)
    stance_by_id = {item.variant_id: item for item in stances.variants}
    for grip in profile.grips:
        stance = stance_by_id.get(grip.stance_variant_id)
        if stance is None or stance.grip_mode not in {"one_handed", "two_handed"}:
            raise ValueError(
                f"Armed directional walk v15 stance drifted: {grip.grip_id}"
            )
        if len(grip.weapon_arm_step_offsets_degrees) != len(profile.frame_order):
            raise ValueError(
                f"Armed directional walk v15 step offsets drifted: {grip.grip_id}"
            )
        sway_limit = (
            ONEHAND_MAX_WEAPON_SWAY_DEGREES
            if grip.grip_id == "onehand_ready"
            else TWOHAND_MAX_WEAPON_SWAY_DEGREES
        )
        if max(abs(value) for value in grip.weapon_arm_step_offsets_degrees) > sway_limit:
            raise ValueError(
                f"Armed directional walk v15 weapon sway is excessive: {grip.grip_id}"
            )
        if not 0.0 <= grip.free_arm_swing_scale <= 0.35:
            raise ValueError(
                f"Armed directional walk v15 free-arm scale is unsafe: {grip.grip_id}"
            )
    return profile
