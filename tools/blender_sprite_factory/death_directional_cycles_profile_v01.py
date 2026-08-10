from __future__ import annotations

from dataclasses import dataclass

from combat_idle_directional_profile_v11 import DIRECTION_ORDER
from death_down_cycle_profile_v01 import (
    DEATH_DOWN_CYCLE_DURATION_SECONDS,
    DEATH_DOWN_CYCLE_FPS,
    DEATH_DOWN_CYCLE_FRAME_ORDER,
    DEATH_DOWN_CYCLE_PHASE_ORDER,
    load_death_down_cycle_profiles_v01,
)
from death_down_keyposes_profile_v01 import DEATH_DOWN_VARIANT_IDS


REVIEW_DIRECTION_ORDER = ("left", "right", "up")
PROFILE_REVISION = "death_directional_cycles_v01_from_approved_down"


@dataclass(frozen=True)
class DeathDirectionalVariantV01:
    death_variant_id: str
    animation_id: str
    source_profile_revision: str
    gore_mode: str
    detached_part_id: str | None
    detachment_frame: int | None


@dataclass(frozen=True)
class DeathDirectionalCyclesProfileV01:
    character_id: str
    revision: str
    directions: tuple[str, ...]
    review_directions: tuple[str, ...]
    frame_order: tuple[int, ...]
    phase_order: tuple[str, ...]
    fps: int
    duration_seconds: float
    loop: bool
    weapon_visible: bool
    final_pose_persistent: bool
    source_stage: str
    variants: tuple[DeathDirectionalVariantV01, ...]


def _build_profile() -> DeathDirectionalCyclesProfileV01:
    source_profiles = load_death_down_cycle_profiles_v01("human_warrior_m01")
    return DeathDirectionalCyclesProfileV01(
        character_id="human_warrior_m01",
        revision=PROFILE_REVISION,
        directions=DIRECTION_ORDER,
        review_directions=REVIEW_DIRECTION_ORDER,
        frame_order=DEATH_DOWN_CYCLE_FRAME_ORDER,
        phase_order=DEATH_DOWN_CYCLE_PHASE_ORDER,
        fps=DEATH_DOWN_CYCLE_FPS,
        duration_seconds=DEATH_DOWN_CYCLE_DURATION_SECONDS,
        loop=False,
        weapon_visible=False,
        final_pose_persistent=True,
        source_stage="base_down_cycles_v01_approved_2026_08_10",
        variants=tuple(
            DeathDirectionalVariantV01(
                death_variant_id=source.death_variant_id,
                animation_id=source.animation_id,
                source_profile_revision=source.revision,
                gore_mode=source.gore_mode,
                detached_part_id=source.detached_part_id,
                detachment_frame=source.detachment_frame,
            )
            for source in source_profiles
        ),
    )


HUMAN_WARRIOR_M01_DEATH_DIRECTIONAL_CYCLES_V01 = _build_profile()


def load_death_directional_cycles_profile_v01(
    character_id: str,
) -> DeathDirectionalCyclesProfileV01:
    profile = HUMAN_WARRIOR_M01_DEATH_DIRECTIONAL_CYCLES_V01
    if character_id != profile.character_id:
        raise KeyError(
            "No death directional cycles v01 profile for "
            f"character_id={character_id}"
        )
    if profile.revision != PROFILE_REVISION:
        raise ValueError("Death directional cycles v01 revision drifted")
    if profile.directions != DIRECTION_ORDER:
        raise ValueError("Death directional cycles v01 direction order drifted")
    if profile.review_directions != REVIEW_DIRECTION_ORDER:
        raise ValueError("Death directional cycles v01 review order drifted")
    if profile.frame_order != DEATH_DOWN_CYCLE_FRAME_ORDER:
        raise ValueError("Death directional cycles v01 frame order drifted")
    if profile.phase_order != DEATH_DOWN_CYCLE_PHASE_ORDER:
        raise ValueError("Death directional cycles v01 phase order drifted")
    if profile.fps != DEATH_DOWN_CYCLE_FPS or profile.loop:
        raise ValueError("Death directional cycles v01 timing drifted")
    if abs(profile.duration_seconds - 0.8) > 1e-9:
        raise ValueError("Death directional cycles v01 duration drifted")
    if profile.weapon_visible or not profile.final_pose_persistent:
        raise ValueError("Death directional cycles v01 safety contract drifted")
    if tuple(item.death_variant_id for item in profile.variants) != (
        DEATH_DOWN_VARIANT_IDS
    ):
        raise ValueError("Death directional cycles v01 variant order drifted")

    source_by_variant = {
        source.death_variant_id: source
        for source in load_death_down_cycle_profiles_v01(character_id)
    }
    for variant in profile.variants:
        source = source_by_variant[variant.death_variant_id]
        if variant.animation_id != source.animation_id:
            raise ValueError(
                f"{variant.death_variant_id} directional animation id drifted"
            )
        if variant.source_profile_revision != source.revision:
            raise ValueError(
                f"{variant.death_variant_id} directional source revision drifted"
            )
        if variant.gore_mode != source.gore_mode:
            raise ValueError(
                f"{variant.death_variant_id} directional gore mode drifted"
            )
        if variant.detached_part_id != source.detached_part_id:
            raise ValueError(
                f"{variant.death_variant_id} detached part contract drifted"
            )
        if variant.detachment_frame != source.detachment_frame:
            raise ValueError(
                f"{variant.death_variant_id} detachment frame drifted"
            )
    return profile
