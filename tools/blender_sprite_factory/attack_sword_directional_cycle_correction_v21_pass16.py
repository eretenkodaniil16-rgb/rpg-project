from __future__ import annotations


CORRECTION_PASS = "v21_pass16"
TWOHAND_RIGHT_BATCH_DIAGNOSTIC_REVISION = (
    "twohand_right_f02_f08_batch_projection_v21_pass16"
)
TARGET_ACTION_ID = "attack_sword_01_twohand_right_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "right"
TARGET_FRAMES = (2, 3, 4, 5, 6, 7, 8)
SOURCE_FRAME_BY_TARGET = {
    2: 1,
    3: 2,
    4: 3,
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
ARM_BLEND_CANDIDATES = (0.0, 0.10, 0.20, 0.30, 0.40, 0.50)
SCREEN_PROJECTION_CANDIDATES = (
    0.95,
    0.90,
    0.86,
    0.82,
    0.78,
    0.74,
    0.70,
    0.66,
    0.62,
)
ANGLE_OFFSET_CANDIDATES = (
    0.0,
    -8.0,
    8.0,
    -16.0,
    16.0,
    -24.0,
    24.0,
    -32.0,
    32.0,
    -40.0,
    40.0,
    -48.0,
    48.0,
    -56.0,
    56.0,
    -64.0,
    64.0,
    -72.0,
    72.0,
    -80.0,
    80.0,
    -88.0,
    88.0,
)
MIN_HEAD_CLEARANCE_PIXELS_BY_FRAME = {
    2: 4.0,
    3: 4.0,
    4: 4.0,
    5: 1.0,
    6: 1.0,
    7: 1.0,
    8: 1.0,
}
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True

SOURCE_FAILED_RUN_ID = 30750340736
SOURCE_FAILED_ARTIFACT_ID = 8834452523
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "9bca0735b70deaabad5c206524b6d5a551d6730c53b135a6c9bbebed055d038c"
)
SOURCE_FAILURE = (
    "pass15 validated approved down, full left, onehand_right f01-f08, and "
    "twohand_right f01; no geometry-safe candidate for "
    "twohand_center_high/right/f02"
)
