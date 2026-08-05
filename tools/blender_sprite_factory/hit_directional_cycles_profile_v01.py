from __future__ import annotations

from dataclasses import dataclass

from combat_idle_directional_profile_v11 import DIRECTION_ORDER
from hit_down_cycle_profile_v01 import (
    HIT_DOWN_CYCLE_DURATION_SECONDS,
    HIT_DOWN_CYCLE_FPS,
    HIT_DOWN_CYCLE_FRAME_ORDER,
    HIT_DOWN_CYCLE_PHASE_ORDER,
    load_hit_down_cycle_profile_v01,
)
from hit_down_twohand_cycle_profile_v01 import (
    load_hit_down_twohand_cycle_profile_v01,
)


REVIEW_DIRECTION_ORDER = ("left", "right", "up")


@dataclass(frozen=True)
class HitDirectionalCycleV01:
    cycle_id: str
    animation_id: str
    stance_variant_id: str
    stance_source_revision: str
    weapon_cycle_id: str
    source_profile_revision: str


@dataclass(frozen=True)
class HitDirectionalCyclesProfileV01:
    character_id: str
    revision: str
    directions: tuple[str, ...]
    review_directions: tuple[str, ...]
    frame_order: tuple[int, ...]
    phase_order: tuple[str, ...]
    fps: int
    duration_seconds: float
    loop: bool
    directional_stance_source_revision: str
    directional_weapon_source_revision: str
    cycles: tuple[HitDirectionalCycleV01, ...]


def _build_profile() -> HitDirectionalCyclesProfileV01:
    onehand = load_hit_down_cycle_profile_v01("human_warrior_m01")
    twohand = load_hit_down_twohand_cycle_profile_v01("human_warrior_m01")
    return HitDirectionalCyclesProfileV01(
        character_id="human_warrior_m01",
        revision="hit_directional_cycles_v01_from_approved_down",
        directions=DIRECTION_ORDER,
        review_directions=REVIEW_DIRECTION_ORDER,
        frame_order=HIT_DOWN_CYCLE_FRAME_ORDER,
        phase_order=HIT_DOWN_CYCLE_PHASE_ORDER,
        fps=HIT_DOWN_CYCLE_FPS,
        duration_seconds=HIT_DOWN_CYCLE_DURATION_SECONDS,
        loop=False,
        directional_stance_source_revision="combat_idle_directional_cycles_v14",
        directional_weapon_source_revision="combat_idle_directional_weapon_v12",
        cycles=(
            HitDirectionalCycleV01(
                cycle_id="onehand_ready",
                animation_id=onehand.animation_id,
                stance_variant_id=onehand.stance_variant_id,
                stance_source_revision=onehand.stance_source_revision,
                weapon_cycle_id=onehand.weapon_cycle_id,
                source_profile_revision=onehand.revision,
            ),
            HitDirectionalCycleV01(
                cycle_id="twohand_center_high",
                animation_id=twohand.animation_id,
                stance_variant_id=twohand.stance_variant_id,
                stance_source_revision=twohand.stance_source_revision,
                weapon_cycle_id=twohand.weapon_cycle_id,
                source_profile_revision=twohand.revision,
            ),
        ),
    )


HUMAN_WARRIOR_M01_HIT_DIRECTIONAL_CYCLES_V01 = _build_profile()


def load_hit_directional_cycles_profile_v01(
    character_id: str,
) -> HitDirectionalCyclesProfileV01:
    profile = HUMAN_WARRIOR_M01_HIT_DIRECTIONAL_CYCLES_V01
    if character_id != profile.character_id:
        raise KeyError(
            f"No hit directional cycles v01 profile for character_id={character_id}"
        )
    if profile.revision != "hit_directional_cycles_v01_from_approved_down":
        raise ValueError("Hit directional cycles v01 revision drifted")
    if profile.directions != DIRECTION_ORDER:
        raise ValueError("Hit directional cycles v01 direction order drifted")
    if profile.review_directions != REVIEW_DIRECTION_ORDER:
        raise ValueError("Hit directional cycles v01 review order drifted")
    if profile.frame_order != HIT_DOWN_CYCLE_FRAME_ORDER:
        raise ValueError("Hit directional cycles v01 frame order drifted")
    if profile.phase_order != HIT_DOWN_CYCLE_PHASE_ORDER:
        raise ValueError("Hit directional cycles v01 phase order drifted")
    if profile.fps != HIT_DOWN_CYCLE_FPS or profile.loop:
        raise ValueError("Hit directional cycles v01 timing drifted")
    if abs(profile.duration_seconds - 0.4) > 1e-9:
        raise ValueError("Hit directional cycles v01 duration drifted")
    if tuple(cycle.cycle_id for cycle in profile.cycles) != (
        "onehand_ready",
        "twohand_center_high",
    ):
        raise ValueError("Hit directional cycles v01 grip order drifted")
    if profile.directional_stance_source_revision != "combat_idle_directional_cycles_v14":
        raise ValueError("Hit directional cycles v01 lost approved stance source")
    if profile.directional_weapon_source_revision != "combat_idle_directional_weapon_v12":
        raise ValueError("Hit directional cycles v01 lost approved weapon source")
    return profile
