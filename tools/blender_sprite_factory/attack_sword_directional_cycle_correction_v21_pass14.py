from __future__ import annotations


CORRECTION_PASS = "v21_pass14"
TWOHAND_LEFT_TAIL_DIAGNOSTIC_REVISION = (
    "twohand_left_followthrough_recovery_batch_projection_v21_pass14"
)
TARGET_ACTION_ID = "attack_sword_01_twohand_left_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "left"
TARGET_FRAMES = (5, 6, 7, 8)
SOURCE_FRAME_BY_TARGET = {
    5: 4,
    6: 5,
    7: 8,
    8: 1,
}
TARGET_BONES = (
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)
ARM_BLEND_CANDIDATES = (0.0, 0.10, 0.20, 0.30, 0.40)
SCREEN_PROJECTION_CANDIDATES = (
    0.95,
    0.90,
    0.86,
    0.82,
    0.78,
    0.74,
    0.70,
    0.66,
)
ANGLE_OFFSET_CANDIDATES = (
    0.0,
    8.0,
    -8.0,
    16.0,
    -16.0,
    24.0,
    -24.0,
    32.0,
    -32.0,
    40.0,
    -40.0,
    48.0,
    -48.0,
    56.0,
    -56.0,
    64.0,
    -64.0,
    72.0,
    -72.0,
    80.0,
    -80.0,
    88.0,
    -88.0,
)
MIN_HEAD_CLEARANCE_PIXELS = 1.0
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True

SOURCE_FAILED_RUN_ID = 30748869155
SOURCE_FAILED_ARTIFACT_ID = 8833935925
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "e3abbf704854eb4c24c60a1d4b086646019495609311d2d16c59d941607a1c50"
)
SOURCE_FAILURE = (
    "pass13 validated twohand_left f02-f04 and then found no geometry-safe "
    "candidate for twohand_center_high/left/f05"
)
