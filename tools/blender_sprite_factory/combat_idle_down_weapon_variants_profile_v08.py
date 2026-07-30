from __future__ import annotations

from dataclasses import replace

from combat_idle_down_weapon_variants_profile_v07 import (
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V07,
    WeaponStanceProfileV05,
)


ONE_HAND_SIDE_X = 0.86
ONE_HAND_BEHIND_Y = 0.30
ONE_HAND_DOWN_Z = -0.62


HUMAN_WARRIOR_M01_WEAPON_STANCES_V08 = replace(
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V07,
    revision="v08",
    variants=(
        replace(
            HUMAN_WARRIOR_M01_WEAPON_STANCES_V07.variants[0],
            display_name="Одноручная боковая низкая — клинок в сторону и назад",
            animation_id="combat_idle_onehand_low_v08",
            weapon_id="sword_01_onehand_side_back_v08",
        ),
        replace(
            HUMAN_WARRIOR_M01_WEAPON_STANCES_V07.variants[1],
            display_name="Одноручная боковая боевая — клинок в сторону и назад",
            animation_id="combat_idle_onehand_ready_v08",
            weapon_id="sword_01_onehand_side_back_v08",
        ),
        HUMAN_WARRIOR_M01_WEAPON_STANCES_V07.variants[2],
        HUMAN_WARRIOR_M01_WEAPON_STANCES_V07.variants[3],
    ),
)


def load_weapon_stance_profile_v08(character_id: str) -> WeaponStanceProfileV05:
    profile = HUMAN_WARRIOR_M01_WEAPON_STANCES_V08
    if character_id != profile.character_id:
        raise KeyError(f"No weapon stance v08 profile for character_id={character_id}")
    if profile.revision != "v08" or profile.direction != "down":
        raise ValueError("Weapon stance v08 identity drifted")
    expected_ids = (
        "onehand_low",
        "onehand_ready",
        "twohand_center_low",
        "twohand_center_high",
    )
    if tuple(item.variant_id for item in profile.variants) != expected_ids:
        raise ValueError("Weapon stance v08 order drifted")
    if not 0.78 <= ONE_HAND_SIDE_X <= 0.92:
        raise ValueError("One-hand v08 sword must remain clearly lateral")
    if not 0.22 <= ONE_HAND_BEHIND_Y <= 0.38:
        raise ValueError("One-hand v08 sword must remain partly behind the hero")
    if not -0.70 <= ONE_HAND_DOWN_Z <= -0.54:
        raise ValueError("One-hand v08 sword must keep its tip downward")
    if ONE_HAND_SIDE_X <= ONE_HAND_BEHIND_Y * 2.0:
        raise ValueError("One-hand v08 must favor side visibility over depth")

    previous = HUMAN_WARRIOR_M01_WEAPON_STANCES_V07.variants
    for index, item in enumerate(profile.variants):
        if item.pose != previous[index].pose:
            raise ValueError(f"Variant {item.variant_id} changed the approved body pose")
        if index < 2:
            if not item.animation_id.endswith("_v08"):
                raise ValueError(f"Variant {item.variant_id} did not advance to v08")
            if item.weapon_id != "sword_01_onehand_side_back_v08":
                raise ValueError(f"Variant {item.variant_id} uses the wrong one-hand sword")
            if item.blade_tip != "down":
                raise ValueError(f"Variant {item.variant_id} must keep the blade tip down")
        else:
            if item != previous[index]:
                raise ValueError(f"Two-hand variant {item.variant_id} must remain exact v06")
    return profile
