from __future__ import annotations


CORRECTION_PASS = "v19_pass06"
TWOHAND_ANTICIPATION_REVISION = "rigid_weapon_depth_projection_v19_pass06"
WEAPON_SCREEN_PROJECTION_MAGNITUDE = 0.82
MIN_WEAPON_SCREEN_PROJECTION_MAGNITUDE = 0.78
MAX_WEAPON_SCREEN_PROJECTION_MAGNITUDE = 0.86


def validate_attack_sword_down_keyposes_v19_pass06() -> None:
    if not (
        MIN_WEAPON_SCREEN_PROJECTION_MAGNITUDE
        <= WEAPON_SCREEN_PROJECTION_MAGNITUDE
        <= MAX_WEAPON_SCREEN_PROJECTION_MAGNITUDE
    ):
        raise ValueError("v19 pass06 weapon screen projection is outside the safe range")
    if WEAPON_SCREEN_PROJECTION_MAGNITUDE >= 1.0:
        raise ValueError("v19 pass06 does not foreshorten the weapon")


validate_attack_sword_down_keyposes_v19_pass06()
