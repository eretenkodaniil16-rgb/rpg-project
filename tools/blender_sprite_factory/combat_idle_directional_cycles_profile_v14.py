from __future__ import annotations

from dataclasses import dataclass

from combat_idle_directional_profile_v11 import DIRECTION_ORDER
from combat_idle_down_cycles_profile_v10 import (
    COMBAT_IDLE_CYCLE_FPS,
    FRAME_ORDER,
    PHASE_ORDER,
    load_combat_idle_cycles_profile_v10,
)


@dataclass(frozen=True)
class DirectionalCombatIdleCycleV14:
    cycle_id: str
    display_name: str
    source_action_id: str
    source_static_animation_id: str
    render_animation_id: str
    grip_mode: str
    fps: int
    loop: bool


@dataclass(frozen=True)
class CombatIdleDirectionalCyclesProfileV14:
    character_id: str
    revision: str
    directions: tuple[str, ...]
    frame_order: tuple[int, ...]
    phase_order: tuple[str, ...]
    static_source_revision: str
    rejected_experiment_revision: str
    cycles: tuple[DirectionalCombatIdleCycleV14, ...]


HUMAN_WARRIOR_M01_COMBAT_IDLE_DIRECTIONAL_CYCLES_V14 = (
    CombatIdleDirectionalCyclesProfileV14(
        character_id="human_warrior_m01",
        revision="v14",
        directions=DIRECTION_ORDER,
        frame_order=FRAME_ORDER,
        phase_order=PHASE_ORDER,
        static_source_revision="v12_artist_approved",
        rejected_experiment_revision="v13_boundary_failure",
        cycles=(
            DirectionalCombatIdleCycleV14(
                cycle_id="onehand_ready",
                display_name="Одноручная боевая стойка — четыре направления",
                source_action_id="combat_idle_onehand_ready_cycle_v10",
                source_static_animation_id="combat_idle_onehand_ready_directional_v12",
                render_animation_id="combat_idle_onehand_ready_directional_cycle_v14",
                grip_mode="one_handed",
                fps=COMBAT_IDLE_CYCLE_FPS,
                loop=True,
            ),
            DirectionalCombatIdleCycleV14(
                cycle_id="twohand_center_high",
                display_name="Двуручная высокая стойка — четыре направления",
                source_action_id="combat_idle_twohand_center_high_cycle_v10",
                source_static_animation_id="combat_idle_twohand_center_high_directional_v12",
                render_animation_id="combat_idle_twohand_center_high_directional_cycle_v14",
                grip_mode="two_handed",
                fps=COMBAT_IDLE_CYCLE_FPS,
                loop=True,
            ),
        ),
    )
)


def load_combat_idle_directional_cycles_profile_v14(
    character_id: str,
) -> CombatIdleDirectionalCyclesProfileV14:
    profile = HUMAN_WARRIOR_M01_COMBAT_IDLE_DIRECTIONAL_CYCLES_V14
    if character_id != profile.character_id:
        raise KeyError(
            f"No combat idle directional cycles v14 profile for character_id={character_id}"
        )
    if profile.revision != "v14" or profile.directions != DIRECTION_ORDER:
        raise ValueError("Combat idle directional cycles v14 identity drifted")
    if profile.frame_order != FRAME_ORDER or profile.phase_order != PHASE_ORDER:
        raise ValueError("Combat idle directional cycles v14 frame contract drifted")
    if profile.static_source_revision != "v12_artist_approved":
        raise ValueError("Combat idle directional cycles v14 lost approved v12 source")
    if profile.rejected_experiment_revision != "v13_boundary_failure":
        raise ValueError("Combat idle directional cycles v14 lost v13 rejection history")
    if tuple(cycle.cycle_id for cycle in profile.cycles) != (
        "onehand_ready",
        "twohand_center_high",
    ):
        raise ValueError("Combat idle directional cycles v14 cycle order drifted")

    source_profile = load_combat_idle_cycles_profile_v10(character_id)
    source_by_id = {cycle.cycle_id: cycle for cycle in source_profile.cycles}
    for cycle in profile.cycles:
        source = source_by_id.get(cycle.cycle_id)
        if source is None or cycle.source_action_id != source.animation_id:
            raise ValueError(
                f"Combat idle directional cycles v14 source drifted: {cycle.cycle_id}"
            )
        if cycle.fps != COMBAT_IDLE_CYCLE_FPS or not cycle.loop:
            raise ValueError(
                f"Combat idle directional cycles v14 timing drifted: {cycle.cycle_id}"
            )
        if cycle.grip_mode != source.grip_mode:
            raise ValueError(
                f"Combat idle directional cycles v14 grip drifted: {cycle.cycle_id}"
            )
    return profile
