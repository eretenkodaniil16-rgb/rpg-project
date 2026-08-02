from __future__ import annotations


CORRECTION_PASS = "v21_pass07"
TWOHAND_LEFT_ARM_REVISION = (
    "twohand_left_windup_to_guard_arm_blend_v21_pass07"
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
WEAPON_OFFSET_CANDIDATES = tuple(
    float(value) for value in range(46, 91, 2)
)
MIN_HEAD_CLEARANCE_PIXELS = 4.0
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True
SOURCE_FAILED_RUN_ID = 30744357391
SOURCE_FAILED_ARTIFACT_ID = 8832432523
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "b7211593521ce8d396e646c0da8b4a7d9ffdbb8e7e13a6a848523707239cad37"
)
SOURCE_FAILURE = (
    "twohand_left/f02 paired-arm diagnostic tested only +46 degrees; "
    "all arm blends cleared the head but retained 5-6 top-edge alpha pixels"
)
SOURCE_OFFSET_DEGREES = 46.0
SOURCE_CLEARANCE_RANGE_PIXELS = (6.20766064009847, 8.021915709971294)
SOURCE_CAMERA_MARGIN_RANGE_PIXELS = (2.7516231536865234, 11.714046478271484)
SOURCE_TOP_EDGE_ALPHA_RANGE = (5, 6)
