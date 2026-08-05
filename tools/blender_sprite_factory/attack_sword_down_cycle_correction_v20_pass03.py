from __future__ import annotations


CORRECTION_PASS = "v20_pass03"
ONEHAND_CONTAINMENT_REVISION = "export_space_rigid_rotation_search_v20_pass03"
TARGET_ANIMATION_ID = "attack_sword_01_onehand_down_v20"
TARGET_FRAME = 6
ANGLE_SEARCH_LIMIT_DEGREES = 40
ANGLE_SEARCH_STEP_DEGREES = 2
MIN_HEAD_CLEARANCE_PIXELS = 4.0
REQUIRE_ZERO_EDGE_ALPHA = True


def validate_attack_sword_down_cycle_v20_pass03() -> None:
    if TARGET_FRAME != 6:
        raise ValueError("v20 pass03 must correct only the rebound frame")
    if ANGLE_SEARCH_LIMIT_DEGREES < 10 or ANGLE_SEARCH_LIMIT_DEGREES > 60:
        raise ValueError("v20 pass03 angle search limit is invalid")
    if ANGLE_SEARCH_STEP_DEGREES <= 0:
        raise ValueError("v20 pass03 angle search step must be positive")
    if MIN_HEAD_CLEARANCE_PIXELS < 4.0:
        raise ValueError("v20 pass03 head clearance is weaker than the locked contract")
    if not REQUIRE_ZERO_EDGE_ALPHA:
        raise ValueError("v20 pass03 must preserve the zero-edge-alpha contract")


validate_attack_sword_down_cycle_v20_pass03()
