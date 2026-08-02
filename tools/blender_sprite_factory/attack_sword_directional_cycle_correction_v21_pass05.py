from __future__ import annotations


CORRECTION_PASS = "v21_pass05"
RECOVERY_CLEARANCE_REVISION = (
    "left_onehand_recovery_arm_weapon_search_v21_pass05"
)
TARGET_ACTION_ID = "attack_sword_01_onehand_left_v21"
TARGET_GRIP_ID = "onehand_ready"
TARGET_DIRECTION = "left"
TARGET_FRAME = 7
GUARD_FRAME = 8
BLEND_CANDIDATES = (
    0.10,
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
    1.00,
)
ANGLE_SEARCH_LIMIT_DEGREES = 60
ANGLE_SEARCH_STEP_DEGREES = 2
MIN_HEAD_CLEARANCE_PIXELS = 1.0
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True
SOURCE_FAILED_RUN_ID = 30742565310
SOURCE_FAILED_ARTIFACT_ID = 8831822735
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "26f16b1fb04a2f412fee04d1bf5ed82c7c5592a1ae5a101f5293eb838135f1e6"
)
SOURCE_FAILURE = (
    "onehand_ready/left/f07 no safe arm-only recovery-to-guard blend"
)
