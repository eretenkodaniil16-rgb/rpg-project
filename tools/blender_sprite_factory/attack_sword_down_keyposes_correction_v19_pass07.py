from __future__ import annotations


CORRECTION_PASS = "v19_pass07"
TWOHAND_ANTICIPATION_REVISION = "clearance_planned_rigid_arc_v19_pass07"
WEAPON_SCREEN_PROJECTION_MAGNITUDE = 0.74
ANGLE_SEARCH_LIMIT_DEGREES = 80
ANGLE_SEARCH_STEP_DEGREES = 5
MIN_CAMERA_MARGIN_PIXELS = 1.0
TARGET_HEAD_CLEARANCE_PIXELS = 6.0


def validate_attack_sword_down_keyposes_v19_pass07() -> None:
    if not 0.68 <= WEAPON_SCREEN_PROJECTION_MAGNITUDE <= 0.82:
        raise ValueError("v19 pass07 projection magnitude is outside the safe range")
    if ANGLE_SEARCH_LIMIT_DEGREES < 30 or ANGLE_SEARCH_LIMIT_DEGREES > 90:
        raise ValueError("v19 pass07 angle search limit is invalid")
    if ANGLE_SEARCH_STEP_DEGREES <= 0:
        raise ValueError("v19 pass07 angle search step must be positive")
    if TARGET_HEAD_CLEARANCE_PIXELS < 4.0:
        raise ValueError("v19 pass07 target clearance is weaker than the locked contract")


validate_attack_sword_down_keyposes_v19_pass07()
