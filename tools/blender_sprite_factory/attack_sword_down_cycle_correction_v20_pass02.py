from __future__ import annotations


CORRECTION_PASS = "v20_pass02"
ONEHAND_CONTAINMENT_REVISION = "minimal_rigid_inward_rotation_v20_pass02"
TARGET_ANIMATION_ID = "attack_sword_01_onehand_down_v20"
TARGET_FRAME = 6
ANGLE_SEARCH_LIMIT_DEGREES = 40
ANGLE_SEARCH_STEP_DEGREES = 2
MIN_CAMERA_MARGIN_PIXELS = 1.0
MIN_HEAD_CLEARANCE_PIXELS = 4.0


def validate_attack_sword_down_cycle_v20_pass02() -> None:
    if TARGET_FRAME != 6:
        raise ValueError("v20 pass02 must correct only the rebound frame")
    if ANGLE_SEARCH_LIMIT_DEGREES < 10 or ANGLE_SEARCH_LIMIT_DEGREES > 60:
        raise ValueError("v20 pass02 angle search limit is invalid")
    if ANGLE_SEARCH_STEP_DEGREES <= 0:
        raise ValueError("v20 pass02 angle search step must be positive")
    if MIN_CAMERA_MARGIN_PIXELS < 1.0:
        raise ValueError("v20 pass02 camera margin is weaker than the canvas contract")
    if MIN_HEAD_CLEARANCE_PIXELS < 4.0:
        raise ValueError("v20 pass02 head clearance is weaker than the locked contract")


validate_attack_sword_down_cycle_v20_pass02()
