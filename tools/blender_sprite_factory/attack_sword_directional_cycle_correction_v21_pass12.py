from __future__ import annotations


CORRECTION_PASS = "v21_pass12"
TWOHAND_LEFT_CONTACT_REVISION = (
    "twohand_left_contact_from_anticipation_projection_v21_pass12"
)
TARGET_ACTION_ID = "attack_sword_01_twohand_left_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "left"
TARGET_FRAME = 4
SOURCE_FRAME = 3
TARGET_BONES = (
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)
ARM_BLEND_CANDIDATES = (0.00, 0.10, 0.20, 0.30, 0.40)
SCREEN_PROJECTION_CANDIDATES = (0.90, 0.86, 0.82, 0.78, 0.74, 0.70)
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
)
MIN_HEAD_CLEARANCE_PIXELS = 4.0
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True
SOURCE_FAILED_RUN_ID = 30747420266
SOURCE_FAILED_ARTIFACT_ID = 8833482546
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "61feb774840b3a8719685ae3a2a39f3df283fd9d82f6c1279985f10dad627fe0"
)
SOURCE_CONTEXT = "full pass09 stopped at f03 before f04 could be evaluated"
F03_REFERENCE_ARM_BLEND = 0.10
F03_REFERENCE_SCREEN_PROJECTION = 0.82
F03_REFERENCE_WEAPON_OFFSET_DEGREES = 64.0
