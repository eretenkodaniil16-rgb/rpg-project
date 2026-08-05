from __future__ import annotations

CORRECTION_PASS = "v21_pass29"
TWOHAND_UP_F01_ARM_DIAGNOSTIC_REVISION = (
    "twohand_up_f01_coordinated_arm_depth_search_v21_pass29"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 1
TARGET_BONES = (
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
)

SOURCE_FRAME_CANDIDATES = (2, 8, 3, 7, 4, 6, 5)
ARM_BLEND_CANDIDATES = (
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
    0.575,
    0.55,
    0.50,
    0.45,
    0.40,
    0.35,
    0.30,
    0.25,
)
ANGLE_OFFSET_CANDIDATES = (
    0.0,
    -12.0,
    12.0,
    -24.0,
    24.0,
    -36.0,
    36.0,
    -48.0,
    48.0,
    -60.0,
    60.0,
    -72.0,
    72.0,
    -84.0,
    84.0,
    -96.0,
    96.0,
)
DEPTH_BRANCH_CANDIDATES = ("source", "flipped")

MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = 1.0
MIN_VISIBLE_BLADE_SAMPLES = 4
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True
MAX_RENDER_CANDIDATES_PER_ARM_POSE = 12

SOURCE_FAILED_RUN_ID = 30850308797
SOURCE_FAILED_ARTIFACT_ID = 8870383301
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "13cb490a9df2a4056ea664aae9e8a68aaa2147385eb033d0a271764c3d7c748e"
)
SOURCE_FAILURE = (
    "all 868 rigid weapon candidates for twohand_center_high/up/f01 had "
    "zero depth-aware visible-blade clearance or fewer than four visible "
    "blade samples with the unchanged two-hand arm pose"
)
