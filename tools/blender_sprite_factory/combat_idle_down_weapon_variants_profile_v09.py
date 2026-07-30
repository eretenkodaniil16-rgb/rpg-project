from __future__ import annotations

from dataclasses import replace

from combat_idle_down_weapon_variants_profile_v08 import (
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V08,
    WeaponStanceProfileV05,
)


ONE_HAND_SIDE_X = -0.82
ONE_HAND_BEHIND_Y = 0.32
ONE_HAND_DOWN_Z = -0.78


HUMAN_WARRIOR_M01_WEAPON_STANCES_V09 = replace(
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V08,
    revision="v09",
    variants=(
        replace(
            HUMAN_WARRIOR_M01_WEAPON_STANCES_V08.variants[0],
            display_name="Одноручная боковая низкая — клинок наружу и назад",
            animation_id="combat_idle_onehand_low_v09",
            weapon_id="sword_01_onehand_outward_back_v09",
        ),
        replace(
            HUMAN_WARRIOR_M01_WEAPON_STANCES_V08.variants[1],
            display_name="Одноручная боковая боевая — клинок наружу и назад",
            animation_id="combat_idle_onehand_ready_v09",
            weapon_id="sword_01_onehand_outward_back_v09",
        ),
        HUMAN_WARRIOR_M01_WEAPON_STANCES_V08.variants[2],
        HUMAN_WARRIOR_M01_WEAPON_STANCES_V08.variants[3],
    ),
)


def load_weapon_stance_profile_v09(character_id: str) -> WeaponStanceProfileV05:
    profile = HUMAN_WARRIOR_M01_WEAPON_STANCES_V09
    if character_id != profile.character_id:
        raise KeyError(f"No weapon stance v09 profile for character_id={character_id}")
    if profile.revision != "v09" or profile.direction != "down":
        raise ValueError("Weapon stance v09 identity drifted")
    expected_ids = (
        "onehand_low",
        "onehand_ready",
        "twohand_center_low",
        "twohand_center_high",
    )
    if tuple(item.variant_id for item in profile.variants) != expected_ids:
        raise ValueError("Weapon stance v09 order drifted")
    if not -0.90 <= ONE_HAND_SIDE_X <= -0.74:
        raise ValueError("One-hand v09 sword must leave the torso on the physical-right side")
    if not 0.24 <= ONE_HAND_BEHIND_Y <= 0.40:
        raise ValueError("One-hand v09 sword must remain partly behind the hero")
    if not -0.86 <= ONE_HAND_DOWN_Z <= -0.70:
        raise ValueError("One-hand v09 sword must keep a clear downward tip")
    if abs(ONE_HAND_SIDE_X) <= ONE_HAND_BEHIND_Y * 2.0:
        raise ValueError("One-hand v09 must favor outward side visibility over depth")

    previous = HUMAN_WARRIOR_M01_WEAPON_STANCES_V08.variants
    for index, item in enumerate(profile.variants):
        if item.pose != previous[index].pose:
            raise ValueError(f"Variant {item.variant_id} changed the approved body pose")
        if index < 2:
            if not item.animation_id.endswith("_v09"):
                raise ValueError(f"Variant {item.variant_id} did not advance to v09")
            if item.weapon_id != "sword_01_onehand_outward_back_v09":
                raise ValueError(f"Variant {item.variant_id} uses the wrong one-hand sword")
            if item.blade_tip != "down":
                raise ValueError(f"Variant {item.variant_id} must keep the blade tip down")
        else:
            if item != previous[index]:
                raise ValueError(f"Two-hand variant {item.variant_id} must remain exact v06")
    return profile
