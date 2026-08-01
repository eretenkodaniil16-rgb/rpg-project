from __future__ import annotations


CORRECTION_PASS = "v20_pass05"
ONEHAND_CONTAINMENT_REVISION = "active_v09_export_space_rotation_v20_pass05"
TARGET_ANIMATION_ID = "attack_sword_01_onehand_down_v20"
TARGET_FRAME = 6
ACTIVE_WEAPON_VARIANT_ID = "onehand_ready"
ACTIVE_WEAPON_SOURCE_REVISION = "v09"
ACTIVE_BLADE_OBJECT_NAME = "combat_onehand_ready_v09_blade"
ACTIVE_GRIP_OBJECT_NAME = "combat_onehand_ready_v09_grip"
ANGLE_SEARCH_LIMIT_DEGREES = 40
ANGLE_SEARCH_STEP_DEGREES = 2
MIN_HEAD_CLEARANCE_PIXELS = 4.0
REQUIRE_ZERO_EDGE_ALPHA = True
MISIDENTIFIED_WEAPON_SOURCE_REVISION = "v06"
DIAGNOSTIC_RUN_IDS = (30719707334, 30720688002, 30721581260)
DIAGNOSTIC_ARTIFACT_IDS = (8824576556, 8824976123, 8825098999)


def validate_attack_sword_down_cycle_v20_pass05() -> None:
    if TARGET_FRAME != 6:
        raise ValueError("v20 pass05 must correct only the rebound frame")
    if ACTIVE_WEAPON_SOURCE_REVISION != "v09":
        raise ValueError("v20 pass05 must target the visible down one-hand v09 module")
    if ACTIVE_BLADE_OBJECT_NAME == "combat_onehand_v06_blade":
        raise ValueError("v20 pass05 must not target the hidden v06 blade")
    if ACTIVE_GRIP_OBJECT_NAME == "combat_onehand_v06_grip":
        raise ValueError("v20 pass05 must not target the hidden v06 grip")
    if ANGLE_SEARCH_LIMIT_DEGREES < 10 or ANGLE_SEARCH_LIMIT_DEGREES > 60:
        raise ValueError("v20 pass05 angle search limit is invalid")
    if ANGLE_SEARCH_STEP_DEGREES <= 0:
        raise ValueError("v20 pass05 angle search step must be positive")
    if MIN_HEAD_CLEARANCE_PIXELS < 4.0:
        raise ValueError("v20 pass05 head clearance is weaker than the locked contract")
    if not REQUIRE_ZERO_EDGE_ALPHA:
        raise ValueError("v20 pass05 must preserve the zero-edge-alpha contract")
    if len(DIAGNOSTIC_RUN_IDS) != len(DIAGNOSTIC_ARTIFACT_IDS):
        raise ValueError("v20 pass05 diagnostic traceability is incomplete")


validate_attack_sword_down_cycle_v20_pass05()
