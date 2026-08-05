from __future__ import annotations

CORRECTION_PASS = "v21_pass34"
TWOHAND_UP_F02_CONTINUITY_REVIEW_REVISION = (
    "twohand_up_f02_corrected_f01_to_f03_continuity_review_v21_pass34"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAME = 2
NEXT_REFERENCE_FRAME = 3

CORRECTED_F01_FRAME = 1
CORRECTED_F01_SOURCE_FRAME = 5
CORRECTED_F01_ARM_BLEND = 0.60
CORRECTED_F01_DEPTH_BRANCH = "source"
CORRECTED_F01_WEAPON_OFFSET_DEGREES = 0.0
CORRECTED_F01_SCREEN_PROJECTION = 0.30

SOURCE_POSE_CODES = (
    101,
    3,
    5,
    4,
    6,
    7,
    8,
)
SOURCE_POSE_LABELS = {
    101: "corrected_f01",
    3: "original_f03",
    5: "original_f05",
    4: "original_f04",
    6: "original_f06",
    7: "original_f07",
    8: "original_f08",
}
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
MAX_ABS_WEAPON_OFFSET_DEGREES = 48.0
TARGET_ABS_WEAPON_OFFSET_DEGREES = 24.0
REVIEW_VARIANT_COUNT = 6

MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = 1.0
MIN_VISIBLE_BLADE_SAMPLES = 4
MIN_CAMERA_MARGIN_PIXELS = 1.0
REQUIRE_ZERO_EDGE_ALPHA = True

CONTINUITY_WEIGHT_FROM_CORRECTED_F01 = 1.0
CONTINUITY_WEIGHT_TO_ORIGINAL_F03 = 0.75

SOURCE_FAILED_RUN_ID = 30854097806
SOURCE_FAILED_ARTIFACT_ID = 8871808585
SOURCE_FAILED_ARTIFACT_SHA256 = (
    "0dd847a9879aa1c88c813be7e0481e22ce1a96e8e002126ae9a056319692a682"
)
SOURCE_FAILURE = (
    "selected central f01 rendered successfully, then the base planner found "
    "no geometry-safe candidate for twohand_center_high/up/f02"
)
