from __future__ import annotations

from dataclasses import replace

from combat_idle_down_weapon_variants_profile_v05 import (
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V05,
    WeaponStanceProfileV05,
)


ONE_HAND_BLADE_LENGTH = 2.02
TWO_HAND_BLADE_LENGTH = 2.62
ONE_HAND_GRIP_LENGTH = 0.54
TWO_HAND_GRIP_LENGTH = 0.96
BLADE_TIP_LENGTH = 0.20
TWO_HAND_CENTER_X_OFFSET = 0.10
TWO_HAND_AWAY_Y = 0.14


HUMAN_WARRIOR_M01_WEAPON_STANCES_V06 = replace(
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V05,
    revision="v06",
    variants=tuple(
        replace(
            item,
            animation_id=item.animation_id.replace("_v05", "_v06"),
        )
        for item in HUMAN_WARRIOR_M01_WEAPON_STANCES_V05.variants
    ),
)


def load_weapon_stance_profile_v06(character_id: str) -> WeaponStanceProfileV05:
    profile = HUMAN_WARRIOR_M01_WEAPON_STANCES_V06
    if character_id != profile.character_id:
        raise KeyError(f"No weapon stance v06 profile for character_id={character_id}")
    if profile.revision != "v06" or profile.direction != "down":
        raise ValueError("Weapon stance v06 identity drifted")
    expected_ids = (
        "onehand_low",
        "onehand_ready",
        "twohand_center_low",
        "twohand_center_high",
    )
    if tuple(item.variant_id for item in profile.variants) != expected_ids:
        raise ValueError("Weapon stance v06 order drifted")
    if ONE_HAND_BLADE_LENGTH <= 1.82:
        raise ValueError("One-hand v06 blade must exceed v05 length")
    if TWO_HAND_BLADE_LENGTH <= 2.12:
        raise ValueError("Two-hand v06 blade must exceed v05 length")
    if TWO_HAND_BLADE_LENGTH <= ONE_HAND_BLADE_LENGTH:
        raise ValueError("Two-hand v06 blade must remain longest")
    if not 0.05 <= TWO_HAND_CENTER_X_OFFSET <= 0.15:
        raise ValueError("Two-hand sword must remain near the model center")
    if TWO_HAND_AWAY_Y <= 0.0:
        raise ValueError("Two-hand blade must angle away from the face")
    for item in profile.variants:
        if not item.animation_id.endswith("_v06"):
            raise ValueError(f"Variant {item.variant_id} animation revision drifted")
        if item.grip_mode == "one_handed":
            if item.blade_tip != "down" or item.pose.upper_arm_left_z_degrees < 26.0:
                raise ValueError(f"Variant {item.variant_id} must keep the free arm away")
        elif item.grip_mode == "two_handed":
            if item.blade_tip != "up":
                raise ValueError(f"Variant {item.variant_id} must point upward")
        else:
            raise ValueError(f"Unknown grip mode: {item.grip_mode}")
    return profile
