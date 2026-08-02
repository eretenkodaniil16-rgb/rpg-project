from __future__ import annotations


CORRECTION_PASS = "v21_pass17"
TWOHAND_RIGHT_WINDUP_REVISION = "twohand_right_windup_arm_rotation_v21_pass17"
TWOHAND_RIGHT_ANTICIPATION_DIAGNOSTIC_REVISION = (
    "twohand_right_f03_deep_projection_source_search_v21_pass17"
)
TARGET_ACTION_ID = "attack_sword_01_twohand_right_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "right"
TARGET_BONES = (
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)

WINDUP_FRAME = 2
WINDUP_SOURCE_FRAME = 1
WINDUP_SELECTED_ARM_BLEND = 0.50
WINDUP_SELECTED_REQUESTED_SCREEN_PROJECTION = 0.95
WINDUP_SELECTED_WEAPON_OFFSET_DEGREES = -72.0
WINDUP_SELECTED_HEAD_CLEARANCE_PIXELS = 4.004
WINDUP_SELECTED_CAMERA_MARGIN_PIXELS = 20.957
WINDUP_SELECTED_ATTEMPT = 1053

TARGET_FRAME = 3
SOURCE_FRAME_CANDIDATES = (2, 4, 1, 5)
ARM_BLEND_CANDIDATES = (
    0.0,
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
SCREEN_PROJECTION_CANDIDATES = (
    0.55,
    0.50,
    0.45,
    0.40,
    0.35,
    0.30,
    0.25,
    0.20,
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
MIN_HEAD_CLEARANCE_PIXELS = 4.0
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True

DIAGNOSTIC_RUN_ID = 30751212090
DIAGNOSTIC_ARTIFACT_ID = 8834533057
DIAGNOSTIC_ARTIFACT_SHA256 = (
    "7fbbe32d0d9adeca91c83f245ebd2082aad3d9f390b8918a58f74a442dc1e446"
)
DIAGNOSTIC_FRAME_SIZE = (96, 96)
DIAGNOSTIC_ALPHA_BBOX = (32, 19, 74, 92)
DIAGNOSTIC_EDGE_ALPHA_COUNTS = {
    "left": 0,
    "right": 0,
    "top": 0,
    "bottom": 0,
}

SOURCE_FAILED_RUN_ID = 30750340736
SOURCE_FAILED_ARTIFACT_ID = 8834452523
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "9bca0735b70deaabad5c206524b6d5a551d6730c53b135a6c9bbebed055d038c"
)
SOURCE_FAILURE = (
    "pass15 validated approved down, full left, onehand_right f01-f08 and "
    "twohand_right f01; pass16 selected f02 but its f03 search never reduced "
    "projection because all requested projections exceeded the source"
)
