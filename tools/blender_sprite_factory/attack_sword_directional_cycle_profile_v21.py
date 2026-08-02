from __future__ import annotations

from dataclasses import dataclass

from attack_sword_down_cycle_profile_v20 import (
    FULL_CYCLE_FPS,
    FULL_CYCLE_FRAME_ORDER,
    FULL_CYCLE_PHASE_ORDER,
    SOURCE_KEYPOSE_REVISION,
    load_attack_sword_down_cycle_profile_v20,
)


DIRECTIONAL_CYCLE_REVISION = "v21"
DIRECTION_ORDER = ("down", "left", "right", "up")
GRIP_ORDER = ("onehand_ready", "twohand_center_high")
TOTAL_ACTION_COUNT = 8
TOTAL_RENDERED_FRAME_COUNT = 64


@dataclass(frozen=True)
class DirectionalAttackActionV21:
    direction: str
    grip_id: str
    display_name: str
    source_action_id: str
    action_id: str
    weapon_cycle_id: str
    trajectory_id: str


@dataclass(frozen=True)
class DirectionalAttackCycleProfileV21:
    character_id: str
    revision: str
    animation_family: str
    directions: tuple[str, ...]
    fps: int
    loop: bool
    frame_order: tuple[int, ...]
    phase_order: tuple[str, ...]
    source_keypose_revision: str
    actions: tuple[DirectionalAttackActionV21, ...]


def _directional_action_id(grip_id: str, direction: str, source_action_id: str) -> str:
    if direction == "down":
        return source_action_id
    grip_token = "onehand" if grip_id == "onehand_ready" else "twohand"
    return f"attack_sword_01_{grip_token}_{direction}_v21"


def load_attack_sword_directional_cycle_profile_v21(
    character_id: str,
) -> DirectionalAttackCycleProfileV21:
    source = load_attack_sword_down_cycle_profile_v20(character_id)
    actions: list[DirectionalAttackActionV21] = []
    grip_by_id = {grip.grip_id: grip for grip in source.grips}
    if tuple(grip_by_id) != GRIP_ORDER:
        raise ValueError(
            "attack sword directional v21 requires the approved one-hand and "
            "two-hand v20 grip order"
        )

    for direction in DIRECTION_ORDER:
        for grip_id in GRIP_ORDER:
            grip = grip_by_id[grip_id]
            actions.append(
                DirectionalAttackActionV21(
                    direction=direction,
                    grip_id=grip.grip_id,
                    display_name=grip.display_name,
                    source_action_id=grip.action_id,
                    action_id=_directional_action_id(
                        grip.grip_id,
                        direction,
                        grip.action_id,
                    ),
                    weapon_cycle_id=grip.weapon_cycle_id,
                    trajectory_id=(
                        f"{grip.trajectory_id}_{direction}_directional_v21"
                    ),
                )
            )

    profile = DirectionalAttackCycleProfileV21(
        character_id=character_id,
        revision=DIRECTIONAL_CYCLE_REVISION,
        animation_family="attack_sword_01",
        directions=DIRECTION_ORDER,
        fps=FULL_CYCLE_FPS,
        loop=False,
        frame_order=FULL_CYCLE_FRAME_ORDER,
        phase_order=FULL_CYCLE_PHASE_ORDER,
        source_keypose_revision=SOURCE_KEYPOSE_REVISION,
        actions=tuple(actions),
    )
    if len(profile.actions) != TOTAL_ACTION_COUNT:
        raise ValueError("attack sword directional v21 must define eight actions")
    if len({action.action_id for action in profile.actions}) != TOTAL_ACTION_COUNT:
        raise ValueError("attack sword directional v21 action identifiers must be unique")
    if tuple(
        action.direction
        for action in profile.actions[::len(GRIP_ORDER)]
    ) != DIRECTION_ORDER:
        raise ValueError("attack sword directional v21 direction order drifted")
    if any(direction not in DIRECTION_ORDER for direction in profile.directions):
        raise ValueError("attack sword directional v21 contains an unknown direction")
    return profile
