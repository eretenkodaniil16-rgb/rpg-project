from __future__ import annotations


CORRECTION_PASS = "v21_pass08"
TWOHAND_LEFT_PROJECTION_REVISION = (
    "twohand_left_windup_projection_planner_v21_pass08"
)
TARGET_ACTION_ID = "attack_sword_01_twohand_left_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "left"
TARGET_FRAME = 2
GUARD_FRAME = 1
TARGET_BONES = (
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)
ARM_BLEND_CANDIDATES = (0.10, 0.20, 0.30, 0.40, 0.50)
SCREEN_PROJECTION_CANDIDATES = (0.82, 0.78, 0.74, 0.70, 0.68)
ANGLE_OFFSET_CANDIDATES = (46.0, 50.0, 54.0, 58.0, 62.0)
MIN_HEAD_CLEARANCE_PIXELS = 4.0
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True
SOURCE_FAILED_RUN_ID = 30744357391
SOURCE_FAILED_ARTIFACT_ID = 8832432523
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "b7211593521ce8d396e646c0da8b4a7d9ffdbb8e7e13a6a848523707239cad37"
)
SOURCE_FAILURE = (
    "twohand_left/f02 paired-arm +46 degree candidates clear the head but "
    "the full-length blade touches the normalized top edge"
)
APPROVED_DOWN_PROJECTION_REFERENCE = 0.74
