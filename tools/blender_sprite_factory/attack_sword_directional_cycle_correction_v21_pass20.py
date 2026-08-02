from __future__ import annotations


CORRECTION_PASS = "v21_pass20"
ONEHAND_UP_TAIL_DIAGNOSTIC_REVISION = (
    "onehand_up_f05_f08_sequential_projection_v21_pass20"
)
TARGET_ACTION_ID = "attack_sword_01_onehand_up_v21"
TARGET_GRIP_ID = "onehand_ready"
TARGET_DIRECTION = "up"
TARGET_FRAMES = (5, 6, 7, 8)
SOURCE_FRAME_BY_TARGET = {5: 4, 6: 5, 7: 8, 8: 1}
TARGET_BONES = (
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)
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
    0.95,
    0.90,
    0.86,
    0.82,
    0.78,
    0.74,
    0.70,
    0.66,
    0.62,
    0.58,
    0.54,
    0.50,
    0.46,
    0.42,
    0.38,
    0.34,
    0.30,
    0.26,
    0.22,
    0.18,
)
ANGLE_OFFSET_CANDIDATES = (
    0.0,
    -6.0,
    6.0,
    -12.0,
    12.0,
    -18.0,
    18.0,
    -24.0,
    24.0,
    -30.0,
    30.0,
    -36.0,
    36.0,
    -42.0,
    42.0,
    -48.0,
    48.0,
    -54.0,
    54.0,
    -60.0,
    60.0,
    -66.0,
    66.0,
    -72.0,
    72.0,
    -78.0,
    78.0,
    -84.0,
    84.0,
    -90.0,
    90.0,
)
MIN_HEAD_CLEARANCE_PIXELS = 1.0
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True

SOURCE_FAILED_RUN_ID = 30752258967
SOURCE_FAILED_ARTIFACT_ID = 8835097632
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "02a36c18e2f64d039dbb51bd00164618f4607420bf4217f8ef11be9249c7d927"
)
SOURCE_FAILURE = (
    "pass19 validated all down, left, right and onehand_up f01-f04; no "
    "geometry-safe candidate for onehand_ready/up/f05"
)
