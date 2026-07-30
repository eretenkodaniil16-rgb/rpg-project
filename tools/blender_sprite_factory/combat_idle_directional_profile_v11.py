from __future__ import annotations

from dataclasses import dataclass

from combat_idle_down_cycles_profile_v10 import load_combat_idle_cycles_profile_v10


DIRECTION_ORDER = ("down", "left", "right", "up")
REVIEW_DIRECTION_ORDER = ("left", "right", "up")


@dataclass(frozen=True)
class CombatIdleDirectionalCandidateV11:
    candidate_id: str
    display_name: str
    render_animation_id: str
    source_cycle_id: str
    source_animation_id: str
    grip_mode: str
    weapon_variant_id: str
    source_revision: str
    directions: tuple[str, ...]


@dataclass(frozen=True)
class CombatIdleDirectionalProfileV11:
    character_id: str
    revision: str
    approved_direction: str
    review_directions: tuple[str, ...]
    candidates: tuple[CombatIdleDirectionalCandidateV11, ...]


def _build_profile() -> CombatIdleDirectionalProfileV11:
    cycles = load_combat_idle_cycles_profile_v10("human_warrior_m01")
    by_id = {cycle.cycle_id: cycle for cycle in cycles.cycles}
    onehand = by_id["onehand_ready"]
    twohand = by_id["twohand_center_high"]
    return CombatIdleDirectionalProfileV11(
        character_id="human_warrior_m01",
        revision="v11",
        approved_direction="down",
        review_directions=REVIEW_DIRECTION_ORDER,
        candidates=(
            CombatIdleDirectionalCandidateV11(
                candidate_id="onehand_ready",
                display_name="Одноручная боевая стойка — четыре направления",
                render_animation_id="combat_idle_onehand_ready_directional_v11",
                source_cycle_id=onehand.cycle_id,
                source_animation_id=onehand.animation_id,
                grip_mode=onehand.grip_mode,
                weapon_variant_id=onehand.weapon_variant_id,
                source_revision="v10_from_ready_v09",
                directions=DIRECTION_ORDER,
            ),
            CombatIdleDirectionalCandidateV11(
                candidate_id="twohand_center_high",
                display_name="Двуручная высокая стойка — четыре направления",
                render_animation_id="combat_idle_twohand_center_high_directional_v11",
                source_cycle_id=twohand.cycle_id,
                source_animation_id=twohand.animation_id,
                grip_mode=twohand.grip_mode,
                weapon_variant_id=twohand.weapon_variant_id,
                source_revision="v10_from_high_v06",
                directions=DIRECTION_ORDER,
            ),
        ),
    )


HUMAN_WARRIOR_M01_COMBAT_IDLE_DIRECTIONAL_V11 = _build_profile()


def load_combat_idle_directional_profile_v11(
    character_id: str,
) -> CombatIdleDirectionalProfileV11:
    profile = HUMAN_WARRIOR_M01_COMBAT_IDLE_DIRECTIONAL_V11
    if character_id != profile.character_id:
        raise KeyError(
            f"No combat idle directional v11 profile for character_id={character_id}"
        )
    if profile.revision != "v11":
        raise ValueError("Combat idle directional v11 revision drifted")
    if profile.approved_direction != "down":
        raise ValueError("Combat idle directional v11 must retain approved down control")
    if profile.review_directions != REVIEW_DIRECTION_ORDER:
        raise ValueError("Combat idle directional v11 review direction order drifted")
    if tuple(candidate.candidate_id for candidate in profile.candidates) != (
        "onehand_ready",
        "twohand_center_high",
    ):
        raise ValueError("Combat idle directional v11 candidate order drifted")

    cycles = load_combat_idle_cycles_profile_v10(character_id)
    cycle_by_id = {cycle.cycle_id: cycle for cycle in cycles.cycles}
    for candidate in profile.candidates:
        source = cycle_by_id[candidate.source_cycle_id]
        if candidate.directions != DIRECTION_ORDER:
            raise ValueError(
                f"Directional candidate {candidate.candidate_id} direction order drifted"
            )
        if candidate.source_animation_id != source.animation_id:
            raise ValueError(
                f"Directional candidate {candidate.candidate_id} source action drifted"
            )
        if candidate.grip_mode != source.grip_mode:
            raise ValueError(
                f"Directional candidate {candidate.candidate_id} grip mode drifted"
            )
        if candidate.weapon_variant_id != source.weapon_variant_id:
            raise ValueError(
                f"Directional candidate {candidate.candidate_id} weapon variant drifted"
            )
        if not candidate.render_animation_id.endswith("_directional_v11"):
            raise ValueError(
                f"Directional candidate {candidate.candidate_id} render id drifted"
            )
    return profile
