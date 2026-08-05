from __future__ import annotations

from dataclasses import dataclass

from attack_sword_down_cycle_profile_v20 import (
    FULL_CYCLE_FPS,
    FULL_CYCLE_FRAME_ORDER,
    FULL_CYCLE_PHASE_ORDER,
    SOURCE_KEYPOSE_REVISION,
)
from attack_sword_twohand_down_overhead_profile_v21 import (
    OVERHEAD_ACTION_ID,
    OVERHEAD_REVIEW_REVISION,
    OVERHEAD_TRAJECTORY_ID,
    load_attack_sword_twohand_down_overhead_profile_v21,
)


DIRECTIONAL_OVERHEAD_REVISION = "twohand_overhead_directional_v21_review"
DIRECTION_ORDER = ("down", "left", "right", "up")
GRIP_ID = "twohand_center_high"
TOTAL_ACTION_COUNT = 4
TOTAL_RENDERED_FRAME_COUNT = 32

DOWN_FRAME_SHA256 = {
    1: "a16c3acd22d1bc0508ef5b94332c54c61a373bf06ead27a9a5691966350f93f6",
    2: "783128aeecb3f8aa716809c80e101f642bf7727aacd25b70abaeef40b907f2a3",
    3: "1a15887f6c523d836db22fc8476b343d5f97cd95ea7a3517922305bc471b7a7c",
    4: "08c19c99b559f4adc280265602082b08717ea1780b6085ce68e831cf75ddebac",
    5: "d20623c4f403dec840c0fac1ba579267b934e7d987fb5691967786fa2f33b2fa",
    6: "0a7536f621d61371ea3e9285549c408121dd0edd726fd9226151a036eda3438c",
    7: "76d72940020dea8b02907eae8feb10b2f27fcad54b19d58a0704f9236e42f440",
    8: "a16c3acd22d1bc0508ef5b94332c54c61a373bf06ead27a9a5691966350f93f6",
}


@dataclass(frozen=True)
class DirectionalOverheadActionV21:
    direction: str
    grip_id: str
    display_name: str
    source_action_id: str
    action_id: str
    weapon_cycle_id: str
    trajectory_id: str


@dataclass(frozen=True)
class DirectionalOverheadProfileV21:
    character_id: str
    revision: str
    animation_family: str
    directions: tuple[str, ...]
    fps: int
    loop: bool
    frame_order: tuple[int, ...]
    phase_order: tuple[str, ...]
    source_keypose_revision: str
    source_overhead_revision: str
    actions: tuple[DirectionalOverheadActionV21, ...]


def _action_id(direction: str) -> str:
    if direction == "down":
        return OVERHEAD_ACTION_ID
    return f"attack_sword_01_twohand_{direction}_overhead_v21"


def load_attack_sword_twohand_overhead_directional_profile_v21(
    character_id: str,
) -> DirectionalOverheadProfileV21:
    source = load_attack_sword_twohand_down_overhead_profile_v21(character_id)
    overhead = source.grips[1]
    if overhead.action_id != OVERHEAD_ACTION_ID:
        raise ValueError("directional overhead v21 source action drifted")
    if overhead.grip_id != GRIP_ID:
        raise ValueError("directional overhead v21 source grip drifted")

    actions = tuple(
        DirectionalOverheadActionV21(
            direction=direction,
            grip_id=GRIP_ID,
            display_name=(
                "Двуручный вертикальный рубящий удар сверху вниз — "
                f"{direction}"
            ),
            source_action_id=OVERHEAD_ACTION_ID,
            action_id=_action_id(direction),
            weapon_cycle_id=overhead.weapon_cycle_id,
            trajectory_id=f"{OVERHEAD_TRAJECTORY_ID}_{direction}",
        )
        for direction in DIRECTION_ORDER
    )
    profile = DirectionalOverheadProfileV21(
        character_id=character_id,
        revision=DIRECTIONAL_OVERHEAD_REVISION,
        animation_family="attack_sword_01",
        directions=DIRECTION_ORDER,
        fps=FULL_CYCLE_FPS,
        loop=False,
        frame_order=FULL_CYCLE_FRAME_ORDER,
        phase_order=FULL_CYCLE_PHASE_ORDER,
        source_keypose_revision=SOURCE_KEYPOSE_REVISION,
        source_overhead_revision=OVERHEAD_REVIEW_REVISION,
        actions=actions,
    )
    if len(profile.actions) != TOTAL_ACTION_COUNT:
        raise ValueError("directional overhead v21 must define four actions")
    if tuple(action.direction for action in profile.actions) != DIRECTION_ORDER:
        raise ValueError("directional overhead v21 direction order drifted")
    if len({action.action_id for action in profile.actions}) != TOTAL_ACTION_COUNT:
        raise ValueError("directional overhead v21 action identifiers must be unique")
    if tuple(DOWN_FRAME_SHA256) != FULL_CYCLE_FRAME_ORDER:
        raise ValueError("directional overhead v21 down hash contract is incomplete")
    return profile
