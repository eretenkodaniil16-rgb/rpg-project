from __future__ import annotations


CORRECTION_PASS = "v21_pass36"
TWOHAND_UP_F02_BALANCED_REVIEW_REVISION = (
    "twohand_up_f02_minimax_continuity_diverse_review_v21_pass36"
)

TARGET_ACTION_ID = "attack_sword_01_twohand_up_v21"
TARGET_GRIP_ID = "twohand_center_high"
TARGET_DIRECTION = "up"
TARGET_FRAMES = (1, 2, 3)

TARGET_ABS_WEAPON_OFFSET_DEGREES = 24.0
USE_MINIMAX_CONTINUITY = True
PREFER_SOURCE_DEPTH_BRANCH = True
SELECT_UNIQUE_ARM_PROFILES_FIRST = True
REVIEW_VARIANT_COUNT = 6

SOURCE_REVIEW_RUN_ID = 30855228696
SOURCE_REVIEW_ARTIFACT_ID = 8872322456
SOURCE_REVIEW_ARTIFACT_SHA256 = (
    "8069f0e1a0df0fb5b039b73adc0025d075f24086f6ef053736d22eed19272957"
)
SOURCE_REVIEW_FINDING = (
    "pass35 validated rear-view zero-clearance weapon candidates but the "
    "weighted-sum ordering selected corrected_f01 blend 1.00 for all six "
    "variants, leaving a 25.385-degree RMS jump to original f03"
)
